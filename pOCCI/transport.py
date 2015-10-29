import json
import pycurl
import re
import sys
if sys.version_info >= (3,):
    from StringIO import BytesIO
else:
    from StringIO import StringIO

import occi


# for curl helper callback function
header = []


def get_header2(buff):
    global header
    header.append(buff)


def get_header3(buff):
    global header
    header.append(buff.decode('iso-8859-1'))


class Transport:
    """Transport base class. Curl is used.

    Available methods: delete(), get(), post(), put().
    """

    reEncoding = re.compile(r';\s*charset=(\S+)')
    reHeader = re.compile(r'([^:]*)\s*:\s*(.*)')
    reStatus = re.compile(r'^HTTP')

    def dprint(self, s):
        if self.verbose:
            print '[pOCCI.curl] %s' % s


    def __init__(self, config):
        self.authtype = config['authtype']
        self.config = config
        self.verbose = False
        if 'curlverbose' in config:
            self.verbose = config['curlverbose']

        if self.authtype == 'basic':
            if 'user' not in config:
                raise occi.TransportError('User and password is required for "basic" authentication')
        elif self.authtype == 'x509':
            if 'cert' not in config:
                raise occi.TransportError('SSL certificate and key is required for "x509" authentication')

        self.curl = pycurl.Curl()
        curl = self.curl
        curl.setopt(pycurl.VERBOSE, self.verbose)
        if 'connectiontimeout' in config:
            curl.setopt(pycurl.CONNECTTIMEOUT, config['connectiontimeout'])
        if 'timeout' in config:
            curl.setopt(pycurl.TIMEOUT, config['timeout'])

        if 'capath' in config and config['capath']:
            curl.setopt(pycurl.CAPATH, config['capath'])
        if 'cachain' in config and config['cachain']:
            curl.setopt(pycurl.CAINFO, config['cachain'])

        # Disable check of SSL certificate
        if 'ignoressl' in config and config['ignoressl']:
            curl.setopt(pycurl.SSL_VERIFYPEER, 0)
            curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        self.dprint('authtype: %s' % self.authtype)
        if self.authtype == 'basic':
            user = self.config['user']
            password = ''
            if 'passwd' in self.config:
                password = self.config['passwd']
            curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_BASIC)
            curl.setopt(pycurl.USERPWD, '%s:%s' % (user, password))
            self.dprint('user: %s' % user)
        elif self.authtype == 'x509':
            if 'cert' in config and config['cert']:
                curl.setopt(pycurl.SSLCERT, config['cert'])
                self.dprint('cert: %s' % config['cert'])
            if 'key' in config and config['key']:
                curl.setopt(pycurl.SSLKEY, config['key'])
                self.dprint('key: %s' % config['key'])
            if 'passphrase' in config and config['passphrase']:
                curl.setopt(pycurl.SSLCERTPASSWD, config['passphrase'])

        # HTTP header response
        if sys.version_info >= (3,):
            curl.setopt(pycurl.HEADERFUNCTION, get_header3)
        else:
            curl.setopt(pycurl.HEADERFUNCTION, get_header2)


    def clean(self):
        curl = self.curl
        curl.unsetopt(pycurl.CUSTOMREQUEST)
        curl.setopt(pycurl.HTTPHEADER, [])
        curl.setopt(pycurl.POST, False)


    def perform(self):
        global header

        curl = self.curl

        if sys.version_info >= (3,):
            buffer = BytesIO()
        else:
            buffer = StringIO()
        curl.setopt(pycurl.WRITEFUNCTION, buffer.write)

        header = []
        try:
            curl.perform()
        except pycurl.error as pe:
            raise occi.TransportError(pe)

        ## 'Server: Apache/2.2.22 (Debian)\r\n'
        h = {}
        http_status = None
        for item in header:
            m = Transport.reHeader.match(item.rstrip())
            if m and m.groups >= 2:
                key = m.group(1)
                value = m.group(2)
                h[key.lower()] = value
            else:
                if Transport.reStatus.match(item):
                    http_status = item.rstrip()
        content_type = None
        if 'content-type' in h:
            content_type = re.split(';', h['content-type'])[0]

        body = buffer.getvalue()
        buffer.close()
        if sys.version_info >= (3,):
            encoding = 'iso-8859-1'
            if content_type:
                match = Transport.reEncoding.search(h['content-type'])
                if match:
                    encoding = match.group(1)
            body = body.decode(encoding)

        return [body, header, http_status, content_type, h]


    def request(self, url=None, mimetype=None, headers=[]):
        if url is None:
            url = self.config['url']
            if not url.endswith('/'):
                url += '/'
            url += '-/'

        if mimetype is None and 'mimetype' in self.config:
            mimetype = self.config['mimetype']

        curl = self.curl

        curl.setopt(pycurl.URL, url)

        # Set appropriate mime type
        if mimetype:
            headers = ['Accept: %s' % mimetype] + headers
        else:
            headers = ['Accept: */*'] + headers

        # Set requested HTTP headers
        if headers:
            curl.setopt(pycurl.HTTPHEADER, headers)

        body, header_list, http_status, content_type, header = self.perform()

        return [body.splitlines(), header_list, http_status, content_type]


    def delete(self, url=None, mimetype=None, headers=[]):
        """Send HTTP DELETE request

        :param string base_url: OCCI server URL (default: from config)
        :param string url: URL
        :param string mimetype: accepted mimetype (empty string='\*/\*')
        :param string headers[]: HTTP Headers

        :return: [body, header, HTTP status, content type]
        :rtype: [string[], string[], string, string]
        """
        self.clean()

        curl = self.curl
        curl.setopt(pycurl.CUSTOMREQUEST, 'DELETE')
        return self.request(url=url, mimetype=mimetype, headers=headers)


    def get(self, url=None, mimetype=None, headers=[]):
        """Send HTTP GET request

        :param string base_url: OCCI server URL (default: from config)
        :param string url: URL
        :param string mimetype: accepted mimetype (empty string='\*/\*')
        :param string headers[]: HTTP Headers

        :return: [body, header, HTTP status, content type]
        :rtype: [string[], string[], string, string]
        """
        self.clean()
        return self.request(url=url, mimetype=mimetype, headers=headers)


    def post(self, url=None, mimetype=None, headers=[], body='OK'):
        """Send HTTP POST request

        :param string base_url: OCCI server URL (default: from config)
        :param string url: URL
        :param string mimetype: accepted mimetype (empty string='\*/\*')
        :param string headers[]: HTTP Headers
        :param string post: HTTP Body

        :return: [body, header, HTTP status, content type]
        :rtype: [string[], string[], string, string]
        """
        self.clean()

        curl = self.curl
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.POSTFIELDS, body)
        if self.verbose:
            print "[pOCCI.curl] ==== POST ===="
            print body
            print "[pOCCI.curl] =============="
        return self.request(url=url, mimetype=mimetype, headers=headers)


    def put(self, url=None, mimetype=None, headers=[], body='OK'):
        """Send HTTP POST request

        :param string base_url: OCCI server URL (default: from config)
        :param string url: URL
        :param string mimetype: accepted mimetype (empty string='\*/\*')
        :param string headers[]: HTTP Headers
        :param string post: HTTP Body

        :return: [body, header, HTTP status, content type]
        :rtype: [string[], string[], string, string]
        """

        self.clean()

        curl = self.curl
        curl.setopt(pycurl.CUSTOMREQUEST, 'PUT')
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.POSTFIELDS, body)
        if self.verbose:
            print "[pOCCI.curl] ==== PUT ===="
            print body
            print "[pOCCI.curl] ============="
        return self.request(url=url, mimetype=mimetype, headers=headers)
