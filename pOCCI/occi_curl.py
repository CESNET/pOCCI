from occi_libs import occi_config
import occi

import pycurl
import re
import sys
import urllib
if sys.version_info >= (3,):
    from StringIO import BytesIO
else:
    from StringIO import StringIO

# Helper callback function
header = []
def get_header2(buff):
	global header
	header.append(buff)
def get_header3(buff):
	global header
	header.append(buff.decode('iso-8859-1'))


def occi_curl(base_url = None, url = '/-/', authtype = None, ignoressl = None, user = None, passwd = None, mimetype = None, headers = [], post = '', custom_request = ''):
    """Send HTTP request

    :param string base_url: OCCI server URL (default: from config)
    :param string url: path element of the URL
    :param string authtype: authentication type (default: from config)
    :param bool ignoressl: ignore SSL problems (default: from config)
    :param string user: user name for 'basic' auth (default: from config)
    :param string passwd: password for 'basic' auth (default: from config)
    :param string mimetype: accepted mimetype (empty string = '\*/\*')
    :param string headers[]: HTTP Headers
    :param string post: HTTP Body
    :param string custom_request: HTTP Request type (default: 'GET' or 'POST')

    :return: [body, header, HTTP status, content type]
    :rtype: [string[], string[], string, string]
    """
    global header

    if base_url == None:
        base_url = occi_config['url']
    if authtype == None:
        authtype = occi_config['authtype']
    if ignoressl == None:
        ignoressl = occi_config['ignoressl']
    if user == None:
        user = occi_config['user']
    if passwd == None:
        passwd = occi_config['passwd']
    if mimetype == None:
        mimetype = occi_config['mimetype']
    curlverbose = occi_config['curlverbose']

    if sys.version_info >= (3,):
        buffer = BytesIO()
    else:
        buffer = StringIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, str(base_url + url))
    curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
    
    # Disable check of SSL certificate
    if ignoressl:
        curl.setopt(pycurl.SSL_VERIFYPEER, 0)   
        curl.setopt(pycurl.SSL_VERIFYHOST, 0)

    if 'capath' in occi_config and occi_config['capath']:
        curl.setopt(pycurl.CAPATH, occi_config['capath'])
    
    if 'cachain' in occi_config and occi_config['cachain']:
        curl.setopt(pycurl.CAINFO, occi_config['cachain'])

    # Name and password for basic auth (ONLY SUPPORTED YET)
    if authtype == "basic":
        curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_BASIC)
        curl.setopt(pycurl.USERPWD, "%s:%s" % (user, passwd))
    elif authtype == "x509":
        if 'cert' in occi_config and occi_config['cert']:
            curl.setopt(pycurl.SSLCERT, occi_config['cert'])
        if 'key' in occi_config and occi_config['key']:
            curl.setopt(pycurl.SSLKEY, occi_config['key'])
        if 'passphrase' in occi_config and occi_config['passphrase']:
            curl.setopt(pycurl.SSLCERTPASSWD, occi_config['passphrase'])
    
    # Verbose mode
    curl.setopt(pycurl.VERBOSE, curlverbose)

    curl.setopt(pycurl.CONNECTTIMEOUT, occi_config['connectiontimeout'])
    curl.setopt(pycurl.TIMEOUT, occi_config['timeout'])

    # Set appropriate mime type
    if mimetype:
        headers = ['Accept: %s' % mimetype] + headers
    else:
        headers = ['Accept: */*'] + headers

    # Set requested HTTP headers
    if headers:
        curl.setopt(pycurl.HTTPHEADER, headers)

    # HTTP header response
    if sys.version_info >= (3,):
        curl.setopt(pycurl.HEADERFUNCTION, get_header3)
    else:
        curl.setopt(pycurl.HEADERFUNCTION, get_header2)

    if post or custom_request == 'POST':
        curl.setopt(pycurl.POST, 1)
        if post:
            curl.setopt(pycurl.POSTFIELDS, post)
        else:
            curl.setopt(pycurl.POSTFIELDS, 'OK')
        if curlverbose:
            print "==== POST ==== "
            print post
            print "============== "

    if custom_request and custom_request != 'POST':
        curl.setopt(pycurl.CUSTOMREQUEST, custom_request)

    # DO IT!
    header = []
    try:
        curl.perform()
        curl.close()
    except pycurl.error as pe:
        raise occi.Error(pe)

    ## 'Server: Apache/2.2.22 (Debian)\r\n'
    h = {}
    for item in header:
        if re.match(r'.*:.*', item):
            key=re.sub(r':.*', r'', item.rstrip())
            value=re.sub(r'([^:]*):\s*(.*)', r'\2', item.rstrip())

            h[key] = value
        else:
            if re.match(r'^HTTP', item):
                http_status = item.rstrip()
    content_type = None
    if 'Content-Type' in h:
        content_type = re.split(';', h['Content-Type'])[0]

    body = buffer.getvalue()
    if sys.version_info >= (3,):
        encoding = 'iso-8859-1'
        if content_type:
            match = re.search(r';\s*charset=(\S+)', h['Content-Type'])
            if match:
                encoding = match.group(1)
        body = body.decode(encoding)

    return [body.splitlines(), header, http_status, content_type]
