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

    :ivar string err_msg[]: list of all errors
    """

    def __init__(self):
        self.err_msg = []


    def check(self, err_msg = None, cleanup = True):
        """Check for errors and cleanup the errors.

        :param string err_msg[]: list where to append the errors
        :param bool cleanup: clean all errors
        :return: if there has been any error
        :rtype: bool
        """
        ok = len(self.err_msg) == 0
        if err_msg != None:
            err_msg += self.err_msg
            if cleanup:
                self.err_msg = []
        return ok
