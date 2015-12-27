# -*- coding: utf-8 -*-
"""
    sphinx.domains.cpp
    ~~~~~~~~~~~~~~~~~~

    The C++ language domain.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
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
              storage-class-specifier ->
                    "static" (only for member_object and function_object)
                  | "register"
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
              (TODO: for now we don't support trailing-eturn-type)
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
            | "(" ptr-declarator ")"
        ptr-operator ->
              "*"  attribute-specifier-seq[opt] cv-qualifier-seq[opt]
            | "&   attribute-specifier-seq[opt]
            | "&&" attribute-specifier-seq[opt]
            | "::"[opt] nested-name-specifier "*" attribute-specifier-seq[opt]
                cv-qualifier-seq[opt] # TOOD: not implemented
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

        enum-head ->
            enum-key attribute-specifier-seq[opt] nested-name-specifier[opt]
                identifier enum-base[opt]
        enum-key -> "enum" | "enum struct" | "enum class"
        enum-base ->
            ":" type
        enumerator-definition ->
              identifier
            | identifier "=" constant-expression

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

    class_object:
        goal: a class declaration, but with specification of a base class
              TODO: what about templates? for now: skip
        grammar:
              nested-name
            | nested-name ":"
                'comma-separated list of nested-name optionally with visibility'

    enum_object:
        goal: an unscoped enum or a scoped enum, optionally with the underlying
              type specified
        grammar:
            ("class" | "struct")[opt] visibility[opt] nested-name (":" type)[opt]
    enumerator_object:
        goal: an element in a scoped or unscoped enum. The name should be
              injected according to the scopedness.
        grammar:
            nested-name ("=" constant-expression)

    namespace_object:
        goal: a directive to put all following declarations in a specific scope
        grammar:
            nested-name
"""

_identifier_re = re.compile(r'(~?\b[a-zA-Z_][a-zA-Z0-9_]*)\b')
_whitespace_re = re.compile(r'\s+(?u)')
_string_re = re.compile(r"[LuU8]?('([^'\\]*(?:\\.[^'\\]*)*)'"
                        r'|"([^"\\]*(?:\\.[^"\\]*)*)")', re.S)
_visibility_re = re.compile(r'\b(public|private|protected)\b')
_operator_re = re.compile(r'''(?x)
        \[\s*\]
    |   \(\s*\)
    |   \+\+ | --
    |   ->\*? | \,
    |   (<<|>>)=? | && | \|\|
    |   [!<>=/*%+|&^~-]=?
''')
# see http://en.cppreference.com/w/cpp/keyword
_keywords = [
    'alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor',
    'bool', 'break', 'case', 'catch', 'char', 'char16_t', 'char32_t', 'class',
    'compl', 'concept', 'const', 'constexpr', 'const_cast', 'continue',
    'decltype', 'default', 'delete', 'do', 'double', 'dynamic_cast', 'else',
    'enum', 'explicit', 'export', 'extern', 'false', 'float', 'for', 'friend',
    'goto', 'if', 'inline', 'int', 'long', 'mutable', 'namespace', 'new',
    'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq',
    'private', 'protected', 'public', 'register', 'reinterpret_cast',
    'requires', 'return', 'short', 'signed', 'sizeof', 'static',
    'static_assert', 'static_cast', 'struct', 'switch', 'template', 'this',
    'thread_local', 'throw', 'true', 'try', 'typedef', 'typeid', 'typename',
    'union', 'unsigned', 'using', 'virtual', 'void', 'volatile', 'wchar_t',
    'while', 'xor', 'xor_eq'
]

# ------------------------------------------------------------------------------
# Id v1 constants
# ------------------------------------------------------------------------------

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

# ------------------------------------------------------------------------------
# Id v2 constants
# ------------------------------------------------------------------------------

_id_prefix_v2 = '_CPPv2'
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


class NoOldIdError(UnicodeMixin, Exception):
    # Used to avoid implementing unneeded id generation for old id schmes.
    def __init__(self, description=""):
        self.description = description

    def __unicode__(self):
        return self.description


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

    def describe_signature(self, signode, mode, env, prefix, parentScope):
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

    def describe_signature(self, signode, mode, env, prefix, parentScope):
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

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        signode += nodes.Text(text_type(self))


class ASTNestedNameElementEmpty(ASTBase):
    """Used if a nested name starts with ::"""

    def get_id_v1(self):
        return u''

    def get_id_v2(self):
        return u''

    def __unicode__(self):
        return u''

    def describe_signature(self, signode, mode, env, prefix, parentScope):
        pass


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
            res.append(u'.'.join(a.get_id_v1() for a in self.templateArgs))
            res.append(':')
        return u''.join(res)

    def get_id_v2(self):
        res = []
        if self.identifier == "std":
            res.append(u'St')
        elif self.identifier[0] == "~":
            # a destructor, just use an arbitrary version of dtors
            res.append("D0")
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

    def describe_signature(self, signode, mode, env, prefix, parentScope):
        _verify_description_mode(mode)
        if mode == 'markType':
            targetText = prefix + text_type(self)
            pnode = addnodes.pending_xref(
                '', refdomain='cpp', reftype='type',
                reftarget=targetText, modname=None, classname=None)
            pnode['cpp:parent'] = [parentScope]
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
                a.describe_signature(signode, 'markType', env,
                                     parentScope=parentScope)
            signode += nodes.Text('>')


