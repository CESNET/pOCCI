import re
import sys
import time
import urlparse

from occi_libs import *
import transport
import occi


renderer = None
renderer_big = None
renderer_httpheaders = None
connection = None

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


class Test:
    """Base class for OCCI compliance tests"""

    objective = None
    categories = []


    @classmethod
    def test(self=None):
        return [False, ['Not implemented']]


    @classmethod
    def fetch_categories(self, err_msg):
        categories = []
        check_parse = True

        body, response_headers, http_status, content_type = connection.get(mimetype=occi_config['mimetype.big'])

        if body is not None:
            try:
                categories = renderer_big.parse_categories(body, response_headers)
            except occi.ParseError as pe:
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

        # for OpenStack
        # TODO: needed?
        for category in categories:
            if 'location' not in category:
                category['location'] = '/' + category['term'] + '/'

        Test.categories = categories
        return [check_parse, body, response_headers, http_status, content_type]


    @classmethod
    def get_category(self, uri):
        for cat in Test.categories:
            if cat['scheme'] + cat['term'] == uri:
                return cat
        return None


    @classmethod
    def clear_categories(self):
        Test.categories = []


    @classmethod
    def search_category(self, filter):
        for cat in Test.categories:
            if match_category(cat, filter):
                return cat
        return None


    @classmethod
    def pretest_http_status(self, http_ok_status, err_msg, force=False):
        check_pretest = True
        check_categories = True
        body = None
        response_headers = None
        http_status = None
        content_type = None

        if not Test.categories or force:
            check_categories, body, response_headers, http_status, content_type = Test.fetch_categories(err_msg)
            check_pretest, tmp_err_msg = check_http_status(http_ok_status, http_status)
            err_msg += tmp_err_msg
        return [body, response_headers, http_status, content_type, check_pretest and check_categories]


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

    self.connection = transport.Transport(occi_config)


def check_content_type(content_type):
    if content_type in ['text/occi', 'text/plain', 'application/occi+json']:
        return [True, []]
    else:
        return [False, ['Wrong Content-Type in response']]


def check_requested_content_type(content_type, big=False, headers=False):
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


def match_category(category, filter):
    for key, value in filter.items():
        if not (key in category and category[key] == value):
            return False
    return True


def match_entity(attributes, filter):
    adict = {}
    for a in attributes:
        adict[a['name']] = a
    for key, value in filter.items():
        a2 = occi.Attribute({'value': value})
        if key not in adict or not occi.Attribute.equals(adict[key], a2):
            #print '[match_entity] bad key %s' % key
            return False

    return True


def check_body_entities(body, headers, err_msg=[]):
    try:
        entities = renderer.parse_locations(body, headers)
    except occi.ParseError as pe:
        err_msg.append(str(pe))
        err_msg.append('HTTP Body doesn\'t contain the OCCI Compute Resource description')
        return None

    return entities


def gen_id(prefix):
    return '%s_%d' % (prefix, time.time())


class CORE_DISCOVERY001(Test):
    objective = 'Retrieving all OCCI Categories supported by the OCCI Server'

    @classmethod
    def test(self=None):
        check_cat = False

        err_msg = []

        body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg, force=True)

        check_ct, tmp_err_msg = check_content_type(content_type)
        err_msg += tmp_err_msg

        check_rct, tmp_err_msg = check_requested_content_type(content_type, big=True)
        err_msg += tmp_err_msg

        count = 0
        for category in required_categories:
            if Test.search_category(category) is not None:
                count += 1

        if count == len(required_categories):
            check_cat = True
        else:
            err_msg.append('Body doesn\'t contain appropriate categories')

        return [check_pretest and check_ct and check_rct and check_cat, err_msg]


class CORE_DISCOVERY002(Test):
    objective = 'Retrieving the OCCI Categories with an OCCI Category filter from the OCCI Server'

    @classmethod
    def test(self=None):
        err_msg = []
        filtered_categories = []

        check = True

        body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg)
        if not Test.categories:
            err_msg += ['No categories returned']
            return [False, err_msg]

        filter = occi.Category({
            'term': Test.categories[0]['term'],
            'scheme': Test.categories[0]['scheme'],
            'class': Test.categories[0]['class'],
        })
        cat_in = []
        cat_in.append('Content-Type: text/occi')
        cat_in += renderer_httpheaders.render_category(filter)[1]

        body, response_headers, http_status, content_type = connection.get(headers=cat_in)

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


