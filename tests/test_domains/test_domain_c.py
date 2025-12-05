"""Tests the C Domain"""

from __future__ import annotations

import itertools
import xml.etree.ElementTree as ET
import zlib
from typing import TYPE_CHECKING

import pytest

from sphinx import addnodes
from sphinx.addnodes import (
    desc,
    desc_content,
    desc_name,
    desc_parameter,
    desc_parameterlist,
    desc_sig_name,
    desc_sig_space,
    desc_signature,
    desc_signature_line,
    pending_xref,
)
from sphinx.domains.c._ids import _id_prefix, _macro_keywords, _max_id
from sphinx.domains.c._parser import DefinitionParser
from sphinx.domains.c._symbol import Symbol
from sphinx.ext.intersphinx._load import load_mappings, validate_intersphinx_mapping
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node
from sphinx.util.cfamily import DefinitionError
from sphinx.writers.text import STDINDENT

from tests.utils import extract_node

if TYPE_CHECKING:
    from io import StringIO


class Config:
    c_id_attributes = ['id_attr', 'LIGHTGBM_C_EXPORT']
    c_paren_attributes = ['paren_attr']
    c_extra_keywords = _macro_keywords


def parse(name, string):
    parser = DefinitionParser(string, location=None, config=Config())
    parser.allowFallbackExpressionParsing = False
    ast = parser.parse_declaration(name, name)
    parser.assert_end()
    return ast


def _check(name, input, id_dict, output, key, as_text_output):
    if key is None:
        key = name
    key += ' '
    if name in {'function', 'member'}:
        input_actual = input
        output_ast = output
        output_as_text = output
    else:
        input_actual = input.format(key='')
        output_ast = output.format(key='')
        output_as_text = output.format(key=key)
    if as_text_output is not None:
        output_as_text = as_text_output

    # first a simple check of the AST
    ast = parse(name, input_actual)
    res = str(ast)
    if res != output_ast:
        print()
        print('Input:    ', input)
        print('Result:   ', res)
        print('Expected: ', output_ast)
        raise DefinitionError
    root_symbol = Symbol(None, None, None, None, None)
    symbol = root_symbol.add_declaration(ast, docname='TestDoc', line=42)
    parent_node = addnodes.desc()
    signode = addnodes.desc_signature(input, '')
    parent_node += signode
    ast.describe_signature(signode, 'lastIsName', symbol, options={})
    res_as_text = parent_node.astext()
    if res_as_text != output_as_text:
        print()
        print('Input:    ', input)
        print('astext(): ', res_as_text)
        print('Expected: ', output_as_text)
        raise DefinitionError

    id_expected = [None]
    for i in range(1, _max_id + 1):
        if i in id_dict:
            id_expected.append(id_dict[i])
        else:
            id_expected.append(id_expected[i - 1])
    id_actual = [None]
    for i in range(1, _max_id + 1):
        # try:
        id = ast.get_id(version=i)
        assert id is not None
        id_actual.append(id[len(_id_prefix[i]) :])
        # except NoOldIdError:
        #     id_actual.append(None)

    res = [True]
    for i in range(1, _max_id + 1):
        res.append(id_expected[i] == id_actual[i])

    if not all(res):
        print('input:    %s' % input.rjust(20))
        for i in range(1, _max_id + 1):
            if res[i]:
                continue
            print('Error in id version %d.' % i)
            print('result:   %s' % id_actual[i])
            print('expected: %s' % id_expected[i])
        # print(root_symbol.dump(0))
        raise DefinitionError


def check(name, input, id_dict, output=None, key=None, as_text_output=None):
    if output is None:
        output = input
    # First, check without semicolon
    _check(name, input, id_dict, output, key, as_text_output)
    if name != 'macro':
        # Second, check with semicolon
        _check(
            name,
            input + ' ;',
            id_dict,
            output + ';',
            key,
            as_text_output + ';' if as_text_output is not None else None,
        )


