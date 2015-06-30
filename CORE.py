#!/usr/bin/python

import json, re
import sys, time
from occi_curl import occi_curl
from occi_libs import *
import my_config

results = []

category = []


def get_categories():
    body, h, http_status, content_type = occi_curl()

    for line in body:
        item = {}
        chunks = re.split(';', line)
        if re.match(r'^Category:', chunks[0]):
            value = re.sub(r'^Category:\s+', '', chunks[0])
            item['id'] = value

            # skip the first chunk (category)
            for chunk in chunks[1:]:
                keyvalue = re.split(r'\s*=\s*', chunk, 1)
                print keyvalue
                key = keyvalue[0]
                value = keyvalue[1].strip('"')
                item[key] = value

            category.append(item)

    return [body,  h, http_status, content_type]


def DISCOVERY001():
    body, h, http_status, content_type = get_categories()

    err_msg = []
    check01 = False
    check02a = False
    check02b = False
    check03 = False

    if content_type in ['text/occi', 'text/plain', 'application/occi+json']:
        check01 = True
    else:
        err_msg.append('Wrong Content-Type')

    if re.match(r'^HTTP/.* 200 OK', http_status):
        check02a = True
    else:
        err_msg.append('HTTP status not 200 OK')

    if content_type == my_config.mimetype:
        check02b = True
    else:
        err_msg.append('Result mime type differs')

    #'Category: offline;scheme="http://schemas.ogf.org/occi/infrastructure/storagelink/action#";class="action";title="deactivate storagelink"'
    categories = ['http://schemas.ogf.org/occi/core#entity', 'http://schemas.ogf.org/occi/core#resource', 'http://schemas.ogf.org/occi/core#link']
    count = 0
    for category in categories:
        for line in body:
            if re.search(r"%s" % category, line):
                count += 1
                break
    if count == 3:
        check03 = True
    else:
        err_msg.append('Body doesn\'t contain appropriate categories')

    return [check01 and check02a and check02b and check03, err_msg]

start_time = time.time()
result, err_msg = DISCOVERY001()
running_time = time.time() - start_time
results.append(occi_test('OCCI/CORE/DISCOVERY/001', result, err_msg, running_time))

results = occi_format(results)
occi_print(results)

if result:
    sys.exit(0)
else:
    sys.exit(1)

