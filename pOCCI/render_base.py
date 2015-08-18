import urlparse


def check_url(body, scheme = False, host = False, path = False):
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

    def render_resource(self, categories, links = None, attributes = None):
        """Render OCCI Resource instance

        :param occi.Category categories[]: OCCI Category array
        :param occi.Link links[]: OCCI Link array
        :param occi.Attribute attributes[]: OCCI Attribute array
        :return: render result
        :rtype: string[]
        """
        if categories == None or not categories:
            raise occi.RenderError('Category required')
