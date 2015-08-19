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
            'ok-dummy.txt',
            'ok-opennebula.txt',
            'duplicity.txt',
            'missing-class.txt',
            'missing-scheme.txt',
            'error-attrdef.txt',
            'error-attrdef2.txt',
            'error-category.txt',
            'error-category2.txt',
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
            'entities.txt',
            'invalid-format.txt',
            'invalid-uri.txt',
        ]:
            self.entities.append(readCollection(os.path.join(os.path.dirname(__file__), 'entity-collection', fname)))


    def testEntitiesOK(self):
        entities = self.renderer.parse_locations(self.entities[0], None)

        assert(entities)
        assert(len(entities))
        assert(re.match(r'https://', entities[-1]))


    def testEntitiesErrorFormat(self):
        with self.assertRaises(occi.ParseError):
            entities = self.renderer.parse_locations(self.entities[1], None)


    def testEntitiesErrorURI(self):
        with self.assertRaises(occi.ParseError):
            entities = self.renderer.parse_locations(self.entities[2], None)


def suite():
        return unittest.TestSuite([
                unittest.TestLoader().loadTestsFromTestCase(TestCategories),
                unittest.TestLoader().loadTestsFromTestCase(TestEntities),
        ])


if __name__ == '__main__':
        suite = suite()
        unittest.TextTestRunner(verbosity=2).run(suite)
