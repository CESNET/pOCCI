OCCI Compliance tests
=======================

Install::

 python setup.py install

Set parameters in ~/.pOCCI.cfg.

Example config file::

 [main]
 url = 'https://example.com:11443'
 authtype = 'basic'
 ignoressl = True
 user = 'rocci'
 passwd = 'good-password'
 mimetype = 'text/plain'
 curlverbose = False
 #outputformat = 'plain'
 outputformat = 'json'

Run pOCCI
