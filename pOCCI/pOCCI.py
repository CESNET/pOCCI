#!/usr/bin/python

import getopt
import json, re
import sys, time
import os

from occi_libs import *

if not occi_config:
    print >> sys.stderr, 'No configuration found'
    sys.exit(2)

from CORE import *
from occi_curl import occi_curl


tests_definitions = {
    'OCCI/CORE/DISCOVERY/001': CORE_DISCOVERY001,
    'OCCI/CORE/DISCOVERY/002': CORE_DISCOVERY002,
    'OCCI/CORE/READ/001': CORE_READ001,
    'OCCI/CORE/READ/002': CORE_READ002,
    'OCCI/CORE/CREATE/001': CORE_CREATE001,
    'OCCI/CORE/CREATE/006': CORE_CREATE006,

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
  -f, --format FORMAT ....... output format (plain, json)\n\
  -t, --tests <TEST1,...> ... list of tests\n\
  -v, --verbose ............. verbose mode\n\
" % os.path.basename(name)


def main(argv=sys.argv[1:]):
    results = []
    tests = []

    try:
        opts, args = getopt.getopt(argv,"hf:t:v",["help", "format=", "tests=", "verbose"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-f", "--format"):
            occi_config['outputformat'] = arg
        elif opt in ("-t", "--tests"):
            tests = arg.split(",")
        elif opt in ("-v", "--verbose"):
            occi_config['curlverbose'] = True

    if not tests:
        tests = sorted(list(set(tests_definitions.keys()) - tests_skipped))

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