class ASTNestedName(ASTBase):
    def __init__(self, names):
        assert len(names) > 0
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
            id = self.names[0].get_id_v1()
            if len(id) > 0:
                res.append(id)
            for n in self.names[1:]:
                res.append(n.get_id_v1())
            return u'::'.join(res)

    def get_id_v2(self, modifiers=""):
        res = []
        if len(self.names) > 1 or len(modifiers) > 0:
            res.append('N')
        res.append(modifiers)
        for n in self.names:
            res.append(n.get_id_v2())
        if len(self.names) > 1 or len(modifiers) > 0:
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

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        if mode == 'lastIsName':
            addname = u'::'.join([text_type(n) for n in self.names[:-1]])
            if len(self.names) > 1:
                addname += u'::'
            name = text_type(self.names[-1])
            signode += addnodes.desc_addname(addname, addname)
            self.names[-1].describe_signature(signode, mode, env, '',
                                              parentScope=parentScope)
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
                    name.describe_signature(signode, mode, env, prefix,
                                            parentScope=parentScope)
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

    def describe_signature(self, signode, mode, env, parentScope):
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

    def describe_signature(self, signode, mode, env, parentScope):
        if self.prefix:
            signode += addnodes.desc_annotation(self.prefix, self.prefix)
            signode += nodes.Text(' ')
        self.nestedName.describe_signature(signode, mode, env,
                                           parentScope=parentScope)


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

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        if self.ellipsis:
            signode += nodes.Text('...')
        else:
            self.arg.describe_signature(signode, mode, env,
                                        parentScope=parentScope)


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

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        paramlist = addnodes.desc_parameterlist()
        for arg in self.args:
            param = addnodes.desc_parameter('', '', noemph=True)
            if mode == 'lastIsName':  # i.e., outer-function params
                arg.describe_signature(param, 'param', env,
                                       parentScope=parentScope)
            else:
                arg.describe_signature(param, 'markType', env,
                                       parentScope=parentScope)
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


class ASTDeclSpecsSimple(ASTBase):
    def __init__(self, storage, inline, virtual, explicit, constexpr, volatile, const):
        self.storage = storage
        self.inline = inline
        self.virtual = virtual
        self.explicit = explicit
        self.constexpr = constexpr
        self.volatile = volatile
        self.const = const

    def mergeWith(self, other):
        if not other:
            return self
        return ASTDeclSpecsSimple(self.storage or other.storage,
                                  self.inline or other.inline,
                                  self.virtual or other.virtual,
                                  self.explicit or other.explicit,
                                  self.constexpr or other.constexpr,
                                  self.volatile or other.volatile,
                                  self.const or other.const)

    def __unicode__(self):
        res = []
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
        return u' '.join(res)

    def describe_signature(self, modifiers):
        def _add(modifiers, text):
            if len(modifiers) > 0:
                modifiers.append(nodes.Text(' '))
            modifiers.append(addnodes.desc_annotation(text, text))
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


class ASTDeclSpecs(ASTBase):
    def __init__(self, outer, visibility, leftSpecs, rightSpecs, trailing):
        # leftSpecs and rightSpecs are used for output
        # allSpecs are used for id generation
        self.outer = outer
        self.visibility = visibility
        self.leftSpecs = leftSpecs
        self.rightSpecs = rightSpecs
        self.allSpecs = self.leftSpecs.mergeWith(self.rightSpecs)
        self.trailingTypeSpec = trailing

    @property
    def name(self):
        return self.trailingTypeSpec.name

    def get_id_v1(self):
        res = []
        res.append(self.trailingTypeSpec.get_id_v1())
        if self.allSpecs.volatile:
            res.append('V')
        if self.allSpecs.const:
            res.append('C')
        return u''.join(res)

    def get_id_v2(self):
        res = []
        if self.leftSpecs.volatile or self.rightSpecs.volatile:
            res.append('V')
        if self.leftSpecs.const or self.rightSpecs.volatile:
            res.append('K')
        res.append(self.trailingTypeSpec.get_id_v2())
        return u''.join(res)

    def _print_visibility(self):
        return (self.visibility and
                not (self.outer in ('type', 'member', 'function') and
                     self.visibility == 'public'))

    def __unicode__(self):
        res = []
        if self._print_visibility():
            res.append(self.visibility)
        l = text_type(self.leftSpecs)
        if len(l) > 0:
            if len(res) > 0:
                res.append(" ")
            res.append(l)
        if self.trailingTypeSpec:
            if len(res) > 0:
                res.append(" ")
            res.append(text_type(self.trailingTypeSpec))
            r = text_type(self.rightSpecs)
            if len(r) > 0:
                if len(res) > 0:
                    res.append(" ")
                res.append(r)
        return "".join(res)

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        modifiers = []

        def _add(modifiers, text):
            if len(modifiers) > 0:
                modifiers.append(nodes.Text(' '))
            modifiers.append(addnodes.desc_annotation(text, text))

        if self._print_visibility():
            _add(modifiers, self.visibility)
        self.leftSpecs.describe_signature(modifiers)

        for m in modifiers:
            signode += m
        if self.trailingTypeSpec:
            if len(modifiers) > 0:
                signode += nodes.Text(' ')
            self.trailingTypeSpec.describe_signature(signode, mode, env,
                                                     parentScope=parentScope)
            modifiers = []
            self.rightSpecs.describe_signature(modifiers)
            if len(modifiers) > 0:
                signode += nodes.Text(' ')
            for m in modifiers:
                signode += m


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


