# -*- coding: utf-8 -*-
"""
    test_cpp_domain
    ~~~~~~~~~~~~~~~

    Tests the C++ Domain

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import text_type

from util import raises

from sphinx.domains.cpp import DefinitionParser, DefinitionError


def parse(name, string):
    return getattr(DefinitionParser(string), 'parse_' + name)()


def test_type_definitions():
    rv = parse('member_object', '  const  std::string  &  name = 42')
    assert text_type(rv) == 'const std::string& name = 42'

    rv = parse('member_object', '  const  std::string  &  name leftover')
    assert text_type(rv) == 'const std::string& name'

    rv = parse('member_object', '  const  std::string  &  name [n] leftover')
    assert text_type(rv) == 'const std::string& name[n]'

    rv = parse('member_object', 'const std::vector< unsigned int, long> &name')
    assert text_type(rv) == 'const std::vector<unsigned int, long>& name'

    x = 'std::vector<std::pair<std::string, int>>& module::test(register ' \
        'foo, bar, std::string baz="foobar, blah, bleh") const = 0'
    assert text_type(parse('function', x)) == x

    x = 'module::myclass::operator std::vector<std::string>()'
    assert text_type(parse('function', x)) == x
    x = 'explicit module::myclass::foo::foo()'
    assert text_type(parse('function', x)) == x

    x = 'int printf(const char* fmt, ...)'
    assert text_type(parse('function', x)) == x

    x = 'int foo(const unsigned int j)'
    assert text_type(parse('function', x)) == x

    x = 'int foo(const unsigned int const j)'
    assert text_type(parse('function', x)) == x

    x = 'int foo(const int* const ptr)'
    assert text_type(parse('function', x)) == x

    x = 'std::vector<std::pair<std::string, long long>> module::blah'
    assert text_type(parse('type_object', x)) == x

    assert text_type(parse('type_object', 'long long int foo')) == 'long long foo'

    x = 'void operator()(const boost::array<VertexID, 2>& v) const'
    assert text_type(parse('function', x)) == x

    x = 'void operator()(const boost::array<VertexID, 2, "foo,  bar">& v) const'
    assert text_type(parse('function', x)) == x

    x = 'MyClass::MyClass(MyClass::MyClass&&)'
    assert text_type(parse('function', x)) == x

    x = 'constexpr int get_value()'
    assert text_type(parse('function', x)) == x

    x = 'static constexpr int get_value()'
    assert text_type(parse('function', x)) == x

    x = 'int get_value() const noexcept'
    assert text_type(parse('function', x)) == x

    x = 'int get_value() const noexcept = delete'
    assert text_type(parse('function', x)) == x

    x = 'MyClass::MyClass(MyClass::MyClass&&) = default'
    assert text_type(parse('function', x)) == x

    x = 'MyClass::a_virtual_function() const override'
    assert text_type(parse('function', x)) == x

    x = 'MyClass::a_member_function() volatile'
    assert text_type(parse('function', x)) == x

    x = 'MyClass::a_member_function() const volatile'
    assert text_type(parse('function', x)) == x

    x = 'MyClass::a_member_function() &&'
    assert text_type(parse('function', x)) == x

    x = 'MyClass::a_member_function() &'
    assert text_type(parse('function', x)) == x

    x = 'MyClass::a_member_function() const &'
    assert text_type(parse('function', x)) == x

    x = 'int main(int argc, char* argv[][])'
    assert text_type(parse('function', x)) == x

    x = 'std::vector<std::pair<std::string, int>>& module::test(register ' \
        'foo, bar[n], std::string baz="foobar, blah, bleh") const = 0'
    assert text_type(parse('function', x)) == x

    x = 'module::myclass foo[n]'
    assert text_type(parse('member_object', x)) == x

    x = 'int foo(Foo f=Foo(double(), std::make_pair(int(2), double(3.4))))'
    assert text_type(parse('function', x)) == x

    x = 'int foo(A a=x(a))'
    assert text_type(parse('function', x)) == x

    x = 'int foo(B b=x(a)'
    raises(DefinitionError, parse, 'function', x)

    x = 'int foo)C c=x(a))'
    raises(DefinitionError, parse, 'function', x)

    x = 'int foo(D d=x(a'
    raises(DefinitionError, parse, 'function', x)

    x = 'int foo(const A&... a)'
    assert text_type(parse('function', x)) == x

def test_bases():
    x = 'A'
    assert text_type(parse('class', x)) == x

    x = 'A : B'
    assert text_type(parse('class', x)) == x

    x = 'A : private B'
    assert text_type(parse('class', x)) == 'A : B'

    x = 'A : public B'
    assert text_type(parse('class', x)) == x

    x = 'A : B, C'
    assert text_type(parse('class', x)) == x

    x = 'A : B, protected C, D'
    assert text_type(parse('class', x)) == x


def test_operators():
    x = parse('function', 'void operator new [  ] ()')
    assert text_type(x) == 'void operator new[]()'

    x = parse('function', 'void operator delete ()')
    assert text_type(x) == 'void operator delete()'

    for op in '*-+=/%!':
        x = parse('function', 'void operator %s ()' % op)
        assert text_type(x) == 'void operator%s()' % op
