import re

import occi
from render_json import *
from render_http import *
from render_text import *


mimetypes = [
    'text/plain',
    'text/occi+plain',
    'text/occi',
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

    category = occi.Category({
        'term': 'kind',
        'class': 'myClass',
        'scheme': 'myScheme',
        'title': 'myTitle',
        'attributes': [
            occi.AttributeDefinition({
                'name': 'occi.core.id',
                'immutable': True,
                'required': True,
            }),
            occi.AttributeDefinition({
                'name': 'occi.core.title',
            }),
        ],
    })

    print
    print 'Python category:'
    print category
    print 'Text category:'
    print plain.render_category(category)

    print
    category['attributes'] = []
    print 'Python category:'
    print category
    print 'Text category:'
    print plain.render_category(category)