class ASTDeclaratorPtr(ASTBase):
    def __init__(self, next, volatile, const):
        assert next
        self.next = next
        self.volatile = volatile
        self.const = const

    @property
    def name(self):
        return self.next.name

    def require_space_after_declSpecs(self):
        # TODO: if has paramPack, then False ?
        return True

    def __unicode__(self):
        res = ['*']
        if self.volatile:
            res.append('volatile ')
        if self.const:
            res.append('const ')
        res.append(text_type(self.next))
        return u''.join(res)

    # Id v1 ------------------------------------------------------------------

    def get_modifiers_id_v1(self):
        return self.next.get_modifiers_id_v1()

    def get_param_id_v1(self):
        return self.next.get_param_id_v1()

    def get_ptr_suffix_id_v1(self):
        res = 'P'
        if self.volatile:
            res += 'V'
        if self.const:
            res += 'C'
        return res + self.next.get_ptr_suffix_id_v1()

    # Id v2 ------------------------------------------------------------------

    def get_modifiers_id_v2(self):
        return self.next.get_modifiers_id_v2()

    def get_param_id_v2(self):
        return self.next.get_param_id_v2()

    def get_ptr_suffix_id_v2(self):
        res = [self.next.get_ptr_suffix_id_v2()]
        res.append('P')
        if self.volatile:
            res.append('V')
        if self.const:
            res.append('C')
        return u''.join(res)

    def get_type_id_v2(self, returnTypeId):
        # ReturnType *next, so we are part of the return type of 'next
        res = ['P']
        if self.volatile:
            res.append('V')
        if self.const:
            res.append('C')
        res.append(returnTypeId)
        return self.next.get_type_id_v2(returnTypeId=u''.join(res))

    # ------------------------------------------------------------------------

    def is_function_type(self):
        return self.next.is_function_type()

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        signode += nodes.Text("*")
        self.next.describe_signature(signode, mode, env,
                                     parentScope=parentScope)


class ASTDeclaratorRef(ASTBase):
    def __init__(self, next):
        assert next
        self.next = next

    @property
    def name(self):
        return self.next.name

    def require_space_after_declSpecs(self):
        return self.next.require_space_after_declSpecs()

    def __unicode__(self):
        return '&' + text_type(self.next)

    # Id v1 ------------------------------------------------------------------

    def get_modifiers_id_v1(self):
        return self.next.get_modifiers_id_v1()

    def get_param_id_v1(self):  # only the parameters (if any)
        return self.next.get_param_id_v1()

    def get_ptr_suffix_id_v1(self):
        return u'R' + self.next.get_ptr_suffix_id_v1()

    # Id v2 ------------------------------------------------------------------

    def get_modifiers_id_v2(self):
        return self.next.get_modifiers_id_v2()

    def get_param_id_v2(self):  # only the parameters (if any)
        return self.next.get_param_id_v2()

    def get_ptr_suffix_id_v2(self):
        return self.next.get_ptr_suffix_id_v2() + u'R'

    def get_type_id_v2(self, returnTypeId):
        # ReturnType &next, so we are part of the return type of 'next
        return self.next.get_type_id_v2(returnTypeId=u'R' + returnTypeId)

    # ------------------------------------------------------------------------

    def is_function_type(self):
        return self.next.is_function_type()

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        signode += nodes.Text("&")
        self.next.describe_signature(signode, mode, env,
                                     parentScope=parentScope)


class ASTDeclaratorParamPack(ASTBase):
    def __init__(self, next):
        assert next
        self.next = next

    @property
    def name(self):
        return self.next.name

    def require_space_after_declSpecs(self):
        return False

    def __unicode__(self):
        res = text_type(self.next)
        if self.next.name:
            res = ' ' + res
        return '...' + res

    # Id v1 ------------------------------------------------------------------

    def get_modifiers_id_v1(self):
        return self.next.get_modifiers_id_v1()

    def get_param_id_v1(self):  # only the parameters (if any)
        return self.next.get_param_id_v1()

    def get_ptr_suffix_id_v1(self):
        return 'Dp' + self.next.get_ptr_suffix_id_v2()

    # Id v2 ------------------------------------------------------------------

    def get_modifiers_id_v2(self):
        return self.next.get_modifiers_id_v2()

    def get_param_id_v2(self):  # only the parameters (if any)
        return self.next.get_param_id_v2()

    def get_ptr_suffix_id_v2(self):
        return self.next.get_ptr_suffix_id_v2() + u'Dp'

    def get_type_id_v2(self, returnTypeId):
        # ReturnType... next, so we are part of the return type of 'next
        return self.next.get_type_id_v2(returnTypeId=u'Dp' + returnTypeId)

    # ------------------------------------------------------------------------

    def is_function_type(self):
        return self.next.is_function_type()

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        signode += nodes.Text("...")
        if self.next.name:
            signode += nodes.Text(' ')
        self.next.describe_signature(signode, mode, env,
                                     parentScope=parentScope)


class ASTDeclaratorParen(ASTBase):
    def __init__(self, inner, next):
        assert inner
        assert next
        self.inner = inner
        self.next = next
        # TODO: we assume the name, params, and qualifiers are in inner

    @property
    def name(self):
        return self.inner.name

    def require_space_after_declSpecs(self):
        return True

    def __unicode__(self):
        res = ['(']
        res.append(text_type(self.inner))
        res.append(')')
        res.append(text_type(self.next))
        return ''.join(res)

    # Id v1 ------------------------------------------------------------------

    def get_modifiers_id_v1(self):
        return self.inner.get_modifiers_id_v1()

    def get_param_id_v1(self):  # only the parameters (if any)
        return self.inner.get_param_id_v1()

    def get_ptr_suffix_id_v1(self):
        raise NoOldIdError()  # TODO: was this implemented before?
        return self.next.get_ptr_suffix_id_v2() + \
            self.inner.get_ptr_suffix_id_v2()

    # Id v2 ------------------------------------------------------------------

    def get_modifiers_id_v2(self):
        return self.inner.get_modifiers_id_v2()

    def get_param_id_v2(self):  # only the parameters (if any)
        return self.inner.get_param_id_v2()

    def get_ptr_suffix_id_v2(self):
        return self.inner.get_ptr_suffix_id_v2() + \
            self.next.get_ptr_suffix_id_v2()

    def get_type_id_v2(self, returnTypeId):
        # ReturnType (inner)next, so 'inner' returns everything outside
        nextId = self.next.get_type_id_v2(returnTypeId)
        return self.inner.get_type_id_v2(returnTypeId=nextId)

    # ------------------------------------------------------------------------

    def is_function_type(self):
        return self.inner.is_function_type()

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        signode += nodes.Text('(')
        self.inner.describe_signature(signode, mode, env,
                                      parentScope=parentScope)
        signode += nodes.Text(')')
        self.next.describe_signature(signode, "noneIsName", env,
                                     parentScope=parentScope)


