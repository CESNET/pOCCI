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
            s += ';%s' % text_link_attributes(key, value)

    return s


class TextRenderer(Renderer):
    """Plain Text OCCI Renderer
    """

    reChunks = re.compile(r';\s*')
    reCategory = re.compile(r'^Category:\s*(.*)')
    reKeyValue = re.compile(r'\s*=\s*')
    reQuoted = re.compile(r'^"(.*)"$')
    reSP = re.compile(r'\s+')
    reAttributes = re.compile(r'([^\{ ]+)(\{[^\}]*\})?\s*')
    reLocation = re.compile(r'^X-OCCI-Location:\s*(.*)')

    def render_category(self, category):
        """Render OCCI Category

        :param occi.Category category: OCCI Category object
        :return: render result
        :rtype: string
        """
        return 'Category: ' + text_category(category)


    def render_categories(self, categories):
        """Render OCCI Category collection

        :param occi.Category category[]: OCCI Category array
        :return: render result
        :rtype: string
        """
        res = []
        for category in categories:
            res.append(self.render_category(category))
        return eol.join(res) + eol


    def render_resource(self, categories, links = None, attributes = None):
        """Render OCCI Resource instance

        :param occi.Category category: OCCI Category object
        :param occi.Link links[]: OCCI Link array
        :param occi.Attribute attributes[]: OCCI Attribute array
        :return: render result
        :rtype: string
        """
        Renderer.render_resource(self, categories, links, attributes)
        cat_s = self.render_categories(categories)
        res = []
        if links != None:
            for link in links:
                res.append(self.render_link(link))
        if attributes != None:
            for attr in attributes:
                res.append(self.render_attribute(attr))
        if res:
            return cat_s + eol.join(res) + eol
        else:
            return cat_s


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

        :param string location: location URI
        :return render result
        :rtype: string
        """
        if not location:
            return ''
        s = []
        for location in locations:
            s.append('X-OCCI-Location: ' + location)
        return ''.join(s)


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


    def parse_category(self, body):
        """Parse OCCI Category.

        Example::

           Category: entity;scheme="http://schemas.ogf.org/occi/core#";class="kind";title="entity";location="/entity/";attributes="occi.core.id{immutable required} occi.core.title"

        :param string body: text to parse
        :return: OCCI Category
        :rtype: occi.Category
        """
        category = occi.Category()

        chunks = TextRenderer.reChunks.split(body)
        matched = TextRenderer.reCategory.match(chunks[0])
        if not matched:
            raise occi.ParseError('Category" expected', chunks[0])

        if not matched.group(1):
            raise occi.ParseERror('Invalid format of category, term expected', chunks[0])

        category['term'] = matched.group(1)

        # skip the first chunk (category term)
        for chunk in chunks[1:]:
            keyvalue = TextRenderer.reKeyValue.split(chunk, 1)

            # every value quoted, only class has quoting optional
            key = keyvalue[0]
            value = keyvalue[1]
            valuematch = TextRenderer.reQuoted.match(value)
            if valuematch == None and key != 'class':
                raise occi.ParseError('Category value not quoted', chunk)
            value = valuematch.group(1)
            # sanity check: there should not be any quotes now
            if value[0] == '"' or (len(value) >= 2 and value[-1] == '"'):
                raise occi.ParseError('Unexpected quotes in category', chunk)

            if key == 'location':
                if not check_url(value):
                    raise occi.ParseError('URL is not valid in category location', chunk)
                category[key] = value
            elif key == 'attributes':
                category[key] = self.parse_attribute_defs(value)
            elif key == 'actions':
                category[key] = self.parse_actions(value)
            elif key in ['scheme', 'class', 'title', 'rel']:
                category[key] = value
            else:
                raise occi.parseerror('unknown key "%s" in category' % key, chunk)

        if not category.validate():
            raise occi.ParseError('Missing fields in category', body)

        return category


    def parse_categories(self, body):
        """Parse OCCI Category Collection

        :param string[]: body text to parse
        :return: Array of OCCI Categories
        :rtype: occi.Category[]
        """
        categories = []
        category_ids = set()
        check_categories = 0
        check_quoting = 0
        check_unique = 0

        for line in body:
            category = self.parse_category(line)

            # check uniqueness
            key = category['term'] + category['scheme']
            if key in category_ids:
                raise occi.ParseError('Category not unique (term "%s", scheme "%s")' % (category['term'], category['scheme']), line)
            category_ids.add(key)

            categories.append(category)

        return categories


    def parse_locations(self, body):
        """Parse OCCI Entity collection

        :param string[]: body text to parse
        :return: Array of links
        :rtype: string[]
        """
        locations = []
        for line in body:
            matched = TextRenderer.reLocation.match(line)
            if not matched:
                raise occi.ParseError('OCCI Location expected in OCCI Entity collection', line)
            uri = matched.group(1)
            if not check_url(uri, scheme = True, host = True):
                raise occi.ParseError('Invalid URI in OCCI Entity collection', line)
            locations.append(uri)

        return locations
