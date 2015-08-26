Python versions
===============

Both Python 2 and Python 3 should work.

pOCCI is primary developed in Python 2. For Python 3 sources are converted by 2to3 tool.


Source code
===========

https://github.com/CESNET/pOCCI


Build
=====

Build::

   python setup.py build

Tests
=====

Unittests are working automatically only with Python 2::

   python setup.py test

For Python 3 tests need to be converted and launched manually::

   PYTHON=python3

   cp -a tests build/lib
   pushd build/lib/tests
   2to3 -w -n *.py
   export PYTHONPATH=$PYTHONPATH:`pwd`/..
   for t in test_*.py; do ${PYTHON} ./${t}; done
   popd
