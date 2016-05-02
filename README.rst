|build-status| |coverage-status|

.. |build-status| image:: https://travis-ci.org/CESNET/pOCCI.svg?branch=master
   :target: https://travis-ci.org/CESNET/pOOCI
   :alt: Build status
.. |coverage-status| image:: https://img.shields.io/coveralls/CESNET/pOCCI.svg
   :target: https://coveralls.io/r/CESNET/pOCCI
   :alt: Test coverage percentage

OCCI Compliance tests
=======================

pOCCI is OCCI standard compliance testing tool. Tests are described `here <http://www.etsi.org/deliver/etsi_ts/103100_103199/103142/01.01.01_60/ts_103142v010101p.pdf>`_.

Features
--------

Basic features:

- OCCI testing
- OCCI messages parsing
- partial OCCI client library for python

Authentization:

- basic auth
- X509
- keystone

Cloud providers:

- dummy (rOCCI server)
- OpenNebula
- Amazon EC2
- OpenStack

Installation
------------

From sources::

 git clone https://github.com/CESNET/pOCCI/ && cd pOCCI
 python setup.py install

From pypi::

 pip install pOCCI

Usage
-----

**OCCI compliance tests**:

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

**OCCI message parser**

Example::

 echo 'Category: entity;scheme="http://schemas.ogf.org/occi/core#";class="kind"' | pOCCI-parse

 curl -u $user:$password -H 'Accept: text/plain' https://occi.example.com:11443/-/ | pOCCI-parse
 curl -u $user:$password -H 'Accept: text/plain' https://occi.example.com:11443/compute/ | pOCCI-parse -t entities -o text/occi
