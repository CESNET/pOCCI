import json, re
import sys, time
import urlparse

from occi_libs import *
from occi_curl import occi_curl
import occi
import render


categories = []
renderer = None
renderer_big = None
renderer_httpheaders = None

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


def testsuite_init():
    """Initialize OCCI testsuite

    Renderers from occi_libs needs to be initialized first.
    """
    self = sys.modules[__name__]
    if 'pOCCI.occi_libs' in sys.modules:
        occi_libs = sys.modules['pOCCI.occi_libs']
    else:
        occi_libs = sys.modules['occi_libs']

    self.renderer = occi_libs.renderer
    self.renderer_big = occi_libs.renderer_big
    self.renderer_httpheaders = occi_libs.renderer_httpheaders

    if not self.renderer:
        print >> sys.stderr, 'No renderer (invalid mimetype?)'
        sys.exit(2)


def get_categories(err_msg):
    global categories
    check_parse = True

    body, response_headers, http_status, content_type = occi_curl(mimetype = occi_config['mimetype.big'])

    try:
        categories = renderer_big.parse_categories(body, response_headers)
    except occi.ParseError as pe:
        categories = []
        check_parse = False
        err_msg.append(str(pe))

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


def check_requested_content_type(content_type, big = False, headers = False):
    if big:
        requested = occi_config['mimetype.big']
    elif headers:
        requested = 'text/occi'
    else:
        requested = occi_config['mimetype']

    if content_type == requested:
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


