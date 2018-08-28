# -*- coding: utf-8 -*-
"""
    test_domain_cpp
    ~~~~~~~~~~~~~~~

    Tests the C++ Domain

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys

import pytest
from six import text_type

import sphinx.domains.cpp as cppDomain
from sphinx import addnodes
from sphinx.domains.cpp import DefinitionParser, DefinitionError, NoOldIdError
from sphinx.domains.cpp import Symbol, _max_id, _id_prefix


def parse(name, string):
    class Config(object):
        cpp_id_attributes = ["id_attr"]
        cpp_paren_attributes = ["paren_attr"]
    parser = DefinitionParser(string, None, Config())
    parser.allowFallbackExpressionParsing = False
    ast = parser.parse_declaration(name)
    parser.assert_end()
    # The scopedness would usually have been set by CPPEnumObject
    if name == "enum":
        ast.scoped = None  # simulate unscoped enum
    return ast


def check(name, input, idDict, output=None):
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
    ast.describe_signature(signode, 'lastIsName', symbol, options={})

    idExpected = [None]
    for i in range(1, _max_id + 1):
        if i in idDict:
            idExpected.append(idDict[i])
        else:
            idExpected.append(idExpected[i - 1])
    idActual = [None]
    for i in range(1, _max_id + 1):
        try:
            id = ast.get_id(version=i)
            assert id is not None
            idActual.append(id[len(_id_prefix[i]):])
        except NoOldIdError:
            idActual.append(None)

    res = [True]
    for i in range(1, _max_id + 1):
        res.append(idExpected[i] == idActual[i])

    if not all(res):
        print("input:    %s" % text_type(input).rjust(20))
        for i in range(1, _max_id + 1):
            if res[i]:
                continue
            print("Error in id version %d." % i)
            print("result:   %s" % str(idActual[i]))
            print("expected: %s" % str(idExpected[i]))
        print(rootSymbol.dump(0))
        raise DefinitionError("")


def test_fundamental_types():
    # see http://en.cppreference.com/w/cpp/language/types
    for t, id_v2 in cppDomain._id_fundamental_v2.items():
        def makeIdV1():
            if t == 'decltype(auto)':
                return None
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
        check("function", "void f(%s arg)" % t, {1: makeIdV1(), 2: makeIdV2()})


def test_expressions():
    def exprCheck(expr, id):
        ids = 'IE1CIA%s_1aE'
        check('class', 'template<> C<a[%s]>' % expr, {2: ids % expr, 3: ids % id})
    # primary
    exprCheck('nullptr', 'LDnE')
    exprCheck('true', 'L1E')
    exprCheck('false', 'L0E')
    ints = ['5', '0', '075', '0xF', '0XF', '0b1', '0B1']
    unsignedSuffix = ['', 'u', 'U']
    longSuffix = ['', 'l', 'L', 'll', 'LL']
    for i in ints:
        for u in unsignedSuffix:
            for l in longSuffix:
                expr = i + u + l
                exprCheck(expr, 'L' + expr + 'E')
                expr = i + l + u
                exprCheck(expr, 'L' + expr + 'E')
    for suffix in ['', 'f', 'F', 'l', 'L']:
        expr = '5.0' + suffix
        exprCheck(expr, 'L' + expr + 'E')
    exprCheck('"abc\\"cba"', 'LA8_KcE')  # string
    exprCheck('this', 'fpT')
    # character literals
    for p, t in [('', 'c'), ('u8', 'c'), ('u', 'Ds'), ('U', 'Di'), ('L', 'w')]:
        exprCheck(p + "'a'", t + "97")
        exprCheck(p + "'\\n'", t + "10")
        exprCheck(p + "'\\012'", t + "10")
        exprCheck(p + "'\\0'", t + "0")
        exprCheck(p + "'\\x0a'", t + "10")
        exprCheck(p + "'\\x0A'", t + "10")
        exprCheck(p + "'\\u0a42'", t + "2626")
        exprCheck(p + "'\\u0A42'", t + "2626")
        if sys.maxunicode > 65535:
            exprCheck(p + "'\\U0001f34c'", t + "127820")
            exprCheck(p + "'\\U0001F34C'", t + "127820")

    # TODO: user-defined lit
    exprCheck('(... + Ns)', '(... + Ns)')
    exprCheck('(5)', 'L5E')
    exprCheck('C', '1C')
    # postfix
    exprCheck('A(2)', 'cl1AL2EE')
    exprCheck('A[2]', 'ix1AL2E')
    exprCheck('a.b.c', 'dtdt1a1b1c')
    exprCheck('a->b->c', 'ptpt1a1b1c')
    exprCheck('i++', 'pp1i')
    exprCheck('i--', 'mm1i')
    exprCheck('dynamic_cast<T&>(i)++', 'ppdcR1T1i')
    exprCheck('static_cast<T&>(i)++', 'ppscR1T1i')
    exprCheck('reinterpret_cast<T&>(i)++', 'pprcR1T1i')
    exprCheck('const_cast<T&>(i)++', 'ppccR1T1i')
    exprCheck('typeid(T).name', 'dtti1T4name')
    exprCheck('typeid(a + b).name', 'dttepl1a1b4name')
    # unary
    exprCheck('++5', 'pp_L5E')
    exprCheck('--5', 'mm_L5E')
    exprCheck('*5', 'deL5E')
    exprCheck('&5', 'adL5E')
    exprCheck('+5', 'psL5E')
    exprCheck('-5', 'ngL5E')
    exprCheck('!5', 'ntL5E')
    exprCheck('~5', 'coL5E')
    exprCheck('sizeof...(a)', 'sZ1a')
    exprCheck('sizeof(T)', 'st1T')
    exprCheck('sizeof -42', 'szngL42E')
    exprCheck('alignof(T)', 'at1T')
    exprCheck('noexcept(-42)', 'nxngL42E')
    # new-expression
    exprCheck('new int', 'nw_iE')
    exprCheck('new volatile int', 'nw_ViE')
    exprCheck('new int[42]', 'nw_AL42E_iE')
    exprCheck('new int()', 'nw_ipiE')
    exprCheck('new int(5, 42)', 'nw_ipiL5EL42EE')
    # delete-expression
    exprCheck('delete p', 'dl1p')
    exprCheck('delete [] p', 'da1p')
    exprCheck('::delete p', 'dl1p')
    exprCheck('::delete [] p', 'da1p')
    # cast
    exprCheck('(int)2', 'cviL2E')
    # binary op
    exprCheck('5 || 42', 'ooL5EL42E')
    exprCheck('5 && 42', 'aaL5EL42E')
    exprCheck('5 | 42', 'orL5EL42E')
    exprCheck('5 ^ 42', 'eoL5EL42E')
    exprCheck('5 & 42', 'anL5EL42E')
    # ['==', '!=']
    exprCheck('5 == 42', 'eqL5EL42E')
    exprCheck('5 != 42', 'neL5EL42E')
    # ['<=', '>=', '<', '>']
    exprCheck('5 <= 42', 'leL5EL42E')
    exprCheck('5 >= 42', 'geL5EL42E')
    exprCheck('5 < 42', 'ltL5EL42E')
    exprCheck('5 > 42', 'gtL5EL42E')
    # ['<<', '>>']
    exprCheck('5 << 42', 'lsL5EL42E')
    exprCheck('5 >> 42', 'rsL5EL42E')
    # ['+', '-']
    exprCheck('5 + 42', 'plL5EL42E')
    exprCheck('5 - 42', 'miL5EL42E')
    # ['*', '/', '%']
    exprCheck('5 * 42', 'mlL5EL42E')
    exprCheck('5 / 42', 'dvL5EL42E')
    exprCheck('5 % 42', 'rmL5EL42E')
    # ['.*', '->*']
    exprCheck('5 .* 42', 'dsL5EL42E')
    exprCheck('5 ->* 42', 'pmL5EL42E')
    # conditional
    # TODO
    # assignment
    exprCheck('a = 5', 'aS1aL5E')
    exprCheck('a *= 5', 'mL1aL5E')
    exprCheck('a /= 5', 'dV1aL5E')
    exprCheck('a %= 5', 'rM1aL5E')
    exprCheck('a += 5', 'pL1aL5E')
    exprCheck('a -= 5', 'mI1aL5E')
    exprCheck('a >>= 5', 'rS1aL5E')
    exprCheck('a <<= 5', 'lS1aL5E')
    exprCheck('a &= 5', 'aN1aL5E')
    exprCheck('a ^= 5', 'eO1aL5E')
    exprCheck('a |= 5', 'oR1aL5E')

    # Additional tests
    # a < expression that starts with something that could be a template
    exprCheck('A < 42', 'lt1AL42E')
    check('function', 'template<> void f(A<B, 2> &v)',
          {2: "IE1fR1AI1BX2EE", 3: "IE1fR1AI1BXL2EEE"})
    exprCheck('A<1>::value', 'N1AIXL1EEE5valueE')
    check('class', "template<int T = 42> A", {2: "I_iE1A"})
    check('enumerator', 'A = std::numeric_limits<unsigned long>::max()', {2: "1A"})

    exprCheck('operator()()', 'clclE')
    exprCheck('operator()<int>()', 'clclIiEE')

    # pack expansion
    exprCheck('a(b(c, 1 + d...)..., e(f..., g))', 'cl1aspcl1b1cspplL1E1dEcl1esp1f1gEE')


def test_type_definitions():
    check("type", "public bool b", {1: "b", 2: "1b"}, "bool b")
    check("type", "bool A::b", {1: "A::b", 2: "N1A1bE"})
    check("type", "bool *b", {1: "b", 2: "1b"})
    check("type", "bool *const b", {1: "b", 2: "1b"})
    check("type", "bool *volatile const b", {1: "b", 2: "1b"})
    check("type", "bool *volatile const b", {1: "b", 2: "1b"})
    check("type", "bool *volatile const *b", {1: "b", 2: "1b"})
    check("type", "bool &b", {1: "b", 2: "1b"})
    check("type", "bool b[]", {1: "b", 2: "1b"})
    check("type", "std::pair<int, int> coord", {1: "coord", 2: "5coord"})
    check("type", "long long int foo", {1: "foo", 2: "3foo"})
    check("type", 'std::vector<std::pair<std::string, long long>> module::blah',
          {1: "module::blah", 2: "N6module4blahE"})
    check("type", "std::function<void()> F", {1: "F", 2: "1F"})
    check("type", "std::function<R(A1, A2)> F", {1: "F", 2: "1F"})
    check("type", "std::function<R(A1, A2, A3)> F", {1: "F", 2: "1F"})
    check("type", "std::function<R(A1, A2, A3, As...)> F", {1: "F", 2: "1F"})
    check("type", "MyContainer::const_iterator",
          {1: "MyContainer::const_iterator", 2: "N11MyContainer14const_iteratorE"})
    check("type",
          "public MyContainer::const_iterator",
          {1: "MyContainer::const_iterator", 2: "N11MyContainer14const_iteratorE"},
          output="MyContainer::const_iterator")
    # test decl specs on right
    check("type", "bool const b", {1: "b", 2: "1b"})
    # test name in global scope
    check("type", "bool ::B::b", {1: "B::b", 2: "N1B1bE"})

    check('type', 'A = B', {2: '1A'})
    check('type', 'A = decltype(b)', {2: '1A'})

    # from breathe#267 (named function parameters for function pointers
    check('type', 'void (*gpio_callback_t)(struct device *port, uint32_t pin)',
          {1: 'gpio_callback_t', 2: '15gpio_callback_t'})
    check('type', 'void (*f)(std::function<void(int i)> g)', {1: 'f', 2: '1f'})

    check('type', 'T = A::template B<int>::template C<double>', {2: '1T'})

    check('type', 'T = Q<A::operator()>', {2: '1T'})
    check('type', 'T = Q<A::operator()<int>>', {2: '1T'})
    check('type', 'T = Q<A::operator bool>', {2: '1T'})


def test_concept_definitions():
    check('concept', 'template<typename Param> A::B::Concept',
          {2: 'I0EN1A1B7ConceptE'})
    check('concept', 'template<typename A, typename B, typename ...C> Foo',
          {2: 'I00DpE3Foo'})
    with pytest.raises(DefinitionError):
        parse('concept', 'Foo')
    with pytest.raises(DefinitionError):
        parse('concept', 'template<typename T> template<typename U> Foo')


def test_member_definitions():
    check('member', '  const  std::string  &  name = 42',
          {1: "name__ssCR", 2: "4name"}, output='const std::string &name = 42')
    check('member', '  const  std::string  &  name', {1: "name__ssCR", 2: "4name"},
          output='const std::string &name')
    check('member', '  const  std::string  &  name [ n ]',
          {1: "name__ssCRA", 2: "4name"}, output='const std::string &name[n]')
    check('member', 'const std::vector< unsigned int, long> &name',
          {1: "name__std::vector:unsigned-i.l:CR", 2: "4name"},
          output='const std::vector<unsigned int, long> &name')
    check('member', 'module::myclass foo[n]', {1: "foo__module::myclassA", 2: "3foo"})
    check('member', 'int *const p', {1: 'p__iPC', 2: '1p'})
    check('member', 'extern int myInt', {1: 'myInt__i', 2: '5myInt'})
    check('member', 'thread_local int myInt', {1: 'myInt__i', 2: '5myInt'})
    check('member', 'extern thread_local int myInt', {1: 'myInt__i', 2: '5myInt'})
    check('member', 'thread_local extern int myInt', {1: 'myInt__i', 2: '5myInt'},
          'extern thread_local int myInt')


def test_function_definitions():
    check('function', 'operator bool() const', {1: "castto-b-operatorC", 2: "NKcvbEv"})
    check('function', 'A::operator bool() const',
          {1: "A::castto-b-operatorC", 2: "NK1AcvbEv"})
    check('function', 'A::operator bool() volatile const &',
          {1: "A::castto-b-operatorVCR", 2: "NVKR1AcvbEv"})
    check('function', 'A::operator bool() volatile const &&',
          {1: "A::castto-b-operatorVCO", 2: "NVKO1AcvbEv"})
    check('function', 'bool namespaced::theclass::method(arg1, arg2)',
          {1: "namespaced::theclass::method__arg1.arg2",
           2: "N10namespaced8theclass6methodE4arg14arg2"})
    x = 'std::vector<std::pair<std::string, int>> &module::test(register int ' \
        'foo, bar, std::string baz = "foobar, blah, bleh") const = 0'
    check('function', x, {1: "module::test__i.bar.ssC",
          2: "NK6module4testEi3barNSt6stringE"})
    check('function', 'void f(std::pair<A, B>)',
          {1: "f__std::pair:A.B:", 2: "1fNSt4pairI1A1BEE"})
    check('function', 'explicit module::myclass::foo::foo()',
          {1: "module::myclass::foo::foo", 2: "N6module7myclass3foo3fooEv"})
    check('function', 'module::myclass::foo::~foo()',
          {1: "module::myclass::foo::~foo", 2: "N6module7myclass3fooD0Ev"})
    check('function', 'int printf(const char *fmt, ...)',
          {1: "printf__cCP.z", 2: "6printfPKcz"})
    check('function', 'int foo(const unsigned int j)',
          {1: "foo__unsigned-iC", 2: "3fooKj"})
    check('function', 'int foo(const int *const ptr)',
          {1: "foo__iCPC", 2: "3fooPCKi"})
    check('function', 'module::myclass::operator std::vector<std::string>()',
          {1: "module::myclass::castto-std::vector:ss:-operator",
           2: "N6module7myclasscvNSt6vectorINSt6stringEEEEv"})
    check('function',
          'void operator()(const boost::array<VertexID, 2> &v) const',
          {1: "call-operator__boost::array:VertexID.2:CRC",
           2: "NKclERKN5boost5arrayI8VertexIDX2EEE",
           3: "NKclERKN5boost5arrayI8VertexIDXL2EEEE"})
    check('function',
          'void operator()(const boost::array<VertexID, 2, "foo,  bar"> &v) const',
          {1: 'call-operator__boost::array:VertexID.2."foo,--bar":CRC',
           2: 'NKclERKN5boost5arrayI8VertexIDX2EX"foo,  bar"EEE',
           3: 'NKclERKN5boost5arrayI8VertexIDXL2EEXLA9_KcEEEE'})
    check('function', 'MyClass::MyClass(MyClass::MyClass&&)',
          {1: "MyClass::MyClass__MyClass::MyClassRR",
           2: "N7MyClass7MyClassERRN7MyClass7MyClassE"})
    check('function', 'constexpr int get_value()', {1: "get_valueCE", 2: "9get_valuev"})
    check('function', 'static constexpr int get_value()',
          {1: "get_valueCE", 2: "9get_valuev"})
    check('function', 'int get_value() const noexcept',
          {1: "get_valueC", 2: "NK9get_valueEv"})
    check('function', 'int get_value() const noexcept = delete',
          {1: "get_valueC", 2: "NK9get_valueEv"})
    check('function', 'int get_value() volatile const',
          {1: "get_valueVC", 2: "NVK9get_valueEv"})
    check('function', 'MyClass::MyClass(MyClass::MyClass&&) = default',
          {1: "MyClass::MyClass__MyClass::MyClassRR",
           2: "N7MyClass7MyClassERRN7MyClass7MyClassE"})
    check('function', 'virtual MyClass::a_virtual_function() const override',
          {1: "MyClass::a_virtual_functionC", 2: "NK7MyClass18a_virtual_functionEv"})
    check('function', 'A B() override', {1: "B", 2: "1Bv"})
    check('function', 'A B() final', {1: "B", 2: "1Bv"})
    check('function', 'A B() final override', {1: "B", 2: "1Bv"})
    check('function', 'A B() override final', {1: "B", 2: "1Bv"},
          output='A B() final override')
    check('function', 'MyClass::a_member_function() volatile',
          {1: "MyClass::a_member_functionV", 2: "NV7MyClass17a_member_functionEv"})
    check('function', 'MyClass::a_member_function() volatile const',
          {1: "MyClass::a_member_functionVC", 2: "NVK7MyClass17a_member_functionEv"})
    check('function', 'MyClass::a_member_function() &&',
          {1: "MyClass::a_member_functionO", 2: "NO7MyClass17a_member_functionEv"})
    check('function', 'MyClass::a_member_function() &',
          {1: "MyClass::a_member_functionR", 2: "NR7MyClass17a_member_functionEv"})
    check('function', 'MyClass::a_member_function() const &',
          {1: "MyClass::a_member_functionCR", 2: "NKR7MyClass17a_member_functionEv"})
    check('function', 'int main(int argc, char *argv[])',
          {1: "main__i.cPA", 2: "4mainiA_Pc"})
    check('function', 'MyClass &MyClass::operator++()',
          {1: "MyClass::inc-operator", 2: "N7MyClassppEv"})
    check('function', 'MyClass::pointer MyClass::operator->()',
          {1: "MyClass::pointer-operator", 2: "N7MyClassptEv"})

    x = 'std::vector<std::pair<std::string, int>> &module::test(register int ' \
        'foo, bar[n], std::string baz = "foobar, blah, bleh") const = 0'
    check('function', x, {1: "module::test__i.barA.ssC",
                          2: "NK6module4testEiAn_3barNSt6stringE",
                          3: "NK6module4testEiA1n_3barNSt6stringE"})
    check('function',
          'int foo(Foo f = Foo(double(), std::make_pair(int(2), double(3.4))))',
          {1: "foo__Foo", 2: "3foo3Foo"})
    check('function', 'int foo(A a = x(a))', {1: "foo__A", 2: "3foo1A"})
    with pytest.raises(DefinitionError):
        parse('function', 'int foo(B b=x(a)')
    with pytest.raises(DefinitionError):
        parse('function', 'int foo)C c=x(a))')
    with pytest.raises(DefinitionError):
        parse('function', 'int foo(D d=x(a')
    check('function', 'int foo(const A&... a)', {1: "foo__ACRDp", 2: "3fooDpRK1A"})
    check('function', 'virtual void f()', {1: "f", 2: "1fv"})
    # test for ::nestedName, from issue 1738
    check("function", "result(int val, ::std::error_category const &cat)",
          {1: "result__i.std::error_categoryCR", 2: "6resultiRNSt14error_categoryE"})
    check("function", "int *f()", {1: "f", 2: "1fv"})
    # tests derived from issue #1753 (skip to keep sanity)
    check("function", "f(int (&array)[10])", {2: "1fRA10_i", 3: "1fRAL10E_i"})
    check("function", "void f(int (&array)[10])", {2: "1fRA10_i", 3: "1fRAL10E_i"})
    check("function", "void f(float *q(double))", {2: "1fFPfdE"})
    check("function", "void f(float *(*q)(double))", {2: "1fPFPfdE"})
    check("function", "void f(float (*q)(double))", {2: "1fPFfdE"})
    check("function", "int (*f(double d))(float)", {1: "f__double", 2: "1fd"})
    check("function", "int (*f(bool b))[5]", {1: "f__b", 2: "1fb"})
    check("function", "int (*A::f(double d) const)(float)",
          {1: "A::f__doubleC", 2: "NK1A1fEd"})
    check("function", "void f(std::shared_ptr<int(double)> ptr)",
          {2: "1fNSt10shared_ptrIFidEEE"})
    check("function", "void f(int *const p)", {1: "f__iPC", 2: "1fPCi"})
    check("function", "void f(int *volatile const p)", {1: "f__iPVC", 2: "1fPVCi"})

    check('function', 'extern int f()', {1: 'f', 2: '1fv'})

    check('function', 'decltype(auto) f()', {1: 'f', 2: "1fv"})

    # TODO: make tests for functions in a template, e.g., Test<int&&()>
    # such that the id generation for function type types is correct.

    check('function', 'friend std::ostream &f(std::ostream &s, int i)',
          {1: 'f__osR.i', 2: '1fRNSt7ostreamEi'})

    # from breathe#223
    check('function', 'void f(struct E e)', {1: 'f__E', 2: '1f1E'})
    check('function', 'void f(class E e)', {1: 'f__E', 2: '1f1E'})
    check('function', 'void f(typename E e)', {1: 'f__E', 2: '1f1E'})
    check('function', 'void f(enum E e)', {1: 'f__E', 2: '1f1E'})
    check('function', 'void f(union E e)', {1: 'f__E', 2: '1f1E'})

    # pointer to member (function)
    check('function', 'void f(int C::*)', {2: '1fM1Ci'})
    check('function', 'void f(int C::* p)', {2: '1fM1Ci'})
    check('function', 'void f(int ::C::* p)', {2: '1fM1Ci'})
    check('function', 'void f(int C::* const)', {2: '1fKM1Ci'})
    check('function', 'void f(int C::* const&)', {2: '1fRKM1Ci'})
    check('function', 'void f(int C::* volatile)', {2: '1fVM1Ci'})
    check('function', 'void f(int C::* const volatile)', {2: '1fVKM1Ci'},
          output='void f(int C::* volatile const)')
    check('function', 'void f(int C::* volatile const)', {2: '1fVKM1Ci'})
    check('function', 'void f(int (C::*)(float, double))', {2: '1fM1CFifdE'})
    check('function', 'void f(int (C::* p)(float, double))', {2: '1fM1CFifdE'})
    check('function', 'void f(int (::C::* p)(float, double))', {2: '1fM1CFifdE'})
    check('function', 'void f(void (C::*)() const &)', {2: '1fM1CKRFvvE'})
    check('function', 'int C::* f(int, double)', {2: '1fid'})
    check('function', 'void f(int C::* *)', {2: '1fPM1Ci'})


def test_operators():
    check('function', 'void operator new [  ] ()',
          {1: "new-array-operator", 2: "nav"}, output='void operator new[]()')
    check('function', 'void operator delete ()',
          {1: "delete-operator", 2: "dlv"}, output='void operator delete()')
    check('function', 'operator bool() const',
          {1: "castto-b-operatorC", 2: "NKcvbEv"}, output='operator bool() const')

    check('function', 'void operator * ()',
          {1: "mul-operator", 2: "mlv"}, output='void operator*()')
    check('function', 'void operator - ()',
          {1: "sub-operator", 2: "miv"}, output='void operator-()')
    check('function', 'void operator + ()',
          {1: "add-operator", 2: "plv"}, output='void operator+()')
    check('function', 'void operator = ()',
          {1: "assign-operator", 2: "aSv"}, output='void operator=()')
    check('function', 'void operator / ()',
          {1: "div-operator", 2: "dvv"}, output='void operator/()')
    check('function', 'void operator % ()',
          {1: "mod-operator", 2: "rmv"}, output='void operator%()')
    check('function', 'void operator ! ()',
          {1: "not-operator", 2: "ntv"}, output='void operator!()')

    check('function', 'void operator "" _udl()',
          {2: 'li4_udlv'}, output='void operator""_udl()')


def test_class_definitions():
    check('class', 'public A', {1: "A", 2: "1A"}, output='A')
    check('class', 'private A', {1: "A", 2: "1A"})
    check('class', 'A final', {1: 'A', 2: '1A'})

    # test bases
    check('class', 'A', {1: "A", 2: "1A"})
    check('class', 'A::B::C', {1: "A::B::C", 2: "N1A1B1CE"})
    check('class', 'A : B', {1: "A", 2: "1A"})
    check('class', 'A : private B', {1: "A", 2: "1A"}, output='A : B')
    check('class', 'A : public B', {1: "A", 2: "1A"})
    check('class', 'A : B, C', {1: "A", 2: "1A"})
    check('class', 'A : B, protected C, D', {1: "A", 2: "1A"})
    check('class', 'A : virtual private B', {1: 'A', 2: '1A'}, output='A : virtual B')
    check('class', 'A : B, virtual C', {1: 'A', 2: '1A'})
    check('class', 'A : public virtual B', {1: 'A', 2: '1A'})
    check('class', 'A : B, C...', {1: 'A', 2: '1A'})
    check('class', 'A : B..., C', {1: 'A', 2: '1A'})

    # from #4094
    check('class', 'template<class, class = std::void_t<>> has_var', {2: 'I00E7has_var'})
    check('class', 'template<class T> has_var<T, std::void_t<decltype(&T::var)>>',
          {2: 'I0E7has_varI1TNSt6void_tIDTadN1T3varEEEEE'})


def test_union_definitions():
    check('union', 'A', {2: "1A"})


def test_enum_definitions():
    check('enum', 'A', {2: "1A"})
    check('enum', 'A : std::underlying_type<B>::type', {2: "1A"})
    check('enum', 'A : unsigned int', {2: "1A"})
    check('enum', 'public A', {2: "1A"}, output='A')
    check('enum', 'private A', {2: "1A"})

    check('enumerator', 'A', {2: "1A"})
    check('enumerator', 'A = std::numeric_limits<unsigned long>::max()', {2: "1A"})


def test_anon_definitions():
    check('class', '@a', {3: "Ut1_a"})
    check('union', '@a', {3: "Ut1_a"})
    check('enum', '@a', {3: "Ut1_a"})
    check('class', '@1', {3: "Ut1_1"})


def test_templates():
    check('class', "A<T>", {2: "IE1AI1TE"}, output="template<> A<T>")
    # first just check which objects support templating
    check('class', "template<> A", {2: "IE1A"})
    check('function', "template<> void A()", {2: "IE1Av"})
    check('member', "template<> A a", {2: "IE1a"})
    check('type', "template<> a = A", {2: "IE1a"})
    with pytest.raises(DefinitionError):
        parse('enum', "template<> A")
    with pytest.raises(DefinitionError):
        parse('enumerator', "template<> A")
    # then all the real tests
    check('class', "template<typename T1, typename T2> A", {2: "I00E1A"})
    check('type', "template<> a", {2: "IE1a"})

    check('class', "template<typename T> A", {2: "I0E1A"})
    check('class', "template<class T> A", {2: "I0E1A"})
    check('class', "template<typename ...T> A", {2: "IDpE1A"})
    check('class', "template<typename...> A", {2: "IDpE1A"})
    check('class', "template<typename = Test> A", {2: "I0E1A"})
    check('class', "template<typename T = Test> A", {2: "I0E1A"})

    check('class', "template<template<typename> typename T> A", {2: "II0E0E1A"})
    check('class', "template<template<typename> typename> A", {2: "II0E0E1A"})
    check('class', "template<template<typename> typename ...T> A", {2: "II0EDpE1A"})
    check('class', "template<template<typename> typename...> A", {2: "II0EDpE1A"})

    check('class', "template<int> A", {2: "I_iE1A"})
    check('class', "template<int T> A", {2: "I_iE1A"})
    check('class', "template<int... T> A", {2: "I_DpiE1A"})
    check('class', "template<int T = 42> A", {2: "I_iE1A"})
    check('class', "template<int = 42> A", {2: "I_iE1A"})

    check('class', "template<> A<NS::B<>>", {2: "IE1AIN2NS1BIEEE"})

    # from #2058
    check('function',
          "template<typename Char, typename Traits> "
          "inline std::basic_ostream<Char, Traits> &operator<<("
          "std::basic_ostream<Char, Traits> &os, "
          "const c_string_view_base<const Char, Traits> &str)",
          {2: "I00ElsRNSt13basic_ostreamI4Char6TraitsEE"
              "RK18c_string_view_baseIK4Char6TraitsE"})

    # template introductions
    with pytest.raises(DefinitionError):
        parse('enum', 'abc::ns::foo{id_0, id_1, id_2} A')
    with pytest.raises(DefinitionError):
        parse('enumerator', 'abc::ns::foo{id_0, id_1, id_2} A')
    check('class', 'abc::ns::foo{id_0, id_1, id_2} xyz::bar',
          {2: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barE'})
    check('class', 'abc::ns::foo{id_0, id_1, ...id_2} xyz::bar',
          {2: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barE'})
    check('class', 'abc::ns::foo{id_0, id_1, id_2} xyz::bar<id_0, id_1, id_2>',
          {2: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barI4id_04id_14id_2EE'})
    check('class', 'abc::ns::foo{id_0, id_1, ...id_2} xyz::bar<id_0, id_1, id_2...>',
          {2: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barI4id_04id_1Dp4id_2EE'})

    check('class', 'template<> Concept{U} A<int>::B', {2: 'IEI0EX7ConceptI1UEEN1AIiE1BE'})

    check('type', 'abc::ns::foo{id_0, id_1, id_2} xyz::bar = ghi::qux',
          {2: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barE'})
    check('type', 'abc::ns::foo{id_0, id_1, ...id_2} xyz::bar = ghi::qux',
          {2: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barE'})
    check('function', 'abc::ns::foo{id_0, id_1, id_2} void xyz::bar()',
          {2: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barEv'})
    check('function', 'abc::ns::foo{id_0, id_1, ...id_2} void xyz::bar()',
          {2: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barEv'})
    check('member', 'abc::ns::foo{id_0, id_1, id_2} ghi::qux xyz::bar',
          {2: 'I000EXN3abc2ns3fooEI4id_04id_14id_2EEN3xyz3barE'})
    check('member', 'abc::ns::foo{id_0, id_1, ...id_2} ghi::qux xyz::bar',
          {2: 'I00DpEXN3abc2ns3fooEI4id_04id_1sp4id_2EEN3xyz3barE'})
    check('concept', 'Iterator{T, U} Another', {2: 'I00EX8IteratorI1T1UEE7Another'})
    check('concept', 'template<typename ...Pack> Numerics = (... && Numeric<Pack>)',
          {2: 'IDpE8Numerics'})

    # explicit specializations of members
    check('member', 'template<> int A<int>::a', {2: 'IEN1AIiE1aE'})
    check('member', 'template int A<int>::a', {2: 'IEN1AIiE1aE'},
          output='template<> int A<int>::a')  # same as above
    check('member', 'template<> template<> int A<int>::B<int>::b', {2: 'IEIEN1AIiE1BIiE1bE'})
    check('member', 'template int A<int>::B<int>::b', {2: 'IEIEN1AIiE1BIiE1bE'},
          output='template<> template<> int A<int>::B<int>::b')  # same as above

    # defaulted constrained type parameters
    check('type', 'template<C T = int&> A', {2: 'I_1CE1A'})


def test_template_args():
    # from breathe#218
    check('function',
          "template<typename F> "
          "void allow(F *f, typename func<F, B, G != 1>::type tt)",
          {2: "I0E5allowP1FN4funcI1F1BXG != 1EE4typeE",
           3: "I0E5allowP1FN4funcI1F1BXne1GL1EEE4typeE"})
    # from #3542
    check('type', "template<typename T> "
          "enable_if_not_array_t = std::enable_if_t<!is_array<T>::value, int>",
          {2: "I0E21enable_if_not_array_t"})


def test_attributes():
    # style: C++
    check('member', '[[]] int f', {1: 'f__i', 2: '1f'})
    check('member', '[ [ ] ] int f', {1: 'f__i', 2: '1f'},
          # this will fail when the proper grammar is implemented
          output='[[ ]] int f')
    check('member', '[[a]] int f', {1: 'f__i', 2: '1f'})
    # style: GNU
    check('member', '__attribute__(()) int f', {1: 'f__i', 2: '1f'})
    check('member', '__attribute__((a)) int f', {1: 'f__i', 2: '1f'})
    check('member', '__attribute__((a, b)) int f', {1: 'f__i', 2: '1f'})
    # style: user-defined id
    check('member', 'id_attr int f', {1: 'f__i', 2: '1f'})
    # style: user-defined paren
    check('member', 'paren_attr() int f', {1: 'f__i', 2: '1f'})
    check('member', 'paren_attr(a) int f', {1: 'f__i', 2: '1f'})
    check('member', 'paren_attr("") int f', {1: 'f__i', 2: '1f'})
    check('member', 'paren_attr(()[{}][]{}) int f', {1: 'f__i', 2: '1f'})
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr(() int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr([) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr({) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr([)]) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr((])) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr({]}) int f')

    # position: decl specs
    check('function', 'static inline __attribute__(()) void f()',
          {1: 'f', 2: '1fv'},
          output='__attribute__(()) static inline void f()')
    # position: declarator
    check('member', 'int *[[attr]] i', {1: 'i__iP', 2:'1i'})
    check('member', 'int *const [[attr]] volatile i', {1: 'i__iPVC', 2: '1i'},
          output='int *[[attr]] volatile const i')
    check('member', 'int &[[attr]] i', {1: 'i__iR', 2: '1i'})
    check('member', 'int *[[attr]] *i', {1: 'i__iPP', 2: '1i'})


# def test_print():
#     # used for getting all the ids out for checking
#     for a in ids:
#         print(a)
#     raise DefinitionError("")


@pytest.mark.sphinx(testroot='domain-cpp')
def test_build_domain_cpp_misuse_of_roles(app, status, warning):
    app.builder.build_all()

    # TODO: properly check for the warnings we expect


@pytest.mark.sphinx(testroot='domain-cpp', confoverrides={'add_function_parentheses': True})
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
        ('ref function without parens ', r'paren_1\(\)'),
        ('ref function with parens ', r'paren_2\(\)'),
        ('ref function without parens, explicit title ', 'paren_3_title'),
        ('ref function with parens, explicit title ', 'paren_4_title'),
        ('ref op call without parens ', r'paren_5::operator\(\)\(\)'),
        ('ref op call with parens ', r'paren_6::operator\(\)\(\)'),
        ('ref op call without parens, explicit title ', 'paren_7_title'),
        ('ref op call with parens, explicit title ', 'paren_8_title')
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


@pytest.mark.sphinx(testroot='domain-cpp', confoverrides={
    'add_function_parentheses': False})
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
        ('ref function with parens, explicit title ', 'paren_4_title'),
        ('ref op call without parens ', r'paren_5::operator\(\)'),
        ('ref op call with parens ', r'paren_6::operator\(\)'),
        ('ref op call without parens, explicit title ', 'paren_7_title'),
        ('ref op call with parens, explicit title ', 'paren_8_title')
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


@pytest.mark.sphinx(testroot='domain-cpp')
def test_xref_consistency(app, status, warning):
    app.builder.build_all()

    test = 'xref_consistency.html'
    output = (app.outdir / test).text()

    def classes(role, tag):
        pattern = (r'{role}-role:.*?'
                   r'<(?P<tag>{tag}) .*?class=["\'](?P<classes>.*?)["\'].*?>'
                   r'.*'
                   r'</(?P=tag)>').format(role=role, tag=tag)
        result = re.search(pattern, output)
        expect = '''\
Pattern for role `{role}` with tag `{tag}`
\t{pattern}
not found in `{test}`
'''.format(role=role, tag=tag, pattern=pattern, test=test)
        assert result, expect
        return set(result.group('classes').split())

    class RoleClasses(object):
        """Collect the classes from the layout that was generated for a given role."""

        def __init__(self, role, root, contents):
            self.name = role
            self.classes = classes(role, root)
            self.content_classes = dict()
            for tag in contents:
                self.content_classes[tag] = classes(role, tag)

    # not actually used as a reference point
    # code_role = RoleClasses('code', 'code', [])
    any_role = RoleClasses('any', 'a', ['code'])
    cpp_any_role = RoleClasses('cpp-any', 'a', ['code'])
    # NYI: consistent looks
    # texpr_role = RoleClasses('cpp-texpr', 'span', ['a', 'code'])
    expr_role = RoleClasses('cpp-expr', 'code', ['a'])
    texpr_role = RoleClasses('cpp-texpr', 'span', ['a', 'span'])

    # XRefRole-style classes

    # any and cpp:any do not put these classes at the root

    # n.b. the generic any machinery finds the specific 'cpp-class' object type
    expect = 'any uses XRefRole classes'
    assert {'xref', 'any', 'cpp', 'cpp-class'} <= any_role.content_classes['code'], expect

    expect = 'cpp:any uses XRefRole classes'
    assert {'xref', 'cpp-any', 'cpp'} <= cpp_any_role.content_classes['code'], expect

    for role in (expr_role, texpr_role):
        name = role.name
        expect = '`{name}` puts the domain and role classes at its root'.format(name=name)
        # NYI: xref should go in the references
        assert {'xref', 'cpp', name} <= role.classes, expect

    # reference classes

    expect = 'the xref roles use the same reference classes'
    assert any_role.classes == cpp_any_role.classes, expect
    assert any_role.classes == expr_role.content_classes['a'], expect
    assert any_role.classes == texpr_role.content_classes['a'], expect
