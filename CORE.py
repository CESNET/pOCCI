#!/usr/bin/python

import json, re
import sys, time
from occi_curl import occi_curl
from occi_libs import *
import my_config

results = []

categories = []

#'Category: offline;scheme="http://schemas.ogf.org/occi/infrastructure/storagelink/action#";class="action";title="deactivate storagelink"'
required_categories = [
    'http://schemas.ogf.org/occi/core#entity',
    'http://schemas.ogf.org/occi/core#resource',
    'http://schemas.ogf.org/occi/core#link'
]


def get_categories():
    body, response_headers, http_status, content_type = occi_curl()

    for line in body:
        item = {}
        chunks = re.split(';', line)
        if re.match(r'^Category:', chunks[0]):
            value = re.sub(r'^Category:\s+', '', chunks[0])
            item['category'] = value

            # skip the first chunk (category)
            for chunk in chunks[1:]:
                keyvalue = re.split(r'\s*=\s*', chunk, 1)
                key = keyvalue[0]
                value = keyvalue[1].strip('"')
                item[key] = value

            categories.append(item)

    return [body, response_headers, http_status, content_type]

def check_content_type(content_type):
    if content_type in ['text/occi', 'text/plain', 'application/occi+json']:
        return [True, []]
    else:
        return [False, ['Wrong Content-Type in response']]


def check_requested_content_type(content_type):
    if content_type == my_config.mimetype:
        return [True, []]
    else:
        return [False, ['Result mime type differs']]


def DISCOVERY001():
    body, response_headers, http_status, content_type = get_categories()

    err_msg = []
    check01 = False
    check02a = False
    check02b = False
    check03 = False

    check01, err_msg = check_content_type(content_type)

    if re.match(r'^HTTP/.* 200 OK', http_status):
        check02a = True
    else:
        err_msg.append('HTTP status not 200 OK (%s)' % http_status)

    check02b, tmp_err_msg = check_requested_content_type(content_type)
    err_msg += tmp_err_msg

    count = 0
    for category in required_categories:
        for line in body:
            if re.search(r"%s" % category, line):
                count += 1
                break
    if count == 3:
        check03 = True
    else:
        err_msg.append('Body doesn\'t contain appropriate categories')

    return [check01 and check02a and check02b and check03, err_msg]


def DISCOVERY002():
    check_pretest = True
    check02 = False
    err_msg = []

    if not categories:
        body, response_headers, http_status, content_type = get_categories()
        if not re.match(r'^HTTP/.* 200 OK', http_status):
            check_pretest = False
            err_msg.append('HTTP status from getting categories not 200 OK (%s)' % http_status)

    cat_in = []
    cat_in.append('Content-Type: text/occi')
    cat_in.append('Category: %s; scheme="%s"; class="%s"' % (categories[0]['category'], categories[0]['scheme'], categories[0]['class']))

    #print cat_in

    body, response_headers, http_status, content_type = occi_curl(headers = cat_in)

    check01, err_msg = check_content_type(content_type)

    check02b, tmp_err_msg = check_requested_content_type(content_type)
    err_msg += tmp_err_msg

    if re.match(r'^HTTP/.* 200 OK', http_status):
        check02 = True
    else:
        err_msg.append('HTTP status on filter not 200 OK (%s)' % http_status)

    for line in body:
        print line

    return [check_pretest and check01 and check02 and check02b, err_msg]


start_time = time.time()
result, err_msg = DISCOVERY001()
running_time = time.time() - start_time
results.append(occi_test('OCCI/CORE/DISCOVERY/001', result, err_msg, running_time))

start_time = time.time()
result, err_msg = DISCOVERY002()
running_time = time.time() - start_time
results.append(occi_test('OCCI/CORE/DISCOVERY/002', result, err_msg, running_time))
results = occi_format(results)

occi_print(results)

if result:
    sys.exit(0)
else:
    sys.exit(1)

