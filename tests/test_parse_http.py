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


class TestHeaderValues(unittest.TestCase):

    bodies_ok = {
        'aaa': ['aaa'],
        'aaa, bbb': ['aaa', 'bbb'],
        'aaa,bbb': ['aaa', 'bbb'],
        'aaa , bbb': ['aaa', 'bbb'],
        'aaa  ,  bbb': ['aaa', 'bbb'],
        'aaa   ,  bbb': ['aaa', 'bbb'],
        '"aaa"': ['"aaa"'],
        '"aaa", "bbb"': ['"aaa"', '"bbb"'],
        'aaa, "bbb"': ['aaa', '"bbb"'],
        '"aaa", bbb': ['"aaa"', 'bbb'],
        'aaa, bbb, "ccc, ccc", "d,d,d\\"d\\"dd", "eee\\"eee"' : ['aaa', 'bbb', '"ccc, ccc"', '"d,d,d\\"d\\"dd"', '"eee\\"eee"'],
        ',' : ['', ''],
        'a,': ['a', ''],
        '""': ['""'],
        '': [],
        'aaa=1, bbb=2': ['aaa=1', 'bbb=2'],
        'aaa="1", bbb="2"': ['aaa="1"', 'bbb="2"'],
        'aaa="1,1", bbb="2,2"': ['aaa="1,1"', 'bbb="2,2"'],
        'aaa, bbb="2,2"': ['aaa', 'bbb="2,2"'],
        'aaa="1,1", bbb': ['aaa="1,1"', 'bbb'],
        'occi.core.id="103",occi.core.title="one-103",occi.core.summary="Instantiated with rOCCI-server on Thu, 20 Aug 2015 13:48:50 +0200.",occi.compute.cores=1,occi.compute.memory=0.125,occi.compute.state="active",org.opennebula.compute.id="103",org.opennebula.compute.cpu=1.0,org.openstack.credentials.publickey.data="ssh-dss AAAAB3NzaC1kc3MAAACBAJAQxCSi3hx/2UKXJMD7MzeHKiMFl7LxWKp0Bw6ArlaKXRAozISe7djcjufCJYyZ8R86Pjh8rYaN9oAmikLQGThJlVsV7TojpcMn1UVrIWz4sC02VoOe8wtVY60akplt7jLfA4Qn1T4wu6Q8jHB4Wv48x7fDO51w01Q/j4CdXXpnAAAAFQDBT/N1u+BKQ/V1+CN50gdBJxplEwAAAIAL/9tgJsF69UQZh/l6M139eFFOxz6GawQd+5H/v6ECjcBICqAZBKpv70JiYrT+5UptmPJ1FKo5S+UHWAWUdyc2Lu8BJ9PsHYI5sNeGoSoTlx/ZlBqrA9Pf5oBb1uO3HMAtrnN17b6JCv6sHBxHCJqRI8ATk5mA2JPxBHwTiqxoDQAAAIAfnCNxwI8T7tQD4x2s7KVYm4oRVE7bO8L+o9An9/JPWIaNYHNTuAkOAoRlW54m9kBexPhAQxt2HF6/JMIgS2lglTAbygAneH63v96xT9L2Gqyj2mAQIZ8NgxVtVFymsQxuhB5s1pkK3WJreOW9PY9np69CU0zjLDKXyZ0J2RCbvw== root@myriads.zcu.cz",org.openstack.compute.user_data="# user data"': [
            'occi.core.id="103"',
            'occi.core.title="one-103"',
            'occi.core.summary="Instantiated with rOCCI-server on Thu, 20 Aug 2015 13:48:50 +0200."',
            'occi.compute.cores=1',
            'occi.compute.memory=0.125',
            'occi.compute.state="active"',
            'org.opennebula.compute.id="103"',
            'org.opennebula.compute.cpu=1.0',
            'org.openstack.credentials.publickey.data="ssh-dss AAAAB3NzaC1kc3MAAACBAJAQxCSi3hx/2UKXJMD7MzeHKiMFl7LxWKp0Bw6ArlaKXRAozISe7djcjufCJYyZ8R86Pjh8rYaN9oAmikLQGThJlVsV7TojpcMn1UVrIWz4sC02VoOe8wtVY60akplt7jLfA4Qn1T4wu6Q8jHB4Wv48x7fDO51w01Q/j4CdXXpnAAAAFQDBT/N1u+BKQ/V1+CN50gdBJxplEwAAAIAL/9tgJsF69UQZh/l6M139eFFOxz6GawQd+5H/v6ECjcBICqAZBKpv70JiYrT+5UptmPJ1FKo5S+UHWAWUdyc2Lu8BJ9PsHYI5sNeGoSoTlx/ZlBqrA9Pf5oBb1uO3HMAtrnN17b6JCv6sHBxHCJqRI8ATk5mA2JPxBHwTiqxoDQAAAIAfnCNxwI8T7tQD4x2s7KVYm4oRVE7bO8L+o9An9/JPWIaNYHNTuAkOAoRlW54m9kBexPhAQxt2HF6/JMIgS2lglTAbygAneH63v96xT9L2Gqyj2mAQIZ8NgxVtVFymsQxuhB5s1pkK3WJreOW9PY9np69CU0zjLDKXyZ0J2RCbvw== root@myriads.zcu.cz"',
            'org.openstack.compute.user_data="# user data"',
        ],
        'a=1;b="2";c="3"': ['a=1;b="2";c="3"'],
        'a=1;b="2,2";c="3\\,3",A=1': ['a=1;b="2,2";c="3\\,3"', 'A=1'],
    }

    bodies_error = [
        # expected separator
        'bbb\\"bbb',
        'bbb\\"bbb\"',
        'aaa, bbb\\"bbb',
        'aaa, bbb\\"bbb\"',
        '"""',
        # parse error
        '"',
    ]


    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/occi')


    def testOK(self):
        for body, result in TestHeaderValues.bodies_ok.iteritems():
            check = True
            chunks = []
            i = 0
            try:
                for chunk in self.renderer.parse_header_values(body):
                    chunks.append(chunk)
                    if chunk != result[i]:
                        check = False
                    i = i + 1
            except occi.ParseError as pe:
                print 'BODY: #%s#' % body
                print chunks
                print result
                raise

            if not check:
                print 'BODY: #%s#' % body
                print chunks
                print result
            assert(check)


    def testError(self):
        for body in TestHeaderValues.bodies_error:
            with self.assertRaises(occi.ParseError):
                #print 'BAD BODY: #%s#' % body
                for chunk in self.renderer.parse_header_values(body):
                    #print '  result: #%s#' % chunk
                    pass


