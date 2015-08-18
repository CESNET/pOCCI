import occi

from render_base import Renderer
from render_text import *


class HTTPHeadersRenderer(Renderer):
    """HTTP Headers OCCI Renderer

    RFC 7230 http://www.ietf.org/rfc/rfc7230.txt.
    """

    def render_category(self, category):
        """Render OCCI Category

        :param occi.Category category: OCCI Category object
        :return: render result
        :rtype: string[]
        """
        return ['Category: ' + text_category(category)]


    def render_categories(self, categories):
        """Render OCCI Category collection

        :param occi.Category category[]: OCCI Category array
        :return: render result
        :rtype: string[]
        """
        if not categories:
            return ''
        res = []
        for category in categories:
            res.append(text_category(category))
        return ['Category: ' + ', '.join(res)]


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
        :rtype: string[]
        """
        Renderer.render_resource(self, categories, links, attributes)
        res = []
        res += self.render_categories(categories)
        if links != None:
            res += self.render_links(links)
        if attributes != None:
            res += self.render_attributes(attributes)
        return res
