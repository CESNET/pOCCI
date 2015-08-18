import json, re
import sys, time
import urlparse

from occi_libs import *
from occi_curl import occi_curl
import occi
import render


categories = []

#'Category: offline;scheme="http://schemas.ogf.org/occi/infrastructure/storagelink/action#";class="action";title="deactivate storagelink"'
required_categories = [
    occi.Category({'scheme': 'http://schemas.ogf.org/occi/core#', 'term': 'entity'}),
    occi.Category({'scheme': 'http://schemas.ogf.org/occi/core#', 'term': 'resource'}),
    occi.Category({'scheme': 'http://schemas.ogf.org/occi/core#', 'term': 'link'}),
]

example_attributes = {
    'occi.core.id': occi.Attribute({'name': 'occi.core.id', 'value': '1'}),
    'occi.core.title': occi.Attribute({'name': 'occi.core.title', 'value': 'Test_title_%d' % time.time()}),
    'occi.storage.size': occi.Attribute({'name': 'occi.storage.size', 'type': 'number', 'value': 0.1}),
}


def get_categories(err_msg):
    global categories
    check_parse = True

    body, response_headers, http_status, content_type = occi_curl()

    try:
        categories = renderer.parse_categories(body)
    except occi.ParseError as pe:
        categories = []
        check_parse = False
        err_msg.append(repr(pe))

    if occi_config['curlverbose']:
        print '==== CATEGORIES ===='
        if check_parse:
            for category in categories:
                print category
        else:
            print 'ERROR: %s' % err_msg[-1]
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
        return [False, ['HTTP status is not %s (%s)' % (http_expected_status, http_status)]]
    else:
        return [True, []]


def pretest_http_status(http_ok_status, err_msg):
    check_pretest = True
    check_categories = True
    body = None
    response_headers = None
    http_status = None
    content_type = None

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
            return [True, line, []]
        else:
            return [False, line, ['HTTP Body doesn\'t contain the OCCI Compute Resource description: "%s" expected "%s"' % (line, expected)]]


def gen_id(prefix):
    return '%s_%d' % (prefix, time.time())


def CORE_DISCOVERY001():
    """
    Checks MIME type, Content-Type and required categories.
    """

    check_cat = False

    err_msg = []

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    check_ct, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg

    check_rct, tmp_err_msg = check_requested_content_type(content_type)
    err_msg += tmp_err_msg

    count = 0
    for category in required_categories:
        if search_category(category) != None:
            count += 1

    if count == len(required_categories):
        check_cat = True
    else:
        err_msg.append('Body doesn\'t contain appropriate categories')

    return [check_pretest and check_ct and check_rct and check_cat, err_msg]


def CORE_DISCOVERY002():
    err_msg = []
    filtered_categories = []

    check = True

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)
    if not categories:
        err_msg += ['No categories returned']
        return [False, err_msg]

    filter = occi.Category({
        'term': categories[0]['term'],
        'scheme': categories[0]['scheme'],
        'class': categories[0]['class'],
    })
    cat_in = []
    cat_in.append('Content-Type: text/occi')
    cat_in += renderer_httpheaders.render_category(filter)

    body, response_headers, http_status, content_type = occi_curl(headers = cat_in)

    check_ct, err_msg = check_content_type(content_type)

    if not re.match(r'^HTTP/.* 200 OK', http_status):
        check = False
        err_msg.append('HTTP status on filter not 200 OK (%s)' % http_status)

    check_rct, tmp_err_msg = check_requested_content_type(content_type)
    err_msg += tmp_err_msg

    try:
        filtered_categories = renderer.parse_categories(body)
    except occi.ParseError as pe:
        check = False

    check_filter = False
    for cat in filtered_categories:
        if match_category(cat, filter):
            check_filter = True
            break
    if not check_filter:
        err_msg.append('Category "%s" (scheme "%s") not in filtered result' % (filter['term'], filter['scheme']))

    return [check and check_pretest and check_ct and check_rct and check_filter, err_msg]