class TestCategories(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/occi')
        self.fulldata = []
        self.data = []
        for fname in [
            'http-ok-dummy.txt',
            'http-ok-ec2.txt',
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
        for i in range(0,2):
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


class TestResource(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.renderer = render.create_renderer('text/occi')
        self.data = []
        for fname in [
            'http-ok-opennebula-compute.txt',
            'http-ok-ec2-compute.txt',
            'http-ok-ignore-unknown.txt',
        ]:
            self.data.append(readCollection(os.path.join(os.path.dirname(__file__), 'resource', fname)))


    def testResourceOK(self):
        for i in range(0,2):
            categories, links, attributes = self.renderer.parse_resource(None, self.data[i])

            assert(categories)
            assert(len(categories))

            assert(links)
            assert(len(links))

            assert(attributes)
            assert(len(attributes))

            #print i
            #for c in categories: print c
            #for l in links: print l
            #for a in attributes: print a

            if i == 0 or i == 2:
                assert(categories[0]['term'] == 'compute')
                assert(attributes[0]['value'] == '103')
                assert(attributes[1]['value'] == 'one-103')
                assert(attributes[3]['value'] == 1)
                assert(re.match(r'/storage/0', links[0]['uri']) != None)
            elif i == 1:
                assert(categories[0]['term'] == 'compute')
                assert(attributes[0]['value'] == 'i-375ab99b')
                assert(attributes[1]['value'] == 'x64')
                assert(attributes[3]['value'] == 0.613)
                assert(re.match(r'/storage/vol-2cc1133a', links[0]['uri']) != None)

            # rendering
            body, headers = self.renderer.render_resource(categories, links, attributes)

            # full compare
            # (with the first datafile without additional fields)
            reference = i
            if i == 2:
                reference = 0
            original = ''.join(self.data[reference])
            rendering = '\n'.join(headers) + '\n'
            #print 'INDEX: %d\n' % i
            #print 'ORIGINAL:\n'; print original
            #print 'RENDERING:\n'; print rendering
            assert(original == rendering)


def suite():
        return unittest.TestSuite([
                unittest.TestLoader().loadTestsFromTestCase(TestHeaderValues),
                unittest.TestLoader().loadTestsFromTestCase(TestCategories),
                unittest.TestLoader().loadTestsFromTestCase(TestEntities),
                unittest.TestLoader().loadTestsFromTestCase(TestResource),
        ])


if __name__ == '__main__':
        suite = suite()
        unittest.TextTestRunner(verbosity=2).run(suite)
