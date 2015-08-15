import occi

from render_base import Renderer
from render_text import *


class HTTPHeadersRenderer(Renderer):
    """ HTTP Headers OCCI Renderer

    RFC 7230 http://www.ietf.org/rfc/rfc7230.txt.
    """

    def render_category(self, category = None):
        return ['Category: ' + text_category(category)]
