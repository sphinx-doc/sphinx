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