class ASTDecleratorNameParamQual(ASTBase):
    def __init__(self, declId, arrayOps, paramQual):
        self.declId = declId
        self.arrayOps = arrayOps
        self.paramQual = paramQual

    @property
    def name(self):
        return self.declId

    # Id v1 ------------------------------------------------------------------

    def get_modifiers_id_v1(self):  # only the modifiers for a function, e.g.,
        # cv-qualifiers
        if self.paramQual:
            return self.paramQual.get_modifiers_id_v1()
        raise Exception(
            "This should only be called on a function: %s" % text_type(self))

    def get_param_id_v1(self):  # only the parameters (if any)
        if self.paramQual:
            return self.paramQual.get_param_id_v1()
        else:
            return ''

    def get_ptr_suffix_id_v1(self):  # only the array specifiers
        return u''.join(a.get_id_v1() for a in self.arrayOps)

    # Id v2 ------------------------------------------------------------------

    def get_modifiers_id_v2(self):  # only the modifiers for a function, e.g.,
        # cv-qualifiers
        if self.paramQual:
            return self.paramQual.get_modifiers_id_v2()
        raise Exception(
            "This should only be called on a function: %s" % text_type(self))

    def get_param_id_v2(self):  # only the parameters (if any)
        if self.paramQual:
            return self.paramQual.get_param_id_v2()
        else:
            return ''

    def get_ptr_suffix_id_v2(self):  # only the array specifiers
        return u''.join(a.get_id_v2() for a in self.arrayOps)

    def get_type_id_v2(self, returnTypeId):
        res = []
        # TOOD: can we actually have both array ops and paramQual?
        res.append(self.get_ptr_suffix_id_v2())
        if self.paramQual:
            res.append(self.get_modifiers_id_v2())
            res.append('F')
            res.append(returnTypeId)
            res.append(self.get_param_id_v2())
            res.append('E')
        else:
            res.append(returnTypeId)
        return u''.join(res)

    # ------------------------------------------------------------------------

    def require_space_after_declSpecs(self):
        return self.declId is not None

    def is_function_type(self):
        return self.paramQual is not None

    def __unicode__(self):
        res = []
        if self.declId:
            res.append(text_type(self.declId))
        for op in self.arrayOps:
            res.append(text_type(op))
        if self.paramQual:
            res.append(text_type(self.paramQual))
        return u''.join(res)

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        if self.declId:
            self.declId.describe_signature(signode, mode, env,
                                           parentScope=parentScope)
        for op in self.arrayOps:
            op.describe_signature(signode, mode, env)
        if self.paramQual:
            self.paramQual.describe_signature(signode, mode, env,
                                              parentScope=parentScope)


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
                res.append(self.prefixedName.get_id_v1())
                res.append(self.decl.get_param_id_v1())
                res.append(self.decl.get_modifiers_id_v1())
                if (self.declSpecs.leftSpecs.constexpr or
                        (self.declSpecs.rightSpecs and
                         self.declSpecs.rightSpecs.constexpr)):
                    res.append('CE')
            elif self.objectType == 'type':  # just the name
                res.append(self.prefixedName.get_id_v1())
            else:
                print(self.objectType)
                assert False
        else:  # only type encoding
            if self.decl.is_function_type():
                raise NoOldIdError()
            res.append(self.declSpecs.get_id_v1())
            res.append(self.decl.get_ptr_suffix_id_v1())
            res.append(self.decl.get_param_id_v1())
        return u''.join(res)

    def get_id_v2(self):
        res = []
        if self.objectType:  # needs the name
            res.append(_id_prefix_v2)
            if self.objectType == 'function':  # also modifiers
                modifiers = self.decl.get_modifiers_id_v2()
                res.append(self.prefixedName.get_id_v2(modifiers))
                res.append(self.decl.get_param_id_v2())
            elif self.objectType == 'type':  # just the name
                res.append(self.prefixedName.get_id_v2())
            else:
                print(self.objectType)
                assert False
        else:  # only type encoding
            # the 'returnType' of a non-function type is simply just the last
            # type, i.e., for 'int*' it is 'int'
            returnTypeId = self.declSpecs.get_id_v2()
            typeId = self.decl.get_type_id_v2(returnTypeId)
            res.append(typeId)
        return u''.join(res)

    def __unicode__(self):
        res = []
        declSpecs = text_type(self.declSpecs)
        res.append(declSpecs)
        if self.decl.require_space_after_declSpecs() and len(declSpecs) > 0:
            res.append(u' ')
        res.append(text_type(self.decl))
        return u''.join(res)

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        self.declSpecs.describe_signature(signode, 'markType', env,
                                          parentScope=parentScope)
        if (self.decl.require_space_after_declSpecs() and
                len(text_type(self.declSpecs)) > 0):
            signode += nodes.Text(' ')
        self.decl.describe_signature(signode, mode, env,
                                     parentScope=parentScope)


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
            return self.prefixedName.get_id_v1() + u'__' + self.type.get_id_v1()
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

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        self.type.describe_signature(signode, mode, env,
                                     parentScope=parentScope)
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

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        if self.visibility != 'private':
            signode += addnodes.desc_annotation(self.visibility,
                                                self.visibility)
            signode += nodes.Text(' ')
        self.name.describe_signature(signode, mode, env,
                                     parentScope=parentScope)


