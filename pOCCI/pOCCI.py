#!/usr/bin/python

import json, re
import sys, time

from occi_libs import *


occi_init()
if not occi_config:
    print >> sys.stderr, 'No configuration found'
    sys.exit(2)

from CORE import *
from occi_curl import occi_curl

import getopt

def main(argv=sys.argv[1:]):
    results = []
    tests = []
    try:
        opts, args = getopt.getopt(argv,"ht:",["help","tests="])
    except getopt.GetoptError:
        print 'pOCCI.py -h -t <TEST1,TEST2>'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print 'pOCCI.py -h -t <TEST1,TEST2>'
            sys.exit()
        elif opt in ("-t", "--tests"):
            tests = arg.split(",")

    if not tests:
        tests = ['DISCOVERY001', 'DISCOVERY002']

    if 'DISCOVERY001' in tests:
        start_time = time.time()
        result, err_msg = DISCOVERY001()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/CORE/DISCOVERY/001', result, err_msg, running_time))

    if 'DISCOVERY002' in tests:
        start_time = time.time()
        result, err_msg = DISCOVERY002()
        running_time = time.time() - start_time
        results.append(occi_test('OCCI/CORE/DISCOVERY/002', result, err_msg, running_time))

    results = occi_format(results)
    occi_print(results, occi_config['outputformat'])

    if results['failed'] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])

