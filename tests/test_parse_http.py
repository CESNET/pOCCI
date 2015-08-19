#! /usr/bin/python

import os
import re
import sys
import unittest

# to launch manually
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pOCCI import occi
from pOCCI import render


def readCollection(fname):
    with open(fname, 'r') as f:
        return f.readlines()


class TestCategories(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/occi')
        self.fulldata = []
        self.data = []
        for fname in [
            'http-ok-dummy.txt',
            'http-ok-opennebula.txt',
        ]:
            headers = readCollection(os.path.join(os.path.dirname(__file__), 'category-collection', fname))
            self.fulldata.append(headers)
            for h in headers:
                if re.match(r'Category:', h):
                    self.data.append(h)
                    break


    def testCategoriesOK(self):
        """Parse headers with category collection.
        """
        for i in range(0,1):
            categories = self.renderer.parse_categories(None, self.fulldata[i])

            assert(categories)
            assert(len(categories))
            assert(categories[-1]['term'] == 'offline')

            #for cat in categories:
            #    print cat
            #    print

            #print 'ORIGINAL:'
            #print self.data[i]
            body, headers = self.renderer.render_categories(categories)
            #print 'RENDERING:'
            #print headers[0]
            #print

            assert(headers[0] + '\r\n' == self.data[i])


class TestEntities(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/occi')
        self.data = []
        for fname in [
            'http-entities.txt',
            'invalid-format.txt',
            'invalid-uri.txt',
        ]:
            self.data.append(readCollection(os.path.join(os.path.dirname(__file__
), 'entity-collection', fname)))


    def testEntitiesOK(self):
        entities = self.renderer.parse_locations(None, self.data[0])

        assert(entities)
        assert(len(entities) == 5)
        for entity in entities:
            assert(re.match(r'https://', entity))


    def testEntitiesErrorFormat(self):
        # invalid format can't be detected, foreign HTTP Headers must be skipped
        #with self.assertRaises(occi.ParseError):
            entities = self.renderer.parse_locations(None, self.data[1])


    def testEntitiesErrorURI(self):
        with self.assertRaises(occi.ParseError):
            entities = self.renderer.parse_locations(None, self.data[2])



def suite():
        return unittest.TestSuite([
                unittest.TestLoader().loadTestsFromTestCase(TestCategories),
                unittest.TestLoader().loadTestsFromTestCase(TestEntities),
        ])


if __name__ == '__main__':
        suite = suite()
        unittest.TextTestRunner(verbosity=2).run(suite)