def test_domain_c_ast_expressions() -> None:
    def expr_check(expr, output=None):
        parser = DefinitionParser(expr, location=None, config=Config())
        parser.allowFallbackExpressionParsing = False
        ast = parser.parse_expression()
        parser.assert_end()
        # first a simple check of the AST
        if output is None:
            output = expr
        res = str(ast)
        if res != output:
            print()
            print('Input:    ', input)
            print('Result:   ', res)
            print('Expected: ', output)
            raise DefinitionError
        display_string = ast.get_display_string()
        if res != display_string:
            # note: if the expression contains an anon name then this will trigger a falsely
            print()
            print('Input:    ', expr)
            print('Result:   ', res)
            print('Display:  ', display_string)
            raise DefinitionError

    # type expressions
    expr_check('int*')
    expr_check('int *const*')
    expr_check('int *volatile*')
    expr_check('int *restrict*')
    expr_check('int *(*)(double)')
    expr_check('const int*')
    expr_check('__int64')
    expr_check('unsigned __int64')

    # actual expressions

    # primary
    expr_check('true')
    expr_check('false')
    ints = [
        '5',
        '0',
        '075',
        '0x0123456789ABCDEF',
        '0XF',
        '0b1',
        '0B1',
        "0b0'1'0",
        "00'1'2",
        "0x0'1'2",
        "1'2'3",
    ]
    unsigned_suffix = ['', 'u', 'U']
    long_suffix = ['', 'l', 'L', 'll', 'LL']
    for i in ints:
        for u in unsigned_suffix:
            for l in long_suffix:
                expr = i + u + l
                expr_check(expr)
                expr = i + l + u
                expr_check(expr)
    for suffix in ('', 'f', 'F', 'l', 'L'):
        for e in (
            '5e42',
            '5e+42',
            '5e-42',
            '5.',
            '5.e42',
            '5.e+42',
            '5.e-42',
            '.5',
            '.5e42',
            '.5e+42',
            '.5e-42',
            '5.0',
            '5.0e42',
            '5.0e+42',
            '5.0e-42',
            "1'2'3e7'8'9",
            "1'2'3.e7'8'9",
            ".4'5'6e7'8'9",
            "1'2'3.4'5'6e7'8'9",
        ):
            expr = e + suffix
            expr_check(expr)
        for e in (
            'ApF',
            'Ap+F',
            'Ap-F',
            'A.',
            'A.pF',
            'A.p+F',
            'A.p-F',
            '.A',
            '.ApF',
            '.Ap+F',
            '.Ap-F',
            'A.B',
            'A.BpF',
            'A.Bp+F',
            'A.Bp-F',
            "A'B'Cp1'2'3",
            "A'B'C.p1'2'3",
            ".D'E'Fp1'2'3",
            "A'B'C.D'E'Fp1'2'3",
        ):
            expr = '0x' + e + suffix
            expr_check(expr)
    expr_check('"abc\\"cba"')  # string
    # character literals
    for p in ('', 'u8', 'u', 'U', 'L'):
        expr_check(p + "'a'")
        expr_check(p + "'\\n'")
        expr_check(p + "'\\012'")
        expr_check(p + "'\\0'")
        expr_check(p + "'\\x0a'")
        expr_check(p + "'\\x0A'")
        expr_check(p + "'\\u0a42'")
        expr_check(p + "'\\u0A42'")
        expr_check(p + "'\\U0001f34c'")
        expr_check(p + "'\\U0001F34C'")

    expr_check('(5)')
    expr_check('C')
    # postfix
    expr_check('A(2)')
    expr_check('A[2]')
    expr_check('a.b.c')
    expr_check('a->b->c')
    expr_check('i++')
    expr_check('i--')
    # unary
    expr_check('++5')
    expr_check('--5')
    expr_check('*5')
    expr_check('&5')
    expr_check('+5')
    expr_check('-5')
    expr_check('!5')
    expr_check('not 5')
    expr_check('~5')
    expr_check('compl 5')
    expr_check('sizeof(T)')
    expr_check('sizeof -42')
    expr_check('alignof(T)')
    # cast
    expr_check('(int)2')
    # binary op
    expr_check('5 || 42')
    expr_check('5 or 42')
    expr_check('5 && 42')
    expr_check('5 and 42')
    expr_check('5 | 42')
    expr_check('5 bitor 42')
    expr_check('5 ^ 42')
    expr_check('5 xor 42')
    expr_check('5 & 42')
    expr_check('5 bitand 42')
    # ['==', '!=']
    expr_check('5 == 42')
    expr_check('5 != 42')
    expr_check('5 not_eq 42')
    # ['<=', '>=', '<', '>']
    expr_check('5 <= 42')
    expr_check('5 >= 42')
    expr_check('5 < 42')
    expr_check('5 > 42')
    # ['<<', '>>']
    expr_check('5 << 42')
    expr_check('5 >> 42')
    # ['+', '-']
    expr_check('5 + 42')
    expr_check('5 - 42')
    # ['*', '/', '%']
    expr_check('5 * 42')
    expr_check('5 / 42')
    expr_check('5 % 42')
    # ['.*', '->*']
    expr_check('5 .* 42')
    expr_check('5 ->* 42')
    # TODO: conditional is unimplemented
    # conditional
    # expr_check('5 ? 7 : 3')
    # assignment
    expr_check('a = 5')
    expr_check('a *= 5')
    expr_check('a /= 5')
    expr_check('a %= 5')
    expr_check('a += 5')
    expr_check('a -= 5')
    expr_check('a >>= 5')
    expr_check('a <<= 5')
    expr_check('a &= 5')
    expr_check('a and_eq 5')
    expr_check('a ^= 5')
    expr_check('a xor_eq 5')
    expr_check('a |= 5')
    expr_check('a or_eq 5')


