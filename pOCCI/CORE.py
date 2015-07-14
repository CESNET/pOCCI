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

example_attributes = {
    'occi.core.id': 1,
}


# occi.core.id{immutable required} occi.core.title occi.core.target occi.core.source{required}
def parse_attributes(chunk, err_msg):
    result = []

    m = True
    while m:
        m = re.match(r'([^\{ ]+)(\{[^\}]*\})?\s*', chunk)
        if not m:
            break
        matches = m.groups()
        name = matches[0]
        attrs = matches[1]
        chunk = chunk[m.end():]

        if attrs:
            attrs = attrs[1:-1]
            attrs = re.split(' ', attrs)

        result.append({'name': name, 'attrs': attrs})

    if chunk:
        err_msg.append('Error parsing OCCI attributes')
        return None

    return result


# parse and check the body, and get categories
def parse_body(body, err_msg):
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

    return [check_headers and check_unique, categories]


def get_categories(err_msg):
    global categories

    body, response_headers, http_status, content_type = occi_curl()

    check_parse, categories = parse_body(body, err_msg)

    if occi_config['curlverbose']:
        print '==== CATEGORIES ===='
        for category in categories:
            print category
        print '===================='

    return [check_parse, body, response_headers, http_status, content_type]


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


def check_http_status(http_expected_status, http_status):
    if not re.match(r'^HTTP/.* %s' % http_expected_status, http_status):
        return [False, ['HTTP status from getting categories not %s (%s)' % (http_expected_status, http_status)]]
    else:
        return [True, []]


def pretest_http_status(http_ok_status, err_msg):
    check_pretest = True
    check_categories = True
    body = None
    response_headers = None
    http_status = None
    content_type = None

    global categories
    if not categories:
        check_categories, body, response_headers, http_status, content_type = get_categories(err_msg)
        check_pretest, tmp_err_msg = check_http_status(http_ok_status, http_status)
        err_msg += tmp_err_msg
    return [body, response_headers, http_status, content_type, check_pretest and check_categories]


def match_category(category, filter):
    for key, value in filter.items():
        if not (key in category and category[key] == value):
            return False
    return True


def search_category(filter):
    for cat in categories:
        if match_category(cat, filter):
            return cat
    return None


def check_body_resource(body):
    #['X-OCCI-Location: https://myriad5.zcu.cz:11443/compute/3eda9528-d40a-4a00-b4e1-d5fe51a95e4a']
    expected = 'X-OCCI-Location:'
    for line in body:
        if re.match(r'%s' % expected, line):
            return [True, []]
        else:
            return [False, ['HTTP Body doesn\'t contain the OCCI Compute Resource description: "%s" expected "%s"' % (line, expected)]]


def CORE_DISCOVERY001():
    err_msg = []
    
    check01 = False
    check02 = False
    check03 = False
    
    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

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


def CORE_DISCOVERY002():
    err_msg = []
    
    check02a = False
    check02b = False

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)
    if not categories:
        err_msg += ['No categories returned']
        return [False, err_msg]

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

    check_parse, filtered_categories = parse_body(body, err_msg)

    category = categories[0]
    check_filter = False
    for item in filtered_categories:
        if category['category'] == item['category'] and category['scheme'] == item['scheme'] and category['class'] == item['class']:
            check_filter = True
            break
    if not check_filter:
        err_msg.append('Category "%s" (schema "%s") not in filtered result' % (category['category'], category['scheme']))

    return [check_pretest and check01 and check02a and check02b and check_parse and check_filter, err_msg]