def CORE_CREATE001():
    """Create an OCCI Resource

    Unsupported test: Creating compute instances without os_tpl is not supported.

    It can be called by::
       pOCCI -t 'CORE/CREATE/001'
    """
    err_msg = []
    has_kind = True

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    #kind = search_category({'class': 'kind'})
    kind = search_category({'class': 'kind', 'term': 'compute'})
    #print kind

    if not kind:
        has_kind = False
        err_msg.append('No OCCI Kind found')
    for item in ['location', 'term', 'scheme']:
        if not item in kind.keys():
            has_kind = False
            err_msg.append('No %s in OCCI Kind' % item)

    new_cat = renderer.render_resource(
        categories = [
            occi.Category({
                'term': 'compute',
                'scheme': 'http://schemas.ogf.org/occi/infrastructure#',
                'class': 'kind',
                'title': 'titulek',
            }),
        ],
        attributes = [
            occi.Attribute({
                'name': 'occi.core.id',
                'value': gen_id('Compute'),
            }),
            occi.Attribute({
                'name': 'occi.core.title',
                'value': 'titulek',
            }),
            occi.Attribute({
                'name': 'occi.core.summary',
                'value': 'sumarko',
            }),
            occi.Attribute({
                'name': 'occi.compute.architecture',
                'value': 'arch',
            }),
        ]
    )

    body, response_headers, http_status, content_type = occi_curl(url = kind['location'], headers = ['Content-Type: text/plain'], post=new_cat)
    # when using HTTP headers rendering:
#    body, response_headers, http_status, content_type = occi_curl(url = kind['location'], headers = ['Content-Type: text/occi'] + new_cat, post=' ')
    check_create, tmp_err_msg = check_http_status("201 Created", http_status)
    err_msg += tmp_err_msg

    if not check_create:
        print body

    return [has_kind and check_create, err_msg]


def CORE_CREATE006():
    """Add an OCCI Mixin definition

    Unsupported test: Not implemented.

    It can be called by::
       pOCCI -t 'CORE/CREATE/006'
    """

    err_msg = []
    new_mixin = 'Category: stufik; scheme="http://example.com/occi/my_stuff#"; class="mixin"; location: "/mixin/resource_tpl/extra_large/", rel: "http://schemas.ogf.org/occi/infrastructure#resource_tpl"'
    #new_mixin = 'Category: stufik; scheme="http://example.com/occi/my_stuff#"; class="mixin"; rel="http:/example.com/occi/something_else#mixin"; location="/my_stuff/"'
    body, response_headers, http_status, content_type = occi_curl(url = '/-/', headers = ['Content-Type: text/plain'], post = new_mixin)
    check_create, tmp_err_msg = check_http_status("200 OK", http_status)
    err_msg += tmp_err_msg

    if not check_create:
        print body

    return [check_create, err_msg]


def CORE_READ_URL(filter):
    check_url = True
    check_200ok = False
    err_msg = []
    url = None

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    check_ct, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg

    mixin = search_category(filter)
    #kind =  search_category({'class': 'kind'})
    for category in [mixin]:
        body, response_headers, http_status, content_type = occi_curl(url = category['location'])
        try:
            locations = renderer.parse_locations(body)
        except occi.ParseError as pe:
            locations = []
            check_url = False
            err_msg.append(repr(pe))
        url = None
        if locations:
            url = locations[0]

        if re.match(r'^HTTP/.* 200 OK', http_status):
            check_200ok = True
        else:
            err_msg.append('Returned HTTP status is not 200 OK (%s)' % http_status)

    return [check_url and check_pretest and check_ct and check_200ok, err_msg, url]


def CORE_READ001():
    check, err_msg, url = CORE_READ_URL({'class': 'mixin'})
    return [check, err_msg]


def CORE_READ002_COMMON(category, links = []):
    check_url = True
    check_200ok = False
    err_msg = []
    headers = []

    headers.append('Content-Type: text/occi')
    headers += renderer_httpheaders.render_category(occi.Category({'term': category['term'], 'scheme': category['scheme'], 'class': category['class']}))

    body, response_headers, http_status, content_type = occi_curl(url = category['location'], headers = headers)
    try:
        locations = renderer.parse_locations(body)
    except occi.ParseError as pe:
        locations = []
        check_url = False
        err_msg.append(repr(pe))
    links[0:] = locations

    if re.match(r'^HTTP/.* 200 OK', http_status):
        check_200ok = True
    else:
        err_msg.append('Returned HTTP status is not 200 OK (%s)' % http_status)

    check_ct2, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg

    return [check_url and check_ct2 and check_200ok, err_msg]


