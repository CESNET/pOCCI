#!/usr/bin/python

import getopt
import re
import sys
import time
import os

from occi_libs import *
from CORE import *
import occi
import version


tests_definitions = {
    'OCCI/CORE/DISCOVERY/001': CORE_DISCOVERY001,
    'OCCI/CORE/DISCOVERY/002': CORE_DISCOVERY002,
    'OCCI/CORE/READ/001': CORE_READ001,
    'OCCI/CORE/READ/002': CORE_READ002,
    'OCCI/CORE/READ/007': CORE_READ007,
    'OCCI/CORE/CREATE/001': CORE_CREATE001,
    'OCCI/CORE/CREATE/006': CORE_CREATE006,
    'OCCI/CORE/DELETE/001': CORE_DELETE001,
    'OCCI/CORE/UPDATE/001': CORE_UPDATE001,
    'OCCI/CORE/MISC/001': CORE_MISC001,

    'OCCI/INFRA/CREATE/001': INFRA_CREATE001,
    'OCCI/INFRA/CREATE/002': INFRA_CREATE002,
    'OCCI/INFRA/CREATE/003': INFRA_CREATE003,
    'OCCI/INFRA/CREATE/004': INFRA_CREATE004,
    'OCCI/INFRA/CREATE/005': INFRA_CREATE005,
    'OCCI/INFRA/CREATE/006': INFRA_CREATE006,
    'OCCI/INFRA/CREATE/007': INFRA_CREATE007,
}


tests_skipped = set([
    'OCCI/CORE/CREATE/001',
    'OCCI/CORE/CREATE/006',
    'OCCI/INFRA/CREATE/005',
])


def usage(name=__file__):
    print "%s [OPTIONS]\n\
\n\
OPTIONS:\n\
  -h, --help ................ usage message\n\
  -a, --auth-type AUTH ...... authentization type\n\
  -c, --cert FILE ........... SSL certificate file\n\
  -e, --endpoint, --url URL . OCCI server endpoint\n\
  -f, --format FORMAT ....... output format (plain, json)\n\
  -k, --key FILE ............ SSL key file\n\
  -l, --list ................ list all test\n\
  -m, --mime-type MIME-TYPE . render format\n\
  -p, --password PWD ........ password for basic auth-type\n\
  -P, --passphrase PASS ..... SSL key passphrase\n\
  -s, --keystone TENANT ..... tenant used for keystone auth\n\
  -S, --ignore-ssl .......... ignore SSL errors\n\
  -t, --tests <TEST1,...> ... list of tests\n\
  -u, --user USER ........... user name for basic auth-type\n\
  -v, --verbose ............. verbose mode\n\
  -V, --version ............. print version information\n\
\n\
MIME-TYPE: text/plain, text/occi\n\
AUTH: basic\n\
" % os.path.basename(name)


def main(argv=sys.argv[1:]):
    results = []
    tests = []

    if not occi_config:
        print >> sys.stderr, 'No configuration found'
        sys.exit(2)

    try:
        opts, args = getopt.getopt(argv, "ha:c:e:f:k:lm:p:Ps::St:u:vV", ["help", "auth-type=", "cert=", "endpoint=", "format=", "ignore-ssl", "keystone=", "key=", "list", "mime-type=", "passphrase=", "password=", "tests=", "url=", "user=", "verbose", "version"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            usage()
            sys.exit()
        elif opt in ["-a", "--auth-type"]:
            occi_config["authtype"] = arg
        elif opt in ["-c", "--cert"]:
            occi_config["cert"] = arg
        elif opt in ["-e", "--endpoint", "--url"]:
            occi_config["url"] = arg
        elif opt in ["-f", "--format"]:
            occi_config['outputformat'] = arg
        elif opt in ["-k", "--key"]:
            occi_config["key"] = arg
        elif opt in ["-l", "--list"]:
            print '\n'.join(sorted(tests_definitions.keys()))
            sys.exit()
        elif opt in ["-m", "--mime-type"]:
            occi_config['mimetype'] = arg
        elif opt in ["-P", "--passphrase"]:
            occi_config["passphrase"] = arg
        elif opt in ["-p", "--password"]:
            occi_config["passwd"] = arg
        elif opt in ["-s", "--keystone"]:
            occi_config["keystone"] = True
        elif opt in ["-S", "--ignore-ssl"]:
            occi_config["ignoressl"] = True
        elif opt in ["-t", "--tests"]:
            tests = arg.split(",")
        elif opt in ["-u", "--user"]:
            occi_config["user"] = arg
        elif opt in ["-v", "--verbose"]:
            occi_config['curlverbose'] = True
        elif opt in ["-V", "--version"]:
            print version.__version__
            sys.exit()

    if not tests:
        tests = sorted(list(set(tests_definitions.keys()) - tests_skipped))

    if 'url' not in occi_config or not occi_config['url']:
        print 'OCCI URL required'
        sys.exit(2)

    if occi_config['authtype'] == 'basic':
        if 'user' not in occi_config or not occi_config['user']:
            print 'User and password is required for "basic" authentization type.'
            sys.exit(2)
    elif occi_config['authtype'] == 'x509':
        if 'X509_USER_PROXY' in os.environ:
            if 'cert' not in occi_config or not occi_config['cert']:
                occi_config['cert'] = os.environ['X509_USER_PROXY']
            if 'cachain' not in occi_config or not occi_config['cachain']:
                occi_config['cachain'] = os.environ['X509_USER_PROXY']
        if 'cert' not in occi_config or not occi_config['cert']:
            print 'SSL certificate and key is required for "x509" authentization type.'
            sys.exit(2)
        if 'capath' not in occi_config or not occi_config['capath']:
            if 'X509_CERT_DIR' in os.environ:
                occi_config['capath'] = os.environ['X509_CERT_DIR']
            elif os.path.isdir('/etc/grid-security/certificates'):
                occi_config['capath'] = '/etc/grid-security/certificates'


    occi_init()
    testsuite_init()

    for test in tests:
        if not re.match(r'OCCI/', test):
            test = 'OCCI/' + test
        if test in tests_definitions.keys():
            start_time = time.time()
            try:
                result, err_msg = tests_definitions[test].test()
            except occi.Error as oe:
                if occi_config['curlverbose']:
                    raise oe
                else:
                    print '%s error: %s' % (test, str(oe))
                    sys.exit(2)
            objective = tests_definitions[test].objective
            running_time = time.time() - start_time
            results.append(occi_test(test, objective, result, err_msg, running_time))

    results = occi_format(results)
    occi_print(results, occi_config['outputformat'])

    if results['failed'] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
