from sphinx.config import string_classes, ENUM

value1 = 123  # wrong type
value2 = 123  # lambda with wrong type
value3 = []  # lambda with correct type
value4 = True  # child type
value5 = 3  # parent type
value6 = ()  # other sequence type, also raises
value7 = ['foo']  # explicitly permitted

class A(object):
    pass
class B(A):
    pass
class C(A):
    pass

value8 = C()  # sibling type

# both have no default or permissible types
value9 = 'foo'
value10 = 123
value11 = u'bar'
value12 = u'bar'
value13 = 'bar'
value14 = u'bar'
value15 = 'bar'
value16 = u'bar'


def setup(app):
    app.add_config_value('value1', 'string', False)
    app.add_config_value('value2', lambda conf: [], False)
    app.add_config_value('value3', [], False)
    app.add_config_value('value4', 100, False)
    app.add_config_value('value5', False, False)
    app.add_config_value('value6', [], False)
    app.add_config_value('value7', 'string', False, [list])
    app.add_config_value('value8', B(), False)
    app.add_config_value('value9', None, False)
    app.add_config_value('value10', None, False)
    app.add_config_value('value11', None, False, [str])
    app.add_config_value('value12', 'string', False)
    app.add_config_value('value13', None, False, string_classes)
    app.add_config_value('value14', None, False, string_classes)
    app.add_config_value('value15', u'unicode', False)
    app.add_config_value('value16', u'unicode', False)
    app.add_config_value('value17', 'default', False, ENUM('default', 'one', 'two'))