def CORE_READ002():
    err_msg = []

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    check_ct, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg

    if not check_pretest:
        return [False, err_msg]

    mixin = search_category({'class': 'mixin'})
    #kind =  search_category({'class': 'kind'})
    for category in [mixin]:
        filter = search_category({'rel': '%s%s' % (category['scheme'], category['term'])})
        check_read, tmp_err_msg = CORE_READ002_COMMON(category = filter)
        err_msg += tmp_err_msg

    return [check_ct and check_read, err_msg]


def get_attributes(attribute_definitions, attributes, err_msg):
    """Fill attribute values from example_attributes for all required attributes.

    :param occi.AttributeDefinition attribute_definitions[]: attribute definitions
    :param occi.Attribute attributes{}: result attributes dictionary
    :param string err_msg[]: list of errors to append
    :return: all required attributes has a value
    :rtype: bool
    """
    has_all_attributes = True

    #print 'list of attributes: %s' % attributes
    for ad in attribute_definitions:
        #print 'attribute: %s' % ad
        if ad.isrequired() and not ad.isimmutable() and not ad['name'] in attributes:
            if ad['name'] not in example_attributes:
                err_msg.append('Tests error: unknown attribute %s' % ad['name'])
                has_all_attributes = False
                continue
            #print 'adding attribute: %s' % ad
            attributes[ad['name']] = example_attributes[ad['name']]

    return has_all_attributes


def CORE_DELETE001():
    err_msg = []

    check, err_msg, tmp_url = CORE_READ_URL({'term': 'compute', 'class': 'kind'})

    if not tmp_url:
        err_msg += ["OCCI entity URL not found!"]
        return [False, err_msg]

    url = urlparse.urlparse(tmp_url).path

    body, response_headers, http_status, content_type = occi_curl(url = url)
    check_exist1, tmp_err_msg = check_http_status("200 OK", http_status)
    err_msg += tmp_err_msg

    body, response_headers, http_status, content_type = occi_curl(url = url, custom_request = 'DELETE')
    check_delete1, tmp_err_msg = check_http_status("200 OK", http_status)
    err_msg += tmp_err_msg

    # It takes some time to delete machine, second delete action force it
    # Not testing result of the operation (various backends have different behaviour)
    body, response_headers, http_status, content_type = occi_curl(url = url, custom_request = 'DELETE')

    body, response_headers, http_status, content_type = occi_curl(url = url)
    check_exist2, tmp_err_msg = check_http_status("404 Not Found", http_status)
    err_msg += tmp_err_msg

    return [check_exist1 and check_exist2 and check_delete1, err_msg]


def INFRA_CREATE_COMMON(resource, categories, additional_attributes, err_msg):
    """Generic help function to create OCCI Infrastructure resources.

    HTTP Headers renderer is always used.

    :param string resource: OCCI Category term (compute, storage, network)
    :param occi.Category categories[]: OCCI Categories to add to rendering
    :param occi.AttributeDefinition additional_attributes[]: additional attributes to set from example defaults
    :param string err_msg[]: error messages list to append
    :return: status and error message list
    :rtype: [bool, string[]]
    """
    has_kind = True
    has_all_attributes = True
    all_attributes = []
    attributes = {}

    kind = search_category({'class': 'kind', 'term': resource, 'scheme': 'http://schemas.ogf.org/occi/infrastructure#'})
    #print kind

    if not kind:
        has_kind = False
        err_msg.append('No OCCI Kind found')
    if not kind:
        return [False, err_msg]

    for item in ['location', 'term', 'scheme']:
        if not item in kind.keys():
            has_kind = False
            err_msg.append('No %s in OCCI Kind' % item)

    if 'attributes' in kind:
        all_attributes += kind['attributes']

    if additional_attributes != None:
        all_attributes += additional_attributes

    #print 'list of attributes: %s' % repr(all_attributes)
    if not get_attributes(all_attributes, attributes, err_msg):
        has_all_attributes = False
    #print 'list of result attribute keys: %s' % repr(attributes.keys())

    post = renderer.render_resource(categories, None, attributes.values())

    body, response_request, http_status, content_type = occi_curl(url = kind['location'], headers = ['Content-Type: text/plain'], post=post)
    check_create, tmp_err_msg = check_http_status("201 Created", http_status)
    err_msg += tmp_err_msg

    check_ct, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg

    check_br, body_resource, tmp_err_msg = check_body_resource(body)
    err_msg += tmp_err_msg

    check_rct, tmp_err_msg = check_requested_content_type(content_type)
    err_msg += tmp_err_msg

    if not check_create:
        print body

    body, response_headers, http_status, content_type = occi_curl(url = kind['location'])
    check_created = False
    for line in body:
        if line == body_resource:
            check_created = True
            break
    if not check_created:
        err_msg.append('OCCI %s Resource hasn\'t been successfully created' % resource.title())

    return [has_kind and has_all_attributes and check_create and check_ct and check_br and check_rct and check_created, err_msg]


