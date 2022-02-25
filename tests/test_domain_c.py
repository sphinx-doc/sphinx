"""
    test_domain_c
    ~~~~~~~~~~~~~

    Tests the C Domain

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import itertools
import zlib
from xml.etree import ElementTree

import pytest

from sphinx import addnodes
from sphinx.addnodes import desc
from sphinx.domains.c import (DefinitionError, DefinitionParser, Symbol, _id_prefix,
                              _macroKeywords, _max_id)
from sphinx.ext.intersphinx import load_mappings, normalize_intersphinx_mapping
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node


class Config:
    c_id_attributes = ["id_attr", 'LIGHTGBM_C_EXPORT']
    c_paren_attributes = ["paren_attr"]
    c_extra_keywords = _macroKeywords


def parse(name, string):
    parser = DefinitionParser(string, location=None, config=Config())
    parser.allowFallbackExpressionParsing = False
    ast = parser.parse_declaration(name, name)
    parser.assert_end()
    return ast


def _check(name, input, idDict, output, key, asTextOutput):
    if key is None:
        key = name
    key += ' '
    if name in ('function', 'member'):
        inputActual = input
        outputAst = output
        outputAsText = output
    else:
        inputActual = input.format(key='')
        outputAst = output.format(key='')
        outputAsText = output.format(key=key)
    if asTextOutput is not None:
        outputAsText = asTextOutput

    # first a simple check of the AST
    ast = parse(name, inputActual)
    res = str(ast)
    if res != outputAst:
        print("")
        print("Input:    ", input)
        print("Result:   ", res)
        print("Expected: ", outputAst)
        raise DefinitionError("")
    rootSymbol = Symbol(None, None, None, None, None)
    symbol = rootSymbol.add_declaration(ast, docname="TestDoc", line=42)
    parentNode = addnodes.desc()
    signode = addnodes.desc_signature(input, '')
    parentNode += signode
    ast.describe_signature(signode, 'lastIsName', symbol, options={})
    resAsText = parentNode.astext()
    if resAsText != outputAsText:
        print("")
        print("Input:    ", input)
        print("astext(): ", resAsText)
        print("Expected: ", outputAsText)
        raise DefinitionError("")

    idExpected = [None]
    for i in range(1, _max_id + 1):
        if i in idDict:
            idExpected.append(idDict[i])
        else:
            idExpected.append(idExpected[i - 1])
    idActual = [None]
    for i in range(1, _max_id + 1):
        # try:
        id = ast.get_id(version=i)
        assert id is not None
        idActual.append(id[len(_id_prefix[i]):])
        # except NoOldIdError:
        #     idActual.append(None)

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
        # print(rootSymbol.dump(0))
        raise DefinitionError("")


def check(name, input, idDict, output=None, key=None, asTextOutput=None):
    if output is None:
        output = input
    # First, check without semicolon
    _check(name, input, idDict, output, key, asTextOutput)
    if name != 'macro':
        # Second, check with semicolon
        _check(name, input + ' ;', idDict, output + ';', key,
               asTextOutput + ';' if asTextOutput is not None else None)


def test_domain_c_ast_expressions():
    def exprCheck(expr, output=None):
        parser = DefinitionParser(expr, location=None, config=Config())
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
        displayString = ast.get_display_string()
        if res != displayString:
            # note: if the expression contains an anon name then this will trigger a falsely
            print("")
            print("Input:    ", expr)
            print("Result:   ", res)
            print("Display:  ", displayString)
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
    ints = ['5', '0', '075', '0x0123456789ABCDEF', '0XF', '0b1', '0B1',
            "0b0'1'0", "00'1'2", "0x0'1'2", "1'2'3"]
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
                '5.0', '5.0e42', '5.0e+42', '5.0e-42',
                "1'2'3e7'8'9", "1'2'3.e7'8'9",
                ".4'5'6e7'8'9", "1'2'3.4'5'6e7'8'9"]:
            expr = e + suffix
            exprCheck(expr)
        for e in [
                'ApF', 'Ap+F', 'Ap-F',
                'A.', 'A.pF', 'A.p+F', 'A.p-F',
                '.A', '.ApF', '.Ap+F', '.Ap-F',
                'A.B', 'A.BpF', 'A.Bp+F', 'A.Bp-F',
                "A'B'Cp1'2'3", "A'B'C.p1'2'3",
                ".D'E'Fp1'2'3", "A'B'C.D'E'Fp1'2'3"]:
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
    exprCheck('not 5')
    exprCheck('~5')
    exprCheck('compl 5')
    exprCheck('sizeof(T)')
    exprCheck('sizeof -42')
    exprCheck('alignof(T)')
    # cast
    exprCheck('(int)2')
    # binary op
    exprCheck('5 || 42')
    exprCheck('5 or 42')
    exprCheck('5 && 42')
    exprCheck('5 and 42')
    exprCheck('5 | 42')
    exprCheck('5 bitor 42')
    exprCheck('5 ^ 42')
    exprCheck('5 xor 42')
    exprCheck('5 & 42')
    exprCheck('5 bitand 42')
    # ['==', '!=']
    exprCheck('5 == 42')
    exprCheck('5 != 42')
    exprCheck('5 not_eq 42')
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
    exprCheck('a and_eq 5')
    exprCheck('a ^= 5')
    exprCheck('a xor_eq 5')
    exprCheck('a |= 5')
    exprCheck('a or_eq 5')


def test_domain_c_ast_fundamental_types():
    def types():
        def signed(t):
            yield t
            yield 'signed  ' + t
            yield 'unsigned  ' + t

        # integer types
        # -------------
        yield 'void'
        yield from ('_Bool', 'bool')
        yield from signed('char')
        yield from signed('short')
        yield from signed('short int')
        yield from signed('int')
        yield from ('signed', 'unsigned')
        yield from signed('long')
        yield from signed('long int')
        yield from signed('long long')
        yield from signed('long long int')
        yield from ('__int128', '__uint128')
        # extensions
        for t in ('__int8', '__int16', '__int32', '__int64', '__int128'):
            yield from signed(t)

        # floating point types
        # --------------------
        yield from ('_Decimal32', '_Decimal64', '_Decimal128')
        for f in ('float', 'double', 'long double'):
            yield f
            yield from (f + "  _Complex", f + "  complex")
            yield from ("_Complex  " + f, "complex  " + f)
            yield from ("_Imaginary  " + f, "imaginary  " + f)
        # extensions
        # https://gcc.gnu.org/onlinedocs/gcc/Floating-Types.html#Floating-Types
        yield from ('__float80', '_Float64x',
                    '__float128', '_Float128',
                    '__ibm128')
        # https://gcc.gnu.org/onlinedocs/gcc/Half-Precision.html#Half-Precision
        yield '__fp16'

        # fixed-point types (extension)
        # -----------------------------
        # https://gcc.gnu.org/onlinedocs/gcc/Fixed-Point.html#Fixed-Point
        for sat in ('', '_Sat  '):
            for t in ('_Fract', 'fract', '_Accum', 'accum'):
                for size in ('short  ', '', 'long  ', 'long long  '):
                    for tt in signed(size + t):
                        yield sat + tt

    for t in types():
        input = "{key}%s foo" % t
        output = ' '.join(input.split())
        check('type', input, {1: 'foo'}, key='typedef', output=output)
        if ' ' in t:
            # try permutations of all components
            tcs = t.split()
            for p in itertools.permutations(tcs):
                input = "{key}%s foo" % ' '.join(p)
                output = ' '.join(input.split())
                check("type", input, {1: 'foo'}, key='typedef', output=output)


def test_domain_c_ast_type_definitions():
    check('type', "{key}T", {1: "T"})

    check('type', "{key}bool *b", {1: 'b'}, key='typedef')
    check('type', "{key}bool *const b", {1: 'b'}, key='typedef')
    check('type', "{key}bool *const *b", {1: 'b'}, key='typedef')
    check('type', "{key}bool *volatile *b", {1: 'b'}, key='typedef')
    check('type', "{key}bool *restrict *b", {1: 'b'}, key='typedef')
    check('type', "{key}bool *volatile const b", {1: 'b'}, key='typedef')
    check('type', "{key}bool *volatile const b", {1: 'b'}, key='typedef')
    check('type', "{key}bool *volatile const *b", {1: 'b'}, key='typedef')
    check('type', "{key}bool b[]", {1: 'b'}, key='typedef')
    check('type', "{key}long long int foo", {1: 'foo'}, key='typedef')
    # test decl specs on right
    check('type', "{key}bool const b", {1: 'b'}, key='typedef')

    # from breathe#267 (named function parameters for function pointers
    check('type', '{key}void (*gpio_callback_t)(struct device *port, uint32_t pin)',
          {1: 'gpio_callback_t'}, key='typedef')


def test_domain_c_ast_macro_definitions():
    check('macro', 'M', {1: 'M'})
    check('macro', 'M()', {1: 'M'})
    check('macro', 'M(arg)', {1: 'M'})
    check('macro', 'M(arg1, arg2)', {1: 'M'})
    check('macro', 'M(arg1, arg2, arg3)', {1: 'M'})
    check('macro', 'M(...)', {1: 'M'})
    check('macro', 'M(arg, ...)', {1: 'M'})
    check('macro', 'M(arg1, arg2, ...)', {1: 'M'})
    check('macro', 'M(arg1, arg2, arg3, ...)', {1: 'M'})
    # GNU extension
    check('macro', 'M(arg1, arg2, arg3...)', {1: 'M'})
    with pytest.raises(DefinitionError):
        check('macro', 'M(arg1, arg2..., arg3)', {1: 'M'})


def test_domain_c_ast_member_definitions():
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


def test_domain_c_ast_function_definitions():
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

    # array declarators
    check('function', 'void f(int arr[])', {1: 'f'})
    check('function', 'void f(int arr[*])', {1: 'f'})
    cvrs = ['', 'const', 'volatile', 'restrict', 'restrict volatile const']
    for cvr in cvrs:
        space = ' ' if len(cvr) != 0 else ''
        check('function', 'void f(int arr[{}*])'.format(cvr), {1: 'f'})
        check('function', 'void f(int arr[{}])'.format(cvr), {1: 'f'})
        check('function', 'void f(int arr[{}{}42])'.format(cvr, space), {1: 'f'})
        check('function', 'void f(int arr[static{}{} 42])'.format(space, cvr), {1: 'f'})
        check('function', 'void f(int arr[{}{}static 42])'.format(cvr, space), {1: 'f'},
              output='void f(int arr[static{}{} 42])'.format(space, cvr))
    check('function', 'void f(int arr[const static volatile 42])', {1: 'f'},
          output='void f(int arr[static volatile const 42])')

    with pytest.raises(DefinitionError):
        parse('function', 'void f(int for)')

    # from #8960
    check('function', 'void f(void (*p)(int, double), int i)', {1: 'f'})


def test_domain_c_ast_nested_name():
    check('struct', '{key}.A', {1: "A"})
    check('struct', '{key}.A.B', {1: "A.B"})
    check('function', 'void f(.A a)', {1: "f"})
    check('function', 'void f(.A.B a)', {1: "f"})


def test_domain_c_ast_struct_definitions():
    check('struct', '{key}A', {1: 'A'})


def test_domain_c_ast_union_definitions():
    check('union', '{key}A', {1: 'A'})


def test_domain_c_ast_enum_definitions():
    check('enum', '{key}A', {1: 'A'})

    check('enumerator', '{key}A', {1: 'A'})
    check('enumerator', '{key}A = 42', {1: 'A'})


def test_domain_c_ast_anon_definitions():
    check('struct', '@a', {1: "@a"}, asTextOutput='struct [anonymous]')
    check('union', '@a', {1: "@a"}, asTextOutput='union [anonymous]')
    check('enum', '@a', {1: "@a"}, asTextOutput='enum [anonymous]')
    check('struct', '@1', {1: "@1"}, asTextOutput='struct [anonymous]')
    check('struct', '@a.A', {1: "@a.A"}, asTextOutput='struct [anonymous].A')


def test_domain_c_ast_initializers():
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


def test_domain_c_ast_attributes():
    # style: C++
    check('member', '[[]] int f', {1: 'f'})
    check('member', '[ [ ] ] int f', {1: 'f'},
          # this will fail when the proper grammar is implemented
          output='[[ ]] int f')
    check('member', '[[a]] int f', {1: 'f'})
    # style: GNU
    check('member', '__attribute__(()) int f', {1: 'f'})
    check('member', '__attribute__((a)) int f', {1: 'f'})
    check('member', '__attribute__((a, b)) int f', {1: 'f'})
    check('member', '__attribute__((optimize(3))) int f', {1: 'f'})
    check('member', '__attribute__((format(printf, 1, 2))) int f', {1: 'f'})
    # style: user-defined id
    check('member', 'id_attr int f', {1: 'f'})
    # style: user-defined paren
    check('member', 'paren_attr() int f', {1: 'f'})
    check('member', 'paren_attr(a) int f', {1: 'f'})
    check('member', 'paren_attr("") int f', {1: 'f'})
    check('member', 'paren_attr(()[{}][]{}) int f', {1: 'f'})
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
    check('function', 'static inline __attribute__(()) void f()', {1: 'f'},
          output='__attribute__(()) static inline void f()')
    check('function', '[[attr1]] [[attr2]] void f()', {1: 'f'})
    # position: declarator
    check('member', 'int *[[attr]] i', {1: 'i'})
    check('member', 'int *const [[attr]] volatile i', {1: 'i'},
          output='int *[[attr]] volatile const i')
    check('member', 'int *[[attr]] *i', {1: 'i'})
    # position: parameters
    check('function', 'void f() [[attr1]] [[attr2]]', {1: 'f'})

    # issue michaeljones/breathe#500
    check('function', 'LIGHTGBM_C_EXPORT int LGBM_BoosterFree(int handle)',
          {1: 'LGBM_BoosterFree'})


def test_extra_keywords():
    with pytest.raises(DefinitionError,
                       match='Expected identifier in nested name'):
        parse('function', 'void complex(void)')


# def test_print():
#     # used for getting all the ids out for checking
#     for a in ids:
#         print(a)
#     raise DefinitionError("")


def split_warnigns(warning):
    ws = warning.getvalue().split("\n")
    assert len(ws) >= 1
    assert ws[-1] == ""
    return ws[:-1]


def filter_warnings(warning, file):
    lines = split_warnigns(warning)
    res = [l for l in lines if "domain-c" in l and "{}.rst".format(file) in l and
           "WARNING: document isn't included in any toctree" not in l]
    print("Filtered warnings for file '{}':".format(file))
    for w in res:
        print(w)
    return res


def extract_role_links(app, filename):
    t = (app.outdir / filename).read_text()
    lis = [l for l in t.split('\n') if l.startswith("<li")]
    entries = []
    for l in lis:
        li = ElementTree.fromstring(l)
        aList = list(li.iter('a'))
        assert len(aList) == 1
        a = aList[0]
        target = a.attrib['href'].lstrip('#')
        title = a.attrib['title']
        assert len(a) == 1
        code = a[0]
        assert code.tag == 'code'
        text = ''.join(code.itertext())
        entries.append((target, title, text))
    return entries


@pytest.mark.sphinx(testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build(app, status, warning):
    app.builder.build_all()
    ws = filter_warnings(warning, "index")
    assert len(ws) == 0


@pytest.mark.sphinx(testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build_namespace(app, status, warning):
    app.builder.build_all()
    ws = filter_warnings(warning, "namespace")
    assert len(ws) == 0
    t = (app.outdir / "namespace.html").read_text()
    for id_ in ('NS.NSVar', 'NULLVar', 'ZeroVar', 'NS2.NS3.NS2NS3Var', 'PopVar'):
        assert 'id="c.{}"'.format(id_) in t


@pytest.mark.sphinx(testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build_anon_dup_decl(app, status, warning):
    app.builder.build_all()
    ws = filter_warnings(warning, "anon-dup-decl")
    assert len(ws) == 2
    assert "WARNING: c:identifier reference target not found: @a" in ws[0]
    assert "WARNING: c:identifier reference target not found: @b" in ws[1]


@pytest.mark.sphinx(confoverrides={'nitpicky': True})
def test_domain_c_build_semicolon(app, warning):
    text = """