class CORE_CREATE001(Test):
    """Create an OCCI Resource

    Unsupported test: Creating compute instances without os_tpl is not supported.

    It can be called by::
       pOCCI -t 'CORE/CREATE/001'
    """

    objective = 'Create an OCCI Resource'

    @classmethod
    def test(self=None):
        err_msg = []

        body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg)

        if not check_pretest:
            return [False, err_msg]

        #kind = Test.search_category({'class': 'kind'})
        kind = Test.search_category({'class': 'kind', 'term': 'compute'})
        #print kind

        if kind:
            for item in ['location', 'term', 'scheme']:
                if item not in kind.keys():
                    err_msg.append('No %s in OCCI Kind' % item)
                    return [False, err_msg]
        else:
            err_msg.append('No OCCI Kind found')
            return [False, err_msg]

        new_cat_s, new_cat_h = renderer.render_resource(
            categories=[
                occi.Category({
                    'term': 'compute',
                    'scheme': 'http://schemas.ogf.org/occi/infrastructure#',
                    'class': 'kind',
                    'title': 'titulek',
                }),
            ],
            attributes=[
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

        body, response_headers, http_status, content_type = connection.post(url=occi_config['url'] + kind['location'], headers=['Content-Type: %s' % occi_config['mimetype']] + new_cat_h, body=new_cat_s)
        Test.clear_categories()
        check_create, tmp_err_msg = check_http_status("201 Created", http_status)
        err_msg += tmp_err_msg

        if not check_create:
            print >> sys.stderr, body

        return [check_create, err_msg]


class CORE_CREATE006(Test):
    """Add an OCCI Mixin definition

    Unsupported test: Not implemented.

    It can be called by::
       pOCCI -t 'CORE/CREATE/006'
    """

    objective = 'Add an OCCI mixin definition'

    @classmethod
    def test(self=None):
        err_msg = []
        new_mixin = 'Category: stufik; scheme="http://example.com/occi/my_stuff#"; class="mixin"; location: "/mixin/resource_tpl/extra_large/", rel: "http://schemas.ogf.org/occi/infrastructure#resource_tpl"'
        #new_mixin = 'Category: stufik; scheme="http://example.com/occi/my_stuff#"; class="mixin"; rel="http:/example.com/occi/something_else#mixin"; location="/my_stuff/"'
        body, response_headers, http_status, content_type = connection.post(url=occi_config['url'] + '/-/', headers=['Content-Type: text/plain'], body=new_mixin)
        check_create, tmp_err_msg = check_http_status("200 OK", http_status)
        err_msg += tmp_err_msg

        if not check_create:
            print >> sys.stderr, body

        return [check_create, err_msg]


def CORE_READ_URL(filter):
    err_msg = []
    check_200ok = False
    check = True

    body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg)

    if content_type:
        check, tmp_err_msg = check_content_type(content_type)
        err_msg += tmp_err_msg

    if not check_pretest:
        return [False, err_msg, None]

    mixin = Test.search_category(filter)
    #kind = Test.search_category({'class': 'kind'})

    if not mixin:
        err_msg.append('No required OCCI Category found')
        return [False, err_msg, None]

    for category in [mixin]:
        body, response_headers, http_status, content_type = connection.get(url=occi_config['url'] + category['location'])
        try:
            locations = renderer.parse_locations(body, response_headers)
        except occi.ParseError as pe:
            locations = []
            check = False
            err_msg.append(str(pe))

        if re.match(r'^HTTP/.* 200 OK', http_status):
            check_200ok = True
        else:
            err_msg.append('Returned HTTP status is not 200 OK (%s)' % http_status)

    return [check_pretest and check and check_200ok, err_msg, locations]


class CORE_READ001(Test):
    objective = 'Retrieve the URLs of all OCCI Entities belonging to an OCCI Kind or OCCI Mixin'

    @classmethod
    def test(self=None):
        check, err_msg, urls = CORE_READ_URL(occi_config['occi.tests.category'])
        return [check, err_msg]


def CORE_READ002_COMMON(category, links=[]):
    check_url = True
    check_200ok = False
    err_msg = []
    headers = []

    headers.append('Content-Type: text/occi')
    headers += renderer_httpheaders.render_category(occi.Category({'term': category['term'], 'scheme': category['scheme'], 'class': category['class']}))[1]

    body, response_headers, http_status, content_type = connection.get(url=occi_config['url'] + category['location'], headers=headers)
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


class CORE_READ002(Test):
    objective = 'Retrieve the URLs of the OCCI Entities belonging to an OCCI Kind or OCCI Mixin and related to an OCCI Category filter'

    @classmethod
    def test(self=None):
        err_msg = []
        check = True

        body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg)

        if content_type:
            check, tmp_err_msg = check_content_type(content_type)
            err_msg += tmp_err_msg

        if not check_pretest:
            return [False, err_msg]

        mixin = Test.search_category({'term': 'resource_tpl', 'class': 'mixin'})
        #kind = Test.search_category({'class': 'kind'})
        for category in [mixin]:
            filter = Test.search_category({'rel': '%s%s' % (category['scheme'], category['term'])})
            if filter is None:
                check_read = False
                tmp_err_msg = ['No desired OCCI Mixin found']
            else:
                check_read, tmp_err_msg = CORE_READ002_COMMON(category=filter)
            err_msg += tmp_err_msg

        return [check and check_read, err_msg]