class ASTClass(ASTBase):
    def __init__(self, name, visibility, bases):
        self.name = name
        self.visibility = visibility
        self.bases = bases

    def get_id_v1(self):
        return self.prefixedName.get_id_v1()
        # name = _id_shortwords.get(self.name)
        # if name is not None:
        #     return name
        # return self.name.replace(u' ', u'-')

    def get_id_v2(self):
        return _id_prefix_v2 + self.prefixedName.get_id_v2()

    def __unicode__(self):
        res = []
        if self.visibility != 'public':
            res.append(self.visibility)
            res.append(' ')
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

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        if self.visibility != 'public':
            signode += addnodes.desc_annotation(
                self.visibility, self.visibility)
            signode += nodes.Text(' ')
        self.name.describe_signature(signode, mode, env,
                                     parentScope=parentScope)
        if len(self.bases) > 0:
            signode += nodes.Text(' : ')
            for b in self.bases:
                b.describe_signature(signode, mode, env,
                                     parentScope=parentScope)
                signode += nodes.Text(', ')
            signode.pop()


class ASTEnum(ASTBase):
    def __init__(self, name, visibility, scoped, underlyingType):
        self.name = name
        self.visibility = visibility
        self.scoped = scoped
        self.underlyingType = underlyingType

    def get_id_v1(self):
        raise NoOldIdError()

    def get_id_v2(self):
        return _id_prefix_v2 + self.prefixedName.get_id_v2()

    def __unicode__(self):
        res = []
        if self.scoped:
            res.append(self.scoped)
            res.append(' ')
        if self.visibility != 'public':
            res.append(self.visibility)
            res.append(' ')
        res.append(text_type(self.name))
        if self.underlyingType:
            res.append(' : ')
            res.append(text_type(self.underlyingType))
        return u''.join(res)

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        # self.scoped has been done by the CPPEnumObject
        if self.visibility != 'public':
            signode += addnodes.desc_annotation(
                self.visibility, self.visibility)
            signode += nodes.Text(' ')
        self.name.describe_signature(signode, mode, env,
                                     parentScope=parentScope)
        if self.underlyingType:
            signode += nodes.Text(' : ')
            self.underlyingType.describe_signature(signode, 'noneIsName', env,
                                                   parentScope=parentScope)


