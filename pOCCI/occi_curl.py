from occi_libs import occi_config

import pycurl
from StringIO import StringIO
import re

# Helper callback function
header = []
def get_header(buff):
	global header
	header.append(buff)

def occi_curl(base_url = occi_config['url'], url = '/-/', authtype = occi_config['authtype'], ignoressl = occi_config['ignoressl'], user = occi_config['user'], passwd = occi_config['passwd'], mimetype = occi_config['mimetype'], curlverbose = occi_config['curlverbose'], headers = []):
    buffer = StringIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, str(base_url + url))
    curl.setopt(pycurl.WRITEDATA, buffer)
    
    # Disable check of SSL certificate
    if ignoressl:
        curl.setopt(pycurl.SSL_VERIFYPEER, 0)   
        curl.setopt(pycurl.SSL_VERIFYHOST, 0)
    
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


#print occi_curl()[1]

# stahuje, parsujeme json, potrebujeme regexp


#print(body)

#for item in headerr:
#	if re.match(r'Content-Type:', item): print item
#	if re.match(r'Status:', item): print item
#

#print(headerr)