.. c:member:: int member;
.. c:var:: int var;
.. c:function:: void f();
.. .. c:macro:: NO_SEMICOLON;
.. c:struct:: Struct;
.. c:union:: Union;
.. c:enum:: Enum;
.. c:enumerator:: Enumerator;
.. c:type:: Type;
.. c:type:: int TypeDef;
"""
    restructuredtext.parse(app, text)
    ws = split_warnigns(warning)
    assert len(ws) == 0


@pytest.mark.sphinx(testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build_function_param_target(app, warning):
    # the anchor for function parameters should be the function
    app.builder.build_all()
    ws = filter_warnings(warning, "function_param_target")
    assert len(ws) == 0
    entries = extract_role_links(app, "function_param_target.html")
    assert entries == [
        ('c.function_param_target.f', 'i', 'i'),
        ('c.function_param_target.f', 'f.i', 'f.i'),
    ]


@pytest.mark.sphinx(testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build_ns_lookup(app, warning):
    app.builder.build_all()
    ws = filter_warnings(warning, "ns_lookup")
    assert len(ws) == 0


@pytest.mark.sphinx(testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build_field_role(app, status, warning):
    app.builder.build_all()
    ws = filter_warnings(warning, "field-role")
    assert len(ws) == 0


def _get_obj(app, queryName):
    domain = app.env.get_domain('c')
    for name, _dispname, objectType, docname, anchor, _prio in domain.get_objects():
        if name == queryName:
            return (docname, anchor, objectType)
    return (queryName, "not", "found")


@pytest.mark.sphinx(testroot='domain-c-intersphinx', confoverrides={'nitpicky': True})
def test_domain_c_build_intersphinx(tempdir, app, status, warning):
    # a splitting of test_ids_vs_tags0 into the primary directives in a remote project,
    # and then the references in the test project
    origSource = """\