def test_domain_c_ast_fundamental_types() -> None:
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
            yield from (f + '  _Complex', f + '  complex')
            yield from ('_Complex  ' + f, 'complex  ' + f)
            yield from ('_Imaginary  ' + f, 'imaginary  ' + f)
        # extensions
        # https://gcc.gnu.org/onlinedocs/gcc/Floating-Types.html#Floating-Types
        yield from (
            '__float80',
            '_Float64x',
            '__float128',
            '_Float128',
            '__ibm128',
        )
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
        input = '{key}%s foo' % t
        output = ' '.join(input.split())
        check('type', input, {1: 'foo'}, key='typedef', output=output)
        if ' ' in t:
            # try permutations of all components
            tcs = t.split()
            for p in itertools.permutations(tcs):
                input = '{key}%s foo' % ' '.join(p)
                output = ' '.join(input.split())
                check('type', input, {1: 'foo'}, key='typedef', output=output)


def test_domain_c_ast_type_definitions() -> None:
    check('type', '{key}T', {1: 'T'})

    check('type', '{key}bool *b', {1: 'b'}, key='typedef')
    check('type', '{key}bool *const b', {1: 'b'}, key='typedef')
    check('type', '{key}bool *const *b', {1: 'b'}, key='typedef')
    check('type', '{key}bool *volatile *b', {1: 'b'}, key='typedef')
    check('type', '{key}bool *restrict *b', {1: 'b'}, key='typedef')
    check('type', '{key}bool *volatile const b', {1: 'b'}, key='typedef')
    check('type', '{key}bool *volatile const b', {1: 'b'}, key='typedef')
    check('type', '{key}bool *volatile const *b', {1: 'b'}, key='typedef')
    check('type', '{key}bool b[]', {1: 'b'}, key='typedef')
    check('type', '{key}long long int foo', {1: 'foo'}, key='typedef')
    # test decl specs on right
    check('type', '{key}bool const b', {1: 'b'}, key='typedef')

    # from https://github.com/breathe-doc/breathe/issues/267
    # (named function parameters for function pointers
    check(
        'type',
        '{key}void (*gpio_callback_t)(struct device *port, uint32_t pin)',
        {1: 'gpio_callback_t'},
        key='typedef',
    )


def test_domain_c_ast_macro_definitions() -> None:
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


def test_domain_c_ast_member_definitions() -> None:
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

    # test from issue https://github.com/sphinx-doc/sphinx/issues/1539
    check('member', 'CK_UTF8CHAR model[16]', {1: 'model'})

    check('member', 'auto int a', {1: 'a'})
    check('member', 'register int a', {1: 'a'})
    check('member', 'extern int a', {1: 'a'})
    check('member', 'static int a', {1: 'a'})

    check('member', 'thread_local int a', {1: 'a'})
    check('member', '_Thread_local int a', {1: 'a'})
    check('member', 'extern thread_local int a', {1: 'a'})
    check('member', 'thread_local extern int a', {1: 'a'}, 'extern thread_local int a')
    check('member', 'static thread_local int a', {1: 'a'})
    check('member', 'thread_local static int a', {1: 'a'}, 'static thread_local int a')

    check('member', 'int b : 3', {1: 'b'})


