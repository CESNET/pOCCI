import collections
import re
import sys

import occi
from render_base import Renderer, check_url


eol = '\r\n'


def text_attribute_def(ad = None):
    s = ad['name']
    immutable = ('immutable' in ad) and ad['immutable']
    required = ('required' in ad) and ad['required']
    if immutable and required:
        s += '{immutable required}'
    elif immutable and not required:
        s += '{immutable}'
    elif not immutable and required:
        s += '{required}'
    return s


def text_attribute_defs(ads = None):
    text_ads = []
    if ads:
        for ad in ads:
            text_ads.append(text_attribute_def(ad))
    return ' '.join(text_ads)


def text_actions(actions = None):
    if actions:
        return ' '.join(actions)
    else:
        return None


def text_category(category = None):
    s = '%s;scheme="%s";class="%s"' % (category['term'], category['scheme'], category['class'])

    for item in ['title', 'rel', 'location']:
        if item in category:
            s += ';%s="%s"' % (item, category[item])

    if 'attributes' in category:
        s += ';%s="%s"' % ('attributes', text_attribute_defs(category['attributes']))

    if 'actions' in category:
        s += ';%s="%s"' % ('actions', text_actions(category['actions']))

    return s


def text_attribute_value(attribute):
    """Render OCCI Attribute value.

    :param occi.Attribute attribute: attribute with a value to render
    :return attribute value renderin
    :rtype string
    """

    if 'type' in attribute:
        type = attribute['type']
    else:
        type = 'string'
    value = attribute['value']

    if type == 'string':
        return '"' + value + '"'
    elif type == 'number':
        return repr(value)
    elif type == 'bool':
        if value:
            return "true"
        else:
            return "false"
    elif type == 'enum':
        return repr(value)


def text_attribute_repr(attribute):
    """Render one OCCI Attribute.
    """

    return attribute['name'] + '=' + text_attribute_value(attribute)


def text_link_attribute(key, value):
    """Render Link Attribute
    """
    # term or quoted string, using only the quotes now
    return key + '=' + '"' + value + '"'


def text_link(link):
    s = '<%s>;rel="%s"' % (link['uri'], ' '.join(link['rel']))

    if 'self' in link:
        s += ';self="%s"' % link['self']
    if 'category' in link:
        s += ';category="%s"' % ' '.join(link['category'])

    if 'attributes' in link:
        for key, value in link['attributes'].iteritems():
            s += ';%s' % text_link_attribute(key, value)

    return s