def CORE_READ_DESCRIPTION(filter=None):
    """Read OCCI Entity Description

    :param string filter{}: required attribute names and values
    :return: status, err_msg, url, entity description
    :rtype: [bool, string[], string, occi.Category[], occi.Link[], occi.Attribute[]]
    """
    categories = []
    links = []
    attributes = []
    found = False
    entity_url = None

    check, err_msg, urls = CORE_READ_URL(occi_config['occi.tests.category'])
    if not check:
        return [False, err_msg, entity_url, None, None, None]

    #print urls
    for entity_url in urls:
        #print base_url, url
        body, headers, http_status, content_type = connection.get(url=entity_url)
        check1, tmp_err_msg = check_http_status("200 OK", http_status)
        err_msg += tmp_err_msg
        if content_type:
            check2, tmp_err_msg = check_requested_content_type(content_type)
            err_msg += tmp_err_msg
        if not check1 or not check2:
            return [False, err_msg, entity_url, None, None, None]

        try:
            categories, links, attributes = renderer.parse_resource(body, headers)
        except occi.ParseError as pe:
            err_msg += [str(pe)]
            return [False, err_msg, entity_url, None, None, None]
        if not categories:
            err_msg += ['HTTP Response doesn\'t contain categories']
            return [False, err_msg, entity_url, None, None, None]
        #print 'Got OCCI Entity: ' + str(categories[0])

        if match_entity(attributes, filter):
            #print 'Hit!'
            found = True
            break

    if not found:
        err_msg.append('No required OCCI Entity instance found')
    return [found, err_msg, entity_url, categories, links, attributes]


class CORE_READ007(Test):
    objective = 'Retrieve the description of an OCCI Entity'

    @classmethod
    def test(self=None):
        check, err_msg, url, categories, links, attributes = CORE_READ_DESCRIPTION({})
        return [check, err_msg]


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


class CORE_DELETE001(Test):
    objective = 'Delete an OCCI Entity'

    @classmethod
    def test(self=None):
        err_msg = []

        check, err_msg, tmp_urls = CORE_READ_URL(occi_config['occi.tests.category'])

        if not tmp_urls:
            err_msg += ["OCCI entity URL not found!"]
            return [False, err_msg]

        url = urlparse.urlparse(tmp_urls[0]).path

        body, response_headers, http_status, content_type = connection.get(url=occi_config['url'] + url)
        check_exist1, tmp_err_msg = check_http_status("200 OK", http_status)
        err_msg += tmp_err_msg

        body, response_headers, http_status, content_type = connection.delete(url=occi_config['url'] + url)
        check_delete1, tmp_err_msg = check_http_status("200 OK", http_status)
        err_msg += tmp_err_msg

        # It takes some time to delete machine, second delete action force it
        # Not testing result of the operation (various backends have different behaviour)
        body, response_headers, http_status, content_type = connection.delete(url=occi_config['url'] + url)

        body, response_headers, http_status, content_type = connection.get(url=occi_config['url'] + url)
        check_exist2, tmp_err_msg = check_http_status("404 Not Found", http_status)
        err_msg += tmp_err_msg

        Test.clear_categories()

        return [check_exist1 and check_exist2 and check_delete1, err_msg]


