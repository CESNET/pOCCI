Python versions
===============

Both Python 2 and Python 3 should work.

pOCCI is primary developed in Python 2. For Python 3 sources are converted by 2to3 tool.


Source code
===========

https://github.com/CESNET/pOCCI


Packages
========

Development packages:

- https://emian.zcu.cz:8443/jenkins/job/pOCCI-build-devel/lastSuccessfulBuild/
  (Debian 8/jessie, SL6, SL7, Ubuntu 14/trusty)
- https://copr-fe.cloud.fedoraproject.org/coprs/valtri/indigo/
  (EL6, EL7, Fedora)


Build
=====

Build::

   python setup.py build


Tests
=====

Unittests
---------

::

   python setup.py test

For Python 3 tests need to be converted and launched manually::

   PYTHON=python3

   cp -a tests build/lib
   pushd build/lib/tests
   2to3 -w -n *.py
   export PYTHONPATH=$PYTHONPATH:`pwd`/..
   for t in test_*.py; do ${PYTHON} ./${t}; done
   popd

Code check
----------

::

   flake8