def check_body_entities(body, headers, err_msg = []):
    try:
        entities = renderer.parse_locations(body, headers)
    except occi.ParseError as pe:
        err_msg.append(str(pe))
        err_msg.append('HTTP Body doesn\'t contain the OCCI Compute Resource description')
        return None

    return entities


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

    check_rct, tmp_err_msg = check_requested_content_type(content_type, big = True)
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
    cat_in += renderer_httpheaders.render_category(filter)[1]

    body, response_headers, http_status, content_type = occi_curl(headers = cat_in)

    check_ct, err_msg = check_content_type(content_type)

    if not re.match(r'^HTTP/.* 200 OK', http_status):
        check = False
        err_msg.append('HTTP status on filter not 200 OK (%s)' % http_status)

    check_rct, tmp_err_msg = check_requested_content_type(content_type)
    err_msg += tmp_err_msg

    try:
        filtered_categories = renderer.parse_categories(body, response_headers)
    except occi.ParseError as pe:
        check = False
        err_msg.append(str(pe))

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

    new_cat_s, new_cat_h = renderer.render_resource(
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

    body, response_headers, http_status, content_type = occi_curl(url = kind['location'], headers = ['Content-Type: %s' % occi_config['mimetype']] + new_cat_h, post=new_cat_s, custom_request = 'POST')
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
            locations = renderer.parse_locations(body, response_headers)
        except occi.ParseError as pe:
            locations = []
            check_url = False
            err_msg.append(str(pe))

        if re.match(r'^HTTP/.* 200 OK', http_status):
            check_200ok = True
        else:
            err_msg.append('Returned HTTP status is not 200 OK (%s)' % http_status)

    return [check_url and check_pretest and check_ct and check_200ok, err_msg, locations]


def CORE_READ001():
    check, err_msg, urls = CORE_READ_URL(occi_config['occi.tests.category'])
    return [check, err_msg]


def CORE_READ002_COMMON(category, links = []):
    check_url = True
    check_200ok = False
    err_msg = []
    headers = []

    headers.append('Content-Type: text/occi')
    headers += renderer_httpheaders.render_category(occi.Category({'term': category['term'], 'scheme': category['scheme'], 'class': category['class']}))[1]

    body, response_headers, http_status, content_type = occi_curl(url = category['location'], headers = headers)
    try:
        locations = renderer.parse_locations(body, response_headers)
    except occi.ParseError as pe:
        locations = []
        check_url = False
        err_msg.append(str(pe))
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

    check, err_msg, tmp_urls = CORE_READ_URL(occi_config['occi.tests.category'])

    if not tmp_urls:
        err_msg += ["OCCI entity URL not found!"]
        return [False, err_msg]

    url = urlparse.urlparse(tmp_urls[0]).path

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


def CORE_UPDATE001():
    """Full update of a specific OCCI Entity

    Requires existing compute machine.

    OpenNebula issues:

    * https://github.com/EGI-FCTF/rOCCI-server/issues/125: poweroff state required
    * https://github.com/EGI-FCTF/rOCCI-server/issues/126: not all attributes implemented
    * https://github.com/EGI-FCTF/rOCCI-server/issues/128: parse error
    """
    err_msg = []
    check_response = True

    check, err_msg, urls = CORE_READ_URL(occi_config['occi.tests.category'])
    if not urls:
        err_msg.append('No OCCI Entity instance found')
        return [False, err_msg]
    #print urls
    url = urls[0]

    body, response_headers, http_status, content_type = occi_curl(base_url = url, url = '')

    categories, links, attributes = renderer.parse_resource(body, response_headers)

    # change one attribute
    #print attributes
    a = None
    for a in attributes:
        if a['name'] == 'occi.core.title':
            break
    if a == None or a['name'] != 'occi.core.title':
        a = occi.Attribute({'name': 'occi.core.title', 'value': gen_id('c_pOCCI')})
        attributes.append(a)
    else:
        a['value'] = gen_id(a['value'])
    body, headers = renderer.render_resource(categories, links, attributes)

    # update
    body, response_headers, http_status, content_type = occi_curl(base_url = url, url = '', headers = ['Content-Type: %s' % occi_config['mimetype']] + headers, post = body, custom_request = 'PUT')
    #print body
    #print http_status

    check_ct, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg
    if content_type != occi_config['mimetype']:
        err_msg += ['Content-Type is not requested "%s"' % occi_config['mimetype']]
        check_ct = False

    check, tmp_err_msg = check_http_status("200 OK", http_status)
    if check:
        # response contains OCCI Entity description
        response_categories, response_links, response_attributes = renderer.parse_resource(body, response_headers)
        if not response_categories or not response_attributes:
            err_msg += ['HTTP Response doesn\'t contain categories or attributes']
            check_response = False
    else:
        check, tmp_err_msg = check_http_status("201 Created", http_status)
        if check:
            response_urls = renderer_httpheaders.parse_locations(None, response_headers)
            #print 'Entity URL'
            #print 'Response URLs:\n  '
            #print response_urls
            check_response = False
            for url in response_urls:
                if response_url == url:
                    check_response = True
            if not check_response:
                err_msg += ['HTTP Location headers is not OCCI Entity URL (%s)' % response_url]

    if not check:
        err_msg.append('HTTP status is neither 200 OK nor 201 Created (%s)' % http_status)
        print body

    return [check and check_ct and check_response, err_msg]


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

    new_cat_s, new_cat_h = renderer.render_resource(categories, None, attributes.values())

    body, response_request, http_status, content_type = occi_curl(url = kind['location'], headers = ['Content-Type: %s' % occi_config['mimetype']] + new_cat_h, post=new_cat_s, custom_request = 'POST')
    check_create, tmp_err_msg = check_http_status("201 Created", http_status)
    err_msg += tmp_err_msg

    check_ct, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg

    entities = check_body_entities(body, response_request, err_msg)
    check_br = (entities != None and entities)

    check_rct, tmp_err_msg = check_requested_content_type(content_type)
    err_msg += tmp_err_msg

    if not check_create:
        print body

    body, response_headers, http_status, content_type = occi_curl(url = kind['location'])
    entities2 = check_body_entities(body, response_headers, err_msg)
    # check if the entity is really created (just check the first: entities[0])
    check_created = False
    if entities:
        for line in entities2:
            if line == entities[0]:
                check_created = True
                break
    if not check_created:
        err_msg.append('OCCI %s Resource hasn\'t been successfully created' % resource.title())

    return [has_kind and has_all_attributes and check_create and check_created and check_ct and check_br and check_rct and check_created, err_msg]


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

    new_resourcelink_s, new_resourcelink_h = renderer.render_resource(
        categories = [
            occi.Category({'term':  resourcelink['term'], 'scheme': resourcelink['scheme'], 'class': resourcelink['class']}),
        ],
        links = None,
        attributes = attributes.values()
    )

    body, response_headers, http_status, content_type = occi_curl(url = resourcelink['location'], headers = ['Content-Type: %s' % occi_config['mimetype']] + new_resourcelink_h, post = new_resourcelink_s, custom_request = 'POST')

    check_create, tmp_err_msg = check_http_status("201 Created", http_status)
    err_msg += tmp_err_msg

    if not check_create:
        print body

    resource_link = resource_links[0]
    resource_link_rel = urlparse.urlparse(resource_link).path

    body, response_headers, http_status, content_type = occi_curl(base_url = compute_links[0], url = '')

    try:
        result_categories, result_links, result_attributes = renderer.parse_resource(body, response_headers)
    except occi.ParseError as pe:
        err_msg += [str(pe)]

    #print resource_link
    #print result_links
    for l in result_links:
        # accept both: relative and absolute URI
        if l['uri'] == resource_link or l['uri'] == resource_link_rel:
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
