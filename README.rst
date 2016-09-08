|build-status| |coverage-status|

.. |build-status| image:: https://travis-ci.org/CESNET/pOCCI.svg?branch=master
   :target: https://travis-ci.org/CESNET/pOOCI
   :alt: Build status
.. |coverage-status| image:: https://img.shields.io/coveralls/CESNET/pOCCI.svg
   :target: https://coveralls.io/r/CESNET/pOCCI
   :alt: Test coverage percentage

pOCCI—OCCI Compliance Test Suite
===================================

Introduction
------------

The European Telecommunication Standards Institute (ETSI) describes a set of tests to verify the compliance of cloud management frameworks with OCCI or CDMI protocols. The title of the document is `CLOUD; Test Descriptions for Cloud Interoperability <http://www.etsi.org/deliver/etsi_ts/103100_103199/103142/01.01.01_60/ts_103142v010101p.pdf>`_.

The pOCCI test suite implements a real-world subset of tests described in the document. In essence, each test that can be carried out with real-world resources (Compute, Storage, Network) is implemented. Tests for abstract OCCI concepts that have no real-world counterpart (such as an OCCI Resource) are omitted because no real-world Cloud Management Framework can be asked to create a "Resource".

The test suite runs against an existing, OCCI-enabled cloud service and produces a compliance report, detailing tests passed or failed.

The pOCCI test suite is intended for the following user groups, ordered by importance (meaning 1 is the main audience while 3 is a group that might be interested but not primarily targeted):

1. Developers of OCCI-compliant services for compliance testing, ideally to be used as a part of their continuous integration process. For their purpose, pOCCI may be used either as a client against a remote service but it may also be used in a local mode just to validate OCCI messages for compliance with the standard.
2. Administrators (integrators) of cloud service sites with OCCI interfaces. Note that in this scenario, pOCCI is intended mainly for *preliminary* testing while the site is being set up. It may be potentially destructive to virtual resources already created in the cloud site.
3. Prospective user groups that use OCCI-compliant clients and wish to verify OCCI compliance of the server side.

Features
--------

Basic features:

- OCCI testing
- OCCI messages parsing
- partial OCCI client library for python

Authentication:

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

From `INDIGO Repository <http://repo.indigo-datacloud.eu/#one>`_::

 yum install python2-pOCCI
 # OR
 apt-get install python-pocci

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
