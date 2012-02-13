# -*- coding: utf-8 -*-
"""
    test_cpp_domain
    ~~~~~~~~~~~~~~~

    Tests the C++ Domain

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import *

from sphinx.domains.cpp import DefinitionParser


def parse(name, string):
    return getattr(DefinitionParser(string), 'parse_' + name)()


def test_type_definitions():
    rv = parse('member_object', '  const  std::string  &  name = 42')
    assert unicode(rv) == 'const std::string& name = 42'

    rv = parse('member_object', '  const  std::string  &  name leftover')
    assert unicode(rv) == 'const std::string& name'

    rv = parse('member_object', '  const  std::string  &  name [n] leftover')
    assert unicode(rv) == 'const std::string& name[n]'

    rv = parse('member_object', 'const std::vector< unsigned int, long> &name')
    assert unicode(rv) == 'const std::vector<unsigned int, long>& name'

    x = 'std::vector<std::pair<std::string, int>>& module::test(register ' \
        'foo, bar, std::string baz="foobar, blah, bleh") const = 0'
    assert unicode(parse('function', x)) == x

    x = 'module::myclass::operator std::vector<std::string>()'
    assert unicode(parse('function', x)) == x
    x = 'explicit module::myclass::foo::foo()'
    assert unicode(parse('function', x)) == x

    x = 'int printf(const char* fmt, ...)'
    assert unicode(parse('function', x)) == x

    x = 'std::vector<std::pair<std::string, long long>> module::blah'
    assert unicode(parse('type_object', x)) == x

    assert unicode(parse('type_object', 'long long int foo')) == 'long long foo'

    x = 'void operator()(const boost::array<VertexID, 2>& v) const'
    assert unicode(parse('function', x)) == x

    x = 'void operator()(const boost::array<VertexID, 2, "foo,  bar">& v) const'
    assert unicode(parse('function', x)) == x

    x = 'MyClass::MyClass(MyClass::MyClass&&)'
    assert unicode(parse('function', x)) == x

    x = 'constexpr int get_value()'
    assert unicode(parse('function', x)) == x

    x = 'int get_value() const noexcept'
    assert unicode(parse('function', x)) == x

    x = 'int main(int argc, char* argv[][])'
    assert unicode(parse('function', x)) == x

    x = 'std::vector<std::pair<std::string, int>>& module::test(register ' \
        'foo, bar[n], std::string baz="foobar, blah, bleh") const = 0'
    assert unicode(parse('function', x)) == x

    x = 'module::myclass foo[n]'
    assert unicode(parse('member_object', x)) == x


def test_bases():
    x = 'A'
    assert unicode(parse('class', x)) == x

    x = 'A : B'
    assert unicode(parse('class', x)) == x

    x = 'A : private B'
    assert unicode(parse('class', x)) == 'A : B'

    x = 'A : public B'
    assert unicode(parse('class', x)) == x

    x = 'A : B, C'
    assert unicode(parse('class', x)) == x

    x = 'A : B, protected C, D'
    assert unicode(parse('class', x)) == x


def test_operators():
    x = parse('function', 'void operator new [  ] ()')
    assert unicode(x) == 'void operator new[]()'

    x = parse('function', 'void operator delete ()')
    assert unicode(x) == 'void operator delete()'

    for op in '*-+=/%!':
        x = parse('function', 'void operator %s ()' % op)
        assert unicode(x) == 'void operator%s()' % op
