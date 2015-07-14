from occi_libs import occi_config

import pycurl
from StringIO import StringIO
import re
import urllib

# Helper callback function
header = []
def get_header(buff):
	global header
	header.append(buff)


def occi_curl(base_url = occi_config['url'], url = '/-/', authtype = occi_config['authtype'], ignoressl = occi_config['ignoressl'], user = occi_config['user'], passwd = occi_config['passwd'], mimetype = occi_config['mimetype'], curlverbose = occi_config['curlverbose'], headers = [], post = ''):
    buffer = StringIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, str(base_url + url))
    curl.setopt(pycurl.WRITEDATA, buffer)
    
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
    
    # Set appropriate mime type
    curl.setopt(pycurl.HTTPHEADER, ['Accept: %s' % mimetype])
    
    # Verbose mode
    curl.setopt(pycurl.VERBOSE, curlverbose)

    curl.setopt(pycurl.CONNECTTIMEOUT, occi_config['connectiontimeout'])
    curl.setopt(pycurl.TIMEOUT, occi_config['timeout'])

    # Set requested HTTP headers
    if headers:
        curl.setopt(pycurl.HTTPHEADER, headers)

    # HTTP header response
    curl.setopt(pycurl.HEADERFUNCTION, get_header)

    if post:
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.POSTFIELDS, post)
        if curlverbose:
            print "==== POST ==== "
            print post
            print "============== "

    # DO IT!
    curl.perform()
    curl.close()

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
    content_type = re.split(';', h['Content-Type'])[0]

    return [buffer.getvalue().splitlines(), header, http_status, content_type]
