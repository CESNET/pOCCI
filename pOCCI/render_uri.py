import occi
from render_base import Renderer, check_url


class URIListRenderer(Renderer):
    """URI list OCCI Renderer

    Empty array is always returned as headers during rendering.
    """

    def render_categories(self, categories):
        """Render OCCI Category collection

        This method can't be used in URI list rendering.

        :param occi.Category category[]: OCCI Category array
        :return: render result
        :rtype: [string, string[]]
        """
        raise occi.RenderError('This method can\'t be used with URI list rendering.')


    def render_resource(self, categories, links=None, attributes=None):
        """Render OCCI Resource instance

        This method can't be used in URI list rendering.

        :param occi.Category categories[]: OCCI Category array
        :param occi.Link links[]: OCCI Link array
        :param occi.Attribute attributes[]: OCCI Attribute array
        :return: render result
        :rtype: [string, string[]]
        """
        raise occi.RenderError('This method can\'t be used with URI list rendering.')


    def render_locations(self, locations):
        """ Render Locations

        :param string location[]: location URI
        :return: render result
        :rtype: [string, string[]]
        """
        return ['\n'.join(locations), []]


    def parse_categories(self, body, headers):
        """Parse OCCI Category Collection

        This method can't be used in URI list rendering.

        :param string body[]: text to parse
        :param string headers[]: headers to parse
        :return: Array of OCCI Categories
        :rtype: occi.Category[]
        """
        raise occi.ParseError('This method can\'t be used with URI list rendering.')


    def parse_locations(self, body, headers):
        """Parse OCCI Entity collection

        :param string body[]: text to parse
        :param string headers[]: headers to parse
        :return: array of renderer-specific strings
        :rtype: string[]
        """
        locations = []
        for uri in body:
            if not check_url(uri, scheme=True, host=True):
                raise occi.ParseError('Invalid URI in OCCI Entity collection', uri)
            locations.append(uri)

        return locations


    def parse_resource(self, body, header):
        """Parse OCCI Resource instance

        This method can't be used in URI list rendering.

        :param string body[]: text to parse
        :param string headers[]: headers to parse
        :return: categories, links, and attributes
        :rtype: [occi.Category categories[], occi.Link links[], occi.Attribute attributes[]]
        """
        raise occi.ParseError('This method can\'t be used with URI list rendering.')
