# Load variables from my_config.py
import my_config

import pycurl
from StringIO import StringIO

# Helper callback function
header = []
def get_header(buff):
	global header
	header.append(buff)

def occi_curl(url = my_config.url, authtype = my_config.authtype, ignoressl = my_config.ignoressl, user = my_config.user, passwd = my_config.passwd, mimetype =my_config.mimetype, curlverbose = my_config.curlverbose, headers = {}):
    buffer = StringIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, str(url))
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

    # Set requested HTTP headers
    request_headers = []
    if headers:
        for key in headers:
            request_headers.append('%s: %s' % (key, headers[key]))
        curl.setopt(pycurl.HTTPHEADER, request_headers)

    # HTTP header response
    curl.setopt(pycurl.HEADERFUNCTION, get_header)
   
    # DO IT!
    curl.perform()
    curl.close()

    return [buffer.getvalue().splitlines(), header]


#print occi_curl()[1]

# stahuje, parsujeme json, potrebujeme regexp


#print(body)

#for item in headerr:
#	if re.match(r'Content-Type:', item): print item
#	if re.match(r'Status:', item): print item
#

#print(headerr)
