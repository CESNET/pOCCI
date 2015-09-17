import json
import os
import sys
import ConfigParser
from collections import OrderedDict

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

    'occi.tests.category': {'term': 'compute', 'class': 'kind', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#'},
    'occi.tests.entity': {},
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

    out = OrderedDict()
    out['tests'] = results
    out['passed'] = count_o
    out['failed'] = count_f
    return out


def html_escape(s):
    s = str(s)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace("\n", "<br>")
    return s


def occi_print(results, outputformat):
    if outputformat == 'plain':
        for r in results['tests']:
            print '%s  %s' % (r['name'], r['status'])
            if 'reason' in r:
                print >> sys.stderr, r['reason']
    elif outputformat == 'json':
        print json.dumps(results, indent=4)
    elif outputformat in ['html', 'htmltable']:
        if outputformat == 'html':
            print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n\
<html>\n\
\n\
<head>\n\
    <title>OCCI Compliance Tests Results</title>\n\
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8">\n\
    <style type="text/css">\n\
        th {text-align:left}\n\
        td.ok {color:green}\n\
        td.fail {color:red}\n\
        td.skipped {color:orange}\n\
    </style>\n\
</head>\n\
\n\
<body>\n\
\n\
<table>\n\
    <tr>\n\
        <th>Test</th>\n\
        <th>Running Time</th>\n\
        <th>Status</th>\n\
        <th>Reason</th>\n\
    </tr>'
        for r in results['tests']:
            css = 'skipped'
            if r['status'] == 'OK':
                css = 'ok'
            elif r['status'] == 'FAIL':
                css = 'fail'
            objective = ''
            if 'objective' in r:
                objective = html_escape(r['objective'])
            reason = ''
            if 'reason' in r:
                reason = '\n'.join(r['reason'])
            print '    <tr class="%s">' % css
            print '        <td class="name">%s</td>' % html_escape(r['name'])
            print '        <td class="objective">%s</td>' % html_escape(objective)
            print '        <td class="time">%s</td>' % html_escape(r['running_time'])
            print '        <td class="%s">%s</td>' % (css, html_escape(r['status']))
            print '        <td class="reason">%s</td>' % html_escape(reason)
            print '    </tr>'
        if outputformat == 'html':
            print '</table>\n\
\n\
</body>\n\
\n\
</html>'
    else:
        print >> sys.stderr, 'Only "plain", "json" output types are possible'


def occi_test(name, objective, status, err_msg, running_time=None):
    test = OrderedDict()
    test['name'] = name
    if objective is not None:
        test['objective'] = objective
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
        if key not in occi_config:
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

    self.renderer = renderer
    self.renderer_big = renderer_big
    self.renderer_httpheaders = renderer_httpheaders


if not occi_config:
    occi_config_init()