class TextRenderer(Renderer):
    """Plain Text OCCI Renderer

    Empty array is always returned as headers during rendering.
    """

    reChunks = re.compile(r';\s*')
    reCategory = re.compile(r'^Category:\s*')
    reLink = re.compile(r'^Link:\s*')
    reAttribute = re.compile(r'^X-OCCI-Attribute:\s*')
    reKeyValue = re.compile(r'\s*?=\s*')
    reKeyCheck = re.compile(r'[A-Za-z0-9_\.-]*$')
    reQuoted = re.compile(r'^"(.*)"$')
    reSP = re.compile(r'\s+')
    reAttributes = re.compile(r'([^\{ ]+)(\{[^\}]*\})?\s*')
    reLocation = re.compile(r'^(X-OCCI-Location|Location):\s*(.*)')
    reQuotedLink = re.compile(r'^<(.*)>$')
    reStringUnescape = re.compile(r'\\(.)')
    reNumber = re.compile(r'^([0-9\.+-]+)$')
    reIntNumber = re.compile(r'^([0-9+-]+)$')
    reBool = re.compile(r'^(true|false)$')


    def render_category(self, category):
        """Render OCCI Category

        :param occi.Category category: OCCI Category object
        :return: render result
        :rtype: [string, string[]]
        """
        return ['Category: ' + text_category(category), []]


    def render_categories(self, categories):
        """Render OCCI Category collection

        :param occi.Category category[]: OCCI Category array
        :return: render result
        :rtype: [string, string[]]
        """
        res = []
        for category in categories:
            cat_s, cat_h = self.render_category(category)
            res.append(cat_s)
        return [eol.join(res) + eol, []]


    def render_resource(self, categories, links = None, attributes = None):
        """Render OCCI Resource instance

        :param occi.Category category: OCCI Category object
        :param occi.Link links[]: OCCI Link array
        :param occi.Attribute attributes[]: OCCI Attribute array
        :return: render result
        :rtype: [string, string[]]
        :return: render result
        """
        Renderer.render_resource(self, categories, links, attributes)
        cat_s, cat_h = self.render_categories(categories)
        res = []
        if links != None:
            for link in links:
                res.append(self.render_link(link))
        if attributes != None:
            for attr in attributes:
                res.append(self.render_attribute(attr))
        if res:
            return [cat_s + eol.join(res) + eol, []]
        else:
            return [cat_s, []]


    def render_link(self, link):
        """ Render OCCI Link

        :param occi.Link link: OCCI Link object
        :return: render result
        :rtype: string
        """
        return 'Link: ' + text_link(link)


    def render_attribute(self, attribute):
        """ Render Attribute

        :param occi.Attribute attribute: OCCI Attribute object
        :return render result
        :rtype: string
        """
        return 'X-OCCI-Attribute: ' + text_attribute_repr(attribute)


    def render_attributes(self, attributes):
        """ Render Attributes

        :param occi.Attribute attribute[]: OCCI Attribute object
        :return render result
        :rtype: string
        """
        if not attributes:
            return ''
        s = []
        for attribute in attributes:
            s.append(TextRenderer.render_attribute(attribute) + eol)
        return ''.join(s) + eol


    def render_locations(self, locations):
        """ Render Locations

        :param string location[]: location URI
        :return render result
        :rtype: [string, string[]]
        """
        if not location:
            return ''
        s = []
        for location in locations:
            s.append('X-OCCI-Location: ' + location)
        return [''.join(s), []]


    def parse_attribute_defs(self, body):
        """ Parse OCCI Attribute Definitions.

        Example::

           occi.core.id{immutable required} occi.core.title occi.core.target occi.core.source{required}

        :param string body: text to parse
        :return: array of OCCI Attribute Definition
        :rtype: occi.AttributeDefinition[]
        """
        result = []

        m = True
        while m:
            m = TextRenderer.reAttributes.match(body)
            if not m:
                break
            matches = m.groups()
            name = matches[0]
            attrs = matches[1]
            body = body[m.end():]

            if attrs:
                attrs = attrs[1:-1]
                attrs = TextRenderer.reSP.split(attrs)

            attribute = occi.AttributeDefinition({'name': name})
            if attrs:
                for a in attrs:
                    if a == 'required':
                        attribute['required'] = True
                    elif a == 'immutable':
                        attribute['immutable'] = True
                    else:
                        raise occi.ParseError('Unknown field in OCCI attribute definitions', a)
            result.append(attribute)

        if body:
            raise occi.ParseError('Error parsing OCCI attribute definitions', body)

        return result


    def parse_actions(self, body):
        """Parse OCCI Actions.

        Example::

           http://schemas.ogf.org/occi/infrastructure/compute/action#start http://schemas.ogf.org/occi/infrastructure/compute/action#stop http://schemas.ogf.org/occi/infrastructure/compute/action#restart http://schemas.ogf.org/occi/infrastructure/compute/action#suspend

        :param string body: text to parse
        :return: array of string
        :rtype: string[]
        """
        actions = TextRenderer.reSP.split(body)
        for action in actions:
            # let's require scheme and hostname in scheme URI
            if not check_url(action, scheme = True, host = True):
                raise occi.ParseError('URI expected as an action', action)
        return actions


    def parse_category_body(self, body):
        """Parse OCCI Category body

        Example::

           entity;scheme="http://schemas.ogf.org/occi/core#";class="kind";title="entity";location="/entity/";attributes="occi.core.id{immutable required} occi.core.title"

        :param string body: text to parse
        :return: OCCI Category
        :rtype: occi.Category
        """
        category = occi.Category()

        chunks = TextRenderer.reChunks.split(body)

        if not chunks[0]:
            raise occi.ParseError('Invalid format of category, term expected', body)

        category['term'] = chunks[0]

        # skip the first chunk (category term)
        for chunk in chunks[1:]:
            keyvalue = TextRenderer.reKeyValue.split(chunk, 1)

            key = keyvalue[0]
            value = keyvalue[1]
            keymatch = TextRenderer.reKeyCheck.match(key)
            if keymatch == None:
                raise occi.ParseError('Invalid characters in category property', chunk)
            # every value quoted, only class has quoting optional
            valuematch = TextRenderer.reQuoted.match(value)
            if valuematch == None and key != 'class':
                raise occi.ParseError('Category value not properly quoted or unexpected EOF', chunk)
            if valuematch:
                value = valuematch.group(1)
            # sanity check: there should not be any quotes now
            if value[0] == '"' or (len(value) >= 2 and value[-1] == '"'):
                raise occi.ParseError('Unexpected quotes in category', chunk)

            if key == 'location':
                if not check_url(value):
                    raise occi.ParseError('URL is not valid in OCCI Category location', chunk)
                category[key] = value
            elif key == 'scheme':
                if not check_url(value):
                    raise occi.ParseError('URL is not valid in OCCI Category scheme', chunk)
                category[key] = value
            elif key == 'attributes':
                category[key] = self.parse_attribute_defs(value)
            elif key == 'actions':
                category[key] = self.parse_actions(value)
            elif key in ['class', 'title', 'rel']:
                category[key] = value
            else:
                raise occi.parseerror('unknown key "%s" in category' % key, chunk)

        if not category.validate():
            raise occi.ParseError('Missing fields in OCCI Category', body)

        return category


    def parse_link_body(self, body):
        """Parse OCCI Link body

        Example::

           </storage/0>;rel="http://schemas.ogf.org/occi/infrastructure#storage";self="/link/storagelink/compute_103_disk_0";category="http://schemas.ogf.org/occi/infrastructure#storagelink http://opennebula.org/occi/infrastructure#storagelink";occi.core.id="compute_103_disk_0";occi.core.title="ttylinux";occi.core.target="/storage/0";occi.core.source="/compute/103";occi.storagelink.deviceid="/dev/hda";occi.storagelink.state="active"

        :param string body: text to parse
        :return: OCCI Link
        :rtype: occi.Link
        """
        link = occi.Link()

        chunks = TextRenderer.reChunks.split(body)

        if not chunks[0]:
            raise occi.ParseError('Invalid format of OCCI Link, URI and "rel" expected', body)

        matched = TextRenderer.reQuotedLink.match(chunks[0])
        if not matched:
            raise occi.ParseError('URI is not properly quoted in OCCI Link', body)

        link['uri'] = matched.group(1)
        if not check_url(link['uri']):
            raise occi.ParseError('URL is not valid in OCCI Link', link['uri'])

        # skip the first chunk (URI)
        for chunk in chunks[1:]:
            keyvalue = TextRenderer.reKeyValue.split(chunk, 1)

            key = keyvalue[0]
            value = keyvalue[1]
            keymatch = TextRenderer.reKeyCheck.match(key)
            if keymatch == None:
                raise occi.ParseError('Invalid characters in link property', chunk)
            valuematch = TextRenderer.reQuoted.match(value)
            # mandatory quoting
            if key in ['rel', 'self', 'category']:
                if valuematch == None:
                    raise occi.ParseError('Link value not properly quoted or unexpected EOF', chunk)
            # quoting of the other attributes optional
            if valuematch != None:
                value = valuematch.group(1)
            # sanity check: there should not be any quotes now
            if value[0] == '"' or (len(value) >= 2 and value[-1] == '"'):
                raise occi.ParseError('Unexpected quotes in OCCI Link values', chunk)

            if key == 'scheme':
                if not check_url(value):
                    raise occi.ParseError('URL is not valid in OCCI Category scheme', chunk)
                link[key] = value
            elif key in ['rel', 'category']:
                link[key] = TextRenderer.reSP.split(value)
            elif key in ['self']:
                link[key] = value
            else:
                if 'attributes' not in link:
                    link['attributes'] = collections.OrderedDict()
                link['attributes'][key] = value

        if not link.validate():
            raise occi.ParseError('Missing fields in OCCI Link', body)

        return link


    def parse_attribute_value(self, body):
        """Parse OCCI Attribute value and detect its type

        string, number, and boolean types are detected, enum is returned as string.

        :param string body: text to parse
        :return: attribute type and value
        :rtype: [string, any]
        """
        if not body:
            raise occi.ParseError('OCCI Attribute value expected')

        matched = TextRenderer.reQuoted.match(body)
        if matched != None:
            t = 'string'
            value = matched.group(1)
            value = TextRenderer.reStringUnescape.sub(r'\1', value)
            if len(value) + 2 < len(body):
                raise occi.ParseError('Unexpected quotes in OCCI Attribute value', body)
            return [t, value]

        matched = TextRenderer.reNumber.match(body)
        if matched != None:
            t = 'number'
            if TextRenderer.reIntNumber.match(body) != None:
                value = int(matched.group(1))
            else:
                value = float(matched.group(1))
            return [t, value]

        matched = TextRenderer.reBool.match(body)
        if matched != None:
            t = 'boolean'
            if matched.group(1) == 'false':
                value = False
            else:
                value = True
            return [t, value]

        raise occi.ParseError('Unexpected format of OCCI Attribute value', body)


    def parse_attribute_body(self, body):
        """Parse OCCI Attribute body

        :param string body: text to parse
        :return: attribute type and value
        :rtype: occi.Attribute
        """

        attribute = occi.Attribute()
        keyvalue = TextRenderer.reKeyValue.split(body, 1)
        key = keyvalue[0]
        value = keyvalue[1]
        keymatch = TextRenderer.reKeyCheck.match(key)
        if keymatch == None:
            raise occi.ParseError('Invalid characters in attribute name', chunk)
        t, v = self.parse_attribute_value(value)

        return occi.Attribute({'name': key, 'type': t, 'value': v})


    def parse_categories(self, body, headers):
        """Parse OCCI Category Collection

        :param string body[]: text to parse
        :param string headers[]: headers to parse (unused in plain/text)
        :return: Array of OCCI Categories
        :rtype: occi.Category[]
        """
        categories = []
        category_ids = set()

        for line in body:
            matched = TextRenderer.reCategory.match(line)
            if not matched:
                raise occi.ParseError('"Category" expected', line)

            category = self.parse_category_body(line[matched.end():])

            # check uniqueness
            key = category['term'] + category['scheme']
            if key in category_ids:
                raise occi.ParseError('Category not unique (term "%s", scheme "%s")' % (category['term'], category['scheme']), line)
            category_ids.add(key)

            categories.append(category)

        return categories


    def parse_locations(self, body, headers):
        """Parse OCCI Entity collection

        :param string body[]: text to parse
        :param string headers[]: headers to parse (unused in text/plain)
        :return: Array of links
        :rtype: string[]
        """
        locations = []
        for line in body:
            matched = TextRenderer.reLocation.match(line)
            if not matched:
                raise occi.ParseError('OCCI Location expected in OCCI Entity collection', line)
            uri = matched.group(2)
            if not check_url(uri, scheme = True, host = True):
                raise occi.ParseError('Invalid URI in OCCI Entity collection', line)
            locations.append(uri)

        return locations


    def parse_resource(self, body, header):
        """Parse OCCI Resource instance

        :param string body[]: text to parse
        :param string headers[]: headers to parse (unused in text/plain)
        :return: categories, links, and attributes
        :rtype: [occi.Category categories[], occi.Link links[], occi.Attribute attributes[]]
        """
        categories = []
        links = []
        attributes = []

        for line in body:
            line = line.rstrip('\r\n')
            matched = TextRenderer.reCategory.match(line)
            if matched != None:
                s = line[matched.end():]
                categories.append(self.parse_category_body(s))
                continue
            matched = TextRenderer.reLink.match(line)
            if matched != None:
                s = line[matched.end():]
                links.append(self.parse_link_body(s))
                continue
            matched = TextRenderer.reAttribute.match(line)
            if matched != None:
                s = line[matched.end():]
                attributes.append(self.parse_attribute_body(s))
                continue
            else:
                raise occi.ParseError('Unexpected content of OCCI Resource instance')

        return [categories, links, attributes]