class CORE_UPDATE001(Test):
    """Full update of a specific OCCI Entity

    Requires existing compute machine.

    OpenNebula issues:

    * https://github.com/EGI-FCTF/rOCCI-server/issues/125: poweroff state required
    * https://github.com/EGI-FCTF/rOCCI-server/issues/126: not all attributes implemented
    * https://github.com/EGI-FCTF/rOCCI-server/issues/128: parse error
    """

    objective = 'Full update of a specific OCCI Entity'

    @classmethod
    def test(self=None):
        err_msg = []
        check_response = True

        check, err_msg, urls = CORE_READ_URL(occi_config['occi.tests.category'])
        if not urls:
            err_msg.append('No OCCI Entity instance found')
            return [False, err_msg]
        #print urls
        url = urls[0]

        body, response_headers, http_status, content_type = connection.get(url=url)

        categories, links, attributes = renderer.parse_resource(body, response_headers)

        # change one attribute
        #print attributes
        a = None
        for a in attributes:
            if a['name'] == 'occi.core.title':
                break
        if a is None or a['name'] != 'occi.core.title':
            a = occi.Attribute({'name': 'occi.core.title', 'value': gen_id('c_pOCCI')})
            attributes.append(a)
        else:
            a['value'] = gen_id(a['value'])
        body, headers = renderer.render_resource(categories, links, attributes)

        # update
        body, response_headers, http_status, content_type = connection.put(url=url, headers=['Content-Type: %s' % occi_config['mimetype']] + headers, body=body)
        #print body
        #print http_status
        Test.clear_categories()

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
            print >> sys.stderr, body

        return [check and check_ct and check_response, err_msg]


class CORE_MISC001(Test):
    objective = 'Trigger OCCI Action on existing OCCI Entity'

    @classmethod
    def test(self=None):
        err_msg = []
        actions = set()

        check, err_msg, entity_url, categories, links, attributes = CORE_READ_DESCRIPTION(filter=occi_config['occi.tests.entity'])
        if not check:
            return [False, err_msg]

        for cat in categories:
            model_cat = Test.get_category(cat['scheme'] + cat['term'])
            #print model_cat['term']
            if 'actions' in model_cat:
                #print model_cat['actions']
                actions |= set(model_cat['actions'])
        if occi_config['curlverbose']:
            print '[OCCI/CORE/MISC/001] actions: ' + str(list(actions))

        # select appropriate action, fallback to the first one
        action = list(actions)[0]
        action_start = action
        action_stop = action
        for act in actions:
            if re.search('#start$', act):
                action_start = act
            if re.search('#suspend$', act):
                action_stop = act
        for a in attributes:
            if a['name'] == 'occi.compute.state':
                break
        if a['name'] == 'occi.compute.state':
            if occi_config['curlverbose']:
                print '[OCCI/CORE/MISC/001] state: %s' % a['value']
            if a['value'] == 'active':
                action = action_stop
            else:
                action = action_start
        if occi_config['curlverbose']:
            print '[OCCI/CORE/MISC/001] selected action: %s' % action

        action_cat = Test.get_category(action)
        if not action_cat:
            return [False, 'Action "%s" not found in OCCI Model' % action]
        #print action_cat

        url = entity_url
        url += '?action=' + action_cat['term']
        if occi_config['curlverbose']:
            print '[OCCI/CORE/MISC/001] calling action: %s' % url

        body, headers = renderer.render_category(action_cat)

        body, response_request, http_status, content_type = connection.post(url=url, headers=['Content-Type: %s' % occi_config['mimetype']] + headers, body=body)

        check, tmp_err_msg = check_http_status("200 OK", http_status)
        err_msg += tmp_err_msg

        return [check, err_msg]


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

    kind = Test.search_category({'class': 'kind', 'term': resource, 'scheme': 'http://schemas.ogf.org/occi/infrastructure#'})
    #print kind

    if not kind:
        has_kind = False
        err_msg.append('No OCCI Kind found')
    if not kind:
        return [False, err_msg]

    for item in ['location', 'term', 'scheme']:
        if item not in kind.keys():
            has_kind = False
            err_msg.append('No %s in OCCI Kind' % item)

    if 'attributes' in kind:
        all_attributes += kind['attributes']

    if additional_attributes is not None:
        all_attributes += additional_attributes

    #print 'list of attributes: %s' % repr(all_attributes)
    if not get_attributes(all_attributes, attributes, err_msg):
        has_all_attributes = False
    #print 'list of result attribute keys: %s' % repr(attributes.keys())

    new_cat_s, new_cat_h = renderer.render_resource(categories, None, attributes.values())

    body, response_request, http_status, content_type = connection.post(url=occi_config['url'] + kind['location'], headers=['Content-Type: %s' % occi_config['mimetype']] + new_cat_h, body=new_cat_s)
    check_create, tmp_err_msg = check_http_status("201 Created", http_status)
    err_msg += tmp_err_msg

    check_ct, tmp_err_msg = check_content_type(content_type)
    err_msg += tmp_err_msg

    entities = check_body_entities(body, response_request, err_msg)
    check_br = (entities is not None and entities)

    check_rct, tmp_err_msg = check_requested_content_type(content_type)
    err_msg += tmp_err_msg

    if not check_create:
        print >> sys.stderr, body

    Test.clear_categories()

    body, response_headers, http_status, content_type = connection.get(url=occi_config['url'] + kind['location'])
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


