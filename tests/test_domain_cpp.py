# -*- coding: utf-8 -*-
"""
    test_domain_cpp
    ~~~~~~~~~~~~~~~

    Tests the C++ Domain

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import text_type

from util import raises

from sphinx.domains.cpp import DefinitionParser, DefinitionError, NoOldIdError

ids = []

def parse(name, string):
    parser = DefinitionParser(string)
    res = getattr(parser, "parse_" + name + "_object")()
    if not parser.eof:
        print("Parsing stopped at", parser.pos)
        print(string)
        print('-'*parser.pos + '^')
        raise DefinitionError("")
    return res

def check(name, input, idv1output=None, idv2output=None, output=None):
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
    # Artificially set the prefixedName, otherwise the get_id fails.
    # It would usually have been set in handle_signarue.
    ast.prefixedName = ast.name

    if idv2output:
        idv2output = "_CPPv2" + idv2output
    try:
        idv1 = ast.get_id_v1()
        assert idv1 != None
    except NoOldIdError:
        idv1 = None
    try:
        idv2 = ast.get_id_v2()
        assert idv2 != None
    except NoOldIdError:
        idv2 = None
    if idv1 != idv1output or idv2 != idv2output:
        print("input:    %s" % text_type(input).rjust(20))
        print("          %s    %s" % ("Id v1".rjust(20), "Id v2".rjust(20)))
        print("result:   %s    %s" % (str(idv1).rjust(20), str(idv2).rjust(20)))
        print("expected: %s    %s" % (str(idv1output).rjust(20),
                                      str(idv2output).rjust(20)))
        raise DefinitionError("")
    ids.append(ast.get_id_v2())
    #print ".. %s:: %s" % (name, input)

def test_type_definitions():
    check("type", "public bool b", "b", "1b", "bool b")
    check("type", "bool A::b", "A::b", "N1A1bE")
    check("type", "bool *b", "b", "1b")
    check("type", "bool *const b", "b", "1b")
    check("type", "bool *volatile const b", "b", "1b")
    check("type", "bool *volatile const b", "b", "1b")
    check("type", "bool *volatile const *b", "b", "1b")
    check("type", "bool &b", "b", "1b")
    check("type", "bool b[]", "b", "1b")
    check("type", "std::pair<int, int> coord", "coord", "5coord")
    check("type", "long long int foo", "foo", "3foo")
    check("type", 'std::vector<std::pair<std::string, long long>> module::blah',
          "module::blah", "N6module4blahE")
    check("type", "std::function<void()> F", "F", "1F")
    check("type", "std::function<R(A1, A2)> F", "F", "1F")
    check("type", "std::function<R(A1, A2, A3)> F", "F", "1F")
    check("type", "std::function<R(A1, A2, A3, As...)> F", "F", "1F")
    check("type", "MyContainer::const_iterator",
          "MyContainer::const_iterator","N11MyContainer14const_iteratorE")
    check("type",
          "public MyContainer::const_iterator",
          "MyContainer::const_iterator", "N11MyContainer14const_iteratorE",
          output="MyContainer::const_iterator")
    # test decl specs on right
    check("type", "bool const b", "b", "1b")

    check('member', '  const  std::string  &  name = 42',
          "name__ssCR", "4name", output='const std::string &name = 42')
    check('member', '  const  std::string  &  name', "name__ssCR", "4name",
          output='const std::string &name')
    check('member', '  const  std::string  &  name [ n ]',
          "name__ssCRA", "4name", output='const std::string &name[n]')
    check('member', 'const std::vector< unsigned int, long> &name',
          "name__std::vector:unsigned-i.l:CR",
          "4name", output='const std::vector<unsigned int, long> &name')
    check('member', 'module::myclass foo[n]', "foo__module::myclassA", "3foo")

    check('function', 'operator bool() const', "castto-b-operatorC", "NKcvbEv")
    check('function', 'A::operator bool() const',
          "A::castto-b-operatorC", "NK1AcvbEv")
    check('function', 'A::operator bool() volatile const &',
          "A::castto-b-operatorVCR", "NVKR1AcvbEv")
    check('function', 'A::operator bool() volatile const &&',
          "A::castto-b-operatorVCO", "NVKO1AcvbEv")
    check('function', 'bool namespaced::theclass::method(arg1, arg2)',
          "namespaced::theclass::method__arg1.arg2",
          "N10namespaced8theclass6methodE4arg14arg2")
    x = 'std::vector<std::pair<std::string, int>> &module::test(register int ' \
        'foo, bar, std::string baz = "foobar, blah, bleh") const = 0'
    check('function', x, "module::test__i.bar.ssC",
          "NK6module4testEi3barNSt6stringE")
    check('function', 'void f(std::pair<A, B>)',
          "f__std::pair:A.B:", "1fNSt4pairI1A1BEE")
    check('function', 'explicit module::myclass::foo::foo()',
          "module::myclass::foo::foo", "N6module7myclass3foo3fooEv")
    check('function', 'module::myclass::foo::~foo()',
          "module::myclass::foo::~foo", "N6module7myclass3fooD0Ev")
    check('function', 'int printf(const char *fmt, ...)',
          "printf__cCP.z", "6printfPKcz")
    check('function', 'int foo(const unsigned int j)',
          "foo__unsigned-iC", "3fooKj")
    check('function', 'int foo(const int *const ptr)',
          "foo__iCPC", "3fooPCKi")
    check('function', 'module::myclass::operator std::vector<std::string>()',
          "module::myclass::castto-std::vector:ss:-operator",
          "N6module7myclasscvNSt6vectorINSt6stringEEEEv")
    check('function',
          'void operator()(const boost::array<VertexID, 2> &v) const',
          "call-operator__boost::array:VertexID.2:CRC",
          "NKclERKN5boost5arrayI8VertexIDX2EEE")
    check('function',
          'void operator()(const boost::array<VertexID, 2, "foo,  bar"> &v) const',
          'call-operator__boost::array:VertexID.2."foo,--bar":CRC',
          'NKclERKN5boost5arrayI8VertexIDX2EX"foo,  bar"EEE')
    check('function', 'MyClass::MyClass(MyClass::MyClass&&)',
          "MyClass::MyClass__MyClass::MyClassRR",
          "N7MyClass7MyClassERRN7MyClass7MyClassE")
    check('function', 'constexpr int get_value()', "get_valueCE", "9get_valuev")
    check('function', 'static constexpr int get_value()',
          "get_valueCE", "9get_valuev")
    check('function', 'int get_value() const noexcept',
          "get_valueC", "NK9get_valueEv")
    check('function', 'int get_value() const noexcept = delete',
          "get_valueC", "NK9get_valueEv")
    check('function', 'int get_value() volatile const',
          "get_valueVC", "NVK9get_valueEv")
    check('function', 'MyClass::MyClass(MyClass::MyClass&&) = default',
          "MyClass::MyClass__MyClass::MyClassRR",
          "N7MyClass7MyClassERRN7MyClass7MyClassE")
    check('function', 'virtual MyClass::a_virtual_function() const override',
          "MyClass::a_virtual_functionC", "NK7MyClass18a_virtual_functionEv")
    check('function', 'A B() override', "B", "1Bv")
    check('function', 'A B() final', "B", "1Bv")
    check('function', 'A B() final override', "B", "1Bv")
    check('function', 'A B() override final', "B", "1Bv",
          output='A B() final override')
    check('function', 'MyClass::a_member_function() volatile',
          "MyClass::a_member_functionV", "NV7MyClass17a_member_functionEv")
    check('function', 'MyClass::a_member_function() volatile const',
          "MyClass::a_member_functionVC", "NVK7MyClass17a_member_functionEv")
    check('function', 'MyClass::a_member_function() &&',
          "MyClass::a_member_functionO", "NO7MyClass17a_member_functionEv")
    check('function', 'MyClass::a_member_function() &',
          "MyClass::a_member_functionR", "NR7MyClass17a_member_functionEv")
    check('function', 'MyClass::a_member_function() const &',
          "MyClass::a_member_functionCR", "NKR7MyClass17a_member_functionEv")
    check('function', 'int main(int argc, char *argv[])',
          "main__i.cPA", "4mainiA_Pc")
    check('function', 'MyClass &MyClass::operator++()',
          "MyClass::inc-operator", "N7MyClassppEv")
    check('function', 'MyClass::pointer MyClass::operator->()',
          "MyClass::pointer-operator", "N7MyClassptEv")

    x = 'std::vector<std::pair<std::string, int>> &module::test(register int ' \
        'foo, bar[n], std::string baz = "foobar, blah, bleh") const = 0'
    check('function', x, "module::test__i.barA.ssC",
          "NK6module4testEiAn_3barNSt6stringE")
    check('function',
          'int foo(Foo f = Foo(double(), std::make_pair(int(2), double(3.4))))',
          "foo__Foo", "3foo3Foo")
    check('function', 'int foo(A a = x(a))', "foo__A", "3foo1A")
    raises(DefinitionError, parse, 'function', 'int foo(B b=x(a)')
    raises(DefinitionError, parse, 'function', 'int foo)C c=x(a))')
    raises(DefinitionError, parse, 'function', 'int foo(D d=x(a')
    check('function', 'int foo(const A&... a)', "foo__ACRDp", "3fooDpRK1A")
    check('function', 'virtual void f()', "f", "1fv")
    # test for ::nestedName, from issue 1738
    check("function", "result(int val, ::std::error_category const &cat)",
          "result__i.std::error_categoryCR", "6resultiRNSt14error_categoryE")
    check("function", "int *f()", "f", "1fv")
    # tests derived from issue #1753 (skip to keep sanity)
    check("function", "f(int (&array)[10])", None, "1fRA10_i")
    check("function", "void f(int (&array)[10])", None, "1fRA10_i")
    check("function", "void f(float *q(double))", None, "1fFPfdE")
    check("function", "void f(float *(*q)(double))", None, "1fPFPfdE")
    check("function", "void f(float (*q)(double))", None, "1fPFfdE")
    check("function", "int (*f(double d))(float)", "f__double", "1fd")
    check("function", "int (*f(bool b))[5]", "f__b", "1fb")
    check("function", "int (*A::f(double d) const)(float)",
          "A::f__doubleC", "NK1A1fEd")
    check("function", "void f(std::shared_ptr<int(double)> ptr)",
          None, "1fNSt10shared_ptrIFidEEE")

    # TODO: make tests for functions in a template, e.g., Test<int&&()>
    # such that the id generation for function type types is correct.

    check('class', 'public A', "A", "1A", output='A')
    check('class', 'private A', "A", "1A")

    check('enum', 'A', None, "1A")
    check('enum', 'A : std::underlying_type<B>::type', None, "1A")
    check('enum', 'A : unsigned int', None, "1A")
    check('enum', 'public A', None, "1A", output='A')
    check('enum', 'private A', None, "1A")

    check('enumerator', 'A', None, "1A")
    check('enumerator', 'A = std::numeric_limits<unsigned long>::max()',
          None, "1A")

def test_bases():
    check('class', 'A', "A", "1A")
    check('class', 'A::B::C', "A::B::C", "N1A1B1CE")
    check('class', 'A : B', "A", "1A")
    check('class', 'A : private B', "A", "1A", output='A : B')
    check('class', 'A : public B', "A", "1A")
    check('class', 'A : B, C', "A", "1A")
    check('class', 'A : B, protected C, D', "A", "1A")

def test_operators():
    check('function', 'void operator new [  ] ()',
          "new-array-operator", "nav", output='void operator new[]()')
    check('function', 'void operator delete ()',
          "delete-operator", "dlv", output='void operator delete()')
    check('function', 'operator bool() const',
          "castto-b-operatorC", "NKcvbEv", output='operator bool() const')

    check('function', 'void operator * ()',
          "mul-operator", "mlv", output='void operator*()')
    check('function', 'void operator - ()',
          "sub-operator", "miv", output='void operator-()')
    check('function', 'void operator + ()',
          "add-operator", "plv", output='void operator+()')
    check('function', 'void operator = ()',
          "assign-operator", "aSv", output='void operator=()')
    check('function', 'void operator / ()',
          "div-operator", "dvv", output='void operator/()')
    check('function', 'void operator % ()',
          "mod-operator", "rmv", output='void operator%()')
    check('function', 'void operator ! ()',
          "not-operator", "ntv", output='void operator!()')

#def test_print():
#    # used for getting all the ids out for checking
#    for a in ids:
#        print(a)
#    raise DefinitionError("")
