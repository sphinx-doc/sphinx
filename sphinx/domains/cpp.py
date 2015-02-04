# -*- coding: utf-8 -*-
"""
    sphinx.domains.cpp
    ~~~~~~~~~~~~~~~~~~

    The C++ language domain.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

"""
    Important note on ids:
    Multiple id generation schemes are used due to backwards compatibility.
    - v1: 1.2.3 <= version < 1.3
          The style used before the rewrite.
          It is not the actual old code, but a replication of the behaviour.
    - v2: 1.3 <= version < now
          Standardised mangling scheme from
          http://mentorembedded.github.io/cxx-abi/abi.html#mangling
          though not completely implemented.
    All versions are generated and attached to elements. The newest is used for
    the index. All of the versions should work as permalinks.

    See http://www.nongnu.org/hcb/ for the grammar.

    common grammar things:
           simple-declaration
        -> attribute-specifier-seq[opt] decl-specifier-seq[opt]
           init-declarator-list[opt] ;
        # Drop the semi-colon. For now: drop the attributes (TODO).
        # Use at most 1 init-declerator.
        -> decl-specifier-seq init-declerator
        -> decl-specifier-seq declerator initializer

        decl-specifier ->
              storage-class-specifier -> "static" (only for member_object and
              function_object)
            | type-specifier -> trailing-type-specifier
            | function-specifier -> "inline" | "virtual" | "explicit" (only
              for function_object)
            | "friend" (only for function_object)
            | "constexpr" (only for member_object and function_object)
        trailing-type-specifier ->
              simple-type-specifier
            | elaborated-type-specifier
            | typename-specifier
            | cv-qualifier -> "const" | "volatile"
        stricter grammar for decl-specifier-seq (with everything, each object
        uses a subset):
            visibility storage-class-specifier function-specifier "friend"
            "constexpr" "volatile" "const" trailing-type-specifier
            # where trailing-type-specifier can no be cv-qualifier
        # Inside e.g., template paramters a strict subset is used
        # (see type-specifier-seq)
        trailing-type-specifier ->
              simple-type-specifier ->
                ::[opt] nested-name-specifier[opt] type-name
              | ::[opt] nested-name-specifier "template" simple-template-id
              | "char" | "bool" | ect.
              | decltype-specifier
            | elaborated-type-specifier ->
                class-key attribute-specifier-seq[opt] ::[opt]
                nested-name-specifier[opt] identifier
              | class-key ::[opt] nested-name-specifier[opt] template[opt]
                simple-template-id
              | "enum" ::[opt] nested-name-specifier[opt] identifier
            | typename-specifier ->
                "typename" ::[opt] nested-name-specifier identifier
              | "typename" ::[opt] nested-name-specifier template[opt]
                simple-template-id
        class-key -> "class" | "struct" | "union"
        type-name ->* identifier | simple-template-id
        # ignoring attributes and decltype, and then some left-factoring
        trailing-type-specifier ->
            rest-of-trailing
            ("class" | "struct" | "union" | "typename") rest-of-trailing
            build-in -> "char" | "bool" | ect.
            decltype-specifier
        rest-of-trailing -> (with some simplification)
            "::"[opt] list-of-elements-separated-by-::
        element ->
            "template"[opt] identifier ("<" template-argument-list ">")[opt]
        template-argument-list ->
              template-argument "..."[opt]
            | template-argument-list "," template-argument "..."[opt]
        template-argument ->
              constant-expression
            | type-specifier-seq abstract-declerator
            | id-expression


        declerator ->
              ptr-declerator
            | noptr-declarator parameters-and-qualifiers trailing-return-type
              (TODO: for now we don't support it)
        ptr-declerator ->
              noptr-declerator
            | ptr-operator ptr-declarator
        noptr-declerator ->
              declarator-id attribute-specifier-seq[opt] ->
                    "..."[opt] id-expression
                  | rest-of-trailing
            | noptr-declerator parameters-and-qualifiers
            | noptr-declarator "[" constant-expression[opt] "]"
              attribute-specifier-seq[opt]
            | "(" ptr-declarator ")"  # TODO: not implemented yet
        # function_object must use a parameters-and-qualifiers, the others may
        # use it (e.g., function poitners)
        parameters-and-qualifiers ->
            "(" parameter-clause ")" attribute-specifier-seq[opt]
            cv-qualifier-seq[opt] ref-qualifier[opt]
            exception-specification[opt]
        ref-qualifier -> "&" | "&&"
        exception-specification ->
            "noexcept" ("(" constant-expression ")")[opt]
            "throw" ("(" type-id-list ")")[opt]
        # TODO: we don't implement attributes
        # member functions can have initializers, but we fold them into here
        memberFunctionInit -> "=" "0"
        # (note: only "0" is allowed as the value, according to the standard,
        # right?)


    We additionally add the possibility for specifying the visibility as the
    first thing.

    type_object:
        goal:
            either a single type (e.g., "MyClass:Something_T" or a typedef-like
            thing (e.g. "Something Something_T" or "int I_arr[]"
        grammar, single type: based on a type in a function parameter, but
        without a name:
               parameter-declaration
            -> attribute-specifier-seq[opt] decl-specifier-seq
               abstract-declarator[opt]
            # Drop the attributes
            -> decl-specifier-seq abstract-declarator[opt]
        grammar, typedef-like: no initilizer
            decl-specifier-seq declerator


    member_object:
        goal: as a type_object which must have a declerator, and optionally
        with a initializer
        grammar:
            decl-specifier-seq declerator initializer

    function_object:
        goal: a function declaration, TODO: what about templates? for now: skip
        grammar: no initializer
           decl-specifier-seq declerator
"""

import re
from copy import deepcopy

from six import iteritems, text_type
from docutils import nodes

from sphinx import addnodes
from sphinx.roles import XRefRole
from sphinx.locale import l_, _
from sphinx.domains import Domain, ObjType
from sphinx.directives import ObjectDescription
from sphinx.util.nodes import make_refnode
from sphinx.util.compat import Directive
from sphinx.util.pycompat import UnicodeMixin
from sphinx.util.docfields import Field, GroupedField


_identifier_re = re.compile(r'(~?\b[a-zA-Z_][a-zA-Z0-9_]*)\b')
_whitespace_re = re.compile(r'\s+(?u)')
_string_re = re.compile(r"[LuU8]?('([^'\\]*(?:\\.[^'\\]*)*)'"
                        r'|"([^"\\]*(?:\\.[^"\\]*)*)")', re.S)
_visibility_re = re.compile(r'\b(public|private|protected)\b')
_array_def_re = re.compile(r'\[\s*([^\]]+?)?\s*\]')
_template_arg_re = re.compile(r'(%s)|([^,>]+)' % _string_re.pattern, re.S)
_operator_re = re.compile(r'''(?x)
        \[\s*\]
    |   \(\s*\)
    |   \+\+ | --
    |   ->\*? | \,
    |   (<<|>>)=? | && | \|\|
    |   [!<>=/*%+|&^~-]=?
''')

#-------------------------------------------------------------------------------
# Id v1 constants
#-------------------------------------------------------------------------------

_id_prefix_v1 = '_CPP'
_id_fundamental_v1 = {
    'char': 'c',
    'signed char': 'c',
    'unsigned char': 'C',
    'int': 'i',
    'signed int': 'i',
    'unsigned int': 'U',
    'long': 'l',
    'signed long': 'l',
    'unsigned long': 'L',
    'bool': 'b'
}
_id_shorthands_v1 = {
    'std::string': 'ss',
    'std::ostream': 'os',
    'std::istream': 'is',
    'std::iostream': 'ios',
    'std::vector': 'v',
    'std::map': 'm'
}
_id_operator_v1 = {
    'new': 'new-operator',
    'new[]': 'new-array-operator',
    'delete': 'delete-operator',
    'delete[]': 'delete-array-operator',
    # the arguments will make the difference between unary and binary
    # '+(unary)' : 'ps',
    # '-(unary)' : 'ng',
    # '&(unary)' : 'ad',
    # '*(unary)' : 'de',
    '~': 'inv-operator',
    '+': 'add-operator',
    '-': 'sub-operator',
    '*': 'mul-operator',
    '/': 'div-operator',
    '%': 'mod-operator',
    '&': 'and-operator',
    '|': 'or-operator',
    '^': 'xor-operator',
    '=': 'assign-operator',
    '+=': 'add-assign-operator',
    '-=': 'sub-assign-operator',
    '*=': 'mul-assign-operator',
    '/=': 'div-assign-operator',
    '%=': 'mod-assign-operator',
    '&=': 'and-assign-operator',
    '|=': 'or-assign-operator',
    '^=': 'xor-assign-operator',
    '<<': 'lshift-operator',
    '>>': 'rshift-operator',
    '<<=': 'lshift-assign-operator',
    '>>=': 'rshift-assign-operator',
    '==': 'eq-operator',
    '!=': 'neq-operator',
    '<': 'lt-operator',
    '>': 'gt-operator',
    '<=': 'lte-operator',
    '>=': 'gte-operator',
    '!': 'not-operator',
    '&&': 'sand-operator',
    '||': 'sor-operator',
    '++': 'inc-operator',
    '--': 'dec-operator',
    ',': 'comma-operator',
    '->*': 'pointer-by-pointer-operator',
    '->': 'pointer-operator',
    '()': 'call-operator',
    '[]': 'subscript-operator'
}

#-------------------------------------------------------------------------------
# Id v2 constants
#-------------------------------------------------------------------------------

_id_prefix_v2 = '_CPP'
_id_fundamental_v2 = {
    # not all of these are actually parsed as fundamental types, TODO: do that
    'void': 'v',
    'bool': 'b',
    'char': 'c',
    'signed char': 'a',
    'unsigned char': 'h',
    'wchar_t': 'w',
    'char32_t': 'Di',
    'char16_t': 'Ds',
    'short': 's',
    'short int': 's',
    'signed short': 's',
    'signed short int': 's',
    'unsigned short': 't',
    'unsigned short int': 't',
    'int': 'i',
    'signed': 'i',
    'signed int': 'i',
    'unsigned': 'j',
    'unsigned int': 'j',
    'long': 'l',
    'long int': 'l',
    'signed long': 'l',
    'signed long int': 'l',
    'unsigned long': 'm',
    'unsigned long int': 'm',
    'long long': 'x',
    'long long int': 'x',
    'signed long long': 'x',
    'signed long long int': 'x',
    'unsigned long long': 'y',
    'unsigned long long int': 'y',
    'float': 'f',
    'double': 'd',
    'long double': 'e',
    'auto': 'Da',
    'decltype(auto)': 'Dc',
    'std::nullptr_t': 'Dn'
}
_id_operator_v2 = {
    'new': 'nw',
    'new[]': 'na',
    'delete': 'dl',
    'delete[]': 'da',
    # the arguments will make the difference between unary and binary
    # '+(unary)' : 'ps',
    # '-(unary)' : 'ng',
    # '&(unary)' : 'ad',
    # '*(unary)' : 'de',
    '~': 'co',
    '+': 'pl',
    '-': 'mi',
    '*': 'ml',
    '/': 'dv',
    '%': 'rm',
    '&': 'an',
    '|': 'or',
    '^': 'eo',
    '=': 'aS',
    '+=': 'pL',
    '-=': 'mI',
    '*=': 'mL',
    '/=': 'dV',
    '%=': 'rM',
    '&=': 'aN',
    '|=': 'oR',
    '^=': 'eO',
    '<<': 'ls',
    '>>': 'rs',
    '<<=': 'lS',
    '>>=': 'rS',
    '==': 'eq',
    '!=': 'ne',
    '<': 'lt',
    '>': 'gt',
    '<=': 'le',
    '>=': 'ge',
    '!': 'nt',
    '&&': 'aa',
    '||': 'oo',
    '++': 'pp',
    '--': 'mm',
    ',': 'cm',
    '->*': 'pm',
    '->': 'pt',
    '()': 'cl',
    '[]': 'ix'
}


class DefinitionError(UnicodeMixin, Exception):
    def __init__(self, description):
        self.description = description

    def __unicode__(self):
        return self.description


class ASTBase(UnicodeMixin):
    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        try:
            for key, value in iteritems(self.__dict__):
                if value != getattr(other, key):
                    return False
        except AttributeError:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None

    def clone(self):
        """Clone a definition expression node."""
        return deepcopy(self)

    def get_id_v1(self):
        """Return the v1 id for the node."""
        raise NotImplementedError(repr(self))

    def get_id_v2(self):
        """Return the v2 id for the node."""
        raise NotImplementedError(repr(self))

    def get_name(self):
        """Return the name.

        Returns either `None` or a node with a name you might call
        :meth:`split_owner` on.
        """
        raise NotImplementedError(repr(self))

    def prefix_nested_name(self, prefix):
        """Prefix a name node (a node returned by :meth:`get_name`)."""
        raise NotImplementedError(repr(self))

    def __unicode__(self):
        raise NotImplementedError(repr(self))

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self)


def _verify_description_mode(mode):
    if mode not in ('lastIsName', 'noneIsName', 'markType', 'param'):
        raise Exception("Description mode '%s' is invalid." % mode)


class ASTOperatorBuildIn(ASTBase):
    def __init__(self, op):
        self.op = op

    def get_id_v1(self):
        if self.op not in _id_operator_v1:
            raise Exception('Internal error: Build-in operator "%s" can not '
                            'be mapped to an id.' % self.op)
        return _id_operator_v1[self.op]

    def get_id_v2(self):
        if self.op not in _id_operator_v2:
            raise Exception('Internal error: Build-in operator "%s" can not '
                            'be mapped to an id.' % self.op)
        return _id_operator_v2[self.op]

    def __unicode__(self):
        if self.op in ('new', 'new[]', 'delete', 'delete[]'):
            return u'operator ' + self.op
        else:
            return u'operator' + self.op

    def get_name_no_template(self):
        return text_type(self)

    def describe_signature(self, signode, mode, env, prefix):
        _verify_description_mode(mode)
        identifier = text_type(self)
        if mode == 'lastIsName':
            signode += addnodes.desc_name(identifier, identifier)
        else:
            signode += addnodes.desc_addname(identifier, identifier)


class ASTOperatorType(ASTBase):
    def __init__(self, type):
        self.type = type

    def __unicode__(self):
        return u''.join(['operator ', text_type(self.type)])

    def get_id_v1(self):
        return u'castto-%s-operator' % self.type.get_id_v1()

    def get_id_v2(self):
        return u'cv' + self.type.get_id_v2()

    def get_name_no_template(self):
        return text_type(self)

    def describe_signature(self, signode, mode, env, prefix):
        _verify_description_mode(mode)
        identifier = text_type(self)
        if mode == 'lastIsName':
            signode += addnodes.desc_name(identifier, identifier)
        else:
            signode += addnodes.desc_addname(identifier, identifier)


class ASTTemplateArgConstant(ASTBase):
    def __init__(self, value):
        self.value = value

    def __unicode__(self):
        return text_type(self.value)

    def get_id_v1(self):
        return text_type(self).replace(u' ', u'-')

    def get_id_v2(self):
        # TODO: doing this properly needs parsing of expressions, let's just
        # juse it verbatim for now
        return u'X' + text_type(self) + u'E'

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        signode += nodes.Text(text_type(self))


class ASTNestedNameElement(ASTBase):
    def __init__(self, identifier, templateArgs):
        self.identifier = identifier
        self.templateArgs = templateArgs

    def get_id_v1(self):
        res = []
        if self.identifier == 'size_t':
            res.append('s')
        else:
            res.append(self.identifier)
        if self.templateArgs:
            res.append(':')
            for a in self.templateArgs:
                res.append(a.get_id_v1())
            res.append(':')
        return u''.join(res)

    def get_id_v2(self):
        res = []
        if self.identifier == "std":
            res.append(u'St')
        else:
            res.append(text_type(len(self.identifier)))
            res.append(self.identifier)
        if self.templateArgs:
            res.append('I')
            for a in self.templateArgs:
                res.append(a.get_id_v2())
            res.append('E')
        return u''.join(res)

    def __unicode__(self):
        res = []
        res.append(self.identifier)
        if self.templateArgs:
            res.append('<')
            first = True
            for a in self.templateArgs:
                if not first:
                    res.append(', ')
                first = False
                res.append(text_type(a))
            res.append('>')
        return u''.join(res)

    def get_name_no_template(self):
        return text_type(self.identifier)

    def describe_signature(self, signode, mode, env, prefix):
        _verify_description_mode(mode)
        if mode == 'markType':
            targetText = prefix + text_type(self)
            pnode = addnodes.pending_xref(
                '', refdomain='cpp', reftype='type',
                reftarget=targetText, modname=None, classname=None)
            if env:  # during testing we don't have an env, do we?
                pnode['cpp:parent'] = env.ref_context.get('cpp:parent')
            pnode += nodes.Text(text_type(self.identifier))
            signode += pnode
        elif mode == 'lastIsName':
            name = text_type(self.identifier)
            signode += addnodes.desc_name(name, name)
        else:
            raise Exception('Unknown description mode: %s' % mode)
        if self.templateArgs:
            signode += nodes.Text('<')
            first = True
            for a in self.templateArgs:
                if not first:
                    signode += nodes.Text(', ')
                first = False
                a.describe_signature(signode, 'markType', env)
            signode += nodes.Text('>')


class ASTNestedName(ASTBase):
    def __init__(self, names):
        """Use an empty string as the first name if it should start with '::'
        """
        self.names = names

    @property
    def name(self):
        return self

    def get_id_v1(self):
        tt = text_type(self)
        if tt in _id_shorthands_v1:
            return _id_shorthands_v1[tt]
        else:
            res = []
            for n in self.names:
                res.append(n.get_id_v1())
            return u'::'.join(res)

    def get_id_v2(self):
        res = []
        if len(self.names) > 1:
            res.append('N')
        for n in self.names:
            res.append(n.get_id_v2())
        if len(self.names) > 1:
            res.append('E')
        return u''.join(res)

    def get_name_no_last_template(self):
        res = u'::'.join([text_type(n) for n in self.names[:-1]])
        if len(self.names) > 1:
            res += '::'
        res += self.names[-1].get_name_no_template()
        return res

    def prefix_nested_name(self, prefix):
        if self.names[0] == '':
            return self  # it's defined at global namespace, don't tuch it
        assert isinstance(prefix, ASTNestedName)
        names = prefix.names[:]
        names.extend(self.names)
        return ASTNestedName(names)

    def __unicode__(self):
        return u'::'.join([text_type(n) for n in self.names])

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        if mode == 'lastIsName':
            addname = u'::'.join([text_type(n) for n in self.names[:-1]])
            if len(self.names) > 1:
                addname += u'::'
            name = text_type(self.names[-1])
            signode += addnodes.desc_addname(addname, addname)
            self.names[-1].describe_signature(signode, mode, env, '')
        elif mode == 'noneIsName':
            name = text_type(self)
            signode += nodes.Text(name)
        elif mode == 'param':
            name = text_type(self)
            signode += nodes.emphasis(name, name)
        elif mode == 'markType':
            # each element should be a pending xref targeting the complete
            # prefix. however, only the identifier part should be a link, such
            # that template args can be a link as well.
            prefix = ''
            first = True
            for name in self.names:
                if not first:
                    signode += nodes.Text('::')
                    prefix += '::'
                first = False
                if name != '':
                    name.describe_signature(signode, mode, env, prefix)
                prefix += text_type(name)
        else:
            raise Exception('Unknown description mode: %s' % mode)


class ASTTrailingTypeSpecFundamental(ASTBase):
    def __init__(self, name):
        self.name = name

    def __unicode__(self):
        return self.name

    def get_id_v1(self):
        res = []
        for a in self.name.split(' '):
            if a in _id_fundamental_v1:
                res.append(_id_fundamental_v1[a])
            else:
                res.append(a)
        return u'-'.join(res)

    def get_id_v2(self):
        if self.name not in _id_fundamental_v2:
            raise Exception(
                'Semi-internal error: Fundamental type "%s" can not be mapped '
                'to an id. Is it a true fundamental type? If not so, the '
                'parser should have rejected it.' % self.name)
        return _id_fundamental_v2[self.name]

    def describe_signature(self, signode, mode, env):
        signode += nodes.Text(text_type(self.name))


class ASTTrailingTypeSpecName(ASTBase):
    def __init__(self, prefix, nestedName):
        self.prefix = prefix
        self.nestedName = nestedName

    @property
    def name(self):
        return self.nestedName

    def get_id_v1(self):
        return self.nestedName.get_id_v1()

    def get_id_v2(self):
        return self.nestedName.get_id_v2()

    def __unicode__(self):
        res = []
        if self.prefix:
            res.append(self.prefix)
            res.append(' ')
        res.append(text_type(self.nestedName))
        return u''.join(res)

    def describe_signature(self, signode, mode, env):
        if self.prefix:
            signode += addnodes.desc_annotation(self.prefix, self.prefix)
            signode += nodes.Text(' ')
        self.nestedName.describe_signature(signode, mode, env)


class ASTFunctinoParameter(ASTBase):
    def __init__(self, arg, ellipsis=False):
        self.arg = arg
        self.ellipsis = ellipsis

    def get_id_v1(self):
        if self.ellipsis:
            return 'z'
        else:
            return self.arg.get_id_v1()

    def get_id_v2(self):
        if self.ellipsis:
            return 'z'
        else:
            return self.arg.get_id_v2()

    def __unicode__(self):
        if self.ellipsis:
            return '...'
        else:
            return text_type(self.arg)

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        if self.ellipsis:
            signode += nodes.Text('...')
        else:
            self.arg.describe_signature(signode, mode, env)


class ASTParametersQualifiers(ASTBase):
    def __init__(self, args, volatile, const, refQual, exceptionSpec, override,
                 final, initializer):
        self.args = args
        self.volatile = volatile
        self.const = const
        self.refQual = refQual
        self.exceptionSpec = exceptionSpec
        self.override = override
        self.final = final
        self.initializer = initializer

    # Id v1 ------------------------------------------------------------------

    def get_modifiers_id_v1(self):
        res = []
        if self.volatile:
            res.append('V')
        if self.const:
            res.append('C')
        if self.refQual == '&&':
            res.append('O')
        elif self.refQual == '&':
            res.append('R')
        return u''.join(res)

    def get_param_id_v1(self):
        if len(self.args) == 0:
            return ''
        else:
            return u'__' + u'.'.join(a.get_id_v1() for a in self.args)

    # Id v2 ------------------------------------------------------------------

    def get_modifiers_id_v2(self):
        res = []
        if self.volatile:
            res.append('V')
        if self.const:
            res.append('K')
        if self.refQual == '&&':
            res.append('O')
        elif self.refQual == '&':
            res.append('R')
        return u''.join(res)

    def get_param_id_v2(self):
        if len(self.args) == 0:
            return 'v'
        else:
            return u''.join(a.get_id_v2() for a in self.args)

    def __unicode__(self):
        res = []
        res.append('(')
        first = True
        for a in self.args:
            if not first:
                res.append(', ')
            first = False
            res.append(text_type(a))
        res.append(')')
        if self.volatile:
            res.append(' volatile')
        if self.const:
            res.append(' const')
        if self.refQual:
            res.append(' ')
            res.append(self.refQual)
        if self.exceptionSpec:
            res.append(' ')
            res.append(text_type(self.exceptionSpec))
        if self.final:
            res.append(' final')
        if self.override:
            res.append(' override')
        if self.initializer:
            res.append(' = ')
            res.append(self.initializer)
        return u''.join(res)

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        paramlist = addnodes.desc_parameterlist()
        for arg in self.args:
            param = addnodes.desc_parameter('', '', noemph=True)
            if mode == 'lastIsName':  # i.e., outer-function params
                arg.describe_signature(param, 'param', env)
            else:
                arg.describe_signature(param, 'markType', env)
            paramlist += param
        signode += paramlist

        def _add_anno(signode, text):
            signode += nodes.Text(' ')
            signode += addnodes.desc_annotation(text, text)

        def _add_text(signode, text):
            signode += nodes.Text(' ' + text)

        if self.volatile:
            _add_anno(signode, 'volatile')
        if self.const:
            _add_anno(signode, 'const')
        if self.refQual:
            _add_text(signode, self.refQual)
        if self.exceptionSpec:
            _add_anno(signode, text_type(self.exceptionSpec))
        if self.final:
            _add_anno(signode, 'final')
        if self.override:
            _add_anno(signode, 'override')
        if self.initializer:
            _add_text(signode, '= ' + text_type(self.initializer))


class ASTDeclSpecs(ASTBase):
    def __init__(self, outer, visibility, storage, inline, virtual, explicit,
                 constexpr, volatile, const, trailing):
        self.outer = outer
        self.visibility = visibility
        self.storage = storage
        self.inline = inline
        self.virtual = virtual
        self.explicit = explicit
        self.constexpr = constexpr
        self.volatile = volatile
        self.const = const
        self.trailingTypeSpec = trailing

    @property
    def name(self):
        return self.trailingTypeSpec.name

    def get_id_v1(self):
        res = []
        res.append(self.trailingTypeSpec.get_id_v1())
        if self.volatile:
            res.append('V')
        if self.const:
            res.append('C')
        return u''.join(res)

    def get_id_v2(self):
        res = []
        if self.volatile:
            res.append('V')
        if self.const:
            res.append('K')
        res.append(self.trailingTypeSpec.get_id_v2())
        return u''.join(res)

    def _print_visibility(self):
        return (self.visibility and
                not (
                    self.outer in ('type', 'member', 'function') and
                    self.visibility == 'public'))

    def __unicode__(self):
        res = []
        if self._print_visibility():
            res.append(self.visibility)
        if self.storage:
            res.append(self.storage)
        if self.inline:
            res.append('inline')
        if self.virtual:
            res.append('virtual')
        if self.explicit:
            res.append('explicit')
        if self.constexpr:
            res.append('constexpr')
        if self.volatile:
            res.append('volatile')
        if self.const:
            res.append('const')
        if self.trailingTypeSpec:
            res.append(text_type(self.trailingTypeSpec))
        return u' '.join(res)

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        modifiers = []

        def _add(modifiers, text):
            if len(modifiers) > 0:
                modifiers.append(nodes.Text(' '))
            modifiers.append(addnodes.desc_annotation(text, text))

        if self._print_visibility():
            _add(modifiers, self.visibility)
        if self.storage:
            _add(modifiers, self.storage)
        if self.inline:
            _add(modifiers, 'inline')
        if self.virtual:
            _add(modifiers, 'virtual')
        if self.explicit:
            _add(modifiers, 'explicit')
        if self.constexpr:
            _add(modifiers, 'constexpr')
        if self.volatile:
            _add(modifiers, 'volatile')
        if self.const:
            _add(modifiers, 'const')
        for m in modifiers:
            signode += m
        if self.trailingTypeSpec:
            if len(modifiers) > 0:
                signode += nodes.Text(' ')
            self.trailingTypeSpec.describe_signature(signode, mode, env)


class ASTPtrOpPtr(ASTBase):
    def __init__(self, volatile, const):
        self.volatile = volatile
        self.const = const

    def __unicode__(self):
        res = ['*']
        if self.volatile:
            res.append('volatile ')
        if self.const:
            res.append('const ')
        return u''.join(res)

    def get_id_v1(self):
        res = ['P']
        if self.volatile:
            res.append('V')
        if self.const:
            res.append('C')
        return u''.join(res)

    def get_id_v2(self):
        res = ['P']
        if self.volatile:
            res.append('V')
        if self.const:
            res.append('C')
        return u''.join(res)


class ASTPtrOpRef(ASTBase):
    def __unicode__(self):
        return '&'

    def get_id_v1(self):
        return 'R'

    def get_id_v2(self):
        return 'R'


class ASTPtrOpParamPack(ASTBase):
    def __unicode__(self):
        return '...'

    def get_id_v1(self):
        return 'Dp'

    def get_id_v2(self):
        return 'Dp'


class ASTArray(ASTBase):
    def __init__(self, size):
        self.size = size

    def __unicode__(self):
        return u''.join(['[', text_type(self.size), ']'])

    def get_id_v1(self):
        return u'A'

    def get_id_v2(self):
        # TODO: this should maybe be done differently
        return u'A' + text_type(self.size) + u'_'

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        signode += nodes.Text(text_type(self))


class ASTDeclerator(ASTBase):
    def __init__(self, ptrOps, declId, suffixOps):
        self.ptrOps = ptrOps
        self.declId = declId
        self.suffixOps = suffixOps

    @property
    def name(self):
        return self.declId

    # Id v1 ------------------------------------------------------------------

    def get_modifiers_id_v1(self):  # only the modifiers for a function, e.g.,
        # cv-qualifiers
        for op in self.suffixOps:
            if isinstance(op, ASTParametersQualifiers):
                return op.get_modifiers_id_v1()
        raise Exception(
            "This should only be called on a function: %s" % text_type(self))

    def get_param_id_v1(self):  # only the parameters (if any)
        for op in self.suffixOps:
            if isinstance(op, ASTParametersQualifiers):
                return op.get_param_id_v1()
        return ''

    def get_ptr_suffix_id_v1(self):  # only the ptr ops and array specifiers
        return u''.join(
            a.get_id_v1()
            for a in self.ptrOps + self.suffixOps
            if not isinstance(a, ASTParametersQualifiers))

    # Id v2 ------------------------------------------------------------------

    def get_modifiers_id_v2(self):  # only the modifiers for a function, e.g.,
        # cv-qualifiers
        for op in self.suffixOps:
            if isinstance(op, ASTParametersQualifiers):
                return op.get_modifiers_id_v2()
        raise Exception(
            "This should only be called on a function: %s" % text_type(self))

    def get_param_id_v2(self):  # only the parameters (if any)
        for op in self.suffixOps:
            if isinstance(op, ASTParametersQualifiers):
                return op.get_param_id_v2()
        return ''

    def get_ptr_suffix_id_v2(self):  # only the ptr ops and array specifiers
        return u''.join(
            a.get_id_v2()
            for a in self.ptrOps + self.suffixOps
            if not isinstance(a, ASTParametersQualifiers))

    def require_start_space(self):
        if (len(self.ptrOps) > 0 and
                isinstance(self.ptrOps[-1], ASTPtrOpParamPack)):
            return False
        else:
            return self.declId is not None

    def __unicode__(self):
        res = []
        for op in self.ptrOps:
            res.append(text_type(op))
            if isinstance(op, ASTPtrOpParamPack) and self.declId:
                res.append(' ')
        if self.declId:
            res.append(text_type(self.declId))
        for op in self.suffixOps:
            res.append(text_type(op))
        return u''.join(res)

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        for op in self.ptrOps:
            signode += nodes.Text(text_type(op))
            if isinstance(op, ASTPtrOpParamPack) and self.declId:
                signode += nodes.Text(' ')
        if self.declId:
            self.declId.describe_signature(signode, mode, env)
        for op in self.suffixOps:
            op.describe_signature(signode, mode, env)


class ASTInitializer(ASTBase):
    def __init__(self, value):
        self.value = value

    def __unicode__(self):
        return u''.join([' = ', text_type(self.value)])

    def describe_signature(self, signode, mode):
        _verify_description_mode(mode)
        signode += nodes.Text(text_type(self))


class ASTType(ASTBase):
    def __init__(self, declSpecs, decl):
        self.declSpecs = declSpecs
        self.decl = decl
        self.objectType = None

    @property
    def name(self):
        name = self.decl.name
        if not name:
            name = self.declSpecs.name
        return name

    def get_id_v1(self):
        res = []
        if self.objectType:  # needs the name
            if self.objectType == 'function':  # also modifiers
                res.append(self.name.get_id_v1())
                res.append(self.decl.get_param_id_v1())
                res.append(self.decl.get_modifiers_id_v1())
            elif self.objectType == 'type':  # just the name
                res.append(self.name.get_id_v1())
            else:
                print(self.objectType)
                assert False
        else:  # only type encoding
            res.append(self.declSpecs.get_id_v1())
            res.append(self.decl.get_ptr_suffix_id_v1())
            res.append(self.decl.get_param_id_v1())
        return u''.join(res)

    def get_id_v2(self):
        res = []
        if self.objectType:  # needs the name
            res.append(_id_prefix_v2)
            if self.objectType == 'function':  # also modifiers
                res.append(self.decl.get_modifiers_id_v2())
                res.append(self.prefixedName.get_id_v2())
                res.append(self.decl.get_param_id_v2())
            elif self.objectType == 'type':  # just the name
                res.append(self.prefixedName.get_id_v2())
            else:
                print(self.objectType)
                assert False
        else:  # only type encoding
            res.append(self.decl.get_ptr_suffix_id_v2())
            res.append(self.declSpecs.get_id_v2())
            res.append(self.decl.get_param_id_v2())
        return u''.join(res)

    def __unicode__(self):
        res = []
        declSpecs = text_type(self.declSpecs)
        res.append(declSpecs)
        if self.decl.require_start_space() and len(declSpecs) > 0:
            res.append(u' ')
        res.append(text_type(self.decl))
        return u''.join(res)

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        self.declSpecs.describe_signature(signode, 'markType', env)
        if (self.decl.require_start_space() and
                len(text_type(self.declSpecs)) > 0):
            signode += nodes.Text(' ')
        self.decl.describe_signature(signode, mode, env)


class ASTTypeWithInit(ASTBase):
    def __init__(self, type, init):
        self.objectType = None
        self.type = type
        self.init = init

    @property
    def name(self):
        return self.type.name

    def get_id_v1(self):
        if self.objectType == 'member':
            return self.name.get_id_v1() + u'__' + self.type.get_id_v1()
        else:
            return self.type.get_id_v1()

    def get_id_v2(self):
        if self.objectType == 'member':
            return _id_prefix_v2 + self.prefixedName.get_id_v2()
        else:
            return self.type.get_id_v2()

    def __unicode__(self):
        res = []
        res.append(text_type(self.type))
        if self.init:
            res.append(text_type(self.init))
        return u''.join(res)

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        self.type.describe_signature(signode, mode, env)
        if self.init:
            self.init.describe_signature(signode, mode)


class ASTBaseClass(ASTBase):
    def __init__(self, name, visibility):
        self.name = name
        self.visibility = visibility

    def __unicode__(self):
        res = []
        if self.visibility != 'private':
            res.append(self.visibility)
            res.append(' ')
        res.append(text_type(self.name))
        return u''.join(res)

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        if self.visibility != 'private':
            signode += addnodes.desc_annotation(
                self.visibility, self.visibility)
            signode += nodes.Text(' ')
            self.name.describe_signature(signode, mode, env)


class ASTClass(ASTBase):
    def __init__(self, name, bases):
        self.name = name
        self.bases = bases

    def get_id_v1(self):
        return self.name.get_id_v1()
        #name = _id_shortwords.get(self.name)
        #if name is not None:
        #    return name
        #return self.name.replace(u' ', u'-')

    def get_id_v2(self):
        return _id_prefix_v2 + self.prefixedName.get_id_v2()

    def __unicode__(self):
        res = []
        res.append(text_type(self.name))
        if len(self.bases) > 0:
            res.append(' : ')
            first = True
            for b in self.bases:
                if not first:
                    res.append(', ')
                first = False
                res.append(text_type(b))
        return u''.join(res)

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        self.name.describe_signature(signode, mode, env)
        if len(self.bases) > 0:
            signode += nodes.Text(' : ')
            for b in self.bases:
                b.describe_signature(signode, mode, env)
                signode += nodes.Text(', ')
            signode.pop()


class DefinitionParser(object):
    # those without signedness and size modifiers
    # see http://en.cppreference.com/w/cpp/language/types
    _simple_fundemental_types = (
        'void', 'bool', 'char', 'wchar_t', 'char16_t', 'char32_t', 'int',
        'float', 'double', 'auto'
    )

    _prefix_keys = ('class', 'struct', 'union', 'typename')

    def __init__(self, definition):
        self.definition = definition.strip()
        self.pos = 0
        self.end = len(self.definition)
        self.last_match = None
        self._previous_state = (0, None)

    def fail(self, msg):
        indicator = '-' * self.pos + '^'
        raise DefinitionError(
            'Invalid definition: %s [error at %d]\n  %s\n  %s' %
            (msg, self.pos, self.definition, indicator))

    def match(self, regex):
        match = regex.match(self.definition, self.pos)
        if match is not None:
            self._previous_state = (self.pos, self.last_match)
            self.pos = match.end()
            self.last_match = match
            return True
        return False

    def backout(self):
        self.pos, self.last_match = self._previous_state

    def skip_string(self, string):
        strlen = len(string)
        if self.definition[self.pos:self.pos + strlen] == string:
            self.pos += strlen
            return True
        return False

    def skip_word(self, word):
        return self.match(re.compile(r'\b%s\b' % re.escape(word)))

    def skip_ws(self):
        return self.match(_whitespace_re)

    def skip_word_and_ws(self, word):
        if self.skip_word(word):
            self.skip_ws()
            return True
        return False

    @property
    def eof(self):
        return self.pos >= self.end

    @property
    def current_char(self):
        try:
            return self.definition[self.pos]
        except IndexError:
            return 'EOF'

    @property
    def matched_text(self):
        if self.last_match is not None:
            return self.last_match.group()

    def read_rest(self):
        rv = self.definition[self.pos:]
        self.pos = self.end
        return rv

    def assert_end(self):
        self.skip_ws()
        if not self.eof:
            self.fail('expected end of definition, got %r' %
                      self.definition[self.pos:])

    def _parse_operator(self):
        self.skip_ws()
        # adapted from the old code
        # thank god, a regular operator definition
        if self.match(_operator_re):
            return ASTOperatorBuildIn(self.matched_text)

        # new/delete operator?
        for op in 'new', 'delete':
            if not self.skip_word(op):
                continue
            self.skip_ws()
            if self.skip_string('['):
                self.skip_ws()
                if not self.skip_string(']'):
                    self.fail('Expected "]" after  "operator ' + op + '["')
                op += '[]'
            return ASTOperatorBuildIn(op)

        # oh well, looks like a cast operator definition.
        # In that case, eat another type.
        type = self._parse_type()
        return ASTOperatorType(type)

    def _parse_nested_name(self):
        names = []

        self.skip_ws()
        if self.skip_string('::'):
            names.append(u'')
        while 1:
            self.skip_ws()
            # TODO: parse the "template" keyword
            if not self.match(_identifier_re):
                self.fail("expected identifier")
            identifier = self.matched_text
            if identifier == 'operator':
                op = self._parse_operator()
                names.append(op)
            else:
                templateArgs = None
                self.skip_ws()
                if self.skip_string('<'):
                    templateArgs = []
                    while 1:
                        pos = self.pos
                        try:
                            type = self._parse_type(allowParams=True)
                            templateArgs.append(type)
                        except DefinitionError:
                            self.pos = pos
                            symbols = []
                            startPos = self.pos
                            self.skip_ws()
                            if self.match(_string_re):
                                value = self.matched_text
                            else:
                                while not self.eof:
                                    if (len(symbols) == 0 and
                                            self.current_char in (
                                            ',', '>')):
                                        break
                                    # TODO: actually implement nice handling
                                    # of quotes, braces, brackets, parens, and
                                    # whatever
                                    self.pos += 1
                                if self.eof:
                                    self.pos = startPos
                                    self.fail(
                                        'Could not find end of constant '
                                        'template argument.')
                                value = self.definition[startPos:self.pos].strip()
                            templateArgs.append(ASTTemplateArgConstant(value))
                        self.skip_ws()
                        if self.skip_string('>'):
                            break
                        elif self.skip_string(','):
                            continue
                        else:
                            self.fail('Expected ">" or "," in template '
                                      'argument list.')
                names.append(ASTNestedNameElement(identifier, templateArgs))

            self.skip_ws()
            if not self.skip_string('::'):
                break
        return ASTNestedName(names)

    def _parse_trailing_type_spec(self):
        # fundemental types
        self.skip_ws()
        for t in self._simple_fundemental_types:
            if self.skip_word(t):
                return ASTTrailingTypeSpecFundamental(t)

        # TODO: this could/should be more strict
        elements = []
        self.skip_ws()
        if self.skip_word_and_ws('signed'):
            elements.append('signed')
        elif self.skip_word_and_ws('unsigned'):
            elements.append('unsigned')
        while 1:
            if self.skip_word_and_ws('short'):
                elements.append('short')
            elif self.skip_word_and_ws('long'):
                elements.append('long')
            else:
                break
        if self.skip_word_and_ws('int'):
            elements.append('int')
        elif self.skip_word_and_ws('double'):
            elements.append('double')
        if len(elements) > 0:
            return ASTTrailingTypeSpecFundamental(u' '.join(elements))

        # decltype
        self.skip_ws()
        if self.skip_word_and_ws('decltype'):
            self.fail('"decltype(.)" in trailing_type_spec not implemented')

        # prefixed
        prefix = None
        self.skip_ws()
        for k in self._prefix_keys:
            if self.skip_word_and_ws(k):
                prefix = k
                break

        nestedName = self._parse_nested_name()
        return ASTTrailingTypeSpecName(prefix, nestedName)

    def _parse_parameters_and_qualifiers(self, paramMode):
        self.skip_ws()
        if not self.skip_string('('):
            if paramMode == 'function':
                self.fail('Expecting "(" in parameters_and_qualifiers.')
            else:
                return None
        args = []
        self.skip_ws()
        if not self.skip_string(')'):
            while 1:
                self.skip_ws()
                if self.skip_string('...'):
                    args.append(ASTFunctinoParameter(None, True))
                    self.skip_ws()
                    if not self.skip_string(')'):
                        self.fail('Expected ")" after "..." in '
                                  'parameters_and_qualifiers.')
                    break
                if paramMode == 'function':
                    arg = self._parse_type_with_init(named='maybe')
                else:
                    arg = self._parse_type()
                # TODO: parse default parameters
                args.append(ASTFunctinoParameter(arg))

                self.skip_ws()
                if self.skip_string(','):
                    continue
                elif self.skip_string(')'):
                    break
                else:
                    self.fail(
                        'Expecting "," or ")" in parameters_and_qualifiers, '
                        'got "%s".' % self.current_char)

        if paramMode != 'function':
            return ASTParametersQualifiers(
                args, None, None, None, None, None, None, None)

        self.skip_ws()
        const = self.skip_word_and_ws('const')
        volatile = self.skip_word_and_ws('volatile')
        if not const:  # the can be permuted
            const = self.skip_word_and_ws('const')

        refQual = None
        if self.skip_string('&&'):
            refQual = '&&'
        if not refQual and self.skip_string('&'):
            refQual = '&'

        exceptionSpec = None
        override = None
        final = None
        initializer = None
        self.skip_ws()
        if self.skip_string('noexcept'):
            exceptionSpec = 'noexcept'
            self.skip_ws()
            if self.skip_string('('):
                self.fail('Parameterised "noexcept" not implemented.')

        self.skip_ws()
        override = self.skip_word_and_ws('override')
        final = self.skip_word_and_ws('final')
        if not override:
            override = self.skip_word_and_ws(
                'override')  # they can be permuted

        self.skip_ws()
        if self.skip_string('='):
            self.skip_ws()
            valid = ('0', 'delete', 'default')
            for w in valid:
                if self.skip_word_and_ws(w):
                    initializer = w
                    break
            if not initializer:
                self.fail(
                    'Expected "%s" in initializer-specifier.'
                    % u'" or "'.join(valid))

        return ASTParametersQualifiers(
            args, volatile, const, refQual, exceptionSpec, override, final,
            initializer)

    def _parse_decl_specs(self, outer, typed=True):
        """
        visibility storage-class-specifier function-specifier "constexpr"
        "volatile" "const" trailing-type-specifier

        storage-class-specifier -> "static" (only for member_object and
        function_object)

        function-specifier -> "inline" | "virtual" | "explicit" (only for
        function_object)

        "constexpr" (only for member_object and function_object)
        """
        visibility = None
        storage = None
        inline = None
        virtual = None
        explicit = None
        constexpr = None
        volatile = None
        const = None

        if outer:
            self.skip_ws()
            if self.match(_visibility_re):
                visibility = self.matched_text

        while 1:  # accept any permutation of a subset of some decl-specs
            self.skip_ws()
            if not storage:
                if outer in ('member', 'function'):
                    if self.skip_word('static'):
                        storage = 'static'
                        continue
                if outer == 'member':
                    if self.skip_word('mutable'):
                        storage = 'mutable'
                        continue
                if outer == 'fuction':
                    # TODO: maybe in more contexts, missing test cases
                    if self.skip_word('register'):
                        storage = 'register'
                        continue

            if outer == 'function':
                # function-specifiers
                if not inline:
                    inline = self.skip_word('inline')
                    if inline:
                        continue
                if not virtual:
                    virtual = self.skip_word('virtual')
                    if virtual:
                        continue
                if not explicit:
                    explicit = self.skip_word('explicit')
                    if explicit:
                        continue

            if not constexpr and outer in ('member', 'function'):
                constexpr = self.skip_word("constexpr")
                if constexpr:
                    continue
            if not volatile and typed:
                volatile = self.skip_word('volatile')
                if volatile:
                    continue
            if not const and typed:
                const = self.skip_word('const')
                if const:
                    continue
            break

        if typed:
            trailing = self._parse_trailing_type_spec()
        else:
            trailing = None
        return ASTDeclSpecs(
            outer, visibility, storage, inline, virtual, explicit, constexpr,
            volatile, const, trailing)

    def _parse_declerator(self, named, paramMode=None, typed=True):
        if paramMode:
            if paramMode not in ('type', 'function'):
                raise Exception(
                    "Internal error, unknown paramMode '%s'." % paramMode)
        ptrOps = []
        while 1:
            if not typed:
                break
            self.skip_ws()
            if self.skip_string('*'):
                self.skip_ws()
                volatile = self.skip_word_and_ws('volatile')
                const = self.skip_word_and_ws('const')
                ptrOps.append(ASTPtrOpPtr(volatile=volatile, const=const))
            elif self.skip_string('&'):
                ptrOps.append(ASTPtrOpRef())
            elif self.skip_string('...'):
                ptrOps.append(ASTPtrOpParamPack())
                break
            else:
                break

        if named == 'maybe':
            try:
                declId = self._parse_nested_name()
            except DefinitionError:
                declId = None
        elif named:
            declId = self._parse_nested_name()
        else:
            declId = None

        suffixOpts = []
        while 1:
            self.skip_ws()
            if typed and self.skip_string('['):
                startPos = self.pos - 1
                openCount = 1
                while not self.eof:
                    c = self.current_char
                    if c == '[':
                        openCount += 1
                    elif c == ']':
                        openCount -= 1
                    if openCount == 0:
                        break
                    self.pos += 1
                if self.eof:
                    self.pos = startPos
                    self.fail(
                        "Could not find closing square bracket for array.")
                self.pos += 1
                suffixOpts.append(ASTArray(
                    self.definition[startPos + 1:self.pos - 1].strip()))
                continue
            if paramMode:
                paramQual = self._parse_parameters_and_qualifiers(paramMode)
                if paramQual:
                    suffixOpts.append(paramQual)
            break

        return ASTDeclerator(ptrOps, declId, suffixOpts)

    def _parse_initializer(self, outer=None):
        self.skip_ws()
        # TODO: support paren and brace initialization for memberObject
        if not self.skip_string('='):
            return None
        else:
            if outer == 'member':
                value = self.read_rest().strip()
                return ASTInitializer(value)
            elif outer is None:  # function parameter
                symbols = []
                startPos = self.pos
                self.skip_ws()
                if self.match(_string_re):
                    value = self.matched_text
                    return ASTInitializer(value)
                while not self.eof:
                    if len(symbols) == 0 and self.current_char in (',', ')'):
                        break
                    elif len(symbols) > 0 and self.current_char == symbols[-1]:
                        symbols.pop()
                    elif self.current_char == '(':
                        symbols.append(')')
                    # TODO: actually implement nice handling of quotes, braces,
                    # brackets, parens, and whatever
                    self.pos += 1
                if self.eof:
                    self.pos = startPos
                    self.fail(
                        'Could not find end of default value for function '
                        'parameter.')
                value = self.definition[startPos:self.pos].strip()
                return ASTInitializer(value)
            else:
                self.fail(
                    "Internal error, initializer for outer '%s' not "
                    "implemented." % outer)

    def _parse_type(self, outer=None, named=False, allowParams=False):
        """
        named=False|'maybe'|True: 'maybe' is e.g., for function objects which
        doesn't need to name the arguments
        """
        if outer:  # always named
            if outer not in ('type', 'member', 'function'):
                raise Exception('Internal error, unknown outer "%s".' % outer)
            assert not named

        if outer in ('type', 'function'):
            # We allow type objects to just be a name.
            # Some functions don't have normal return types: constructors,
            # destrutors, cast operators
            startPos = self.pos
            # first try without the type
            try:
                declSpecs = self._parse_decl_specs(outer=outer, typed=False)
                decl = self._parse_declerator(named=True, paramMode=outer,
                                              typed=False)
                self.assert_end()
            except DefinitionError as exUntyped:
                self.pos = startPos
                try:
                    declSpecs = self._parse_decl_specs(outer=outer)
                    decl = self._parse_declerator(named=True, paramMode=outer)
                except DefinitionError as exTyped:
                    if outer == 'type':
                        raise DefinitionError(
                            'Type must be either just a name or a '
                            'typedef-like declaration.\nJust a name error: '
                            '%s\nTypedef-like expression error: %s'
                            % (exUntyped.description, exTyped.description))
                    else:
                        # do it again to get the proper traceback (how do you
                        # relieable save a traceback when an exception is
                        # constructed?)
                        self.pos = startPos
                        declSpecs = self._parse_decl_specs(outer=outer)
                        decl = self._parse_declerator(named=True,
                                                      paramMode=outer)
        else:
            if outer:
                named = True
                allowParams = True
            if allowParams:
                paramMode = 'type'
            else:
                paramMode = None
            declSpecs = self._parse_decl_specs(outer=outer)
            decl = self._parse_declerator(named=named, paramMode=paramMode)
        return ASTType(declSpecs, decl)

    def _parse_type_with_init(self, outer=None, named=False):
        if outer:
            assert outer in ('type', 'member', 'function')
        type = self._parse_type(outer=outer, named=named)
        init = self._parse_initializer(outer=outer)
        return ASTTypeWithInit(type, init)

    def _parse_class(self):
        name = self._parse_nested_name()
        bases = []
        self.skip_ws()
        if self.skip_string(':'):
            while 1:
                self.skip_ws()
                visibility = 'private'
                if self.match(_visibility_re):
                    visibility = self.matched_text
                baseName = self._parse_nested_name()
                bases.append(ASTBaseClass(baseName, visibility))
                self.skip_ws()
                if self.skip_string(','):
                    continue
                else:
                    break
        return ASTClass(name, bases)

    def parse_type_object(self):
        res = self._parse_type(outer='type')
        res.objectType = 'type'
        return res

    def parse_member_object(self):
        res = self._parse_type_with_init(outer='member')
        res.objectType = 'member'
        return res

    def parse_function_object(self):
        res = self._parse_type(outer='function')
        res.objectType = 'function'
        return res

    def parse_class_object(self):
        res = self._parse_class()
        res.objectType = 'class'
        return res

    def parse_namespace_object(self):
        res = self._parse_nested_name()
        res.objectType = 'namespace'
        return res

    def parse_xref_object(self):
        res = self._parse_nested_name()
        res.objectType = 'xref'
        return res


class CPPObject(ObjectDescription):
    """Description of a C++ language object."""

    doc_field_types = [
        GroupedField('parameter', label=l_('Parameters'),
                     names=('param', 'parameter', 'arg', 'argument'),
                     can_collapse=True),
        GroupedField('exceptions', label=l_('Throws'), rolename='cpp:class',
                     names=('throws', 'throw', 'exception'),
                     can_collapse=True),
        Field('returnvalue', label=l_('Returns'), has_arg=False,
              names=('returns', 'return')),
    ]

    def add_target_and_index(self, ast, sig, signode):
        ids = [ # the newest should be first
               ast.get_id_v2(),
               ast.get_id_v1()
               ]
        theid = ids[1] # TODO: change this to ids[0] when testing is done
        name = text_type(ast.prefixedName)
        if theid not in self.state.document.ids:
            # if the name is not unique, the first one will win
            objects = self.env.domaindata['cpp']['objects']
            if name not in objects:
                signode['names'].append(name)
            else:
                pass
                #print("[CPP] non-unique name:", name)
            for id in ids:
                signode['ids'].append(id)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            if name not in objects:
                objects.setdefault(name,
                                   (self.env.docname, ast.objectType, theid))
                # add the uninstantiated template if it doesn't exist
                uninstantiated = ast.prefixedName.get_name_no_last_template()
                if uninstantiated != name and uninstantiated not in objects:
                    signode['names'].append(uninstantiated)
                    objects.setdefault(uninstantiated, (
                        self.env.docname, ast.objectType, theid))
            self.env.ref_context['cpp:lastname'] = ast.prefixedName

        indextext = self.get_index_text(name)
        if not re.compile(r'^[a-zA-Z0-9_]*$').match(theid):
            self.state_machine.reporter.warning(
                'Index id generation for C++ object "%s" failed, please '
                'report as bug (id=%s).' % (text_type(ast), theid),
                line=self.lineno)
        self.indexnode['entries'].append(('single', indextext, theid, ''))

    def parse_definition(self, parser):
        raise NotImplementedError()

    def describe_signature(self, signode, ast):
        raise NotImplementedError()

    def handle_signature(self, sig, signode):
        parser = DefinitionParser(sig)
        try:
            ast = self.parse_definition(parser)
            parser.assert_end()
        except DefinitionError as e:
            self.state_machine.reporter.warning(e.description,
                                                line=self.lineno)
            raise ValueError
        self.describe_signature(signode, ast)

        parent = self.env.ref_context.get('cpp:parent')
        if parent and len(parent) > 0:
            ast = ast.clone()
            ast.prefixedName = ast.name.prefix_nested_name(parent[-1])
        else:
            ast.prefixedName = ast.name
        return ast


class CPPTypeObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ type)') % name

    def parse_definition(self, parser):
        return parser.parse_type_object()

    def describe_signature(self, signode, ast):
        signode += addnodes.desc_annotation('type ', 'type ')
        ast.describe_signature(signode, 'lastIsName', self.env)


class CPPMemberObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ member)') % name

    def parse_definition(self, parser):
        return parser.parse_member_object()

    def describe_signature(self, signode, ast):
        ast.describe_signature(signode, 'lastIsName', self.env)


class CPPFunctionObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ function)') % name

    def parse_definition(self, parser):
        return parser.parse_function_object()

    def describe_signature(self, signode, ast):
        ast.describe_signature(signode, 'lastIsName', self.env)


class CPPClassObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ class)') % name

    def before_content(self):
        lastname = self.env.ref_context['cpp:lastname']
        assert lastname
        if 'cpp:parent' in self.env.ref_context:
            self.env.ref_context['cpp:parent'].append(lastname)
        else:
            self.env.ref_context['cpp:parent'] = [lastname]

    def after_content(self):
        self.env.ref_context['cpp:parent'].pop()

    def parse_definition(self, parser):
        return parser.parse_class_object()

    def describe_signature(self, signode, ast):
        signode += addnodes.desc_annotation('class ', 'class ')
        ast.describe_signature(signode, 'lastIsName', self.env)


class CPPNamespaceObject(Directive):
    """
    This directive is just to tell Sphinx that we're documenting stuff in
    namespace foo.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        if self.arguments[0].strip() in ('NULL', '0', 'nullptr'):
            env.ref_context['cpp:parent'] = []
        else:
            parser = DefinitionParser(self.arguments[0])
            try:
                prefix = parser.parse_namespace_object()
                parser.assert_end()
            except DefinitionError as e:
                self.state_machine.reporter.warning(e.description,
                                                    line=self.lineno)
            else:
                env.ref_context['cpp:parent'] = [prefix]
        return []


class CPPXRefRole(XRefRole):
    def process_link(self, env, refnode, has_explicit_title, title, target):
        parent = env.ref_context.get('cpp:parent')
        if parent:
            refnode['cpp:parent'] = parent[:]
        if not has_explicit_title:
            target = target.lstrip('~')  # only has a meaning for the title
            # if the first character is a tilde, don't display the module/class
            # parts of the contents
            if title[:1] == '~':
                title = title[1:]
                dcolon = title.rfind('::')
                if dcolon != -1:
                    title = title[dcolon + 2:]
        return title, target


class CPPDomain(Domain):
    """C++ language domain."""
    name = 'cpp'
    label = 'C++'
    object_types = {
        'class': ObjType(l_('class'), 'class'),
        'function': ObjType(l_('function'), 'func'),
        'member': ObjType(l_('member'), 'member'),
        'type': ObjType(l_('type'), 'type')
    }

    directives = {
        'class': CPPClassObject,
        'function': CPPFunctionObject,
        'member': CPPMemberObject,
        'type': CPPTypeObject,
        'namespace': CPPNamespaceObject
    }
    roles = {
        'class': CPPXRefRole(),
        'func': CPPXRefRole(fix_parens=True),
        'member': CPPXRefRole(),
        'type': CPPXRefRole()
    }
    initial_data = {
        'objects': {},  # prefixedName -> (docname, objectType, id)
    }

    def clear_doc(self, docname):
        for fullname, data in list(self.data['objects'].items()):
            if data[0] == docname:
                del self.data['objects'][fullname]

    def merge_domaindata(self, docnames, otherdata):
        # XXX check duplicates
        for fullname, data in otherdata['objects'].items():
            if data[0] in docnames:
                self.data['objects'][fullname] = data

    def _resolve_xref_inner(self, env, fromdocname, builder,
                            target, node, contnode, warn=True):
        def _create_refnode(nameAst):
            name = text_type(nameAst)
            if name not in self.data['objects']:
                # try dropping the last template
                name = nameAst.get_name_no_last_template()
                if name not in self.data['objects']:
                    return None, None
            docname, objectType, id = self.data['objects'][name]
            return make_refnode(builder, fromdocname, docname, id, contnode,
                                name), objectType

        parser = DefinitionParser(target)
        try:
            nameAst = parser.parse_xref_object().name
            parser.skip_ws()
            if not parser.eof:
                raise DefinitionError('')
        except DefinitionError:
            if warn:
                env.warn_node('unparseable C++ definition: %r' % target, node)
            return None, None

        # try as is the name is fully qualified
        res = _create_refnode(nameAst)
        if res[0]:
            return res

        # try qualifying it with the parent
        parent = node.get('cpp:parent', None)
        if parent and len(parent) > 0:
            return _create_refnode(nameAst.prefix_nested_name(parent[-1]))
        else:
            return None, None

    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):
        return self._resolve_xref_inner(env, fromdocname, builder, target, node,
                                        contnode)[0]

    def resolve_any_xref(self, env, fromdocname, builder, target,
                         node, contnode):
        node, objtype = self._resolve_xref_inner(env, fromdocname, builder,
                                                 target, node, contnode, warn=False)
        if node:
            return [('cpp:' + self.role_for_objtype(objtype), node)]
        return []

    def get_objects(self):
        for refname, (docname, type, theid) in iteritems(self.data['objects']):
            yield (refname, refname, type, docname, refname, 1)
