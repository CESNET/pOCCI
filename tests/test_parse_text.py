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
        for line in f.readlines():
            yield line.rstrip('\r\n')


class TestCategories(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/plain')
        self.categories = []
        for fname in [
            'text-ok-dummy.txt',
            'text-ok-opennebula.txt',
            'text-ok-ec2.txt',
            'text-duplicity.txt',
            'text-missing-class.txt',
            'text-missing-scheme.txt',
            'text-error-attrdef.txt',
            'text-error-attrdef2.txt',
            'text-error-category.txt',
            'text-error-category2.txt',
        ]:
            self.categories.append(list(readCollection(os.path.join(os.path.dirname(__file__), 'category-collection', fname))))


    def testCategoriesOK(self):
        """Parse text body with category collection, then render the parsed result and compare with the original text.
        """
        for i in range(0, 2):
            categories = self.renderer.parse_categories(self.categories[i], None)

            assert(categories)
            assert(len(categories))
            assert(categories[-1]['term'] == 'offline')

            body, headers = self.renderer.render_categories(categories)
            assert(len(headers) == 0)

            # full compare
            original = '\r\n'.join(self.categories[i]) + '\r\n'
            rendering = body
            assert(original == rendering)


    def testCategoriesDuplicity(self):
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_categories(self.categories[3], None)


    def testCategoriesMissingFields(self):
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_categories(self.categories[4], None)
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_categories(self.categories[5], None)


    def testCategoriesError(self):
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_categories(self.categories[6], None)
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_categories(self.categories[7], None)
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_categories(self.categories[8], None)
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_categories(self.categories[9], None)


class TestEntities(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/plain')
        self.entities = []
        for fname in [
            'text-ok-entities.txt',
            'invalid-format.txt',
            'invalid-uri.txt',
        ]:
            self.entities.append(list(readCollection(os.path.join(os.path.dirname(__file__), 'entity-collection', fname))))


    def testEntitiesOK(self):
        entities = self.renderer.parse_locations(self.entities[0], None)

        assert(entities)
        assert(len(entities))
        for entity in entities:
            assert(re.match(r'https://', entity))

        body, headers = self.renderer.render_locations(entities)

        # full compare
        original = '\r\n'.join(self.entities[0]) + '\r\n'
        rendering = body
        assert(original == rendering)


    def testEntitiesErrorFormat(self):
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_locations(self.entities[1], None)


    def testEntitiesErrorURI(self):
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_locations(self.entities[2], None)


class TestResource(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/plain')
        self.data = []
        for fname in [
            'text-ok-opennebula-compute.txt',
            'text-ok-ec2-compute.txt',
            'text-bad-quote-attribute.txt',
            'text-bad-quote-category.txt',
            'text-bad-quote-link.txt',
            'text-invalid-format.txt',
        ]:
            self.data.append(list(readCollection(os.path.join(os.path.dirname(__file__), 'resource', fname))))


    def testResourceOK(self):
        for i in range(0, 1):
            categories, links, attributes = self.renderer.parse_resource(self.data[i], None)

            assert(categories)
            assert(len(categories))

            assert(links)
            assert(len(links))

            assert(attributes)
            assert(len(attributes))

            #for c in categories: print c
            #for l in links: print l
            #for a in attributes: print a

            if i == 0:
                assert(categories[0]['term'] == 'compute')
                assert(attributes[0]['value'] == '103')
                assert(attributes[1]['value'] == 'one-103')
                assert(attributes[3]['value'] == 1)
                assert(re.match(r'/compute/103', links[0]['uri']) is not None)
            elif i == 1:
                assert(categories[0]['term'] == 'compute')
                assert(attributes[0]['value'] == 'i-375ab99b')
                assert(attributes[1]['value'] == 'x64')
                assert(attributes[3]['value'] == 0.613)
                assert(re.match(r'/compute/i-375ab99b', links[0]['uri']) is not None)

            # rendering
            body, headers = self.renderer.render_resource(categories, links, attributes)

            # full compare
            original = '\r\n'.join(self.data[i]) + '\r\n'
            rendering = body
            #print 'ORIGINAL:\n'; print original
            #print 'RENDERING:\n'; print rendering
            assert(original == rendering)


    def testResourceBadQuoting(self):
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_resource(self.data[2], None)
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_resource(self.data[3], None)
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_resource(self.data[4], None)


    def testResourceErrorFormat(self):
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_resource(self.data[5], None)


    def testResourceErrorEmpty(self):
        with self.assertRaises(occi.RenderError):
            self.renderer.render_resource(None, None, None)
        with self.assertRaises(occi.RenderError):
            self.renderer.render_resource([], None, None)


def suite():
        return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(TestCategories),
            unittest.TestLoader().loadTestsFromTestCase(TestEntities),
            unittest.TestLoader().loadTestsFromTestCase(TestResource),
        ])


if __name__ == '__main__':
        suite = suite()
        unittest.TextTestRunner(verbosity=2).run(suite)
