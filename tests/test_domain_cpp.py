# -*- coding: utf-8 -*-
"""
    test_domain_cpp
    ~~~~~~~~~~~~~~~

    Tests the C++ Domain

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import text_type

from util import raises

from sphinx.domains.cpp import DefinitionParser, DefinitionError

def parse(name, string):
    parser = DefinitionParser(string)
    res = getattr(parser, "parse_" + name + "_object")()
    if not parser.eof:
        print("Parsing stopped at", parser.pos)
        print(string)
        print('-'*parser.pos + '^')
        raise DefinitionError("")
    return res

def check(name, input, output=None):
    # first a simple check of the AST
    if output is None:
        output = input
    ast = parse(name, input)
    res = text_type(ast)
    if res != output:
        print("Input:    ", text_type(input))
        print("Result:   ", res)
        print("Expected: ", output)
        raise DefinitionError("")
    ast.describe_signature([], 'lastIsName', None)
    ast.prefixedName = ast.name  # otherwise the get_id fails, it would be set
                                 # in handle_signarue
    ast.get_id()
    #print ".. %s:: %s" % (name, input)

def test_type_definitions():
    check("type", "public bool b", "bool b")
    check("type", "bool A::b")
    check("type", "bool *b")
    check("type", "bool *const b")
    check("type", "bool *volatile const b")
    check("type", "bool *volatile const b")
    check("type", "bool *volatile const *b")
    check("type", "bool &b")
    check("type", "bool b[]")
    check("type", "std::pair<int, int> coord")
    check("type", "long long int foo")
    check("type", 'std::vector<std::pair<std::string, long long>> module::blah')
    check("type", "std::function<void()> F")
    check("type", "std::function<R(A1, A2, A3)> F")
    check("type", "std::function<R(A1, A2, A3, As...)> F")
    check("type", "MyContainer::const_iterator")
    check("type",
          "public MyContainer::const_iterator",
          "MyContainer::const_iterator")
    # test decl specs on right
    check("type", "bool const b")

    check('member',
          '  const  std::string  &  name = 42',
          'const std::string &name = 42')
    check('member', '  const  std::string  &  name', 'const std::string &name')
    check('member',
          '  const  std::string  &  name [ n ]',
          'const std::string &name[n]')
    check('member',
          'const std::vector< unsigned int, long> &name',
          'const std::vector<unsigned int, long> &name')
    check('member', 'module::myclass foo[n]')

    check('function', 'operator bool() const')
    check('function', 'bool namespaced::theclass::method(arg1, arg2)')
    x = 'std::vector<std::pair<std::string, int>> &module::test(register ' \
        'foo, bar, std::string baz = "foobar, blah, bleh") const = 0'
    check('function', x)
    check('function', 'explicit module::myclass::foo::foo()')
    check('function', 'module::myclass::foo::~foo()')
    check('function', 'int printf(const char *fmt, ...)')
    check('function', 'int foo(const unsigned int j)')
    check('function', 'int foo(const int *const ptr)')
    check('function', 'module::myclass::operator std::vector<std::string>()')
    check('function',
          'void operator()(const boost::array<VertexID, 2> &v) const')
    check('function',
          'void operator()(const boost::array<VertexID, 2, "foo,  bar"> &v) const')
    check('function', 'MyClass::MyClass(MyClass::MyClass&&)')
    check('function', 'constexpr int get_value()')
    check('function', 'static constexpr int get_value()')
    check('function', 'int get_value() const noexcept')
    check('function', 'int get_value() const noexcept = delete')
    check('function', 'MyClass::MyClass(MyClass::MyClass&&) = default')
    check('function', 'virtual MyClass::a_virtual_function() const override')
    check('function', 'A B() override')
    check('function', 'A B() final')
    check('function', 'A B() final override')
    check('function', 'A B() override final', 'A B() final override')
    check('function', 'MyClass::a_member_function() volatile')
    check('function', 'MyClass::a_member_function() volatile const')
    check('function', 'MyClass::a_member_function() &&')
    check('function', 'MyClass::a_member_function() &')
    check('function', 'MyClass::a_member_function() const &')
    check('function', 'int main(int argc, char *argv[])')
    check('function', 'MyClass &MyClass::operator++()')
    check('function', 'MyClass::pointer MyClass::operator->()')

    x = 'std::vector<std::pair<std::string, int>> &module::test(register ' \
        'foo, bar[n], std::string baz = "foobar, blah, bleh") const = 0'
    check('function', x)
    check('function',
          'int foo(Foo f = Foo(double(), std::make_pair(int(2), double(3.4))))')
    check('function', 'int foo(A a = x(a))')
    raises(DefinitionError, parse, 'function', 'int foo(B b=x(a)')
    raises(DefinitionError, parse, 'function', 'int foo)C c=x(a))')
    raises(DefinitionError, parse, 'function', 'int foo(D d=x(a')
    check('function', 'int foo(const A&... a)')
    check('function', 'virtual void f()')

def test_bases():
    check('class', 'A')
    check('class', 'A::B::C')
    check('class', 'A : B')
    check('class', 'A : private B', 'A : B')
    check('class', 'A : public B')
    check('class', 'A : B, C')
    check('class', 'A : B, protected C, D')


def test_operators():
    check('function', 'void operator new [  ] ()', 'void operator new[]()')
    check('function', 'void operator delete ()', 'void operator delete()')
    check('function', 'void operator bool() const', 'void operator bool() const')
    for op in '*-+=/%!':
        check('function', 'void operator %s ()' % op, 'void operator%s()' % op)
