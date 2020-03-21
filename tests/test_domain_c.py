"""
    test_domain_c
    ~~~~~~~~~~~~~

    Tests the C Domain

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest

from docutils import nodes
import sphinx.domains.c as cDomain
from sphinx import addnodes
from sphinx.addnodes import (
    desc, desc_addname, desc_annotation, desc_content, desc_name, desc_optional,
    desc_parameter, desc_parameterlist, desc_returns, desc_signature, desc_type,
    pending_xref
)
from sphinx.domains.c import DefinitionParser, DefinitionError
from sphinx.domains.c import _max_id, _id_prefix, Symbol
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node
from sphinx.util import docutils


def parse(name, string):
    parser = DefinitionParser(string, location=None)
    parser.allowFallbackExpressionParsing = False
    ast = parser.parse_declaration(name, name)
    parser.assert_end()
    return ast


def check(name, input, idDict, output=None):
    # first a simple check of the AST
    if output is None:
        output = input
    ast = parse(name, input)
    res = str(ast)
    if res != output:
        print("")
        print("Input:    ", input)
        print("Result:   ", res)
        print("Expected: ", output)
        raise DefinitionError("")
    rootSymbol = Symbol(None, None, None, None)
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
        #try:
        id = ast.get_id(version=i)
        assert id is not None
        idActual.append(id[len(_id_prefix[i]):])
        #except NoOldIdError:
        #    idActual.append(None)

    res = [True]
    for i in range(1, _max_id + 1):
        res.append(idExpected[i] == idActual[i])

    if not all(res):
        print("input:    %s" % input.rjust(20))
        for i in range(1, _max_id + 1):
            if res[i]:
                continue
            print("Error in id version %d." % i)
            print("result:   %s" % idActual[i])
            print("expected: %s" % idExpected[i])
        #print(rootSymbol.dump(0))
        raise DefinitionError("")


def test_expressions():
    def exprCheck(expr, output=None):
        parser = DefinitionParser(expr, location=None)
        parser.allowFallbackExpressionParsing = False
        ast = parser.parse_expression()
        parser.assert_end()
        # first a simple check of the AST
        if output is None:
            output = expr
        res = str(ast)
        if res != output:
            print("")
            print("Input:    ", input)
            print("Result:   ", res)
            print("Expected: ", output)
            raise DefinitionError("")
    # type expressions
    exprCheck('int*')
    exprCheck('int *const*')
    exprCheck('int *volatile*')
    exprCheck('int *restrict*')
    exprCheck('int *(*)(double)')
    exprCheck('const int*')
    exprCheck('__int64')
    exprCheck('unsigned __int64')

    # actual expressions

    # primary
    exprCheck('true')
    exprCheck('false')
    ints = ['5', '0', '075', '0x0123456789ABCDEF', '0XF', '0b1', '0B1']
    unsignedSuffix = ['', 'u', 'U']
    longSuffix = ['', 'l', 'L', 'll', 'LL']
    for i in ints:
        for u in unsignedSuffix:
            for l in longSuffix:
                expr = i + u + l
                exprCheck(expr)
                expr = i + l + u
                exprCheck(expr)
    for suffix in ['', 'f', 'F', 'l', 'L']:
        for e in [
                '5e42', '5e+42', '5e-42',
                '5.', '5.e42', '5.e+42', '5.e-42',
                '.5', '.5e42', '.5e+42', '.5e-42',
                '5.0', '5.0e42', '5.0e+42', '5.0e-42']:
            expr = e + suffix
            exprCheck(expr)
        for e in [
                'ApF', 'Ap+F', 'Ap-F',
                'A.', 'A.pF', 'A.p+F', 'A.p-F',
                '.A', '.ApF', '.Ap+F', '.Ap-F',
                'A.B', 'A.BpF', 'A.Bp+F', 'A.Bp-F']:
            expr = "0x" + e + suffix
            exprCheck(expr)
    exprCheck('"abc\\"cba"')  # string
    # character literals
    for p in ['', 'u8', 'u', 'U', 'L']:
        exprCheck(p + "'a'")
        exprCheck(p + "'\\n'")
        exprCheck(p + "'\\012'")
        exprCheck(p + "'\\0'")
        exprCheck(p + "'\\x0a'")
        exprCheck(p + "'\\x0A'")
        exprCheck(p + "'\\u0a42'")
        exprCheck(p + "'\\u0A42'")
        exprCheck(p + "'\\U0001f34c'")
        exprCheck(p + "'\\U0001F34C'")

    exprCheck('(5)')
    exprCheck('C')
    # postfix
    exprCheck('A(2)')
    exprCheck('A[2]')
    exprCheck('a.b.c')
    exprCheck('a->b->c')
    exprCheck('i++')
    exprCheck('i--')
    # unary
    exprCheck('++5')
    exprCheck('--5')
    exprCheck('*5')
    exprCheck('&5')
    exprCheck('+5')
    exprCheck('-5')
    exprCheck('!5')
    exprCheck('~5')
    exprCheck('sizeof(T)')
    exprCheck('sizeof -42')
    exprCheck('alignof(T)')
    # cast
    exprCheck('(int)2')
    # binary op
    exprCheck('5 || 42')
    exprCheck('5 && 42')
    exprCheck('5 | 42')
    exprCheck('5 ^ 42')
    exprCheck('5 & 42')
    # ['==', '!=']
    exprCheck('5 == 42')
    exprCheck('5 != 42')
    # ['<=', '>=', '<', '>']
    exprCheck('5 <= 42')
    exprCheck('5 >= 42')
    exprCheck('5 < 42')
    exprCheck('5 > 42')
    # ['<<', '>>']
    exprCheck('5 << 42')
    exprCheck('5 >> 42')
    # ['+', '-']
    exprCheck('5 + 42')
    exprCheck('5 - 42')
    # ['*', '/', '%']
    exprCheck('5 * 42')
    exprCheck('5 / 42')
    exprCheck('5 % 42')
    # ['.*', '->*']
    # conditional
    # TODO
    # assignment
    exprCheck('a = 5')
    exprCheck('a *= 5')
    exprCheck('a /= 5')
    exprCheck('a %= 5')
    exprCheck('a += 5')
    exprCheck('a -= 5')
    exprCheck('a >>= 5')
    exprCheck('a <<= 5')
    exprCheck('a &= 5')
    exprCheck('a ^= 5')
    exprCheck('a |= 5')


def test_type_definitions():
    check('type', "T", {1: "T"})

    check('type', "bool *b", {1: 'b'})
    check('type', "bool *const b", {1: 'b'})
    check('type', "bool *const *b", {1: 'b'})
    check('type', "bool *volatile *b", {1: 'b'})
    check('type', "bool *restrict *b", {1: 'b'})
    check('type', "bool *volatile const b", {1: 'b'})
    check('type', "bool *volatile const b", {1: 'b'})
    check('type', "bool *volatile const *b", {1: 'b'})
    check('type', "bool b[]", {1: 'b'})
    check('type', "long long int foo", {1: 'foo'})
    # test decl specs on right
    check('type', "bool const b", {1: 'b'})

    # from breathe#267 (named function parameters for function pointers
    check('type', 'void (*gpio_callback_t)(struct device *port, uint32_t pin)',
          {1: 'gpio_callback_t'})


def test_macro_definitions():
    check('macro', 'M', {1: 'M'})
    check('macro', 'M()', {1: 'M'})
    check('macro', 'M(arg)', {1: 'M'})
    check('macro', 'M(arg1, arg2)', {1: 'M'})
    check('macro', 'M(arg1, arg2, arg3)', {1: 'M'})
    check('macro', 'M(...)', {1: 'M'})
    check('macro', 'M(arg, ...)', {1: 'M'})
    check('macro', 'M(arg1, arg2, ...)', {1: 'M'})
    check('macro', 'M(arg1, arg2, arg3, ...)', {1: 'M'})


def test_member_definitions():
    check('member', 'void a', {1: 'a'})
    check('member', '_Bool a', {1: 'a'})
    check('member', 'bool a', {1: 'a'})
    check('member', 'char a', {1: 'a'})
    check('member', 'int a', {1: 'a'})
    check('member', 'float a', {1: 'a'})
    check('member', 'double a', {1: 'a'})

    check('member', 'unsigned long a', {1: 'a'})
    check('member', '__int64 a', {1: 'a'})
    check('member', 'unsigned __int64 a', {1: 'a'})

    check('member', 'int .a', {1: 'a'})

    check('member', 'int *a', {1: 'a'})
    check('member', 'int **a', {1: 'a'})
    check('member', 'const int a', {1: 'a'})
    check('member', 'volatile int a', {1: 'a'})
    check('member', 'restrict int a', {1: 'a'})
    check('member', 'volatile const int a', {1: 'a'})
    check('member', 'restrict const int a', {1: 'a'})
    check('member', 'restrict volatile int a', {1: 'a'})
    check('member', 'restrict volatile const int a', {1: 'a'})

    check('member', 'T t', {1: 't'})

    check('member', 'int a[]', {1: 'a'})

    check('member', 'int (*p)[]', {1: 'p'})

    check('member', 'int a[42]', {1: 'a'})
    check('member', 'int a = 42', {1: 'a'})
    check('member', 'T a = {}', {1: 'a'})
    check('member', 'T a = {1}', {1: 'a'})
    check('member', 'T a = {1, 2}', {1: 'a'})
    check('member', 'T a = {1, 2, 3}', {1: 'a'})

    # test from issue #1539
    check('member', 'CK_UTF8CHAR model[16]', {1: 'model'})

    check('member', 'auto int a', {1: 'a'})
    check('member', 'register int a', {1: 'a'})
    check('member', 'extern int a', {1: 'a'})
    check('member', 'static int a', {1: 'a'})

    check('member', 'thread_local int a', {1: 'a'})
    check('member', '_Thread_local int a', {1: 'a'})
    check('member', 'extern thread_local int a', {1: 'a'})
    check('member', 'thread_local extern int a', {1: 'a'},
          'extern thread_local int a')
    check('member', 'static thread_local int a', {1: 'a'})
    check('member', 'thread_local static int a', {1: 'a'},
          'static thread_local int a')

    check('member', 'int b : 3', {1: 'b'})


def test_function_definitions():
    check('function', 'void f()', {1: 'f'})
    check('function', 'void f(int)', {1: 'f'})
    check('function', 'void f(int i)', {1: 'f'})
    check('function', 'void f(int i, int j)', {1: 'f'})
    check('function', 'void f(...)', {1: 'f'})
    check('function', 'void f(int i, ...)', {1: 'f'})
    check('function', 'void f(struct T)', {1: 'f'})
    check('function', 'void f(struct T t)', {1: 'f'})
    check('function', 'void f(union T)', {1: 'f'})
    check('function', 'void f(union T t)', {1: 'f'})
    check('function', 'void f(enum T)', {1: 'f'})
    check('function', 'void f(enum T t)', {1: 'f'})

    # test from issue #1539
    check('function', 'void f(A x[])', {1: 'f'})

    # test from issue #2377
    check('function', 'void (*signal(int sig, void (*func)(int)))(int)', {1: 'signal'})

    check('function', 'extern void f()', {1: 'f'})
    check('function', 'static void f()', {1: 'f'})
    check('function', 'inline void f()', {1: 'f'})

    # tests derived from issue #1753 (skip to keep sanity)
    check('function', "void f(float *q(double))", {1: 'f'})
    check('function', "void f(float *(*q)(double))", {1: 'f'})
    check('function', "void f(float (*q)(double))", {1: 'f'})
    check('function', "int (*f(double d))(float)", {1: 'f'})
    check('function', "int (*f(bool b))[5]", {1: 'f'})
    check('function', "void f(int *const p)", {1: 'f'})
    check('function', "void f(int *volatile const p)", {1: 'f'})

    # from breathe#223
    check('function', 'void f(struct E e)', {1: 'f'})
    check('function', 'void f(enum E e)', {1: 'f'})
    check('function', 'void f(union E e)', {1: 'f'})


def test_union_definitions():
    check('struct', 'A', {1: 'A'})


def test_union_definitions():
    check('union', 'A', {1: 'A'})


def test_enum_definitions():
    check('enum', 'A', {1: 'A'})

    check('enumerator', 'A', {1: 'A'})
    check('enumerator', 'A = 42', {1: 'A'})


def test_anon_definitions():
    return  # TODO
    check('class', '@a', {3: "Ut1_a"})
    check('union', '@a', {3: "Ut1_a"})
    check('enum', '@a', {3: "Ut1_a"})
    check('class', '@1', {3: "Ut1_1"})
    check('class', '@a::A', {3: "NUt1_a1AE"})


def test_initializers():
    idsMember = {1: 'v'}
    idsFunction = {1: 'f'}
    # no init
    check('member', 'T v', idsMember)
    check('function', 'void f(T v)', idsFunction)
    # with '=', assignment-expression
    check('member', 'T v = 42', idsMember)
    check('function', 'void f(T v = 42)', idsFunction)
    # with '=', braced-init
    check('member', 'T v = {}', idsMember)
    check('function', 'void f(T v = {})', idsFunction)
    check('member', 'T v = {42, 42, 42}', idsMember)
    check('function', 'void f(T v = {42, 42, 42})', idsFunction)
    check('member', 'T v = {42, 42, 42,}', idsMember)
    check('function', 'void f(T v = {42, 42, 42,})', idsFunction)
    # TODO: designator-list


def test_attributes():
    return  # TODO
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
    check('function', '[[attr1]] [[attr2]] void f()',
          {1: 'f', 2: '1fv'},
          output='[[attr1]] [[attr2]] void f()')
    # position: declarator
    check('member', 'int *[[attr]] i', {1: 'i__iP', 2: '1i'})
    check('member', 'int *const [[attr]] volatile i', {1: 'i__iPVC', 2: '1i'},
          output='int *[[attr]] volatile const i')
    check('member', 'int &[[attr]] i', {1: 'i__iR', 2: '1i'})
    check('member', 'int *[[attr]] *i', {1: 'i__iPP', 2: '1i'})


# def test_print():
#     # used for getting all the ids out for checking
#     for a in ids:
#         print(a)
#     raise DefinitionError("")


def filter_warnings(warning, file):
    lines = warning.getvalue().split("\n");
    res = [l for l in lines if "domain-c" in l and "{}.rst".format(file) in l and
           "WARNING: document isn't included in any toctree" not in l]
    print("Filtered warnings for file '{}':".format(file))
    for w in res:
        print(w)
    return res


@pytest.mark.sphinx(testroot='domain-c', confoverrides={'nitpicky': True})
def test_build_domain_c(app, status, warning):
    app.builder.build_all()
    ws = filter_warnings(warning, "index")
    assert len(ws) == 0


def test_cfunction(app):
    text = (".. c:function:: PyObject* "
            "PyType_GenericAlloc(PyTypeObject *type, Py_ssize_t nitems)")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1], addnodes.desc, desctype="function",
                domain="c", objtype="function", noindex=False)

    domain = app.env.get_domain('c')
    entry = domain.objects.get('PyType_GenericAlloc')
    assert entry == ('index', 'c.PyType_GenericAlloc', 'function')


def test_cmember(app):
    text = ".. c:member:: PyObject* PyTypeObject.tp_bases"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1], addnodes.desc, desctype="member",
                domain="c", objtype="member", noindex=False)

    domain = app.env.get_domain('c')
    entry = domain.objects.get('PyTypeObject.tp_bases')
    assert entry == ('index', 'c.PyTypeObject.tp_bases', 'member')


def test_cvar(app):
    text = ".. c:var:: PyObject* PyClass_Type"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1], addnodes.desc, desctype="var",
                domain="c", objtype="var", noindex=False)

    domain = app.env.get_domain('c')
    entry = domain.objects.get('PyClass_Type')
    assert entry == ('index', 'c.PyClass_Type', 'var')
