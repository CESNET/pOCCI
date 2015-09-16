|build-status| |coverage-status|

.. |build-status| image:: https://travis-ci.org/CESNET/pOCCI.svg?branch=master
   :target: https://travis-ci.org/CESNET/pOOCI
   :alt: Build status
.. |coverage-status| image:: https://img.shields.io/coveralls/CESNET/pOCCI.svg
   :target: https://coveralls.io/r/CESNET/pOCCI
   :alt: Test coverage percentage

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
 user = 'oneadmin'
 passwd = 'good-password'
 mimetype = 'text/plain'
 curlverbose = False
 #outputformat = 'plain'
 outputformat = 'json'
 connectiontimeout = 60
 timeout = 120
 occi.tests.entity = {'occi.core.title': 'My Machine'}

Launch tests::

 pOCCI

See manual page for all options.

OCCI Messages parser
====================

Example::

 echo 'Category: entity;scheme="http://schemas.ogf.org/occi/core#";class="kind"' | pOCCI-parse

 curl -u $user:$password -H 'Accept: text/plain' https://occi.example.com:11443/-/ | pOCCI-parse
 curl -u $user:$password -H 'Accept: text/plain' https://occi.example.com:11443/compute/ | pOCCI-parse -t entities -o text/occi
