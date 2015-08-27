import json
import os
import sys
import ConfigParser

import occi
import render


# keep in sync with pOCCI/pOCCI.cfg
occi_defaults = {
    'authtype': 'basic',
    'ignoressl': False,
    'mimetype': 'text/plain',
    'outputformat': 'json',
    'curlverbose': False,
    'connectiontimeout': 60,
    'timeout': 120,

    'tests.category': 'Category:compute;class=kind;scheme="http://schemas.ogf.org/occi/infrastructure#"',
}

occi_config = {}
renderers = {}
renderer = None
renderer_big = None
renderer_httpheaders = None


def occi_format(results):
    count_f = 0
    count_o = 0
    for r in results:
        if 'status' in r:
            if r['status']:
                count_o += 1
            else:
                count_f += 1

            r['status'] = result2str(r['status'])
        
        if 'running_time' in r:
            r['running_time'] = round(r['running_time'], 3)

    out = {}
    out['tests'] = results
    out['passed'] = count_o
    out['failed'] = count_f
    return out


def occi_print(results, outputformat):
    if outputformat == 'plain':
        for r in results['tests']:
            print '%s  %s' % (r['name'], r['status'])
            if 'reason' in r:
                print >> sys.stderr, r['reason']
    elif outputformat == 'json':
        print json.dumps(results, indent=4, sort_keys=True)
    else:
        print 'Only "plain", "json" output types are possible'


def occi_test(name, status, err_msg, running_time = None):
    test = {}
    test['name'] = name
    test['status'] = status
    if running_time is not None:
        test['running_time'] = running_time
    if err_msg:
        test['reason'] = err_msg

    return test


def result2str(result):
    return 'OK' if result else 'FAIL'


def occi_init():
    """Initialize pOCCI.
    """

    # bigger data requires anything except HTTP Headers renderer
    if occi_config['mimetype'] == 'text/occi':
        occi_config['mimetype.big'] = 'text/plain'
    else:
        occi_config['mimetype.big'] = occi_config['mimetype']

    occi_render_init()


def occi_config_init():
    """Initialize pOCCI configuration.

    Reads the configuration file: /etc/pOCCI.cfg, ~/.pOCCI.cfg.
    """
    global occi_config

    config = ConfigParser.ConfigParser()
    config.read(['/etc/pOCCI.cfg', os.path.expanduser('~/.pOCCI.cfg')])
    if config.has_section('main'):
        for key, value in config.items('main'):
            #print 'config: %s = %s (%s)' % (key, value, type(eval(value)))
            occi_config[key] = eval(value)

    for key, value in occi_defaults.iteritems():
        if not key in occi_config:
            occi_config[key] = value

    return True


def occi_render_init():
    """Initialize pOCCI renderers.

    Limitations:
       - For HTTP GET requests 'text/occi' is always needed
       - For bigger data 'text/occi' should not be used (using 'text/plain')
    """
    mimetypes = ['text/plain', 'text/occi']
    self = sys.modules[__name__]

    # renderers always needed
    for mime in mimetypes:
        renderers[mime] = render.create_renderer(mime)

    # user configurable renderer
    if occi_config['mimetype'] in mimetypes:
        renderer = renderers[occi_config['mimetype']]
    else:
        renderer = render.create_renderer(occi_config['mimetype'])

    # big data requires anything except HTTP Headers renderer
    renderer_big = renderer
    if occi_config['mimetype'] != occi_config['mimetype.big']:
        if occi_config['mimetype.big'] in mimetypes:
            renderer_big = renderers[occi_config['mimetype.big']]
        else:
            renderer_big = render.create_renderer(occi_config['mimetype.big'])

    # HTTP GET requests needs HTTP Headers renderer
    renderer_httpheaders = renderer
    if occi_config['mimetype'] != 'text/occi':
        renderer_httpheaders = renderers['text/occi']

    # configurable filters
    for f in ['tests.category', 'tests.entity']:
        if f in occi_config:
            try:
                categories = renderers['text/plain'].parse_categories([occi_config[f]], None)
            except occi.ParseError as pe:
                print ("Can't parse '%s' config option: " % f) + str(pe)
                sys.exit(2)
            if categories:
                occi_config['occi.%s' % f] = categories[0]
            if occi_config['curlverbose']:
                print ("[config] '%s'=" % f) + str(categories[0])

    self.renderer = renderer
    self.renderer_big = renderer_big
    self.renderer_httpheaders = renderer_httpheaders


if not occi_config:
    occi_config_init()