class ASTEnumerator(ASTBase):
    def __init__(self, name, init):
        self.name = name
        self.init = init

    def get_id_v1(self):
        raise NoOldIdError()

    def get_id_v2(self):
        return _id_prefix_v2 + self.prefixedName.get_id_v2()

    def __unicode__(self):
        res = []
        res.append(text_type(self.name))
        if self.init:
            res.append(text_type(self.init))
        return u''.join(res)

    def describe_signature(self, signode, mode, env, parentScope):
        _verify_description_mode(mode)
        self.name.describe_signature(signode, mode, env,
                                     parentScope=parentScope)
        if self.init:
            self.init.describe_signature(signode, 'noneIsName')


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

    def _parse_expression(self, end):
        # Stupidly "parse" an expression.
        # 'end' should be a list of characters which ends the expression.
        assert end
        self.skip_ws()
        startPos = self.pos
        if self.match(_string_re):
            value = self.matched_text
        else:
            # TODO: add handling of more bracket-like things, and quote handling
            brackets = {'(': ')', '[': ']'}
            symbols = []
            while not self.eof:
                if (len(symbols) == 0 and self.current_char in end):
                    break
                if self.current_char in brackets.keys():
                    symbols.append(brackets[self.current_char])
                elif len(symbols) > 0 and self.current_char == symbols[-1]:
                    symbols.pop()
                self.pos += 1
            if self.eof:
                self.fail("Could not find end of expression starting at %d."
                          % startPos)
            value = self.definition[startPos:self.pos].strip()
        return value.strip()

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
        type = self._parse_type(named=False, outer="operatorCast")
        return ASTOperatorType(type)

    def _parse_nested_name(self):
        names = []

        self.skip_ws()
        if self.skip_string('::'):
            names.append(ASTNestedNameElementEmpty())
        while 1:
            self.skip_ws()
            if self.skip_word_and_ws('template'):
                self.fail("'template' in nested name not implemented.")
            elif self.skip_word_and_ws('operator'):
                op = self._parse_operator()
                names.append(op)
            else:
                if not self.match(_identifier_re):
                    self.fail("Expected identifier in nested name.")
                identifier = self.matched_text
                # make sure there isn't a keyword
                if identifier in _keywords:
                    self.fail("Expected identifier in nested name, "
                              "got keyword: %s" % identifier)
                templateArgs = None
                self.skip_ws()
                if self.skip_string('<'):
                    templateArgs = []
                    while 1:
                        pos = self.pos
                        try:
                            type = self._parse_type(named=False)
                            templateArgs.append(type)
                        except DefinitionError:
                            self.pos = pos
                            try:
                                value = self._parse_expression(end=[',', '>'])
                            except DefinitionError:
                                assert False  # TODO: make nice error
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
                    arg = self._parse_type_with_init(outer=None, named='maybe')
                else:
                    arg = self._parse_type(named=False)
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

    def _parse_decl_specs_simple(self, outer, typed):
        """Just parse the simple ones."""
        storage = None
        inline = None
        virtual = None
        explicit = None
        constexpr = None
        volatile = None
        const = None
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
        return ASTDeclSpecsSimple(storage, inline, virtual, explicit, constexpr,
                                  volatile, const)

    def _parse_decl_specs(self, outer, typed=True):
        if outer:
            if outer not in ('type', 'member', 'function'):
                raise Exception('Internal error, unknown outer "%s".' % outer)
        """
        visibility storage-class-specifier function-specifier "constexpr"
        "volatile" "const" trailing-type-specifier

        storage-class-specifier ->
              "static" (only for member_object and function_object)
            | "register"

        function-specifier -> "inline" | "virtual" | "explicit" (only for
        function_object)

        "constexpr" (only for member_object and function_object)
        """
        visibility = None
        leftSpecs = None
        rightSpecs = None
        if outer:
            self.skip_ws()
            if self.match(_visibility_re):
                visibility = self.matched_text
        leftSpecs = self._parse_decl_specs_simple(outer, typed)

        if typed:
            trailing = self._parse_trailing_type_spec()
            rightSpecs = self._parse_decl_specs_simple(outer, typed)
        else:
            trailing = None
        return ASTDeclSpecs(outer, visibility, leftSpecs, rightSpecs, trailing)

    def _parse_declarator_name_param_qual(self, named, paramMode, typed):
        # now we should parse the name, and then suffixes
        if named == 'maybe':
            try:
                declId = self._parse_nested_name()
            except DefinitionError:
                declId = None
        elif named:
            declId = self._parse_nested_name()
        else:
            declId = None
        self.skip_ws()
        if typed and declId:
            if self.skip_string("*"):
                self.fail("Member pointers not implemented.")

        arrayOps = []
        while 1:
            self.skip_ws()
            if typed and self.skip_string('['):
                value = self._parse_expression(end=[']'])
                res = self.skip_string(']')
                assert res
                arrayOps.append(ASTArray(value))
                continue
            else:
                break
        paramQual = self._parse_parameters_and_qualifiers(paramMode)
        return ASTDecleratorNameParamQual(declId=declId, arrayOps=arrayOps,
                                          paramQual=paramQual)

    def _parse_declerator(self, named, paramMode, typed=True):
        # 'typed' here means 'parse return type stuff'
        if paramMode not in ('type', 'function', 'operatorCast'):
            raise Exception(
                "Internal error, unknown paramMode '%s'." % paramMode)
        self.skip_ws()
        if typed and self.skip_string('*'):
            self.skip_ws()
            volatile = False
            const = False
            while 1:
                if not volatile:
                    volatile = self.skip_word_and_ws('volatile')
                    if volatile:
                        continue
                if not const:
                    const = self.skip_word_and_ws('const')
                    if const:
                        continue
                break
            next = self._parse_declerator(named, paramMode, typed)
            return ASTDeclaratorPtr(next=next, volatile=volatile, const=const)
        # TODO: shouldn't we parse an R-value ref here first?
        elif typed and self.skip_string("&"):
            next = self._parse_declerator(named, paramMode, typed)
            return ASTDeclaratorRef(next=next)
        elif typed and self.skip_string("..."):
            next = self._parse_declerator(named, paramMode, False)
            return ASTDeclaratorParamPack(next=next)
        elif typed and self.current_char == '(':  # note: peeking, not skipping
            if paramMode == "operatorCast":
                # TODO: we should be able to parse cast operators which return
                # function pointers. For now, just hax it and ignore.
                return ASTDecleratorNameParamQual(declId=None, arrayOps=[],
                                                  paramQual=None)
            # maybe this is the beginning of params and quals,try that first,
            # otherwise assume it's noptr->declarator > ( ptr-declarator )
            startPos = self.pos
            try:
                # assume this is params and quals
                res = self._parse_declarator_name_param_qual(named, paramMode,
                                                             typed)
                return res
            except DefinitionError as exParamQual:
                self.pos = startPos
                try:
                    assert self.current_char == '('
                    self.skip_string('(')
                    # TODO: hmm, if there is a name, it must be in inner, right?
                    # TODO: hmm, if there must be parameters, they must b
                    # inside, right?
                    inner = self._parse_declerator(named, paramMode, typed)
                    if not self.skip_string(')'):
                        self.fail("Expected ')' in \"( ptr-declarator )\"")
                    next = self._parse_declerator(named=False,
                                                  paramMode="type",
                                                  typed=typed)
                    return ASTDeclaratorParen(inner=inner, next=next)
                except DefinitionError as exNoPtrParen:
                    raise DefinitionError(
                        "If declId, parameters, and qualifiers {\n%s\n"
                        "} else If parenthesis in noptr-declarator {\n%s\n}"
                        % (exParamQual, exNoPtrParen))
        else:
            return self._parse_declarator_name_param_qual(named, paramMode,
                                                          typed)

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
                value = self._parse_expression(end=[',', ')'])
                return ASTInitializer(value)
            else:
                self.fail("Internal error, initializer for outer '%s' not "
                          "implemented." % outer)

    def _parse_type(self, named, outer=None):
        """
        named=False|'maybe'|True: 'maybe' is e.g., for function objects which
        doesn't need to name the arguments

        outer == operatorCast: annoying case, we should not take the params
        """
        if outer:  # always named
            if outer not in ('type', 'member', 'function', 'operatorCast'):
                raise Exception('Internal error, unknown outer "%s".' % outer)
            if outer != 'operatorCast':
                assert named

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
                    # Retain the else branch for easier debugging.
                    # TODO: it would be nice to save the previous stacktrace
                    #       and output it here.
                    if True:
                        if outer == 'type':
                            desc = ('Type must be either just a name or a '
                                    'typedef-like declaration.\n'
                                    'Just a name error: %s\n'
                                    'Typedef-like expression error: %s')
                        elif outer == 'function':
                            desc = ('Error when parsing function declaration:\n'
                                    'If no return type {\n%s\n'
                                    '} else if return type {\n%s\n}')
                        else:
                            assert False
                        raise DefinitionError(
                            desc % (exUntyped.description, exTyped.description))
                    else:
                        # For testing purposes.
                        # do it again to get the proper traceback (how do you
                        # relieable save a traceback when an exception is
                        # constructed?)
                        self.pos = startPos
                        declSpecs = self._parse_decl_specs(outer=outer, typed=False)
                        decl = self._parse_declerator(named=True, paramMode=outer,
                                                      typed=False)
        else:
            paramMode = 'type'
            if outer == 'member':  # i.e., member
                named = True
            elif outer == 'operatorCast':
                paramMode = 'operatorCast'
                outer = None
            declSpecs = self._parse_decl_specs(outer=outer)
            decl = self._parse_declerator(named=named, paramMode=paramMode)
        return ASTType(declSpecs, decl)

    def _parse_type_with_init(self, named, outer):
        if outer:
            assert outer in ('type', 'member', 'function')
        type = self._parse_type(outer=outer, named=named)
        init = self._parse_initializer(outer=outer)
        return ASTTypeWithInit(type, init)

    def _parse_class(self):
        classVisibility = 'public'
        if self.match(_visibility_re):
            classVisibility = self.matched_text
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
        return ASTClass(name, classVisibility, bases)

    def _parse_enum(self):
        scoped = None  # is set by CPPEnumObject
        self.skip_ws()
        visibility = 'public'
        if self.match(_visibility_re):
            visibility = self.matched_text
        self.skip_ws()
        name = self._parse_nested_name()
        self.skip_ws()
        underlyingType = None
        if self.skip_string(':'):
            underlyingType = self._parse_type(named=False)
        return ASTEnum(name, visibility, scoped, underlyingType)

    def _parse_enumerator(self):
        name = self._parse_nested_name()
        self.skip_ws()
        init = None
        if self.skip_string('='):
            self.skip_ws()
            init = ASTInitializer(self.read_rest())
        return ASTEnumerator(name, init)

    def parse_type_object(self):
        res = self._parse_type(named=True, outer='type')
        res.objectType = 'type'
        return res

    def parse_member_object(self):
        res = self._parse_type_with_init(named=True, outer='member')
        res.objectType = 'member'
        return res

    def parse_function_object(self):
        res = self._parse_type(named=True, outer='function')
        res.objectType = 'function'
        return res

    def parse_class_object(self):
        res = self._parse_class()
        res.objectType = 'class'
        return res

    def parse_enum_object(self):
        res = self._parse_enum()
        res.objectType = 'enum'
        return res

    def parse_enumerator_object(self):
        res = self._parse_enumerator()
        res.objectType = 'enumerator'
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
        # general note: name must be lstrip(':')'ed, to remove "::"
        try:
            id_v1 = ast.get_id_v1()
        except NoOldIdError:
            id_v1 = None
        id_v2 = ast.get_id_v2()
        # store them in reverse order, so the newest is first
        ids  = [id_v2, id_v1]

        theid = ids[0]
        ast.newestId = theid
        assert theid  # shouldn't be None
        name = text_type(ast.prefixedName).lstrip(':')
        if theid not in self.state.document.ids:
            # if the name is not unique, the first one will win
            objects = self.env.domaindata['cpp']['objects']
            if name not in objects:
                signode['names'].append(name)
            else:
                pass
                # print("[CPP] non-unique name:", name)
            for id in ids:
                if id:  # is None when the element didn't exist in that version
                    signode['ids'].append(id)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            if name not in objects:
                objects.setdefault(name, (self.env.docname, ast))
                if ast.objectType == 'enumerator':
                    # find the parent, if it exists && is an enum
                    #                     && it's unscoped,
                    #                  then add the name to the parent scope
                    assert len(ast.prefixedName.names) > 0
                    parentPrefixedAstName = ASTNestedName(ast.prefixedName.names[:-1])
                    parentPrefixedName = text_type(parentPrefixedAstName).lstrip(':')
                    if parentPrefixedName in objects:
                        docname, parentAst = objects[parentPrefixedName]
                        if parentAst.objectType == 'enum' and not parentAst.scoped:
                            enumeratorName = ASTNestedName([ast.prefixedName.names[-1]])
                            assert len(parentAst.prefixedName.names) > 0
                            enumScope = ASTNestedName(parentAst.prefixedName.names[:-1])
                            unscopedName = enumeratorName.prefix_nested_name(enumScope)
                            txtUnscopedName = text_type(unscopedName).lstrip(':')
                            if txtUnscopedName not in objects:
                                objects.setdefault(txtUnscopedName,
                                                   (self.env.docname, ast))
                # add the uninstantiated template if it doesn't exist
                uninstantiated = ast.prefixedName.get_name_no_last_template().lstrip(':')
                if uninstantiated != name and uninstantiated not in objects:
                    signode['names'].append(uninstantiated)
                    objects.setdefault(uninstantiated, (self.env.docname, ast))

        indextext = self.get_index_text(name)
        if not re.compile(r'^[a-zA-Z0-9_]*$').match(theid):
            self.state_machine.reporter.warning(
                'Index id generation for C++ object "%s" failed, please '
                'report as bug (id=%s).' % (text_type(ast), theid),
                line=self.lineno)
        self.indexnode['entries'].append(('single', indextext, theid, ''))

    def parse_definition(self, parser):
        raise NotImplementedError()

    def describe_signature(self, signode, ast, parentScope):
        raise NotImplementedError()

    def handle_signature(self, sig, signode):
        def set_lastname(name):
            parent = self.env.ref_context.get('cpp:parent')
            if parent and len(parent) > 0:
                res = name.prefix_nested_name(parent[-1])
            else:
                res = name
            assert res
            self.env.ref_context['cpp:lastname'] = res
            return res

        parser = DefinitionParser(sig)
        try:
            ast = self.parse_definition(parser)
            parser.assert_end()
        except DefinitionError as e:
            self.state_machine.reporter.warning(e.description,
                                                line=self.lineno)
            # It is easier to assume some phony name than handling the error in
            # the possibly inner declarations.
            name = ASTNestedName([
                ASTNestedNameElement("PhonyNameDueToError", None)
            ])
            set_lastname(name)
            raise ValueError
        ast.prefixedName = set_lastname(ast.name)
        assert ast.prefixedName
        self.describe_signature(signode, ast, parentScope=ast.prefixedName)
        return ast


class CPPTypeObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ type)') % name

    def parse_definition(self, parser):
        return parser.parse_type_object()

    def describe_signature(self, signode, ast, parentScope):
        signode += addnodes.desc_annotation('type ', 'type ')
        ast.describe_signature(signode, 'lastIsName', self.env,
                               parentScope=parentScope)


class CPPMemberObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ member)') % name

    def parse_definition(self, parser):
        return parser.parse_member_object()

    def describe_signature(self, signode, ast, parentScope):
        ast.describe_signature(signode, 'lastIsName', self.env,
                               parentScope=parentScope)


class CPPFunctionObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ function)') % name

    def parse_definition(self, parser):
        return parser.parse_function_object()

    def describe_signature(self, signode, ast, parentScope):
        ast.describe_signature(signode, 'lastIsName', self.env,
                               parentScope=parentScope)


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

    def describe_signature(self, signode, ast, parentScope):
        signode += addnodes.desc_annotation('class ', 'class ')
        ast.describe_signature(signode, 'lastIsName', self.env,
                               parentScope=parentScope)


class CPPEnumObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ enum)') % name

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
        ast = parser.parse_enum_object()
        # self.objtype is set by ObjectDescription in run()
        if self.objtype == "enum":
            ast.scoped = None
        elif self.objtype == "enum-struct":
            ast.scoped = "struct"
        elif self.objtype == "enum-class":
            ast.scoped = "class"
        else:
            assert False
        return ast

    def describe_signature(self, signode, ast, parentScope):
        prefix = 'enum '
        if ast.scoped:
            prefix += ast.scoped
            prefix += ' '
        signode += addnodes.desc_annotation(prefix, prefix)
        ast.describe_signature(signode, 'lastIsName', self.env,
                               parentScope=parentScope)


class CPPEnumeratorObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ enumerator)') % name

    def parse_definition(self, parser):
        return parser.parse_enumerator_object()

    def describe_signature(self, signode, ast, parentScope):
        signode += addnodes.desc_annotation('enumerator ', 'enumerator ')
        ast.describe_signature(signode, 'lastIsName', self.env,
                               parentScope=parentScope)


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
        if refnode['reftype'] == 'any':
            # Remove parentheses from the target (not from title)
            title, target = self._fix_parens(env, True, title, target)
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
        'type': ObjType(l_('type'), 'type'),
        'enum': ObjType(l_('enum'), 'enum'),
        'enumerator': ObjType(l_('enumerator'), 'enumerator')
    }

    directives = {
        'class': CPPClassObject,
        'function': CPPFunctionObject,
        'member': CPPMemberObject,
        'var': CPPMemberObject,
        'type': CPPTypeObject,
        'enum': CPPEnumObject,
        'enum-struct': CPPEnumObject,
        'enum-class': CPPEnumObject,
        'enumerator': CPPEnumeratorObject,
        'namespace': CPPNamespaceObject
    }
    roles = {
        'any': CPPXRefRole(),
        'class': CPPXRefRole(),
        'func': CPPXRefRole(fix_parens=True),
        'member': CPPXRefRole(),
        'var': CPPXRefRole(),
        'type': CPPXRefRole(),
        'enum': CPPXRefRole(),
        'enumerator': CPPXRefRole()
    }
    initial_data = {
        'objects': {},  # prefixedName -> (docname, ast)
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
            name = text_type(nameAst).lstrip(':')
            if name not in self.data['objects']:
                # try dropping the last template
                name = nameAst.get_name_no_last_template()
                if name not in self.data['objects']:
                    return None, None
            docname, ast = self.data['objects'][name]
            if node['reftype'] == 'any' and ast.objectType == 'function':
                title = contnode.pop(0).astext()
                if title.endswith('()'):
                    # remove parentheses
                    title = title[:-2]
                if env.config.add_function_parentheses:
                    # add them back to all occurrences if configured
                    title += '()'
                contnode.insert(0, nodes.Text(title))
            return make_refnode(builder, fromdocname, docname, ast.newestId,
                                contnode, name), ast.objectType

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
        # If a name starts with ::, then it is global scope, so if
        # parent[0] = A::B
        # parent[1] = ::C
        # then we should look up in ::C, and in ::
        # Therefore, use only the last name as the basis of lookup.
        parent = node.get('cpp:parent', None)
        if parent and len(parent) > 0:
            parentScope = parent[-1].clone()
        else:
            # env.warn_node("C++ xref has no 'parent' set: %s" %  target, node)
            parentScope = ASTNestedName([ASTNestedNameElementEmpty()])
        while len(parentScope.names) > 0:
            name = nameAst.prefix_nested_name(parentScope)
            res = _create_refnode(name)
            if res[0]:
                return res
            parentScope.names.pop()
        # finally try in global scope (we might have done that already though)
        return _create_refnode(nameAst)

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
        for refname, (docname, ast) in iteritems(self.data['objects']):
            yield (refname, refname, ast.objectType, docname, ast.newestId, 1)
