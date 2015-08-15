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
    """
    __slots__ = []


    def validate(self):
        return 'name' in self and 'value' in self;


class AttributeDefinition(Generic):
    """OCCI Attribute Definition

    :ivar bool immutable: attribute can't be changed [false]
    :ivar bool required: attribute is required [false]
    :ivar string type: 'string', 'number', 'boolean' [string]
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
