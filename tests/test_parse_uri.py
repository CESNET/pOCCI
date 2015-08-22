#! /usr/bin/python

import os
import sys
import unittest

# to launch manually
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pOCCI import occi
from pOCCI import render


def readCollection(fname):
    with open(fname, 'r') as f:
        for line in f.readlines():
            yield line.rstrip('\r\n')


class TestURIList(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/uri-list')
        self.data = []

        for fname in [
            'uri-ok-entities.txt',
            'uri-invalid-uri.txt',
        ]:
            uris = list(readCollection(os.path.join(os.path.dirname(__file__), 'entity-collection', fname)))
            self.data.append(uris)


    def testOK(self):
        uris = self.renderer.parse_locations(self.data[0], None)
        assert(len(uris) == 5)
        for i in range(0,4):
            assert(uris[i] == 'https://example.com:11443/compute/%d' % (i + 88))


    def testInvalidURI(self):
        with self.assertRaises(occi.ParseError):
            uris = self.renderer.parse_locations(self.data[1], None)


    def testInvalidMethods(self):
        with self.assertRaises(occi.RenderError):
            self.renderer.render_categories([])
        with self.assertRaises(occi.RenderError):
            self.renderer.render_resource([])
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_categories(self.data[0], None)
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_resource(self.data[0], None)


def suite():
        return unittest.TestSuite([
                unittest.TestLoader().loadTestsFromTestCase(TestURIList),
        ])


if __name__ == '__main__':
        suite = suite()
        unittest.TextTestRunner(verbosity=2).run(suite)