def test_domain_c_ast_function_definitions() -> None:
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

    # test from issue https://github.com/sphinx-doc/sphinx/issues/1539
    check('function', 'void f(A x[])', {1: 'f'})

    # test from issue https://github.com/sphinx-doc/sphinx/issues/2377
    check('function', 'void (*signal(int sig, void (*func)(int)))(int)', {1: 'signal'})

    check('function', 'extern void f()', {1: 'f'})
    check('function', 'static void f()', {1: 'f'})
    check('function', 'inline void f()', {1: 'f'})

    # tests derived from https://github.com/sphinx-doc/sphinx/issues/1753
    # (skip to keep sanity)
    check('function', 'void f(float *q(double))', {1: 'f'})
    check('function', 'void f(float *(*q)(double))', {1: 'f'})
    check('function', 'void f(float (*q)(double))', {1: 'f'})
    check('function', 'int (*f(double d))(float)', {1: 'f'})
    check('function', 'int (*f(bool b))[5]', {1: 'f'})
    check('function', 'void f(int *const p)', {1: 'f'})
    check('function', 'void f(int *volatile const p)', {1: 'f'})

    # from https://github.com/breathe-doc/breathe/issues/223
    check('function', 'void f(struct E e)', {1: 'f'})
    check('function', 'void f(enum E e)', {1: 'f'})
    check('function', 'void f(union E e)', {1: 'f'})

    # array declarators
    check('function', 'void f(int arr[])', {1: 'f'})
    check('function', 'void f(int arr[*])', {1: 'f'})
    cvrs = ['', 'const', 'volatile', 'restrict', 'restrict volatile const']
    for cvr in cvrs:
        space = ' ' if len(cvr) != 0 else ''
        check('function', f'void f(int arr[{cvr}*])', {1: 'f'})
        check('function', f'void f(int arr[{cvr}])', {1: 'f'})
        check('function', f'void f(int arr[{cvr}{space}42])', {1: 'f'})
        check('function', f'void f(int arr[static{space}{cvr} 42])', {1: 'f'})
        check(
            'function',
            f'void f(int arr[{cvr}{space}static 42])',
            {1: 'f'},
            output=f'void f(int arr[static{space}{cvr} 42])',
        )
    check(
        'function',
        'void f(int arr[const static volatile 42])',
        {1: 'f'},
        output='void f(int arr[static volatile const 42])',
    )

    with pytest.raises(DefinitionError):
        parse('function', 'void f(int for)')

    # from https://github.com/sphinx-doc/sphinx/issues/8960
    check('function', 'void f(void (*p)(int, double), int i)', {1: 'f'})


def test_domain_c_ast_nested_name() -> None:
    check('struct', '{key}.A', {1: 'A'})
    check('struct', '{key}.A.B', {1: 'A.B'})
    check('function', 'void f(.A a)', {1: 'f'})
    check('function', 'void f(.A.B a)', {1: 'f'})


def test_domain_c_ast_struct_definitions() -> None:
    check('struct', '{key}A', {1: 'A'})


def test_domain_c_ast_union_definitions() -> None:
    check('union', '{key}A', {1: 'A'})


def test_domain_c_ast_enum_definitions() -> None:
    check('enum', '{key}A', {1: 'A'})

    check('enumerator', '{key}A', {1: 'A'})
    check('enumerator', '{key}A = 42', {1: 'A'})


def test_domain_c_ast_anon_definitions() -> None:
    check('struct', '@a', {1: '@a'}, as_text_output='struct [anonymous]')
    check('union', '@a', {1: '@a'}, as_text_output='union [anonymous]')
    check('enum', '@a', {1: '@a'}, as_text_output='enum [anonymous]')
    check('struct', '@1', {1: '@1'}, as_text_output='struct [anonymous]')
    check('struct', '@a.A', {1: '@a.A'}, as_text_output='struct [anonymous].A')


