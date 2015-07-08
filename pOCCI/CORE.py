import json, re
import sys, time

from occi_libs import *
from occi_curl import occi_curl

categories = []

#'Category: offline;scheme="http://schemas.ogf.org/occi/infrastructure/storagelink/action#";class="action";title="deactivate storagelink"'
required_categories = [
    'http://schemas.ogf.org/occi/core#entity',
    'http://schemas.ogf.org/occi/core#resource',
    'http://schemas.ogf.org/occi/core#link'
]


# parse and check the body, and get categories
def parse_body(body):
    err_msg = []
    categories = []
    category_ids = {}
    check_headers = True
    check_unique = True

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

            # check uniqueness
            key = item['category'] + item['scheme']
            if key in category_ids.keys():
                check_unique = False
                duplicate_item = item
            else:
                category_ids[key] = True
        else:
            check_headers = False

    if not check_headers:
        err_msg.append('Only "Category" expected response headers')

    if not check_unique:
        err_msg.append('Category not unique (term "%s", scheme "%s")' % (duplicate_item['category'], duplicate_item['scheme']))

    return [check_headers and check_unique, categories, err_msg]


def get_categories():
    global categories

    body, response_headers, http_status, content_type = occi_curl()

    # TODO: ignoring possible errors
    check_parse, categories, err_msg = parse_body(body)

    return [body, response_headers, http_status, content_type]


def check_content_type(content_type):
    if content_type in ['text/occi', 'text/plain', 'application/occi+json']:
        return [True, []]
    else:
        return [False, ['Wrong Content-Type in response']]


def check_requested_content_type(content_type):
    if content_type == occi_config['mimetype']:
        return [True, []]
    else:
        return [False, ['Result mime type differs']]

def pretest_http_status(http_ok_status):
    err_msg = []
    check_pretest = True
    body = None
    response_headers = None
    http_status = None
    content_type = None

    global categories
    if not categories:
        body, response_headers, http_status, content_type = get_categories()
        if not re.match(r'^HTTP/.* %i OK' % http_ok_status, http_status):
            check_pretest = False
            err_msg.append('HTTP status from getting categories not %i OK (%s)' % (http_ok_status, http_status))
    return [body, response_headers, http_status, content_type, check_pretest, err_msg]

def DISCOVERY001():
    err_msg = []
    
    check01 = False
    check02 = False
    check03 = False
    
    body, response_headers, http_status, content_type, check_pretest, tmp_err_msg = pretest_http_status(200)
    err_msg += tmp_err_msg

    check01, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg
    
    check02, tmp_err_msg = check_requested_content_type(content_type)
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

    return [check_pretest and check01 and check02 and check03, err_msg]


def DISCOVERY002():
    err_msg = []
    
    check02a = False
    check02b = False

    body, response_headers, http_status, content_type, check_pretest, tmp_err_msg = pretest_http_status(200)
    err_msg += tmp_err_msg

    cat_in = []
    cat_in.append('Content-Type: text/occi')
    cat_in.append('Category: %s; scheme="%s"; class="%s"' % (categories[0]['category'], categories[0]['scheme'], categories[0]['class']))

    body, response_headers, http_status, content_type = occi_curl(headers = cat_in)

    check01, err_msg = check_content_type(content_type)
    
    if re.match(r'^HTTP/.* 200 OK', http_status):
        check02a = True
    else:
        err_msg.append('HTTP status on filter not 200 OK (%s)' % http_status)

    check02b, tmp_err_msg = check_requested_content_type(content_type)
    err_msg += tmp_err_msg

    check_parse, filtered_categories, tmp_err_msg = parse_body(body)
    err_msg += tmp_err_msg

    category = categories[0]
    check_filter = False
    for item in filtered_categories:
        if category['category'] == item['category'] and category['scheme'] == item['scheme'] and category['class'] == item['class']:
            check_filter = True
            break
    if not check_filter:
        err_msg.append('Category "%s" (schema "%s") not in filtered result' % (category['category'], category['scheme']))

    return [check_pretest and check01 and check02a and check02b and check_parse and check_filter, err_msg]
