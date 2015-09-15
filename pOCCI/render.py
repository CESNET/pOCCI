import re

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