.. c:member:: int _member
.. c:var:: int _var
.. c:function:: void _function()
.. c:macro:: _macro
.. c:struct:: _struct
.. c:union:: _union
.. c:enum:: _enum

    .. c:enumerator:: _enumerator

.. c:type:: _type
.. c:function:: void _functionParam(int param)
"""  # noqa
    inv_file = tempdir / 'inventory'
    inv_file.write_bytes(b'''\
# Sphinx inventory version 2
# Project: C Intersphinx Test
# Version: 
# The remainder of this file is compressed using zlib.
''' + zlib.compress(b'''\
_enum c:enum 1 index.html#c.$ -
_enum._enumerator c:enumerator 1 index.html#c.$ -
_enumerator c:enumerator 1 index.html#c._enum.$ -
_function c:function 1 index.html#c.$ -
_functionParam c:function 1 index.html#c.$ -
_functionParam.param c:functionParam 1 index.html#c._functionParam -
_macro c:macro 1 index.html#c.$ -
_member c:member 1 index.html#c.$ -
_struct c:struct 1 index.html#c.$ -
_type c:type 1 index.html#c.$ -
_union c:union 1 index.html#c.$ -
_var c:member 1 index.html#c.$ -
'''))  # noqa
    app.config.intersphinx_mapping = {
        'https://localhost/intersphinx/c/': inv_file,
    }
    app.config.intersphinx_cache_limit = 0
    # load the inventory and check if it's done correctly
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)

    app.builder.build_all()
    ws = filter_warnings(warning, "index")
    assert len(ws) == 0


def test_domain_c_parse_cfunction(app):
    text = (".. c:function:: PyObject* "
            "PyType_GenericAlloc(PyTypeObject *type, Py_ssize_t nitems)")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1], addnodes.desc, desctype="function",
                domain="c", objtype="function", noindex=False)

    entry = _get_obj(app, 'PyType_GenericAlloc')
    assert entry == ('index', 'c.PyType_GenericAlloc', 'function')


def test_domain_c_parse_cmember(app):
    text = ".. c:member:: PyObject* PyTypeObject.tp_bases"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1], addnodes.desc, desctype="member",
                domain="c", objtype="member", noindex=False)

    entry = _get_obj(app, 'PyTypeObject.tp_bases')
    assert entry == ('index', 'c.PyTypeObject.tp_bases', 'member')


def test_domain_c_parse_cvar(app):
    text = ".. c:var:: PyObject* PyClass_Type"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1], addnodes.desc, desctype="var",
                domain="c", objtype="var", noindex=False)

    entry = _get_obj(app, 'PyClass_Type')
    assert entry == ('index', 'c.PyClass_Type', 'member')


def test_domain_c_parse_noindexentry(app):
    text = (".. c:function:: void f()\n"
            ".. c:function:: void g()\n"
            "   :noindexentry:\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, desc, addnodes.index, desc))
    assert_node(doctree[0], addnodes.index, entries=[('single', 'f (C function)', 'c.f', '', None)])
    assert_node(doctree[2], addnodes.index, entries=[])
