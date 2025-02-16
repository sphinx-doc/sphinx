from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.domains.c._ast import (
    ASTAlignofExpr,
    ASTArray,
    ASTAssignmentExpr,
    ASTBinOpExpr,
    ASTBooleanLiteral,
    ASTBracedInitList,
    ASTCastExpr,
    ASTCharLiteral,
    ASTDeclaration,
    ASTDeclaratorNameBitField,
    ASTDeclaratorNameParam,
    ASTDeclaratorParen,
    ASTDeclaratorPtr,
    ASTDeclSpecs,
    ASTDeclSpecsSimple,
    ASTEnum,
    ASTEnumerator,
    ASTFallbackExpr,
    ASTFunctionParameter,
    ASTIdentifier,
    ASTIdExpression,
    ASTInitializer,
    ASTMacro,
    ASTMacroParameter,
    ASTNestedName,
    ASTNumberLiteral,
    ASTParameters,
    ASTParenExpr,
    ASTParenExprList,
    ASTPostfixArray,
    ASTPostfixCallExpr,
    ASTPostfixDec,
    ASTPostfixExpr,
    ASTPostfixInc,
    ASTPostfixMemberOfPointer,
    ASTSizeofExpr,
    ASTSizeofType,
    ASTStringLiteral,
    ASTStruct,
    ASTTrailingTypeSpecFundamental,
    ASTTrailingTypeSpecName,
    ASTType,
    ASTTypeWithInit,
    ASTUnaryOpExpr,
    ASTUnion,
)
from sphinx.domains.c._ids import (
    _expression_assignment_ops,
    _expression_bin_ops,
    _expression_unary_ops,
    _keywords,
    _simple_type_specifiers_re,
    _string_re,
)
from sphinx.util.cfamily import (
    ASTAttributeList,
    BaseParser,
    DefinitionError,
    UnsupportedMultiCharacterCharLiteral,
    binary_literal_re,
    char_literal_re,
    float_literal_re,
    float_literal_suffix_re,
    hex_literal_re,
    identifier_re,
    integer_literal_re,
    integers_literal_suffix_re,
    octal_literal_re,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any

    from sphinx.domains.c._ast import (
        ASTDeclarator,
        ASTExpression,
        ASTLiteral,
        ASTPostfixOp,
        ASTTrailingTypeSpec,
        DeclarationType,
    )


class DefinitionParser(BaseParser):
    @property
    def language(self) -> str:
        return 'C'

    @property
    def id_attributes(self) -> Sequence[str]:
        return self.config.c_id_attributes

    @property
    def paren_attributes(self) -> Sequence[str]:
        return self.config.c_paren_attributes

    def _parse_string(self) -> str | None:
        if self.current_char != '"':
            return None
        start_pos = self.pos
        self.pos += 1
        escape = False
        while True:
            if self.eof:
                self.fail('Unexpected end during inside string.')
            elif self.current_char == '"' and not escape:
                self.pos += 1
                break
            elif self.current_char == '\\':
                escape = True
            else:
                escape = False
            self.pos += 1
        return self.definition[start_pos : self.pos]

    def _parse_literal(self) -> ASTLiteral | None:
        # -> integer-literal
        #  | character-literal
        #  | floating-literal
        #  | string-literal
        #  | boolean-literal -> "false" | "true"
        self.skip_ws()
        if self.skip_word('true'):
            return ASTBooleanLiteral(True)
        if self.skip_word('false'):
            return ASTBooleanLiteral(False)
        pos = self.pos
        if self.match(float_literal_re):
            self.match(float_literal_suffix_re)
            return ASTNumberLiteral(self.definition[pos : self.pos])
        for regex in (
            binary_literal_re,
            hex_literal_re,
            integer_literal_re,
            octal_literal_re,
        ):
            if self.match(regex):
                self.match(integers_literal_suffix_re)
                return ASTNumberLiteral(self.definition[pos : self.pos])

        string = self._parse_string()
        if string is not None:
            return ASTStringLiteral(string)

        # character-literal
        if self.match(char_literal_re):
            prefix = self.last_match.group(1)  # may be None when no prefix
            data = self.last_match.group(2)
            try:
                return ASTCharLiteral(prefix, data)
            except UnicodeDecodeError as e:
                self.fail(
                    'Can not handle character literal. Internal error was: %s' % e
                )
            except UnsupportedMultiCharacterCharLiteral:
                self.fail(
                    'Can not handle character literal'
                    ' resulting in multiple decoded characters.'
                )
        return None

    def _parse_paren_expression(self) -> ASTExpression | None:
        # "(" expression ")"
        if self.current_char != '(':
            return None
        self.pos += 1
        res = self._parse_expression()
        self.skip_ws()
        if not self.skip_string(')'):
            self.fail("Expected ')' in end of parenthesized expression.")
        return ASTParenExpr(res)

    def _parse_primary_expression(self) -> ASTExpression | None:
        # literal
        # "(" expression ")"
        # id-expression -> we parse this with _parse_nested_name
        self.skip_ws()
        res: ASTExpression | None = self._parse_literal()
        if res is not None:
            return res
        res = self._parse_paren_expression()
        if res is not None:
            return res
        nn = self._parse_nested_name()
        if nn is not None:
            return ASTIdExpression(nn)
        return None

    def _parse_initializer_list(
        self, name: str, open: str, close: str
    ) -> tuple[list[ASTExpression] | None, bool | None]:
        # Parse open and close with the actual initializer-list in between
        # -> initializer-clause '...'[opt]
        #  | initializer-list ',' initializer-clause '...'[opt]
        # TODO: designators
        self.skip_ws()
        if not self.skip_string_and_ws(open):
            return None, None
        if self.skip_string(close):
            return [], False

        exprs = []
        trailing_comma = False
        while True:
            self.skip_ws()
            expr = self._parse_expression()
            self.skip_ws()
            exprs.append(expr)
            self.skip_ws()
            if self.skip_string(close):
                break
            if not self.skip_string_and_ws(','):
                self.fail(f"Error in {name}, expected ',' or '{close}'.")
            if self.current_char == close == '}':
                self.pos += 1
                trailing_comma = True
                break
        return exprs, trailing_comma

    def _parse_paren_expression_list(self) -> ASTParenExprList | None:
        # -> '(' expression-list ')'
        # though, we relax it to also allow empty parens
        # as it's needed in some cases
        #
        # expression-list
        # -> initializer-list
        exprs, trailing_comma = self._parse_initializer_list(
            'parenthesized expression-list', '(', ')'
        )
        if exprs is None:
            return None
        return ASTParenExprList(exprs)

    def _parse_braced_init_list(self) -> ASTBracedInitList | None:
        # -> '{' initializer-list ','[opt] '}'
        #  | '{' '}'
        exprs, trailing_comma = self._parse_initializer_list(
            'braced-init-list', '{', '}'
        )
        if exprs is None:
            return None
        return ASTBracedInitList(exprs, trailing_comma)

    def _parse_postfix_expression(self) -> ASTPostfixExpr:
        # -> primary
        #  | postfix "[" expression "]"
        #  | postfix "[" braced-init-list [opt] "]"
        #  | postfix "(" expression-list [opt] ")"
        #  | postfix "." id-expression  // taken care of in primary by nested name
        #  | postfix "->" id-expression
        #  | postfix "++"
        #  | postfix "--"

        prefix = self._parse_primary_expression()

        # and now parse postfixes
        post_fixes: list[ASTPostfixOp] = []
        while True:
            self.skip_ws()
            if self.skip_string_and_ws('['):
                expr = self._parse_expression()
                self.skip_ws()
                if not self.skip_string(']'):
                    self.fail("Expected ']' in end of postfix expression.")
                post_fixes.append(ASTPostfixArray(expr))
                continue
            if self.skip_string('->'):
                if self.skip_string('*'):
                    # don't steal the arrow
                    self.pos -= 3
                else:
                    name = self._parse_nested_name()
                    post_fixes.append(ASTPostfixMemberOfPointer(name))
                    continue
            if self.skip_string('++'):
                post_fixes.append(ASTPostfixInc())
                continue
            if self.skip_string('--'):
                post_fixes.append(ASTPostfixDec())
                continue
            lst = self._parse_paren_expression_list()
            if lst is not None:
                post_fixes.append(ASTPostfixCallExpr(lst))
                continue
            break
        return ASTPostfixExpr(prefix, post_fixes)

    def _parse_unary_expression(self) -> ASTExpression:
        # -> postfix
        #  | "++" cast
        #  | "--" cast
        #  | unary-operator cast -> (* | & | + | - | ! | ~) cast
        # The rest:
        #  | "sizeof" unary
        #  | "sizeof" "(" type-id ")"
        #  | "alignof" "(" type-id ")"
        self.skip_ws()
        for op in _expression_unary_ops:
            # TODO: hmm, should we be able to backtrack here?
            if op[0] in 'cn':
                res = self.skip_word(op)
            else:
                res = self.skip_string(op)
            if res:
                expr = self._parse_cast_expression()
                return ASTUnaryOpExpr(op, expr)
        if self.skip_word_and_ws('sizeof'):
            if self.skip_string_and_ws('('):
                typ = self._parse_type(named=False)
                self.skip_ws()
                if not self.skip_string(')'):
                    self.fail("Expecting ')' to end 'sizeof'.")
                return ASTSizeofType(typ)
            expr = self._parse_unary_expression()
            return ASTSizeofExpr(expr)
        if self.skip_word_and_ws('alignof'):
            if not self.skip_string_and_ws('('):
                self.fail("Expecting '(' after 'alignof'.")
            typ = self._parse_type(named=False)
            self.skip_ws()
            if not self.skip_string(')'):
                self.fail("Expecting ')' to end 'alignof'.")
            return ASTAlignofExpr(typ)
        return self._parse_postfix_expression()

    def _parse_cast_expression(self) -> ASTExpression:
        # -> unary  | "(" type-id ")" cast
        pos = self.pos
        self.skip_ws()
        if self.skip_string('('):
            try:
                typ = self._parse_type(False)
                if not self.skip_string(')'):
                    self.fail("Expected ')' in cast expression.")
                expr = self._parse_cast_expression()
                return ASTCastExpr(typ, expr)
            except DefinitionError as ex_cast:
                self.pos = pos
                try:
                    return self._parse_unary_expression()
                except DefinitionError as ex_unary:
                    errs = [
                        (ex_cast, 'If type cast expression'),
                        (ex_unary, 'If unary expression'),
                    ]
                    raise self._make_multi_error(
                        errs, 'Error in cast expression.'
                    ) from ex_unary
        else:
            return self._parse_unary_expression()

    def _parse_logical_or_expression(self) -> ASTExpression:
        # logical-or     = logical-and      ||
        # logical-and    = inclusive-or     &&
        # inclusive-or   = exclusive-or     |
        # exclusive-or   = and              ^
        # and            = equality         &
        # equality       = relational       ==, !=
        # relational     = shift            <, >, <=, >=
        # shift          = additive         <<, >>
        # additive       = multiplicative   +, -
        # multiplicative = pm               *, /, %
        # pm             = cast             .*, ->*
        def _parse_bin_op_expr(self: DefinitionParser, op_id: int) -> ASTExpression:
            if op_id + 1 == len(_expression_bin_ops):

                def parser() -> ASTExpression:
                    return self._parse_cast_expression()

            else:

                def parser() -> ASTExpression:
                    return _parse_bin_op_expr(self, op_id + 1)

            exprs = []
            ops = []
            exprs.append(parser())
            while True:
                self.skip_ws()
                pos = self.pos
                one_more = False
                for op in _expression_bin_ops[op_id]:
                    if op[0] in 'abcnox':
                        if not self.skip_word(op):
                            continue
                    else:
                        if not self.skip_string(op):
                            continue
                    if op == self.current_char == '&':
                        # don't split the && 'token'
                        self.pos -= 1
                        # and btw. && has lower precedence, so we are done
                        break
                    try:
                        expr = parser()
                        exprs.append(expr)
                        ops.append(op)
                        one_more = True
                        break
                    except DefinitionError:
                        self.pos = pos
                if not one_more:
                    break
            return ASTBinOpExpr(exprs, ops)  # type: ignore[return-value]

        return _parse_bin_op_expr(self, 0)

    def _parse_conditional_expression_tail(
        self, or_expr_head: Any
    ) -> ASTExpression | None:
        # -> "?" expression ":" assignment-expression
        return None

    def _parse_assignment_expression(self) -> ASTExpression:
        # -> conditional-expression
        #  | logical-or-expression assignment-operator initializer-clause
        # -> conditional-expression ->
        #     logical-or-expression
        #   | logical-or-expression "?" expression ":" assignment-expression
        #   | logical-or-expression assignment-operator initializer-clause
        exprs = []
        ops = []
        or_expr = self._parse_logical_or_expression()
        exprs.append(or_expr)
        # TODO: handle ternary with _parse_conditional_expression_tail
        while True:
            one_more = False
            self.skip_ws()
            for op in _expression_assignment_ops:
                if op[0] in 'abcnox':
                    if not self.skip_word(op):
                        continue
                else:
                    if not self.skip_string(op):
                        continue
                expr = self._parse_logical_or_expression()
                exprs.append(expr)
                ops.append(op)
                one_more = True
            if not one_more:
                break
        return ASTAssignmentExpr(exprs, ops)

    def _parse_constant_expression(self) -> ASTExpression:
        # -> conditional-expression
        or_expr = self._parse_logical_or_expression()
        # TODO: use _parse_conditional_expression_tail
        return or_expr

    def _parse_expression(self) -> ASTExpression:
        # -> assignment-expression
        #  | expression "," assignment-expression
        # TODO: actually parse the second production
        return self._parse_assignment_expression()

    def _parse_expression_fallback(
        self, end: list[str], parser: Callable[[], ASTExpression], allow: bool = True
    ) -> ASTExpression:
        # Stupidly "parse" an expression.
        # 'end' should be a list of characters which ends the expression.

        # first try to use the provided parser
        prev_pos = self.pos
        try:
            return parser()
        except DefinitionError as e:
            # some places (e.g., template parameters) we really don't want to use fallback,
            # and for testing we may want to globally disable it
            if not allow or not self.allowFallbackExpressionParsing:
                raise
            self.warn(
                'Parsing of expression failed. Using fallback parser.'
                ' Error was:\n%s' % e
            )
            self.pos = prev_pos
        # and then the fallback scanning
        assert end is not None
        self.skip_ws()
        start_pos = self.pos
        if self.match(_string_re):
            value = self.matched_text
        else:
            # TODO: add handling of more bracket-like things, and quote handling
            brackets = {'(': ')', '{': '}', '[': ']'}
            symbols: list[str] = []
            while not self.eof:
                if len(symbols) == 0 and self.current_char in end:
                    break
                if self.current_char in brackets:
                    symbols.append(brackets[self.current_char])
                elif len(symbols) > 0 and self.current_char == symbols[-1]:
                    symbols.pop()
                self.pos += 1
            if len(end) > 0 and self.eof:
                self.fail(
                    'Could not find end of expression starting at %d.' % start_pos
                )
            value = self.definition[start_pos : self.pos].strip()
        return ASTFallbackExpr(value.strip())

    def _parse_nested_name(self) -> ASTNestedName:
        names: list[Any] = []

        self.skip_ws()
        rooted = False
        if self.skip_string('.'):
            rooted = True
        while 1:
            self.skip_ws()
            if not self.match(identifier_re):
                self.fail('Expected identifier in nested name.')
            identifier = self.matched_text
            # make sure there isn't a keyword
            if identifier in _keywords:
                self.fail(
                    'Expected identifier in nested name, got keyword: %s' % identifier
                )
            if self.matched_text in self.config.c_extra_keywords:
                msg = (
                    'Expected identifier, got user-defined keyword: %s.'
                    ' Remove it from c_extra_keywords to allow it as identifier.\n'
                    'Currently c_extra_keywords is %s.'
                )
                self.fail(msg % (self.matched_text, str(self.config.c_extra_keywords)))
            ident = ASTIdentifier(identifier)
            names.append(ident)

            self.skip_ws()
            if not self.skip_string('.'):
                break
        return ASTNestedName(names, rooted)

    def _parse_simple_type_specifier(self) -> str | None:
        if self.match(_simple_type_specifiers_re):
            return self.matched_text
        for t in ('bool', 'complex', 'imaginary'):
            if t in self.config.c_extra_keywords:
                if self.skip_word(t):
                    return t
        return None

    def _parse_simple_type_specifiers(self) -> ASTTrailingTypeSpecFundamental | None:
        names: list[str] = []

        self.skip_ws()
        while True:
            t = self._parse_simple_type_specifier()
            if t is None:
                break
            names.append(t)
            self.skip_ws()
        if len(names) == 0:
            return None
        return ASTTrailingTypeSpecFundamental(names)

    def _parse_trailing_type_spec(self) -> ASTTrailingTypeSpec:
        # fundamental types, https://en.cppreference.com/w/c/language/type
        # and extensions
        self.skip_ws()
        res = self._parse_simple_type_specifiers()
        if res is not None:
            return res

        # prefixed
        prefix = None
        self.skip_ws()
        for k in ('struct', 'enum', 'union'):
            if self.skip_word_and_ws(k):
                prefix = k
                break

        nested_name = self._parse_nested_name()
        return ASTTrailingTypeSpecName(prefix, nested_name)

    def _parse_parameters(self, param_mode: str) -> ASTParameters | None:
        self.skip_ws()
        if not self.skip_string('('):
            if param_mode == 'function':
                self.fail('Expecting "(" in parameters.')
            else:
                return None

        args = []
        self.skip_ws()
        if not self.skip_string(')'):
            while 1:
                self.skip_ws()
                if self.skip_string('...'):
                    args.append(ASTFunctionParameter(None, True))
                    self.skip_ws()
                    if not self.skip_string(')'):
                        self.fail('Expected ")" after "..." in parameters.')
                    break
                # note: it seems that function arguments can always be named,
                # even in function pointers and similar.
                arg = self._parse_type_with_init(outer=None, named='single')
                # TODO: parse default parameters # TODO: didn't we just do that?
                args.append(ASTFunctionParameter(arg))

                self.skip_ws()
                if self.skip_string(','):
                    continue
                if self.skip_string(')'):
                    break
                self.fail(
                    f'Expecting "," or ")" in parameters, got "{self.current_char}".'
                )

        attrs = self._parse_attribute_list()
        return ASTParameters(args, attrs)

    def _parse_decl_specs_simple(
        self, outer: str | None, typed: bool
    ) -> ASTDeclSpecsSimple:
        """Just parse the simple ones."""
        storage = None
        thread_local = None
        inline = None
        restrict = None
        volatile = None
        const = None
        attrs = []
        while 1:  # accept any permutation of a subset of some decl-specs
            self.skip_ws()
            if not storage:
                if outer == 'member':
                    if self.skip_word('auto'):
                        storage = 'auto'
                        continue
                    if self.skip_word('register'):
                        storage = 'register'
                        continue
                if outer in {'member', 'function'}:
                    if self.skip_word('static'):
                        storage = 'static'
                        continue
                    if self.skip_word('extern'):
                        storage = 'extern'
                        continue
            if outer == 'member' and not thread_local:
                if self.skip_word('thread_local'):
                    thread_local = 'thread_local'
                    continue
                if self.skip_word('_Thread_local'):
                    thread_local = '_Thread_local'
                    continue
            if outer == 'function' and not inline:
                inline = self.skip_word('inline')
                if inline:
                    continue

            if not restrict and typed:
                restrict = self.skip_word('restrict')
                if restrict:
                    continue
            if not volatile and typed:
                volatile = self.skip_word('volatile')
                if volatile:
                    continue
            if not const and typed:
                const = self.skip_word('const')
                if const:
                    continue
            attr = self._parse_attribute()
            if attr:
                attrs.append(attr)
                continue
            break
        return ASTDeclSpecsSimple(
            storage,
            thread_local,
            inline,
            restrict,
            volatile,
            const,
            ASTAttributeList(attrs),
        )

    def _parse_decl_specs(self, outer: str | None, typed: bool = True) -> ASTDeclSpecs:
        if outer:
            if outer not in {'type', 'member', 'function'}:
                raise Exception('Internal error, unknown outer "%s".' % outer)
        left_specs = self._parse_decl_specs_simple(outer, typed)
        right_specs = None

        if typed:
            trailing = self._parse_trailing_type_spec()
            right_specs = self._parse_decl_specs_simple(outer, typed)
        else:
            trailing = None
        return ASTDeclSpecs(outer, left_specs, right_specs, trailing)

    def _parse_declarator_name_suffix(
        self, named: bool | str, param_mode: str, typed: bool
    ) -> ASTDeclarator:
        assert named in {True, False, 'single'}
        # now we should parse the name, and then suffixes
        if named == 'single':
            if self.match(identifier_re):
                if self.matched_text in _keywords:
                    self.fail(
                        'Expected identifier, got keyword: %s' % self.matched_text
                    )
                if self.matched_text in self.config.c_extra_keywords:
                    msg = (
                        'Expected identifier, got user-defined keyword: %s. '
                        'Remove it from c_extra_keywords to allow it as identifier.\n'
                        'Currently c_extra_keywords is %s.'
                    )
                    self.fail(
                        msg % (self.matched_text, str(self.config.c_extra_keywords))
                    )
                identifier = ASTIdentifier(self.matched_text)
                decl_id = ASTNestedName([identifier], rooted=False)
            else:
                decl_id = None
        elif named:
            decl_id = self._parse_nested_name()
        else:
            decl_id = None
        array_ops = []
        while 1:
            self.skip_ws()
            if typed and self.skip_string('['):
                self.skip_ws()
                static = False
                const = False
                volatile = False
                restrict = False
                while True:
                    if not static:
                        if self.skip_word_and_ws('static'):
                            static = True
                            continue
                    if not const:
                        if self.skip_word_and_ws('const'):
                            const = True
                            continue
                    if not volatile:
                        if self.skip_word_and_ws('volatile'):
                            volatile = True
                            continue
                    if not restrict:
                        if self.skip_word_and_ws('restrict'):
                            restrict = True
                            continue
                    break
                vla = False if static else self.skip_string_and_ws('*')
                if vla:
                    if not self.skip_string(']'):
                        self.fail("Expected ']' in end of array operator.")
                    size = None
                else:
                    if self.skip_string(']'):
                        size = None
                    else:

                        def parser() -> ASTExpression:
                            return self._parse_expression()

                        size = self._parse_expression_fallback([']'], parser)
                        self.skip_ws()
                        if not self.skip_string(']'):
                            self.fail("Expected ']' in end of array operator.")
                array_ops.append(ASTArray(static, const, volatile, restrict, vla, size))
            else:
                break
        param = self._parse_parameters(param_mode)
        if param is None and len(array_ops) == 0:
            # perhaps a bit-field
            if named and param_mode == 'type' and typed:
                self.skip_ws()
                if self.skip_string(':'):
                    size = self._parse_constant_expression()
                    return ASTDeclaratorNameBitField(declId=decl_id, size=size)
        return ASTDeclaratorNameParam(declId=decl_id, arrayOps=array_ops, param=param)

    def _parse_declarator(
        self, named: bool | str, param_mode: str, typed: bool = True
    ) -> ASTDeclarator:
        # 'typed' here means 'parse return type stuff'
        if param_mode not in {'type', 'function'}:
            raise Exception("Internal error, unknown param_mode '%s'." % param_mode)
        prev_errors = []
        self.skip_ws()
        if typed and self.skip_string('*'):
            self.skip_ws()
            restrict = False
            volatile = False
            const = False
            attrs = []
            while 1:
                if not restrict:
                    restrict = self.skip_word_and_ws('restrict')
                    if restrict:
                        continue
                if not volatile:
                    volatile = self.skip_word_and_ws('volatile')
                    if volatile:
                        continue
                if not const:
                    const = self.skip_word_and_ws('const')
                    if const:
                        continue
                attr = self._parse_attribute()
                if attr is not None:
                    attrs.append(attr)
                    continue
                break
            next = self._parse_declarator(named, param_mode, typed)
            return ASTDeclaratorPtr(
                next=next,
                restrict=restrict,
                volatile=volatile,
                const=const,
                attrs=ASTAttributeList(attrs),
            )
        if typed and self.current_char == '(':  # note: peeking, not skipping
            # maybe this is the beginning of params, try that first,
            # otherwise assume it's noptr->declarator > ( ptr-declarator )
            pos = self.pos
            try:
                # assume this is params
                res = self._parse_declarator_name_suffix(named, param_mode, typed)
                return res
            except DefinitionError as ex_param_qual:
                msg = 'If declarator-id with parameters'
                if param_mode == 'function':
                    msg += " (e.g., 'void f(int arg)')"
                prev_errors.append((ex_param_qual, msg))
                self.pos = pos
                try:
                    assert self.current_char == '('
                    self.skip_string('(')
                    # TODO: hmm, if there is a name, it must be in inner, right?
                    # TODO: hmm, if there must be parameters, they must b
                    # inside, right?
                    inner = self._parse_declarator(named, param_mode, typed)
                    if not self.skip_string(')'):
                        self.fail('Expected \')\' in "( ptr-declarator )"')
                    next = self._parse_declarator(
                        named=False, param_mode='type', typed=typed
                    )
                    return ASTDeclaratorParen(inner=inner, next=next)
                except DefinitionError as ex_no_ptr_paren:
                    self.pos = pos
                    msg = 'If parenthesis in noptr-declarator'
                    if param_mode == 'function':
                        msg += " (e.g., 'void (*f(int arg))(double)')"
                    prev_errors.append((ex_no_ptr_paren, msg))
                    header = 'Error in declarator'
                    raise self._make_multi_error(
                        prev_errors, header
                    ) from ex_no_ptr_paren
        pos = self.pos
        try:
            return self._parse_declarator_name_suffix(named, param_mode, typed)
        except DefinitionError as e:
            self.pos = pos
            prev_errors.append((e, 'If declarator-id'))
            header = 'Error in declarator or parameters'
            raise self._make_multi_error(prev_errors, header) from e

    def _parse_initializer(
        self, outer: str | None = None, allow_fallback: bool = True
    ) -> ASTInitializer | None:
        self.skip_ws()
        if outer == 'member' and False:  # NoQA: SIM223,TD005  # TODO
            braced_init = self._parse_braced_init_list()
            if braced_init is not None:
                return ASTInitializer(braced_init, hasAssign=False)

        if not self.skip_string('='):
            return None

        braced_init = self._parse_braced_init_list()
        if braced_init is not None:
            return ASTInitializer(braced_init)

        if outer == 'member':
            fallback_end: list[str] = []
        elif outer is None:  # function parameter
            fallback_end = [',', ')']
        else:
            self.fail(
                "Internal error, initializer for outer '%s' not implemented." % outer
            )

        def parser() -> ASTExpression:
            return self._parse_assignment_expression()

        value = self._parse_expression_fallback(
            fallback_end, parser, allow=allow_fallback
        )
        return ASTInitializer(value)

    def _parse_type(self, named: bool | str, outer: str | None = None) -> ASTType:
        """named=False|'single'|True: 'single' is e.g., for function objects which
        doesn't need to name the arguments, but otherwise is a single name
        """
        if outer:  # always named
            if outer not in {'type', 'member', 'function'}:
                raise Exception('Internal error, unknown outer "%s".' % outer)
            assert named

        if outer == 'type':
            # We allow type objects to just be a name.
            prev_errors = []
            start_pos = self.pos
            # first try without the type
            try:
                decl_specs = self._parse_decl_specs(outer=outer, typed=False)
                decl = self._parse_declarator(named=True, param_mode=outer, typed=False)
                self.assert_end(allowSemicolon=True)
            except DefinitionError as ex_untyped:
                desc = 'If just a name'
                prev_errors.append((ex_untyped, desc))
                self.pos = start_pos
                try:
                    decl_specs = self._parse_decl_specs(outer=outer)
                    decl = self._parse_declarator(named=True, param_mode=outer)
                except DefinitionError as ex_typed:
                    self.pos = start_pos
                    desc = 'If typedef-like declaration'
                    prev_errors.append((ex_typed, desc))
                    # Retain the else branch for easier debugging.
                    # TODO: it would be nice to save the previous stacktrace
                    #       and output it here.
                    if True:
                        header = 'Type must be either just a name or a '
                        header += 'typedef-like declaration.'
                        raise self._make_multi_error(prev_errors, header) from ex_typed
                    else:
                        # For testing purposes.
                        # do it again to get the proper traceback (how do you
                        # reliably save a traceback when an exception is
                        # constructed?)
                        self.pos = start_pos
                        typed = True
                        decl_specs = self._parse_decl_specs(outer=outer, typed=typed)
                        decl = self._parse_declarator(
                            named=True, param_mode=outer, typed=typed
                        )
        elif outer == 'function':
            decl_specs = self._parse_decl_specs(outer=outer)
            decl = self._parse_declarator(named=True, param_mode=outer)
        else:
            param_mode = 'type'
            if outer == 'member':  # i.e., member
                named = True
            decl_specs = self._parse_decl_specs(outer=outer)
            decl = self._parse_declarator(named=named, param_mode=param_mode)
        return ASTType(decl_specs, decl)

    def _parse_type_with_init(
        self, named: bool | str, outer: str | None
    ) -> ASTTypeWithInit:
        if outer:
            assert outer in {'type', 'member', 'function'}
        type = self._parse_type(outer=outer, named=named)
        init = self._parse_initializer(outer=outer)
        return ASTTypeWithInit(type, init)

    def _parse_macro(self) -> ASTMacro:
        self.skip_ws()
        ident = self._parse_nested_name()
        if ident is None:
            self.fail('Expected identifier in macro definition.')
        self.skip_ws()
        if not self.skip_string_and_ws('('):
            return ASTMacro(ident, None)
        if self.skip_string(')'):
            return ASTMacro(ident, [])
        args = []
        while 1:
            self.skip_ws()
            if self.skip_string('...'):
                args.append(ASTMacroParameter(None, True))
                self.skip_ws()
                if not self.skip_string(')'):
                    self.fail('Expected ")" after "..." in macro parameters.')
                break
            if not self.match(identifier_re):
                self.fail('Expected identifier in macro parameters.')
            nn = ASTNestedName([ASTIdentifier(self.matched_text)], rooted=False)
            # Allow named variadic args:
            # https://gcc.gnu.org/onlinedocs/cpp/Variadic-Macros.html
            self.skip_ws()
            if self.skip_string_and_ws('...'):
                args.append(ASTMacroParameter(nn, False, True))
                self.skip_ws()
                if not self.skip_string(')'):
                    self.fail('Expected ")" after "..." in macro parameters.')
                break
            args.append(ASTMacroParameter(nn))
            if self.skip_string_and_ws(','):
                continue
            if self.skip_string_and_ws(')'):
                break
            self.fail("Expected identifier, ')', or ',' in macro parameter list.")
        return ASTMacro(ident, args)

    def _parse_struct(self) -> ASTStruct:
        name = self._parse_nested_name()
        return ASTStruct(name)

    def _parse_union(self) -> ASTUnion:
        name = self._parse_nested_name()
        return ASTUnion(name)

    def _parse_enum(self) -> ASTEnum:
        name = self._parse_nested_name()
        return ASTEnum(name)

    def _parse_enumerator(self) -> ASTEnumerator:
        name = self._parse_nested_name()
        attrs = self._parse_attribute_list()
        self.skip_ws()
        init = None
        if self.skip_string('='):
            self.skip_ws()

            def parser() -> ASTExpression:
                return self._parse_constant_expression()

            init_val = self._parse_expression_fallback([], parser)
            init = ASTInitializer(init_val)
        return ASTEnumerator(name, init, attrs)

    def parse_declaration(self, objectType: str, directiveType: str) -> ASTDeclaration:
        object_type = objectType
        directive_type = directiveType
        if object_type not in {
            'function',
            'member',
            'macro',
            'struct',
            'union',
            'enum',
            'enumerator',
            'type',
        }:
            raise Exception('Internal error, unknown objectType "%s".' % object_type)
        if directive_type not in {
            'function',
            'member',
            'var',
            'macro',
            'struct',
            'union',
            'enum',
            'enumerator',
            'type',
        }:
            raise Exception(
                'Internal error, unknown directiveType "%s".' % directive_type
            )

        declaration: DeclarationType | None = None
        if object_type == 'member':
            declaration = self._parse_type_with_init(named=True, outer='member')
        elif object_type == 'function':
            declaration = self._parse_type(named=True, outer='function')
        elif object_type == 'macro':
            declaration = self._parse_macro()
        elif object_type == 'struct':
            declaration = self._parse_struct()
        elif object_type == 'union':
            declaration = self._parse_union()
        elif object_type == 'enum':
            declaration = self._parse_enum()
        elif object_type == 'enumerator':
            declaration = self._parse_enumerator()
        elif object_type == 'type':
            declaration = self._parse_type(named=True, outer='type')
        else:
            raise AssertionError
        if object_type != 'macro':
            self.skip_ws()
            semicolon = self.skip_string(';')
        else:
            semicolon = False
        return ASTDeclaration(object_type, directive_type, declaration, semicolon)

    def parse_namespace_object(self) -> ASTNestedName:
        return self._parse_nested_name()

    def parse_xref_object(self) -> ASTNestedName:
        name = self._parse_nested_name()
        # if there are '()' left, just skip them
        self.skip_ws()
        self.skip_string('()')
        self.assert_end()
        return name

    def parse_expression(self) -> ASTExpression | ASTType:
        pos = self.pos
        res: ASTExpression | ASTType | None = None
        try:
            res = self._parse_expression()
            self.skip_ws()
            self.assert_end()
        except DefinitionError as ex_expr:
            self.pos = pos
            try:
                res = self._parse_type(False)
                self.skip_ws()
                self.assert_end()
            except DefinitionError as ex_type:
                header = 'Error when parsing (type) expression.'
                errs = [
                    (ex_expr, 'If expression'),
                    (ex_type, 'If type'),
                ]
                raise self._make_multi_error(errs, header) from ex_type
        return res
