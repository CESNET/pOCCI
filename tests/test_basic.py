#! /usr/bin/python

import os
import sys
import unittest

# to launch manually
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pOCCI import occi
from pOCCI import render


attributes = [
    occi.Attribute({
        'name': 'occi.core.id',
        'type': 'number',
        'value': 1,
    }),
    occi.Attribute({
        'name': 'occi.core.title',
        'value': 'Title 1',
    }),
    occi.Attribute({
        'name': 'pocci.test.enabled',
        'type': 'bool',
        'value': True,
    }),
    occi.Attribute({
        'name': 'pocci.test.fs',
        'type': 'enum',
        'value': 'ext3',
    }),
]
attributes2 = [
    occi.Attribute({
        'name': 'occi.core.id',
        'type': 'number',
        'value': 1,
    }),
    occi.Attribute({
        'name': 'occi.core.title',
        'type': 'enum',
        'value': 'Title 1',
    }),
    occi.Attribute({
        'name': 'pocci.test.enabled',
        'type': 'bool',
        'value': True,
    }),
    occi.Attribute({
        'name': 'pocci.test.fs',
        'type': 'string',
        'value': 'ext3',
    }),
]


def readLines(fname):
    with open(fname, 'r') as f:
        for line in f.readlines():
            yield line.rstrip('\r\n')


class TestRender(unittest.TestCase):
    """Rendering from the code"""

    @classmethod
    def setUpClass(self):
        self.plain = render.create_renderer('text/plain')
        self.http = render.create_renderer('text/occi')
        self.json = render.create_renderer('application/occi+json')
        self.err = render.create_renderer('unexistand')

        self.data = []
        for fname in [
            'text-category1.txt',
            'text-category2.txt',
            'text-resource.txt',
            'http-resource.txt',
            'text-resource2.txt',
            'http-resource2.txt',
        ]:
            self.data.append(list(readLines(os.path.join(os.path.dirname(__file__), 'basic', fname))))

        self.attr_defs = [
            occi.AttributeDefinition({
                'name': 'occi.core.id',
                'type': 'number',
                'immutable': True,
                'required': True,
            }),
            occi.AttributeDefinition({
                'name': 'occi.core.title',
            }),
        ]
        self.category = occi.Category({
            'term': 'kind',
            'class': 'myClass',
            'scheme': 'myScheme',
            'title': 'myTitle',
        })
        self.links = [
            occi.Link({
                'uri': 'http://localhost/myresource1',
                'rel': ['/rel'],
            }),
            occi.Link({
                'uri': 'http://localhost/myresource2',
                'rel': ['/relA', '/relB'],
            }),
        ]
        self.attr_values = attributes


    def testInit(self):
        assert(self.plain)
        assert(self.http)
        assert(self.json)
        assert(self.err is None)


    def testRender(self):
        category = self.category

        body, headers = self.plain.render_category(category)
        assert(self.data[0][0] == body)

        category['attributes'] = self.attr_defs
        body, headers = self.plain.render_category(category)
        assert(self.data[1][0] == body)


    def testRenderResourceNoLinks(self):
        category = self.category
        attr_values = self.attr_values

        original = '\r\n'.join(self.data[2]) + '\r\n'
        body, headers = self.plain.render_resource([category], None, attr_values)
        assert(original == body)

        body, headers = self.http.render_resource([category], None, attr_values)
        assert(self.data[3] == headers)


    def testRenderResourceWithLinks(self):
        category = self.category
        attr_values = self.attr_values
        links = self.links

        original = '\r\n'.join(self.data[4]) + '\r\n'
        body, headers = self.plain.render_resource([category], links, attr_values)
        assert(original == body)

        body, headers = self.http.render_resource([category], links, attr_values)
        assert(self.data[5] == headers)


class TestTypes(unittest.TestCase):
    """Base OCCI Types"""


    def testAttributeEquals(self):
        for a in attributes:
            assert(occi.Attribute.equals(a, a) is True)
        assert(occi.Attribute.equals(attributes[1], occi.Attribute({'value': 'Title 1'})) is True)


    def testAttributeEqualDifferentType(self):
        for a1, a2 in zip(attributes, attributes2):
            assert(occi.Attribute.equals(a1, a2) is True)


    def testAttributeNotEqual(self):
        assert(occi.Attribute.equals(attributes[0], occi.Attribute({'value': 2})) is False)
        assert(occi.Attribute.equals(attributes[1], occi.Attribute({'value': 'Title 2'})) is False)


def suite():
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(TestRender),
        unittest.TestLoader().loadTestsFromTestCase(TestTypes),
    ])


if __name__ == '__main__':
        suite = suite()
        unittest.TextTestRunner(verbosity=2).run(suite)