def test_domain_c_ast_initializers() -> None:
    ids_member = {1: 'v'}
    ids_function = {1: 'f'}
    # no init
    check('member', 'T v', ids_member)
    check('function', 'void f(T v)', ids_function)
    # with '=', assignment-expression
    check('member', 'T v = 42', ids_member)
    check('function', 'void f(T v = 42)', ids_function)
    # with '=', braced-init
    check('member', 'T v = {}', ids_member)
    check('function', 'void f(T v = {})', ids_function)
    check('member', 'T v = {42, 42, 42}', ids_member)
    check('function', 'void f(T v = {42, 42, 42})', ids_function)
    check('member', 'T v = {42, 42, 42,}', ids_member)
    check('function', 'void f(T v = {42, 42, 42,})', ids_function)
    # TODO: designator-list


def test_domain_c_ast_attributes() -> None:
    # style: C++
    check('member', '[[]] int f', {1: 'f'})
    check(
        'member',
        '[ [ ] ] int f',
        {1: 'f'},
        # this will fail when the proper grammar is implemented
        output='[[ ]] int f',
    )
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
    check(
        'function',
        'static inline __attribute__(()) void f()',
        {1: 'f'},
        output='__attribute__(()) static inline void f()',
    )
    check('function', '[[attr1]] [[attr2]] void f()', {1: 'f'})
    # position: declarator
    check('member', 'int *[[attr1]] [[attr2]] i', {1: 'i'})
    check(
        'member',
        'int *const [[attr1]] [[attr2]] volatile i',
        {1: 'i'},
        output='int *[[attr1]] [[attr2]] volatile const i',
    )
    check('member', 'int *[[attr1]] [[attr2]] *i', {1: 'i'})
    # position: parameters
    check('function', 'void f() [[attr1]] [[attr2]]', {1: 'f'})

    # position: enumerator
    check('enumerator', '{key}Foo [[attr1]] [[attr2]]', {1: 'Foo'})
    check('enumerator', '{key}Foo [[attr1]] [[attr2]] = 42', {1: 'Foo'})

    # issue https://github.com/breathe-doc/breathe/issues/500
    check(
        'function',
        'LIGHTGBM_C_EXPORT int LGBM_BoosterFree(int handle)',
        {1: 'LGBM_BoosterFree'},
    )


def test_extra_keywords() -> None:
    with pytest.raises(DefinitionError, match='Expected identifier in nested name'):
        parse('function', 'void complex(void)')


# def test_print() -> None:
#     # used for getting all the ids out for checking
#     for a in ids:
#         print(a)
#     raise DefinitionError


def split_warnings(warning: StringIO) -> list[str]:
    ws = warning.getvalue().split('\n')
    assert len(ws) >= 1
    assert ws[-1] == ''
    return ws[:-1]


def filter_warnings(warning: StringIO, file: str) -> list[str]:
    lines = split_warnings(warning)
    res = [
        l
        for l in lines
        if 'domain-c' in l
        and f'{file}.rst' in l
        and "WARNING: document isn't included in any toctree" not in l
    ]
    print(f"Filtered warnings for file '{file}':")
    for w in res:
        print(w)
    return res


def extract_role_links(app, filename):
    t = (app.outdir / filename).read_text(encoding='utf8')
    lis = [l for l in t.split('\n') if l.startswith('<li')]
    entries = []
    for l in lis:
        li = ET.fromstring(l)  # NoQA: S314  # using known data in tests
        a_list = list(li.iter('a'))
        assert len(a_list) == 1
        a = a_list[0]
        target = a.attrib['href'].lstrip('#')
        title = a.attrib['title']
        assert len(a) == 1
        code = a[0]
        assert code.tag == 'code'
        text = ''.join(code.itertext())
        entries.append((target, title, text))
    return entries


@pytest.mark.sphinx('html', testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'index')
    assert len(ws) == 0


