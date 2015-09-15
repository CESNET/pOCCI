import urlparse

import occi


def check_url(body, scheme=False, host=False, path=False):
    """Check validity of URL.

    :param string body: validated URL
    :param bool scheme: scheme required
    :param bool host: hostname required
    :param bool path: local path required
    :return: URL validity, empty string considered as not valid
    :rtype: bool
    """
    url = urlparse.urlparse(body)

    if not url:
        return False

    if scheme and not url.scheme:
        return False
    if host and not url.netloc:
        return False
    if path and not url.path:
        return False
    if not url.scheme and not url.netloc and not url.path:
        return False

    return True


class Renderer:
    """ OCCI Renderer base skeleton.
    """

    def render_category(self, category):
        """Render OCCI Category

        :param occi.Category category: OCCI Category object
        :return: render result
        :rtype: [string, string[]]
        """

    def render_categories(self, categories):
        """Render OCCI Category collection

        :param occi.Category category[]: OCCI Category array
        :return: render result
        :rtype: [string, string[]]
        """


    def render_resource(self, categories, links=None, attributes=None):
        """Render OCCI Resource instance

        :param occi.Category categories[]: OCCI Category array
        :param occi.Link links[]: OCCI Link array
        :param occi.Attribute attributes[]: OCCI Attribute array
        :return: render result
        :rtype: [string, string[]]
        """
        if categories is None or not categories:
            raise occi.RenderError('Category required')


    def parse_categories(self, body, headers):
        """Parse OCCI Category Collection

        :param string body[]: text to parse
        :param string headers[]: headers to parse
        :return: Array of OCCI Categories
        :rtype: occi.Category[]
        """


    def parse_locations(self, body, headers):
        """Parse OCCI Entity collection

        :param string body[]: text to parse
        :param string headers[]: headers to parse
        :return: array of renderer-specific strings
        :rtype: string[]
        """


    def parse_resource(self, body, header):
        """Parse OCCI Resource instance

        :param string body[]: text to parse
        :param string headers[]: headers to parse
        :return: categories, links, and attributes
        :rtype: [occi.Category categories[], occi.Link links[], occi.Attribute attributes[]]
        """
