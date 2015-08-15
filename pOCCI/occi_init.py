import ConfigParser
import os

import render

occi_config = {}
renderer = None
renderer_httpheaders = None


def occi_init():
    """Initialize pOCCI.
    """

    occi_config_init()
    occi_render_init()


def occi_config_init():
    """Initialize pOCCI configuration.

    Reads the configuration file: /etc/pOCCI.cfg, ~/.pOCCI.cfg.
    """
    global occi_config

    config = ConfigParser.ConfigParser()
    config.read(['/etc/pOCCI.cfg', os.path.expanduser('~/.pOCCI.cfg')])
    if not config.has_section('main'):
        return False
    for key, value in config.items('main'):
        #print 'config: %s = %s (%s)' % (key, value, type(eval(value)))
        occi_config[key] = eval(value)
    return True


def occi_render_init():
    """Initialize pOCCI renderers.
    """
    global renderer
    global renderer_httpheaders
    renderer = render.create_renderer(occi_config['mimetype'])
    renderer_httpheaders = render.create_renderer('text/occi')


if not occi_config:
    occi_init()