class INFRA_CREATE001(Test):
    objective = 'Create an OCCI Compute Resource'

    @classmethod
    def test(self=None):
        err_msg = []
        category = occi.Category({'term': 'compute', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#', 'class': 'kind'})

        body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg)
        if not check_pretest:
            return [False, err_msg]

        return INFRA_CREATE_COMMON('compute', [category], [], err_msg)


class INFRA_CREATE002(Test):
    objective = 'Create an OCCI Storage Resource'

    @classmethod
    def test(self=None):
        err_msg = []
        category = occi.Category({'term': 'storage', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#', 'class': 'kind'})
        additional_attributes = [
            occi.AttributeDefinition({"name": "occi.core.title", "required": True}),
            occi.AttributeDefinition({"name": "occi.storage.size", "required": True}),
        ]

        body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg)
        if not check_pretest:
            return [False, err_msg]

        return INFRA_CREATE_COMMON('storage', [category], additional_attributes, err_msg)


class INFRA_CREATE003(Test):
    objective = 'Create an OCCI Network Resource'

    @classmethod
    def test(self=None):
        err_msg = []
        category = occi.Category({'term': 'network', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#', 'class': 'kind'})
        additional_attributes = [occi.AttributeDefinition({"name": "occi.core.title", "required": True})]

        body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg)
        if not check_pretest:
            return [False, err_msg]

        return INFRA_CREATE_COMMON('network', [category], additional_attributes, err_msg)


class INFRA_CREATE004(Test):
    objective = 'Create an OCCI Compute Resource using an OS and resource template'

    @classmethod
    def test(self=None):
        err_msg = []
        categories = [
            occi.Category({'term': 'compute', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#', 'class': 'kind'})
        ]

        body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg)
        if not check_pretest:
            return [False, err_msg]

        os_tpl = Test.search_category({'class': 'mixin', 'rel': 'http://schemas.ogf.org/occi/infrastructure#os_tpl'})
        if occi_config['curlverbose']:
            print '[OCCI/INFRA/CREATE/004] os_tpl: %s' % str(os_tpl)
        if not os_tpl:
            err_msg.append('No OS template found')
            return [False, err_msg]

        # 'term': 'uuid_ttylinux_0', 'scheme': 'http://occi.myriad5.zcu.cz/occi/infrastructure/os_tpl#', 'class': 'mixin'
        categories.append(occi.Category({'term': os_tpl['term'], 'scheme': os_tpl['scheme'], 'class': 'mixin'}))

        if 'attributes' in os_tpl:
            os_tpl_attributes = os_tpl['attributes']
        else:
            os_tpl_attributes = []
        return INFRA_CREATE_COMMON('compute', categories, os_tpl_attributes, err_msg)


class INFRA_CREATE005(Test):
    """
    Unsupported test, os_tpl required.

    It can be called by pOCCI -t 'INFRA/CREATE/005'
    """

    objective = 'Create an OCCI Compute Resource with an OCCI Storagelink and an OCCI Networkinterface'

    @classmethod
    def test(self=None):
        network_links = []
        storage_links = []
        err_msg = []
        check = True

        body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg)

        if content_type:
            check, tmp_err_msg = check_content_type(content_type)
            err_msg += tmp_err_msg

        if not check_pretest:
            return [False, err_msg]

        storage = Test.search_category({'term': 'storage', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#'})
        network = Test.search_category({'term': 'network', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#'})
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

        compute = Test.search_category({'term': 'compute', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#'})

        new_compute = 'Category: %s; scheme="%s"; class="%s"\n\r\
Link: <%s>; rel="%s"; category="%s"\n\r\
Link: <%s>; rel="%s"; category="%s"\n\r\
' % (compute['term'], compute['scheme'], compute['class'], storage_links[0], storage['scheme'] + storage['term'], 'http://schemas.ogf.org/occi/infrastructure#storagelink', network_links[0], network['scheme'] + network['term'], 'http://schemas.ogf.org/occi/infrastructure#networkinterface')

        body, response_headers, http_status, content_type = connection.post(url=occi_config['url'] + compute['location'], headers=['Content-Type: text/plain'], body=new_compute)
        check_create, tmp_err_msg = check_http_status("201 Created", http_status)
        err_msg += tmp_err_msg

        if not check_create:
            print >> sys.stderr, body

        Test.clear_categories()

        return [check and check_create, err_msg]


def INFRA_CREATE_LINK(resource_name, resource_type):
    """
    Opennebula requires running compute instance.

    :param string resource_name: Resource Name (storage, network)
    :param string resource_type: Resource Type (link, interface)
    :return: status, err_msg
    :rtype: [bool, string[]]
    """

    err_msg = []
    check = True
    check_link = False
    compute_links = []
    resource_links = []
    resourcelink = None
    attributes = {}
    attribute_definitions = []

    body, response_headers, http_status, content_type, check_pretest = Test.pretest_http_status("200 OK", err_msg)
    if not check_pretest:
        return [False, err_msg]

    compute = Test.search_category({'term': 'compute', 'scheme': 'http://schemas.ogf.org/occi/infrastructure#'})
    resource = Test.search_category({'term': resource_name, 'scheme': 'http://schemas.ogf.org/occi/infrastructure#'})

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

    resourcelink = Test.search_category({'term': '%s%s' % (resource_name, resource_type), 'scheme': 'http://schemas.ogf.org/occi/infrastructure#', 'class': 'kind'})
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
        categories=[
            occi.Category({'term': resourcelink['term'], 'scheme': resourcelink['scheme'], 'class': resourcelink['class']}),
        ],
        links=None,
        attributes=attributes.values()
    )

    body, response_headers, http_status, content_type = connection.post(url=occi_config['url'] + resourcelink['location'], headers=['Content-Type: %s' % occi_config['mimetype']] + new_resourcelink_h, body=new_resourcelink_s)

    check_create, tmp_err_msg = check_http_status("201 Created", http_status)
    err_msg += tmp_err_msg

    if not check_create:
        print >> sys.stderr, body

    Test.clear_categories()

    resource_link = resource_links[0]
    resource_link_rel = urlparse.urlparse(resource_link).path

    body, response_headers, http_status, content_type = connection.get(url=compute_links[0])

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
        print >> sys.stderr, body

    return [check and check_create and check_link, err_msg]


class INFRA_CREATE006(Test):
    """
    Opennebula requires running compute instance.
    """

    objective = 'Create an OCCI Storagelink between an existing OCCI Compute and OCCI Storage Resource'

    @classmethod
    def test(self=None):
        return INFRA_CREATE_LINK('storage', 'link')


class INFRA_CREATE007(Test):
    """
    Opennebula requires running compute instance.
    """

    objective = 'Create an OCCI Networkinterface between an existing OCCI Compute and OCCI Network Resource'

    @classmethod
    def test(self=None):
        return INFRA_CREATE_LINK('network', 'interface')
