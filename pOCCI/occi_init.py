import ConfigParser
import os

occi_config = {}

def occi_init():
    """Initialize pOCCI.

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

if not occi_config:
    occi_init()

