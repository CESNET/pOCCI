#!/usr/bin/python

import getopt
import json, re
import sys, time
import os

from occi_libs import *
from CORE import *
from occi_curl import occi_curl
import version


tests_definitions = {
    'OCCI/CORE/DISCOVERY/001': CORE_DISCOVERY001,
    'OCCI/CORE/DISCOVERY/002': CORE_DISCOVERY002,
    'OCCI/CORE/READ/001': CORE_READ001,
    'OCCI/CORE/READ/002': CORE_READ002,
    'OCCI/CORE/CREATE/001': CORE_CREATE001,
    'OCCI/CORE/CREATE/006': CORE_CREATE006,
    'OCCI/CORE/DELETE/001': CORE_DELETE001,
    'OCCI/CORE/UPDATE/001': CORE_UPDATE001,

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


def usage(name = __file__):
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
  --passphrase PASS ......... SSL key passphrase\n\
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
        opts, args = getopt.getopt(argv,"ha:c:e:f:k:lm:p:t:u:vV",["help", "auth-type=", "cert=", "endpoint=", "format=", "key=", "list", "mime-type=", "passphrase=", "password=", "tests=", "url=", "user=", "verbose", "version"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-a", "--auth-type"):
            occi_config["authtype"] = arg
        elif opt in ("-c", "--cert"):
            occi_config["cert"] = arg
        elif opt in ("-e", "--endpoint", "--url"):
            occi_config["url"] = arg
        elif opt in ("-f", "--format"):
            occi_config['outputformat'] = arg
        elif opt in ("-k", "--key"):
            occi_config["key"] = arg
        elif opt in ("-l", "--list"):
            print '\n'.join(sorted(tests_definitions.keys()));
            sys.exit();
        elif opt in ("-m", "--mime-type"):
            occi_config['mimetype'] = arg
        elif opt in ("--passphrase"):
            occi_config["passphrase"] = arg
        elif opt in ("-p", "--password"):
            occi_config["passwd"] = arg
        elif opt in ("-t", "--tests"):
            tests = arg.split(",")
        elif opt in ("-u", "--user"):
            occi_config["user"] = arg
        elif opt in ("-v", "--verbose"):
            occi_config['curlverbose'] = True
        elif opt in ("-V", "--version"):
            print version.__version__
            sys.exit()

    if not tests:
        tests = sorted(list(set(tests_definitions.keys()) - tests_skipped))

    if 'url' not in occi_config or not occi_config['url']:
        print 'OCCI URL required'
        sys.exit(2)

    if occi_config['authtype'] == 'basic':
        if 'user' not in occi_config or not occi_config['user'] or 'passwd' not in occi_config or not occi_config['passwd']:
            print 'User and password is required for "basic" authentization type.'
            sys.exit(2)
    elif occi_config['authtype'] == 'x509':
        if 'cert' not in occi_config or not occi_config['cert'] or 'key' not in occi_config or not occi_config['key']:
            print 'SSL certificate and key is required for "x509" authentization type.'
            sys.exit(2)

    occi_init()
    testsuite_init()

    for test in tests:
        if not re.match(r'OCCI/', test):
            test = 'OCCI/' + test
        if test in tests_definitions.keys():
            start_time = time.time()
            result, err_msg = tests_definitions[test]()
            running_time = time.time() - start_time
            results.append(occi_test(test, result, err_msg, running_time))

    results = occi_format(results)
    occi_print(results, occi_config['outputformat'])

    if results['failed'] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
