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
    """Transport base class. Curl is used, keystone authentication supported.

    Available methods: delete(), get(), post(), put().
    """

    reEncoding = re.compile(r';\s*charset=(\S+)')
    reHeader = re.compile(r'([^:]*)\s*:\s*(.*)')
    reStatus = re.compile(r'^HTTP')

    def dprint(self, s):
        if self.verbose:
            print '[pOCCI.curl] %s' % s


    def __init__(self, config):
        self.auth = {}
        self.authtype = config['authtype']
        self.config = config
        self.retry = False
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
        self.retry = False

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


    def auth_keystone(self, url, tenants=True):
        if not url.endswith('/'):
            url += '/'
        self.auth['url'] = url
        self.dprint('Keystone URL: %s' % self.auth['url'])

        version = 'v2.0'
        url += version

        if self.authtype == 'basic':
            user = self.config['user']
            password = ''
            if 'passwd' in self.config:
                password = self.config['passwd']
            body = {
                'auth': {
                    'passwordCredentials': {
                        'username': user,
                        'password': password,
                    },
                },
            }
        elif self.authtype == 'x509':
            body = {
                'auth': {
                    'voms': True,
                },
            }
            if 'keystone' in self.config:
                body['auth']['tenantName'] = self.config['keystone']

        curl = self.curl

        self.clean()
        self.retry = True
        curl.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json'])
        curl.setopt(pycurl.URL, url + '/tokens')
        curl.setopt(pycurl.POST, 1)
        body = json.dumps(body, indent=4)
        curl.setopt(pycurl.POSTFIELDS, body)
        self.dprint('Keystone sending: %s' % body)

        body, header_list, http_status, content_type, header = self.perform()
        if self.verbose:
            self.dprint('Keystone result: %s' % http_status)
            #self.dprint('  headers: ' + str(header))
            #self.dprint('  body: ' + body)
        if re.match(r'200 OK', http_status) is not None:
            raise occi.TransportError('Keystone failed: %s' % http_status)

        keystone = json.loads(body)
        if 'access' not in keystone or 'token' not in keystone['access'] or 'id' not in keystone['access']['token']:
            raise occi.TransportError("Can't get keystone token from: %s" % body)
        self.auth['token'] = keystone['access']['token']['id']

        if tenants and 'tenants' not in self.auth:
            # request tenants, if not already in the response
            if 'tenant' not in keystone['access']['token']:
                self.clean()
                self.retry = True
                curl.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json', 'X-Auth-Token: %s' % self.auth['token']])
                curl.setopt(pycurl.URL, url + '/tenants')

                self.dprint('Keystone exploring tenants')
                body, header_list, http_status, content_type, header = self.perform()
                #self.dprint('  ==> body: %s' % body)
                tenants = json.loads(body)
                #self.dprint('  ==> json: %s' % tenants['tenants'])
                self.auth['tenants'] = tenants['tenants']
            else:
                self.auth['tenants'] = [keystone['access']['token']['tenant']]

            self.auth['tenants_list'] = []
            for t in self.auth['tenants']:
                if 'enabled' not in t or t['enabled']:
                    self.auth['tenants_list'] += [t['name']]
            self.dprint('  ==> tenants: %s' % ','.join(self.auth['tenants_list']))


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

        # Keystone
        if 'token' in self.auth:
            headers = ['X-Auth-Token: %s' % self.auth['token']] + headers

        # Set appropriate mime type
        if mimetype:
            headers = ['Accept: %s' % mimetype] + headers
        else:
            headers = ['Accept: */*'] + headers

        # Set requested HTTP headers
        if headers:
            curl.setopt(pycurl.HTTPHEADER, headers)

        body, header_list, http_status, content_type, header = self.perform()
        self.dprint('First request status: %s' % http_status)

        if re.match(r'HTTP/.* 401 .*', http_status) and 'www-authenticate' in header:
            self.dprint('WWW-Authenticate extension detected')
            m = re.match(r'Keystone uri=\'([^\']*)\'', header['www-authenticate'])
            if m and m.group(1):
                self.dprint('Keystone detected')
                self.auth_keystone(url=m.group(1))
            return [None, None, http_status, content_type]
        else:
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
        l = self.request(url=url, mimetype=mimetype, headers=headers)

        if self.retry:
            self.dprint('repeating the DELETE request...')
            self.clean()
            curl.setopt(pycurl.CUSTOMREQUEST, 'DELETE')
            l = self.request(url=url, mimetype=mimetype, headers=headers)

        return l


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
        l = self.request(url=url, mimetype=mimetype, headers=headers)

        if self.retry:
            self.dprint('repeating the GET request...')
            self.clean()
            l = self.request(url=url, mimetype=mimetype, headers=headers)

        return l


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
        l = self.request(url=url, mimetype=mimetype, headers=headers)

        if self.retry:
            self.dprint('repeating the POST request...')
            self.clean()
            curl.setopt(pycurl.POST, 1)
            curl.setopt(pycurl.POSTFIELDS, body)
            l = self.request(url=url, mimetype=mimetype, headers=headers)

        return l


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
        l = self.request(url=url, mimetype=mimetype, headers=headers)

        if self.retry:
            self.dprint('repeating the PUT request...')
            self.clean()
            curl.setopt(pycurl.CUSTOMREQUEST, 'PUT')
            curl.setopt(pycurl.POST, 1)
            curl.setopt(pycurl.POSTFIELDS, body)
            l = self.request(url=url, mimetype=mimetype, headers=headers)

        return l
