#! /usr/bin/python

import os
import sys
import unittest

# to launch manually
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pOCCI import occi
from pOCCI import transport


class TestConnect(unittest.TestCase):
    """Failed connection test"""

    @classmethod
    def setUpClass(self):
        self.transport = transport.Transport({
            'authtype': 'basic',
            'url': 'http://localhost:22',
            'user': 'test',
        })


    def testDelete(self):
        with self.assertRaises(occi.TransportError):
            self.transport.delete()


    def testGet(self):
        with self.assertRaises(occi.TransportError):
            self.transport.get()


    def testPost(self):
        with self.assertRaises(occi.TransportError):
            self.transport.post()


    def testPut(self):
        with self.assertRaises(occi.TransportError):
            self.transport.put()


def suite():
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(TestConnect),
    ])


if __name__ == '__main__':
        suite = suite()
        unittest.TextTestRunner(verbosity=2).run(suite)
