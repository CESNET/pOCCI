class Error(Exception):
    """Base class for pOCCI exceptions."""
    pass


class ParseError(Error):
    """Parse exception."""

    def __init__(self, value, body = None):
        self.value = value
        self.body = body

    def __str__(self):
        if self.body != None:
            return str(self.value) + ' (%s)' % str(self.body)
        else:
            return str(self.value)


class RenderError(Error):
    """Render exception."""


class Generic(dict):
    """ Generic OCCI object in python. """

    """ Memory optimization
    """
    __slots__ = []

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def validate():
        """ Validate OCCI object.

        :return: OCCI object is valid
        :rtype: bool
        """
        return True


class Attribute(Generic):
    """OCCI Attribute Instance

    :ivar string name: attribute name
    :ivar value: attribute value (any type)
    :ivar string type: 'string', 'number', 'boolean', 'enum' [string]
    """
    __slots__ = []


    def validate(self):
        return 'name' in self and 'value' in self;


class AttributeDefinition(Generic):
    """OCCI Attribute Definition

    :ivar bool immutable: attribute can't be changed [false]
    :ivar bool required: attribute is required [false]
    :ivar string type: 'string', 'number', 'boolean', 'enum' [string]
    :ivar default: default value
    :ivar string description: description
    """
    __slots__ = []


    def isrequired(self):
        return 'required' in self and self['required']


    def isimmutable(self):
        return 'immutable' in self and self['immutable']


class Category(Generic):
    """OCCI Category

    :ivar string term: term
    :ivar string scheme: scheme
    :ivar string class: class
    :ivar ...: other fields (location, actions, attributes, ...)
    """
    __slots__ = []


    def validate(self):
        return 'term' in self and 'scheme' in self and 'class' in self;


class Link(Category):
    """OCCI Link

    :ivar string uri: URI
    :ivar rel string[]: resource types
    :ivar self string: self URI
    :ivar string category[]: types
    :ivar string attributes{}: attributes
    """

    def validate(self):
        return 'uri' in self and rel in self