@pytest.mark.sphinx('html', testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build_namespace(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'namespace')
    assert len(ws) == 0
    t = (app.outdir / 'namespace.html').read_text(encoding='utf8')
    for id_ in ('NS.NSVar', 'NULLVar', 'ZeroVar', 'NS2.NS3.NS2NS3Var', 'PopVar'):
        assert f'id="c.{id_}"' in t


@pytest.mark.sphinx('html', testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build_anon_dup_decl(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'anon-dup-decl')
    assert len(ws) == 2
    assert 'WARNING: c:identifier reference target not found: @a' in ws[0]
    assert 'WARNING: c:identifier reference target not found: @b' in ws[1]


@pytest.mark.sphinx('html', testroot='_blank', confoverrides={'nitpicky': True})
def test_domain_c_build_semicolon(app):
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
    ws = split_warnings(app.warning)
    assert len(ws) == 0


@pytest.mark.sphinx('html', testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build_function_param_target(app):
    # the anchor for function parameters should be the function
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'function_param_target')
    assert len(ws) == 0
    entries = extract_role_links(app, 'function_param_target.html')
    assert entries == [
        ('c.function_param_target.f', 'i', 'i'),
        ('c.function_param_target.f', 'f.i', 'f.i'),
    ]


@pytest.mark.sphinx('html', testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build_ns_lookup(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'ns_lookup')
    assert len(ws) == 0


@pytest.mark.sphinx('html', testroot='domain-c', confoverrides={'nitpicky': True})
def test_domain_c_build_field_role(app):
    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'field-role')
    assert len(ws) == 0


def _get_obj(app, query_name):
    domain = app.env.domains.c_domain
    for name, _dispname, object_type, docname, anchor, _prio in domain.get_objects():
        if name == query_name:
            return docname, anchor, object_type
    return query_name, 'not', 'found'


@pytest.mark.sphinx(
    'html', testroot='domain-c-intersphinx', confoverrides={'nitpicky': True}
)
def test_domain_c_build_intersphinx(tmp_path, app):
    # a splitting of test_ids_vs_tags0 into the primary directives in a remote project,
    # and then the references in the test project
    orig_source = """\
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
"""
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(
        b"""\
# Sphinx inventory version 2
# Project: C Intersphinx Test
# Version:
# The remainder of this file is compressed using zlib.
"""
        + zlib.compress(b"""\
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
""")
    )
    app.config.intersphinx_mapping = {
        'local': ('https://localhost/intersphinx/c/', str(inv_file)),
    }
    app.config.intersphinx_cache_limit = 0
    # load the inventory and check if it's done correctly
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)

    app.build(force_all=True)
    ws = filter_warnings(app.warning, 'index')
    assert len(ws) == 0


@pytest.mark.sphinx('html', testroot='_blank')
def test_domain_c_parse_cfunction(app):
    text = (
        '.. c:function:: PyObject* '
        'PyType_GenericAlloc(PyTypeObject *type, Py_ssize_t nitems)'
    )
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='c',
        objtype='function',
        no_index=False,
    )

    entry = _get_obj(app, 'PyType_GenericAlloc')
    assert entry == ('index', 'c.PyType_GenericAlloc', 'function')


@pytest.mark.sphinx('html', testroot='_blank')
def test_domain_c_parse_cmember(app):
    text = '.. c:member:: PyObject* PyTypeObject.tp_bases'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='member',
        domain='c',
        objtype='member',
        no_index=False,
    )

    entry = _get_obj(app, 'PyTypeObject.tp_bases')
    assert entry == ('index', 'c.PyTypeObject.tp_bases', 'member')


@pytest.mark.sphinx('html', testroot='_blank')
def test_domain_c_parse_cvar(app):
    text = '.. c:var:: PyObject* PyClass_Type'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='var',
        domain='c',
        objtype='var',
        no_index=False,
    )

    entry = _get_obj(app, 'PyClass_Type')
    assert entry == ('index', 'c.PyClass_Type', 'member')


@pytest.mark.sphinx('html', testroot='_blank')
def test_domain_c_parse_no_index_entry(app):
    text = '.. c:function:: void f()\n.. c:function:: void g()\n   :no-index-entry:\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, desc, addnodes.index, desc))
    assert_node(
        doctree[0],
        addnodes.index,
        entries=[('single', 'f (C function)', 'c.f', '', None)],
    )
    assert_node(doctree[2], addnodes.index, entries=[])


