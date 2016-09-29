# -*- coding: utf-8 -*-
"""
    test_domain_cpp
    ~~~~~~~~~~~~~~~

    Tests the C++ Domain

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from six import text_type

from util import raises, with_app

from sphinx import addnodes
from sphinx.domains.cpp import DefinitionParser, DefinitionError, NoOldIdError
from sphinx.domains.cpp import Symbol
import sphinx.domains.cpp as cppDomain

ids = []


def parse(name, string):
    class Config(object):
        cpp_id_attributes = ["id_attr"]
        cpp_paren_attributes = ["paren_attr"]
    parser = DefinitionParser(string, None, Config())
    ast = parser.parse_declaration(name)
    if not parser.eof:
        print("Parsing stopped at", parser.pos)
        print(string)
        print('-'*parser.pos + '^')
        raise DefinitionError("")
    # The scopedness would usually have been set by CPPEnumObject
    if name == "enum":
        ast.scoped = None  # simulate unscoped enum
    return ast


def check(name, input, idv1output=None, idv2output=None, output=None):
    # first a simple check of the AST
    if output is None:
        output = input
    ast = parse(name, input)
    res = text_type(ast)
    if res != output:
        print("")
        print("Input:    ", text_type(input))
        print("Result:   ", res)
        print("Expected: ", output)
        raise DefinitionError("")
    rootSymbol = Symbol(None, None, None, None, None, None)
    symbol = rootSymbol.add_declaration(ast, docname="TestDoc")
    parentNode = addnodes.desc()
    signode = addnodes.desc_signature(input, '')
    parentNode += signode
    ast.describe_signature(signode, 'lastIsName', symbol)

    if idv2output:
        idv2output = "_CPPv2" + idv2output
    try:
        idv1 = ast.get_id_v1()
        assert idv1 is not None
    except NoOldIdError:
        idv1 = None
    try:
        idv2 = ast.get_id_v2()
        assert idv2 is not None
    except NoOldIdError:
        idv2 = None
    if idv1 != idv1output or idv2 != idv2output:
        print("input:    %s" % text_type(input).rjust(20))
        print("          %s    %s" % ("Id v1".rjust(20), "Id v2".rjust(20)))
        print("result:   %s    %s" % (str(idv1).rjust(20), str(idv2).rjust(20)))
        print("expected: %s    %s" % (str(idv1output).rjust(20),
                                      str(idv2output).rjust(20)))
        print(rootSymbol.dump(0))
        raise DefinitionError("")
    ids.append(ast.get_id_v2())
    # print ".. %s:: %s" % (name, input)


def test_fundamental_types():
    # see http://en.cppreference.com/w/cpp/language/types
    for t, id_v2 in cppDomain._id_fundamental_v2.items():
        if t == "decltype(auto)":
            continue

        def makeIdV1():
            id = t.replace(" ", "-").replace("long", "l").replace("int", "i")
            id = id.replace("bool", "b").replace("char", "c")
            id = id.replace("wc_t", "wchar_t").replace("c16_t", "char16_t")
            id = id.replace("c32_t", "char32_t")
            return "f__%s" % id

        def makeIdV2():
            id = id_v2
            if t == "std::nullptr_t":
                id = "NSt9nullptr_tE"
            return "1f%s" % id
        check("function", "void f(%s arg)" % t, makeIdV1(), makeIdV2())


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
          "MyContainer::const_iterator", "N11MyContainer14const_iteratorE")
    check("type",
          "public MyContainer::const_iterator",
          "MyContainer::const_iterator", "N11MyContainer14const_iteratorE",
          output="MyContainer::const_iterator")
    # test decl specs on right
    check("type", "bool const b", "b", "1b")
    # test name in global scope
    check("type", "bool ::B::b", "B::b", "N1B1bE")

    check('type', 'A = B', None, '1A')

    # from breathe#267 (named function parameters for function pointers
    check('type', 'void (*gpio_callback_t)(struct device *port, uint32_t pin)',
          'gpio_callback_t', '15gpio_callback_t')
    check('type', 'void (*f)(std::function<void(int i)> g)', 'f', '1f')


def test_concept_definitions():
    check('concept', 'template<typename Param> A::B::Concept',
          None, 'I0EN1A1B7ConceptE')
    check('concept', 'template<typename A, typename B, typename ...C> Foo',
          None, 'I00DpE3Foo')
    check('concept', 'template<typename Param> A::B::Concept()',
          None, 'I0EN1A1B7ConceptE')
    check('concept', 'template<typename A, typename B, typename ...C> Foo()',
          None, 'I00DpE3Foo')
    raises(DefinitionError, parse, 'concept', 'Foo')
    raises(DefinitionError, parse, 'concept',
           'template<typename T> template<typename U> Foo')


def test_member_definitions():
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
    check('member', 'int *const p', 'p__iPC', '1p')
    check('member', 'extern int myInt', 'myInt__i', '5myInt')
    check('member', 'thread_local int myInt', 'myInt__i', '5myInt')
    check('member', 'extern thread_local int myInt', 'myInt__i', '5myInt')
    check('member', 'thread_local extern int myInt', 'myInt__i', '5myInt',
          'extern thread_local int myInt')


def test_function_definitions():
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
    check("function", "void f(int *const p)", "f__iPC", "1fPCi")
    check("function", "void f(int *volatile const p)", "f__iPVC", "1fPVCi")

    check('function', 'extern int f()', 'f', '1fv')

    # TODO: make tests for functions in a template, e.g., Test<int&&()>
    # such that the id generation for function type types is correct.

    check('function', 'friend std::ostream &f(std::ostream&, int)',
          'f__osR.i', '1fRNSt7ostreamEi')

    # from breathe#223
    check('function', 'void f(struct E e)', 'f__E', '1f1E')
    check('function', 'void f(class E e)', 'f__E', '1f1E')
    check('function', 'void f(typename E e)', 'f__E', '1f1E')
    check('function', 'void f(enum E e)', 'f__E', '1f1E')
    check('function', 'void f(union E e)', 'f__E', '1f1E')

    # pointer to member (function)
    check('function', 'void f(int C::*)', None, '1fM1Ci')
    check('function', 'void f(int C::* p)', None, '1fM1Ci')
    check('function', 'void f(int ::C::* p)', None, '1fM1Ci')
    check('function', 'void f(int C::* const)', None, '1fKM1Ci')
    check('function', 'void f(int C::* const&)', None, '1fRKM1Ci')
    check('function', 'void f(int C::* volatile)', None, '1fVM1Ci')
    check('function', 'void f(int C::* const volatile)', None, '1fVKM1Ci',
          output='void f(int C::* volatile const)')
    check('function', 'void f(int C::* volatile const)', None, '1fVKM1Ci')
    check('function', 'void f(int (C::*)(float, double))', None, '1fM1CFifdE')
    check('function', 'void f(int (C::* p)(float, double))', None, '1fM1CFifdE')
    check('function', 'void f(int (::C::* p)(float, double))', None, '1fM1CFifdE')
    check('function', 'void f(void (C::*)() const &)', None, '1fM1CKRFvvE')
    check('function', 'int C::* f(int, double)', None, '1fid')
    check('function', 'void f(int C::* *)', None, '1fPM1Ci')


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

    check('function', 'void operator "" _udl()',
          None, 'li4_udlv', output='void operator""_udl()')


def test_class_definitions():
    check('class', 'public A', "A", "1A", output='A')
    check('class', 'private A', "A", "1A")
    check('class', 'A final', 'A', '1A')

    # test bases
    check('class', 'A', "A", "1A")
    check('class', 'A::B::C', "A::B::C", "N1A1B1CE")
    check('class', 'A : B', "A", "1A")
    check('class', 'A : private B', "A", "1A", output='A : B')
    check('class', 'A : public B', "A", "1A")
    check('class', 'A : B, C', "A", "1A")
    check('class', 'A : B, protected C, D', "A", "1A")
    check('class', 'A : virtual private B', 'A', '1A', output='A : virtual B')
    check('class', 'A : B, virtual C', 'A', '1A')
    check('class', 'A : public virtual B', 'A', '1A')
    check('class', 'A : B, C...', 'A', '1A')
    check('class', 'A : B..., C', 'A', '1A')


def test_enum_definitions():
    check('enum', 'A', None, "1A")
    check('enum', 'A : std::underlying_type<B>::type', None, "1A")
    check('enum', 'A : unsigned int', None, "1A")
    check('enum', 'public A', None, "1A", output='A')
    check('enum', 'private A', None, "1A")

    check('enumerator', 'A', None, "1A")
    check('enumerator', 'A = std::numeric_limits<unsigned long>::max()',
          None, "1A")


def test_templates():
    check('class', "A<T>", None, "IE1AI1TE", output="template<> A<T>")
    # first just check which objects support templating
    check('class', "template<> A", None, "IE1A")
    check('function', "template<> void A()", None, "IE1Av")
    check('member', "template<> A a", None, "IE1a")
    check('type', "template<> a = A", None, "IE1a")
    raises(DefinitionError, parse, 'enum', "template<> A")
    raises(DefinitionError, parse, 'enumerator', "template<> A")
    # then all the real tests
    check('class', "template<typename T1, typename T2> A", None, "I00E1A")
    check('type', "template<> a", None, "IE1a")

    check('class', "template<typename T> A", None, "I0E1A")
    check('class', "template<class T> A", None, "I0E1A")
    check('class', "template<typename ...T> A", None, "IDpE1A")
    check('class', "template<typename...> A", None, "IDpE1A")
    check('class', "template<typename = Test> A", None, "I0E1A")
    check('class', "template<typename T = Test> A", None, "I0E1A")

    check('class', "template<template<typename> typename T> A",
          None, "II0E0E1A")
    check('class', "template<int> A", None, "I_iE1A")
    check('class', "template<int T> A", None, "I_iE1A")
    check('class', "template<int... T> A", None, "I_DpiE1A")
    check('class', "template<int T = 42> A", None, "I_iE1A")
    check('class', "template<int = 42> A", None, "I_iE1A")

    # from breathe#218
    check('function',
          "template<typename F> "
          "void allow(F *f, typename func<F, B, G!=1>::type tt)",
          None, "I0E5allowP1FN4funcI1F1BXG!=1EE4typeE")

    # from #2058
    check('function',
          "template<typename Char, typename Traits> "
          "inline std::basic_ostream<Char, Traits> &operator<<("
          "std::basic_ostream<Char, Traits> &os, "
          "const c_string_view_base<const Char, Traits> &str)",
          None, "I00ElsRNSt13basic_ostreamI4Char6TraitsEE"
          "RK18c_string_view_baseIK4Char6TraitsE")

    # template introductions
    raises(DefinitionError, parse, 'enum', 'abc::ns::foo{id_0, id_1, id_2} A')
    raises(DefinitionError, parse, 'enumerator', 'abc::ns::foo{id_0, id_1, id_2} A')
    check('class', 'abc::ns::foo{id_0, id_1, id_2} xyz::bar',
          None, 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barE')
    check('class', 'abc::ns::foo{id_0, id_1, ...id_2} xyz::bar',
          None, 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barE')
    check('class', 'abc::ns::foo{id_0, id_1, id_2} xyz::bar<id_0, id_1, id_2>',
          None, 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barI4id_04id_14id_2EE')
    check('class', 'abc::ns::foo{id_0, id_1, ...id_2} xyz::bar<id_0, id_1, id_2...>',
          None, 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barI4id_04id_1Dp4id_2EE')

    check('class', 'template<> Concept{U} A<int>::B',
          None, 'IEI0EX7ConceptI1UEEN1AIiE1BE')

    check('type', 'abc::ns::foo{id_0, id_1, id_2} xyz::bar = ghi::qux',
          None, 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barE')
    check('type', 'abc::ns::foo{id_0, id_1, ...id_2} xyz::bar = ghi::qux',
          None, 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barE')
    check('function', 'abc::ns::foo{id_0, id_1, id_2} void xyz::bar()',
          None, 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barEv')
    check('function', 'abc::ns::foo{id_0, id_1, ...id_2} void xyz::bar()',
          None, 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barEv')
    check('member', 'abc::ns::foo{id_0, id_1, id_2} ghi::qux xyz::bar',
          None, 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barE')
    check('member', 'abc::ns::foo{id_0, id_1, ...id_2} ghi::qux xyz::bar',
          None, 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barE')
    check('concept', 'Iterator{T, U} Another',
          None, 'I00EX8IteratorI1T1UEE7Another')
    check('concept', 'template<typename ...Pack> Numerics = (... && Numeric<Pack>)',
          None, 'IDpE8Numerics')


def test_attributes():
    # style: C++
    check('member', '[[]] int f', 'f__i', '1f')
    check('member', '[ [ ] ] int f', 'f__i', '1f',
          # this will fail when the proper grammar is implemented
          output='[[ ]] int f')
    check('member', '[[a]] int f', 'f__i', '1f')
    # style: GNU
    check('member', '__attribute__(()) int f', 'f__i', '1f')
    check('member', '__attribute__((a)) int f', 'f__i', '1f')
    check('member', '__attribute__((a, b)) int f', 'f__i', '1f')
    # style: user-defined id
    check('member', 'id_attr int f', 'f__i', '1f')
    # style: user-defined paren
    check('member', 'paren_attr() int f', 'f__i', '1f')
    check('member', 'paren_attr(a) int f', 'f__i', '1f')
    check('member', 'paren_attr("") int f', 'f__i', '1f')
    check('member', 'paren_attr(()[{}][]{}) int f', 'f__i', '1f')
    raises(DefinitionError, parse, 'member', 'paren_attr(() int f')
    raises(DefinitionError, parse, 'member', 'paren_attr([) int f')
    raises(DefinitionError, parse, 'member', 'paren_attr({) int f')
    raises(DefinitionError, parse, 'member', 'paren_attr([)]) int f')
    raises(DefinitionError, parse, 'member', 'paren_attr((])) int f')
    raises(DefinitionError, parse, 'member', 'paren_attr({]}) int f')

    # position: decl specs
    check('function', 'static inline __attribute__(()) void f()',
          'f', '1fv',
          output='__attribute__(()) static inline void f()')



# def test_print():
#     # used for getting all the ids out for checking
#     for a in ids:
#         print(a)
#     raise DefinitionError("")


@with_app(testroot='domain-cpp', confoverrides={'add_function_parentheses': True})
def test_build_domain_cpp_with_add_function_parentheses_is_True(app, status, warning):
    app.builder.build_all()

    def check(spec, text, file):
        pattern = '<li>%s<a .*?><code .*?><span .*?>%s</span></code></a></li>' % spec
        res = re.search(pattern, text)
        if not res:
            print("Pattern\n\t%s\nnot found in %s" % (pattern, file))
            assert False
    rolePatterns = [
        ('', 'Sphinx'),
        ('', 'Sphinx::version'),
        ('', 'version'),
        ('', 'List'),
        ('', 'MyEnum')
    ]
    parenPatterns = [
        ('ref function without parens ', 'paren_1\(\)'),
        ('ref function with parens ', 'paren_2\(\)'),
        ('ref function without parens, explicit title ', 'paren_3_title'),
        ('ref function with parens, explicit title ', 'paren_4_title')
    ]

    f = 'roles.html'
    t = (app.outdir / f).text()
    for s in rolePatterns:
        check(s, t, f)
    for s in parenPatterns:
        check(s, t, f)

    f = 'any-role.html'
    t = (app.outdir / f).text()
    for s in parenPatterns:
        check(s, t, f)


@with_app(testroot='domain-cpp', confoverrides={'add_function_parentheses': False})
def test_build_domain_cpp_with_add_function_parentheses_is_False(app, status, warning):
    app.builder.build_all()

    def check(spec, text, file):
        pattern = '<li>%s<a .*?><code .*?><span .*?>%s</span></code></a></li>' % spec
        res = re.search(pattern, text)
        if not res:
            print("Pattern\n\t%s\nnot found in %s" % (pattern, file))
            assert False
    rolePatterns = [
        ('', 'Sphinx'),
        ('', 'Sphinx::version'),
        ('', 'version'),
        ('', 'List'),
        ('', 'MyEnum')
    ]
    parenPatterns = [
        ('ref function without parens ', 'paren_1'),
        ('ref function with parens ', 'paren_2'),
        ('ref function without parens, explicit title ', 'paren_3_title'),
        ('ref function with parens, explicit title ', 'paren_4_title')
    ]

    f = 'roles.html'
    t = (app.outdir / f).text()
    for s in rolePatterns:
        check(s, t, f)
    for s in parenPatterns:
        check(s, t, f)

    f = 'any-role.html'
    t = (app.outdir / f).text()
    for s in parenPatterns:
        check(s, t, f)
