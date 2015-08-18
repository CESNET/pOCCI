import re
import sys

import occi
from render_base import Renderer, check_url


eol = '\n\r'


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
    text_actions = []
    if actions:
        for action in actions:
            text_actions.append(actions)
    return ' '.join(text_actions)


def text_category(category = None):
    s = '%s; scheme="%s"; class="%s"' % (category['term'], category['scheme'], category['class'])

    for item in ['title', 'rel', 'location']:
        if item in category:
            s += '; %s="%s"' % (item, category[item])

    if 'attributes' in category:
        s += '; %s="%s"' % ('attributes', text_attribute_defs(category['attributes']))

    if 'actions' in category:
        s += '; %s="%s"' % ('actions', text_actions(category['actions']))

    return s


class TextRenderer(Renderer):
    """ Plain Text OCCI Renderer
    """

    reChunks = re.compile(r';\s*')
    reCategory = re.compile(r'^Category:\s*(.*)')
    reKeyValue = re.compile(r'\s*=\s*')
    reQuoted = re.compile(r'^".*"$')
    reSP = re.compile(r'\s')

    reAttributes = re.compile(r'([^\{ ]+)(\{[^\}]*\})?\s*')


    def render_category(self, category = None):
        """ Render OCCI Category

        :param occi.Category category: OCCI Category object
        :return: render result
        :rtpye: string
        """
        return 'Category: ' + text_category(category) + eol


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
                if 'required' in attrs:
                    attribute['required'] = True
                if 'immutable' in attrs:
                    attribute['immutable'] = True
            result.append(attribute)

        if body:
            raise occi.ParseError('Error parsing OCCI attribute definitions', body)

        return result


    def parse_actions(self, body):
        """Parse OCCI Actions. TODO

        Example::

           TODO

        :param string body: text to parse
        :return: array of OCCI Action
        :rtype: occi.Action[]
        """
        return []


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
            if key != 'class' or TextRenderer.reQuoted.match(value):
                value = value.strip('"')
            # sanity check: there should not be any quotes now
            if TextRenderer.reQuoted.match(value):
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
            raise occi.parseerror('Missing fields in category', body)

        return category


    def parse_categories(self, body):
        """Parse OCCI Category Collection.

        :param string: body text to parse
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


if __name__ == "__main__":
    body = []

    r = TextRenderer()
    print r

    with open('../body.txt') as f:
        for line in f:
            body.append(line.rstrip('\r\n'))

    print body
    print

    categories = r.parse_categories(body)

    print categories
