import ConfigParser
import os

import render


occi_defaults = {
    'mimetype': 'text/plain',
}

occi_config = {}
renderer = None
renderer_big = None
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

    for key, value in occi_defaults.iteritems():
        if not key in occi_config:
            occi_config[key] = value

    # bigger data requires anything except HTTP Headers renderer
    if occi_config['mimetype'] == 'text/occi':
        occi_config['mimetype.big'] = 'text/plain'
    else:
        occi_config['mimetype.big'] = occi_config['mimetype']

    return True


def occi_render_init():
    """Initialize pOCCI renderers.

    Limitations:
       - For HTTP GET requests 'text/occi' is always needed
       - For bigger data 'text/occi' should not be used (using 'text/plain')
    """
    global renderer
    global renderer_big
    global renderer_httpheaders

    # user configurable renderer
    renderer = render.create_renderer(occi_config['mimetype'])

    # big data requires anything except HTTP Headers renderer
    renderer_big = renderer
    if occi_config['mimetype'] != occi_config['mimetype.big']:
        renderer_big = render.create_renderer(occi_config['mimetype.big'])

    # HTTP GET requests needs HTTP Headers renderer
    renderer_httpheaders = renderer
    if occi_config['mimetype'] != 'text/occi':
        renderer_httpheaders = render.create_renderer('text/occi')


if not occi_config:
    occi_init()