def INFRA_CREATE001():
    err_msg = []
    category = occi.Category({'term': 'compute', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#', 'class': 'kind'})

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    return INFRA_CREATE_COMMON('compute', [category], [], err_msg)


def INFRA_CREATE002():
    err_msg = []
    category = occi.Category({'term': 'storage', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#', 'class': 'kind'})
    additional_attributes = [
        occi.AttributeDefinition({"name": "occi.core.title", "required": True}),
        occi.AttributeDefinition({"name": "occi.storage.size", "required": True}),
    ]

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    return INFRA_CREATE_COMMON('storage', [category], additional_attributes, err_msg)


def INFRA_CREATE003():
    err_msg = []
    category = occi.Category({'term': 'network', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#', 'class': 'kind'})
    additional_attributes = [occi.AttributeDefinition({"name": "occi.core.title", "required": True})]

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    return INFRA_CREATE_COMMON('network', [category], additional_attributes, err_msg)


def INFRA_CREATE004():
    err_msg = []
    has_tpl = True
    categories = [
        occi.Category({'term': 'compute', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#', 'class': 'kind'})
    ]

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    os_tpl = search_category({'class': 'mixin', 'rel': 'http://schemas.ogf.org/occi/infrastructure#os_tpl'})
    #print os_tpl
    if not os_tpl:
        has_tpl = False
        err_msg.append('No OS template found')
        return [False, err_msg]

    # 'term': 'uuid_ttylinux_0', 'scheme': 'http://occi.myriad5.zcu.cz/occi/infrastructure/os_tpl#', 'class': 'mixin'
    categories.append(occi.Category({'term': os_tpl['term'], 'scheme': os_tpl['scheme'], 'class': 'mixin'}))

    if 'attributes' in os_tpl:
        os_tpl_attributes = os_tpl['attributes']
    else:
        os_tpl_attributes = []
    return INFRA_CREATE_COMMON('compute', categories, os_tpl_attributes, err_msg)


def INFRA_CREATE005():
    """
    Unsupported test, os_tpl required.

    It can be called by pOCCI -t 'INFRA/CREATE/005'
    """

    network_links = []
    storage_links = []
    err_msg = []
    check = True

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)

    check_ct, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg

    if not check_pretest:
        return [False, err_msg]

    storage = search_category({'term': 'storage', 'scheme':'http://schemas.ogf.org/occi/infrastructure#'})
    network = search_category({'term': 'network', 'scheme':'http://schemas.ogf.org/occi/infrastructure#'})
    check_read, tmp_err_msg = CORE_READ002_COMMON(category=storage, links=storage_links)
    if not check_read:
        check = False
    err_msg += tmp_err_msg

    check_read, tmp_err_msg = CORE_READ002_COMMON(category=network, links=network_links)
    if not check_read:
        check = False
    err_msg += tmp_err_msg

    print storage_links
    print network_links
    if not storage_links or not network_links:
        if not storage_links:
            err_msg.append('No storage found')
        if not network_links:
            err_msg.append('No network found')
        return [False, err_msg]

    compute = search_category({'term': 'compute', 'scheme':'http://schemas.ogf.org/occi/infrastructure#'})

    new_compute = 'Category: %s; scheme="%s"; class="%s"\n\r\
Link: <%s>; rel="%s"; category="%s"\n\r\
Link: <%s>; rel="%s"; category="%s"\n\r\
' % (compute['term'], compute['scheme'], compute['class'], storage_links[0], storage['scheme'] + storage['term'], 'http://schemas.ogf.org/occi/infrastructure#storagelink', network_links[0], network['scheme'] + network['term'], 'http://schemas.ogf.org/occi/infrastructure#networkinterface')

    body, response_headers, http_status, content_type = occi_curl(url = compute['location'], headers = ['Content-Type: text/plain'], post = new_compute)
    check_create, tmp_err_msg = check_http_status("201 Created", http_status)
    err_msg += tmp_err_msg

    if not check_create:
        print body

    return [check and check_create, err_msg]


def INFRA_CREATE_LINK(resource_name, resource_type):
    """
    Opennebula requires running compute instance.
    """

    err_msg = []
    check = True
    check_link = False
    compute_links = []
    resource_links = []
    resourcelink = None
    attributes = {}
    attribute_definitions = []

    body, response_headers, http_status, content_type, check_pretest = pretest_http_status("200 OK", err_msg)
    if not check_pretest:
        return [False, err_msg]

    compute = search_category({'term':'compute', 'scheme':'http://schemas.ogf.org/occi/infrastructure#'})
    resource = search_category({'term':resource_name, 'scheme':'http://schemas.ogf.org/occi/infrastructure#'})

    check_read, tmp_err_msg = CORE_READ002_COMMON(category=compute, links=compute_links)
    if not check_read:
        check = False
    err_msg += tmp_err_msg

    check_read, tmp_err_msg = CORE_READ002_COMMON(category=resource, links=resource_links)
    if not check_read:
        check = False
    err_msg += tmp_err_msg

    #print resource_links
    #print compute_links

    if not resource_links or not compute_links:
        if not resource_links:
            err_msg.append('No %s found' % resource_name)
        if not compute_links:
            err_msg.append('No compute found')
        return [False, err_msg]

    resourcelink = search_category({'term':'%s%s' % (resource_name, resource_type), 'scheme':'http://schemas.ogf.org/occi/infrastructure#', 'class': 'kind'})
    if not resourcelink:
        err_msg.append('No %slink kind found' % resource_name)
        return [False, err_msg]
    #print resourcelink

    if 'attributes' in resourcelink:
        attribute_definitions += resourcelink['attributes']

    attributes['occi.core.id'] = occi.Attribute({'name': 'occi.core.id', 'value': gen_id('%s%s' % (resource_name.capitalize(), resource_type))})
    attributes['occi.core.source'] = occi.Attribute({'name': 'occi.core.source', 'value': compute_links[0]})
    attributes['occi.core.target'] = occi.Attribute({'name': 'occi.core.target', 'value': resource_links[0]})
    if not get_attributes(attribute_definitions, attributes, err_msg):
        check = False
    #print attributes

    new_resourcelink = renderer.render_resource(
        categories = [
            occi.Category({'term':  resourcelink['term'], 'scheme': resourcelink['scheme'], 'class': resourcelink['class']}),
        ],
        links = None,
        attributes = attributes.values()
    )

    body, response_headers, http_status, content_type = occi_curl(url = resourcelink['location'], headers = ['Content-Type: text/plain'], post = new_resourcelink)

    check_create, tmp_err_msg = check_http_status("201 Created", http_status)
    err_msg += tmp_err_msg

    if not check_create:
        print body

    resource_link = urlparse.urlparse(resource_links[0]).path

    body, response_headers, http_status, content_type = occi_curl(base_url = compute_links[0], url = '', headers = ['Content-Type: text/plain'])
    #print body
    for line in body:
        if re.match(r'^Link: <.*%s>' % resource_link, line):
            check_link = True
            break

    if not check_link:
        err_msg += ["OCCI Compute Resource is NOT linked with OCCI %s Resource!" % (resource_name.capitalize())]
        print body

    return [check and check_create and check_link, err_msg]


def INFRA_CREATE006():
    """
    Opennebula requires running compute instance.
    """

    return INFRA_CREATE_LINK('storage', 'link')


def INFRA_CREATE007():
    """
    Opennebula requires running compute instance.
    """

    return INFRA_CREATE_LINK('network', 'interface')
