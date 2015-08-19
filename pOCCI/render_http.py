import re

import occi

from render_base import Renderer
from render_text import *


class HTTPHeadersRenderer(TextRenderer):
    """HTTP Headers OCCI Renderer

    RFC 7230 http://www.ietf.org/rfc/rfc7230.txt.

    Empty string is always returned as body during rendering.

    Beware of HTTP Headers size limitations. It is better to not use 'text/occi' mimetype for transfering OCCI Category Collection.
    """

    reSEP = re.compile(r'\s*,\s*')

    def render_category(self, category):
        """Render OCCI Category

        :param occi.Category category: OCCI Category object
        :return: render result
        :rtype: [string, string[]]
        """
        return ['', ['Category: ' + text_category(category)]]


    def render_categories(self, categories):
        """Render OCCI Category collection

        :param occi.Category category[]: OCCI Category array
        :return: render result
        :rtype: [string, string[]]
        """
        if not categories:
            return ['', []]
        res = []
        for category in categories:
            res.append(text_category(category))
        return ['', ['Category: ' + ','.join(res)]]


    def render_links(self, links):
        """ Render OCCI Links

        :param occi.Link link[]: OCCI Link array
        :return: render result
        :rtype: string[]
        """
        if not links:
            return []
        res = []
        for link in links:
            res.append(text_link(link))
        return ['Link: ' + ', '.join(res)]


    def render_attributes(self, attributes):
        """Render Attributes

        :param occi.Attribute attribute[]: OCCI Attribute object
        :return: render result
        :rtype: string[]
        """
        if not attributes:
            return []

        s = []
        for attribute in attributes:
            s.append(text_attribute_repr(attribute))
        return ['X-OCCI-Attribute: ' + ','.join(s)]


    def render_locations(self, locations):
        """ Render Locations

        :param string location: location URI
        :return: render result
        :rtype: string[]
        """
        return ['X-OCCI-Location: ' + ','.join(location)]


    def render_resource(self, categories, links = None, attributes = None):
        """Render OCCI Resource instance

        :param occi.Category category: OCCI Category object
        :param occi.Link links[]: OCCI Link array
        :param occi.Attribute attributes[]: OCCI Attribute array
        :return: render result
        :rtype: [string, string[]]
        """
        Renderer.render_resource(self, categories, links, attributes)
        res = []
        cat_s, cat_h = self.render_categories(categories)
        res += cat_h
        if links != None:
            res += self.render_links(links)
        if attributes != None:
            res += self.render_attributes(attributes)
        return ['', res]


    def parse_categories(self, body, headers):
        """Parse OCCI Category Collection

        Beware of HTTP Headers size limitations. It is better to not use 'text/occi' mimetype for transfering OCCI Category Collection.

        :param string body[]: text to parse (unused in plain/occi)
        :param string headers[]: headers to parse
        :return: Array of OCCI Categories
        :rtype: occi.Category[]
        """
        categories = []
        category_ids = set()

        for line in headers:
            matched = TextRenderer.reCategory.match(line)
            if not matched:
                continue

            line = line[matched.end():]
            #print 'CATEGORY HIT:'
            #print line
            bodies = HTTPHeadersRenderer.reSEP.split(line)
            #print 'SPLAT BODIES:'
            #print '\n\n'.join(bodies)

            for cat_s in bodies:
                # use the helper parser function inherited from text/plain renderer
                category = TextRenderer.parse_category_body(self, cat_s)

                # check uniqueness
                key = category['term'] + category['scheme']
                if key in category_ids:
                    raise occi.ParseError('Category not unique (term "%s", scheme "%s")' % (category['term'], category['scheme']), cat_s)
                category_ids.add(key)

                categories.append(category)

        return categories


    def parse_locations(self, body, headers):
        """Parse OCCI Entity collection

        :param string body[]: text to parse (unused in text/occi)
        :param string headers[]: headers to parse
        :return: Array of links
        :rtype: string[]
        """
        locations = []
        for line in headers:
            matched = TextRenderer.reLocation.match(line)
            if not matched:
                continue
            uris_str = matched.group(2)
            uris = HTTPHeadersRenderer.reSEP.split(uris_str)
            for uri in uris:
                if not check_url(uri, scheme = True, host = True):
                    raise occi.ParseError('Invalid URI in OCCI Entity collection', line)
                locations.append(uri)

        return locations
