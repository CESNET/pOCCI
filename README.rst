OCCI Compliance tests
=======================

|build-status| |coverage-status|

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
 connectiontimeout = 60
 timeout = 120

Run pOCCI

.. |build-status| image:: https://travis-ci.org/CESNET/pOCCI.svg?branch=master
   :target: https://travis-ci.org/CESNET/pOOCI
   :alt: Build status
.. |coverage-status| image:: https://img.shields.io/coveralls/CESNET/pOCCI.svg
   :target: https://coveralls.io/r/CESNET/pOCCI
   :alt: Test coverage percentage
