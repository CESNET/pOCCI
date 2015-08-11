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
        tests = ['CORE/DISCOVERY/001', 'CORE/DISCOVERY/002', 'INFRA/CREATE/001', 'INFRA/CREATE/002', 'INFRA/CREATE/003', 'INFRA/CREATE/004', 'CORE/READ/001', 'CORE/READ/002']

    if 'CORE/DISCOVERY/001' in tests:
        start_time = time.time()
        result, err_msg = CORE_DISCOVERY001()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/CORE/DISCOVERY/001', result, err_msg, running_time))

    if 'CORE/DISCOVERY/002' in tests:
        start_time = time.time()
        result, err_msg = CORE_DISCOVERY002()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/CORE/DISCOVERY/002', result, err_msg, running_time))

    if 'CORE/READ/001' in tests:
        start_time = time.time()
        result, err_msg = CORE_READ001()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/CORE/READ/001', result, err_msg, running_time))

    if 'CORE/READ/002' in tests:
        start_time = time.time()
        result, err_msg = CORE_READ002()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/CORE/READ/002', result, err_msg, running_time))

    if 'CORE/CREATE/001' in tests:
        start_time = time.time()
        result, err_msg = CORE_CREATE001()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/CORE/CREATE/001', result, err_msg, running_time))

    if 'INFRA/CREATE/001' in tests:
        start_time = time.time()
        result, err_msg = INFRA_CREATE001()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/INFRA/CREATE/001', result, err_msg, running_time))

    if 'INFRA/CREATE/002' in tests:
        start_time = time.time()
        result, err_msg = INFRA_CREATE002()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/INFRA/CREATE/002', result, err_msg, running_time))

    if 'INFRA/CREATE/003' in tests:
        start_time = time.time()
        result, err_msg = INFRA_CREATE003()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/INFRA/CREATE/003', result, err_msg, running_time))

    if 'INFRA/CREATE/004' in tests:
        start_time = time.time()
        result, err_msg = INFRA_CREATE004()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/INFRA/CREATE/004', result, err_msg, running_time))

    if 'INFRA/CREATE/005' in tests:
        start_time = time.time()
        result, err_msg = INFRA_CREATE005()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/INFRA/CREATE/005', result, err_msg, running_time))

    if 'INFRA/CREATE/006' in tests:
        start_time = time.time()
        result, err_msg = INFRA_CREATE006()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/INFRA/CREATE/006', result, err_msg, running_time))

    results = occi_format(results)
    occi_print(results, occi_config['outputformat'])

    if results['failed'] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])