@pytest.mark.sphinx(
    'html',
    testroot='_blank',
    confoverrides={
        'c_maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cfunction_signature_with_c_maximum_signature_line_length_equal(app):
    text = '.. c:function:: str hello(str name)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='c',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'name'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        desc_parameterlist,
        multi_line_parameter_list=False,
    )


@pytest.mark.sphinx(
    'html',
    testroot='_blank',
    confoverrides={
        'c_maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cfunction_signature_with_c_maximum_signature_line_length_force_single(app):
    text = '.. c:function:: str hello(str names)\n   :single-line-parameter-list:'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='c',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'names'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        desc_parameterlist,
        multi_line_parameter_list=False,
    )


@pytest.mark.sphinx(
    'html',
    testroot='_blank',
    confoverrides={
        'c_maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cfunction_signature_with_c_maximum_signature_line_length_break(app):
    text = '.. c:function:: str hello(str names)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='c',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'names'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        desc_parameterlist,
        multi_line_parameter_list=True,
    )


@pytest.mark.sphinx(
    'html',
    testroot='_blank',
    confoverrides={
        'maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cfunction_signature_with_maximum_signature_line_length_equal(app):
    text = '.. c:function:: str hello(str name)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='c',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'name'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        desc_parameterlist,
        multi_line_parameter_list=False,
    )


@pytest.mark.sphinx(
    'html',
    testroot='_blank',
    confoverrides={
        'maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cfunction_signature_with_maximum_signature_line_length_force_single(app):
    text = '.. c:function:: str hello(str names)\n   :single-line-parameter-list:'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='c',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'names'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        desc_parameterlist,
        multi_line_parameter_list=False,
    )


@pytest.mark.sphinx(
    'html',
    testroot='_blank',
    confoverrides={
        'maximum_signature_line_length': len('str hello(str name)'),
    },
)
def test_cfunction_signature_with_maximum_signature_line_length_break(app):
    text = '.. c:function:: str hello(str names)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_signature_line,
                                (
                                    pending_xref,
                                    desc_sig_space,
                                    [desc_name, [desc_sig_name, 'hello']],
                                    desc_parameterlist,
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='c',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'names'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        desc_parameterlist,
        multi_line_parameter_list=True,
    )


@pytest.mark.sphinx(
    'html',
    testroot='_blank',
    confoverrides={
        'c_maximum_signature_line_length': len('str hello(str name)'),
        'maximum_signature_line_length': 1,
    },
)
def test_c_maximum_signature_line_length_overrides_global(app):
    text = '.. c:function:: str hello(str name)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        ([
                            desc_signature_line,
                            (
                                pending_xref,
                                desc_sig_space,
                                [desc_name, [desc_sig_name, 'hello']],
                                desc_parameterlist,
                            ),
                        ]),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='c',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [pending_xref, [desc_sig_name, 'str']],
                desc_sig_space,
                [desc_sig_name, 'name'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 0, 3),
        desc_parameterlist,
        multi_line_parameter_list=False,
    )


@pytest.mark.sphinx('html', testroot='domain-c-c_maximum_signature_line_length')
def test_domain_c_c_maximum_signature_line_length_in_html(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf-8')
    expected = """\

<dl>
<dd>\
<span class="n"><span class="pre">str</span></span>\
<span class="w"> </span>\
<span class="n"><span class="pre">name</span></span>\
</dd>
</dl>

<span class="sig-paren">)</span>\
<a class="headerlink" href="#c.hello" title="Link to this definition">¶</a>\
<br />\
</dt>
"""
    assert expected in content


@pytest.mark.sphinx(
    'text',
    testroot='domain-c-c_maximum_signature_line_length',
)
def test_domain_c_c_maximum_signature_line_length_in_text(app):
    app.build()
    content = (app.outdir / 'index.txt').read_text(encoding='utf8')
    param_line_fmt = STDINDENT * ' ' + '{}\n'

    expected_parameter_list_hello = '(\n{})'.format(param_line_fmt.format('str name'))

    assert expected_parameter_list_hello in content
