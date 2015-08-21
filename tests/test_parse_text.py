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
        self.renderer = render.create_renderer('text/plain')
        self.categories = []
        for fname in [
            'text-ok-dummy.txt',
            'text-ok-opennebula.txt',
            'text-duplicity.txt',
            'text-missing-class.txt',
            'text-missing-scheme.txt',
            'text-error-attrdef.txt',
            'text-error-attrdef2.txt',
            'text-error-category.txt',
            'text-error-category2.txt',
        ]:
            self.categories.append(readCollection(os.path.join(os.path.dirname(__file__), 'category-collection', fname)))


    def testCategoriesOK(self):
        """Parse text body with category collection, then render the parsed result and compare with the original text.

        TODO: better to have OCCI Category collection rendering instead to render it one by one here.
        """
        for i in range(0,1):
            categories = self.renderer.parse_categories(self.categories[i], None)

            assert(categories)
            assert(len(categories))
            assert(categories[-1]['term'] == 'offline')

            body = []
            for cat in categories:
                body.append(self.renderer.render_category(cat)[0])

            # compare only several lines first
            assert(self.categories[i][0] == body[0] + '\n')
            assert(self.categories[i][1] == body[1] + '\n')
            assert(self.categories[i][2] == body[2] + '\n')

            # full compare
            original = ''.join(self.categories[i])
            rendering = '\n'.join(body) + '\n'
            assert(original == rendering)


    def testCategoriesDuplicity(self):
        with self.assertRaises(occi.ParseError):
            categories = self.renderer.parse_categories(self.categories[2], None)


    def testCategoriesMissingFields(self):
        with self.assertRaises(occi.ParseError):
            categories = self.renderer.parse_categories(self.categories[3], None)
        with self.assertRaises(occi.ParseError):
            categories = self.renderer.parse_categories(self.categories[4], None)


    def testCategoriesError(self):
        with self.assertRaises(occi.ParseError):
            categories = self.renderer.parse_categories(self.categories[5], None)
        with self.assertRaises(occi.ParseError):
            categories = self.renderer.parse_categories(self.categories[6], None)
        with self.assertRaises(occi.ParseError):
            categories = self.renderer.parse_categories(self.categories[7], None)
        with self.assertRaises(occi.ParseError):
            categories = self.renderer.parse_categories(self.categories[8], None)


class TestEntities(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/plain')
        self.entities = []
        for fname in [
            'text-entities.txt',
            'invalid-format.txt',
            'invalid-uri.txt',
        ]:
            self.entities.append(readCollection(os.path.join(os.path.dirname(__file__), 'entity-collection', fname)))


    def testEntitiesOK(self):
        entities = self.renderer.parse_locations(self.entities[0], None)

        assert(entities)
        assert(len(entities))
        for entity in entities:
            assert(re.match(r'https://', entity))


    def testEntitiesErrorFormat(self):
        with self.assertRaises(occi.ParseError):
            entities = self.renderer.parse_locations(self.entities[1], None)


    def testEntitiesErrorURI(self):
        with self.assertRaises(occi.ParseError):
            entities = self.renderer.parse_locations(self.entities[2], None)


class TestResource(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/plain')
        self.data = []
        for fname in [
            'text-ok-opennebula-compute.txt',
            'text-bad-quote-attribute.txt',
            'text-bad-quote-category.txt',
            'text-bad-quote-link.txt',
            'text-invalid-format.txt',
        ]:
            self.data.append(readCollection(os.path.join(os.path.dirname(__file__), 'resource', fname)))


    def testResourceOK(self):
        categories, links, attributes = self.renderer.parse_resource(self.data[0], None)

        assert(categories)
        assert(len(categories))

        assert(links)
        assert(len(links))

        assert(attributes)
        assert(len(attributes))

        #for c in categories: print c
        #for l in links: print l
        #for a in attributes: print a

        assert(categories[0]['term'] == 'compute')
        assert(attributes[0]['value'] == '103')
        assert(attributes[1]['value'] == 'one-103')
        assert(attributes[3]['value'] == 1)
        assert(re.match(r'/compute/103', links[0]['uri']) != None)

        # rendering
        body, headers = self.renderer.render_resource(categories, links, attributes)

        # full compare
        original = ''.join(self.data[0])
        rendering = body
        #print 'ORIGINAL:\n'; print original
        #print 'RENDERING:\n'; print rendering
        assert(original == rendering)


    def testResourceBadQuoting(self):
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_resource(self.data[1], None)
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_resource(self.data[2], None)
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_resource(self.data[3], None)


    def testResourceErrorFormat(self):
        with self.assertRaises(occi.ParseError):
            self.renderer.parse_resource(self.data[4], None)


def suite():
        return unittest.TestSuite([
                unittest.TestLoader().loadTestsFromTestCase(TestCategories),
                unittest.TestLoader().loadTestsFromTestCase(TestEntities),
                unittest.TestLoader().loadTestsFromTestCase(TestResource),
        ])


if __name__ == '__main__':
        suite = suite()
        unittest.TextTestRunner(verbosity=2).run(suite)