def CORE_CREATE001():
    err_msg = []
    has_kind = True

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    #kind = search_category({'class': 'kind'})
    kind = search_category({'class': 'kind', 'category': 'compute'})
    #print kind

    if not kind:
        has_kind = False
        err_msg.append('No OCCI Kind found')
    for item in ['location', 'category', 'scheme']:
        if not item in kind.keys():
            has_kind = False
            err_msg.append('No %s in OCCI Kind' % item)

    #new_cat = '\n\r'.join([
    #    'Category: %s; scheme="%s"; class="%s";' % (kind['category'], kind['scheme'], kind['class']),
    #])
    #new_cat = dict()
    #new_cat['Category'], '%s; scheme="%s"; class="%s";' % (kind['category'], kind['scheme'], kind['class'])
    ##new_cat['X-OOCI-Attribute'] = 'occi.core.id=1'

    new_cat = 'Category: compute; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind"; title="titulek"\n\r\
X-OCCI-Attribute: occi.core.id="titulek"\n\r\
X-OCCI-Attribute: occi.core.title="titulek"\n\r\
X-OCCI-Attribute: occi.core.summary="sumarko"\n\r\
X-OCCI-Attribute: occi.compute.architecture="arch"\n\r\
'

    body, response_headers, http_status, content_type = occi_curl(url = kind['location'], headers = ['Content-Type: text/plain'], post=new_cat)
#, headers = ['Content-Type: text/plain', 'Category: compute; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind"; title="titulek2"']
    check_create, tmp_err_msg = check_http_status("201 Created", http_status)
    err_msg += tmp_err_msg

    if not check_create:
        print body

    return [has_kind and check_create, err_msg]


def INFRA_CREATE001():
    err_msg = []
    has_kind = True
    has_tpl = True
    has_all_attributes = True
    check_attributes = True
    attributes = {}

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    kind = search_category({'class': 'kind', 'category': 'compute', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#'})
    os_tpl = search_category({'class': 'mixin', 'rel': 'http://schemas.ogf.org/occi/infrastructure#os_tpl'})
    #print kind
    #print os_tpl

    if not kind:
        has_kind = False
        err_msg.append('No OCCI Kind found')
    if not os_tpl:
        has_tpl = False
        err_msg.append('No OS template found')
    if not kind or not os_tpl:
        return [False, err_msg]

    for item in ['location', 'category', 'scheme']:
        if not item in kind.keys():
            has_kind = False
            err_msg.append('No %s in OCCI Kind' % item)

    request = []
    request.append('Category: compute; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind"')
    # 'category': 'uuid_ttylinux_0', 'scheme': 'http://occi.myriad5.zcu.cz/occi/infrastructure/os_tpl#', 'class': 'mixin'
    request.append('Category: %s; scheme="%s"; class="%s"' % (os_tpl['category'], os_tpl['scheme'], 'mixin'))

    attributes_compute = []
    if 'attributes' in kind:
        attributes_compute = parse_attributes(kind['attributes'], err_msg)
    if attributes_compute == None:
        attributes_compute = []
        check_attributes = False

    attributes_os_tpl = []
    if 'attributes' in os_tpl:
        attributes_os_tpl = parse_attributes(os_tpl['attributes'], err_msg)
    if attributes_os_tpl == None:
        attributes_os_tpl = []
        check_attributes = False

    attributess = attributes_compute + attributes_os_tpl
    #print attribues
    for a in attributes:
        #print 'attribute: %s' % a
        if a['attrs'] and 'required' in a['attrs']:
            if a['name'] not in example_attributes:
                err_msg.append('Tests error: unknown attribute %s' % a['name'])
                has_all_attributes = False
                continue
            request.append('X-OCCI-Attribute: %s="%s"' % (a['name'], example_attributes[a['name']]))

    post = '\n'.join(request)

    body, response_request, http_status, content_type = occi_curl(url = kind['location'], headers = ['Content-Type: text/plain'], post=post)
    check_create, tmp_err_msg = check_http_status("201 Created", http_status)
    err_msg += tmp_err_msg

    check_ct, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg

    check_br, tmp_err_msg = check_body_resource(body)
    err_msg += tmp_err_msg

    if not check_create:
        print body

    return [has_kind and has_tpl and check_attributes and has_all_attributes and check_create and check_ct and check_br, err_msg]
