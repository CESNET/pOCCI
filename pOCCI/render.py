import re

import occi
from render_json import *
from render_http import *
from render_text import *
from render_uri import *


mimetypes = [
    'text/plain',
    'text/occi+plain',
    'text/occi',
    'text/uri-list',
    'application/occi+json',
]


def parse_mimetype(mimetype):
    """ Parse mimetype name string.

    Example::
       text/plain; charset=iso-8859-1

    :param string mimetype: mimetype
    :result: (mimetype, charset) tuple
    :rtype: (string, string)
    """
    charset = None

    m = re.split(r';\s*', mimetype, 2)

    if len(m) > 2:
        return (None, None)

    if len(m) == 2:
        charset = m[1]

    return (m[0], charset)


def create_renderer(req_mimetype):
    """Create OCCI Renderer.

    :param string req_mimetype: requested mimetype
    :return: renderer or None
    :rtype: RenderBase
    """
    renderer = None
    mimetype, charset = parse_mimetype(req_mimetype)

    if mimetype in ['text/plain', 'text/occi+plain']:
        renderer = TextRenderer()
    elif mimetype in ['text/occi']:
        renderer = HTTPHeadersRenderer()
    elif mimetype in ['text/uri-list']:
        renderer = URIListRenderer()
    elif mimetype in ['application/occi+json']:
        renderer = JSONRenderer()

    return renderer


if __name__ == "__main__":
    plain = create_renderer('text/plain')
    http = create_renderer('text/occi')
    json = create_renderer('application/occi+json')
    err = create_renderer('unexistand')

    print plain
    print http
    print json
    print err
    print

    attr_defs = [
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
    category = occi.Category({
        'term': 'kind',
        'class': 'myClass',
        'scheme': 'myScheme',
        'title': 'myTitle',
    })
    links = [
        occi.Link({
            'uri': 'http://localhost/myresource1',
            'rel': ['/rel'],
        }),
        occi.Link({
            'uri': 'http://localhost/myresource2',
            'rel': ['/relA', '/relB'],
        }),
    ]
    attr_values = [
        occi.Attribute({
            'name': 'occi.core.id',
            'type': 'number',
            'value': 1,
        }),
        occi.Attribute({
            'name': 'occi.core.title',
            'value': 'Title 1',
        }),
    ]

    print 'Python category:'
    print category
    print 'Text category:'
    print plain.render_category(category)
    print

    category['attributes'] = attr_defs
    print 'Python category:'
    print category
    print 'Text category:'
    print plain.render_category(category)
    print

    print 'Resource instance without links (plain):'
    print plain.render_resource([category], None, attr_values)

    print 'Resource instance without links (http):'
    print http.render_resource([category], None, attr_values)
    print

    print 'Resource instance (plain):'
    print plain.render_resource([category], links, attr_values)

    print 'Resource instance (http):'
    print http.render_resource([category], links, attr_values)
    print
