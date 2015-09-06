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
        template-declaration ->
            "template" "<" template-parameter-list ">" declaration
        template-parameter-list ->
              template-parameter
            | template-parameter-list "," template-parameter
        template-parameter ->
              type-parameter
            | parameter-declaration # i.e., same as a function argument

        type-parameter ->
              "class"    "..."[opt] identifier[opt]
            | "class"               identifier[opt] "=" type-id
            | "typename" "..."[opt] identifier[opt]
            | "typename"            identifier[opt] "=" type-id
            | "template" "<" template-parameter-list ">"
                "class"  "..."[opt] identifier[opt]
            | "template" "<" template-parameter-list ">"
                "class"             identifier[opt] "=" id-expression
            # also, from C++17 we can have "typname" in template templates
        templateDeclPrefix ->
            "template" "<" template-parameter-list ">"

        simple-declaration ->
            attribute-specifier-seq[opt] decl-specifier-seq[opt]
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
        Can start with a templateDeclPrefix.

    member_object:
        goal: as a type_object which must have a declerator, and optionally
        with a initializer
        grammar:
            decl-specifier-seq declerator initializer
        Can start with a templateDeclPrefix.

    function_object:
        goal: a function declaration, TODO: what about templates? for now: skip
        grammar: no initializer
           decl-specifier-seq declerator
        Can start with a templateDeclPrefix.

    class_object:
        goal: a class declaration, but with specification of a base class
              TODO: what about templates? for now: skip
        grammar:
              nested-name
            | nested-name ":"
                'comma-separated list of nested-name optionally with visibility'
        Can start with a templateDeclPrefix.

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


class ASTIdentifier(ASTBase):
    def __init__(self, identifier):
        assert identifier is not None
        self.identifier = identifier

    def get_id_v1(self):
        if self.identifier == 'size_t':
            return 's'
        else:
            return self.identifier

    def get_id_v2(self):
        if self.identifier == "std":
            return 'St'
        elif self.identifier[0] == "~":
            # a destructor, just use an arbitrary version of dtors
            return 'D0'
        else:
            return text_type(len(self.identifier)) + self.identifier

    def __unicode__(self):
        return self.identifier

    def describe_signature(self, signode, mode, env, prefix, symbol):
        _verify_description_mode(mode)
        if mode == 'markType':
            targetText = prefix + self.identifier
            pnode = addnodes.pending_xref('', refdomain='cpp', reftype='type',
                                          reftarget=targetText, modname=None,
                                          classname=None)
            key = symbol.get_lookup_key()
            assert key
            pnode['cpp:parentKey'] = key
            pnode += nodes.Text(self.identifier)
            signode += pnode
        elif mode == 'lastIsName':
            signode += addnodes.desc_name(self.identifier, self.identifier)
        elif mode == 'noneIsName':
            signode += nodes.Text(self.identifier)
        else:
            raise Exception('Unknown description mode: %s' % mode)


class ASTTemplateKeyParamPackIdDefault(ASTBase):
    def __init__(self, key, identifier, parameterPack, default):
        assert key
        if parameterPack:
            assert default is None
        self.key = key
        self.identifier = identifier
        self.parameterPack = parameterPack
        self.default = default

    def get_identifier(self):
        return self.identifier

    def get_id_v2(self):
        # this is not part of the normal name mangling in C++
        res = []
        if self.parameterPack:
            res.append('Dp')
        else:
            res.append('0')  # we need to put something
        return ''.join(res)

    def __unicode__(self):
        res = [self.key]
        if self.parameterPack:
            if self.identifier:
                res.append(' ')
            res.append('...')
        if self.identifier:
            if not self.parameterPack:
                res.append(' ')
            res.append(text_type(self.identifier))
        if self.default:
            res.append(' = ')
            res.append(text_type(self.default))
        return ''.join(res)

    def describe_signature(self, signode, mode, env, symbol):
        signode += nodes.Text(self.key)
        if self.parameterPack:
            if self.identifier:
                signode += nodes.Text(' ')
            signode += nodes.Text('...')
        if self.identifier:
            if not self.parameterPack:
                signode += nodes.Text(' ')
            self.identifier.describe_signature(signode, mode, env, '', symbol)
        if self.default:
            signode += nodes.Text(' = ')
            self.default.describe_signature(signode, 'markType', env, symbol)


class ASTTemplateParamType(ASTBase):
    def __init__(self, data):
        assert data
        self.data = data

    @property
    def name(self):
        id = self.get_identifier()
        return ASTNestedName([ASTNestedNameElement(id, None)], rooted=False)

    def get_identifier(self):
        return self.data.get_identifier()

    def get_id_v2(self, objectType=None, symbol=None):
        # this is not part of the normal name mangling in C++
        if symbol:
            # the anchor will be our parent
            return symbol.parent.declaration.get_id_v2(prefixed=None)
        else:
            return self.data.get_id_v2()

    def __unicode__(self):
        return text_type(self.data)

    def describe_signature(self, signode, mode, env, symbol):
        self.data.describe_signature(signode, mode, env, symbol)


class ASTTemplateParamTemplateType(ASTBase):
    def __init__(self, nestedParams, data):
        assert nestedParams
        assert data
        self.nestedParams = nestedParams
        self.data = data

    @property
    def name(self):
        id = self.get_identifier()
        return ASTNestedName([ASTNestedNameElement(id, None)], rooted=False)

    def get_identifier(self):
        return self.data.get_identifier()

    def get_id_v2(self, objectType=None, symbol=None):
        # this is not part of the normal name mangling in C++
        if symbol:
            # the anchor will be our parent
            return symbol.parent.declaration.get_id_v2(prefixed=None)
        else:
            return self.nestedParams.get_id_v2() + self.data.get_id_v2()

    def __unicode__(self):
        return text_type(self.nestedParams) + text_type(self.data)

    def describe_signature(self, signode, mode, env, symbol):
        self.nestedParams.describe_signature(signode, 'noneIsName', env, symbol)
        signode += nodes.Text(' ')
        self.data.describe_signature(signode, mode, env, symbol)


class ASTTemplateParamNonType(ASTBase):
    def __init__(self, param):
        assert param
        self.param = param

    @property
    def name(self):
        id = self.get_identifier()
        return ASTNestedName([ASTNestedNameElement(id, None)], rooted=False)

    def get_identifier(self):
        name = self.param.name
        if name:
            assert len(name.names) == 1
            assert name.names[0].identifier
            assert not name.names[0].templateArgs
            return name.names[0].identifier
        else:
            return None

    def get_id_v2(self, objectType=None, symbol=None):
        # this is not part of the normal name mangling in C++
        if symbol:
            # the anchor will be our parent
            return symbol.parent.declaration.get_id_v2(prefixed=None)
        else:
            return '_' + self.param.get_id_v2()

    def __unicode__(self):
        return text_type(self.param)

    def describe_signature(self, signode, mode, env, symbol):
        self.param.describe_signature(signode, mode, env, symbol)


class ASTTemplateParams(ASTBase):
    def __init__(self, params):
        assert params is not None
        self.params = params

    def get_id_v2(self):
        res = []
        res.append("I")
        for param in self.params:
            res.append(param.get_id_v2())
        res.append("E")
        return ''.join(res)

    def __unicode__(self):
        res = []
        res.append(u"template<")
        res.append(u", ".join(text_type(a) for a in self.params))
        res.append(u"> ")
        return ''.join(res)

    def describe_signature(self, signode, mode, env, symbol):
        signode += nodes.Text("template<")
        first = True
        for param in self.params:
            if not first:
                signode += nodes.Text(", ")
            first = False
            param.describe_signature(signode, mode, env, symbol)
        signode += nodes.Text(">")


class ASTTemplateDeclarationPrefix(ASTBase):
    def __init__(self, templates):
        assert templates is not None
        assert len(templates) > 0
        self.templates = templates

    # id_v1 does not exist

    def get_id_v2(self):
        # this is not part of a normal name mangling system
        res = []
        for t in self.templates:
            res.append(t.get_id_v2())
        return u''.join(res)

    def __unicode__(self):
        res = []
        for t in self.templates:
            res.append(text_type(t))
        return u''.join(res)

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        for t in self.templates:
            templateNode = nodes.line()
            t.describe_signature(templateNode, 'lastIsName', env, symbol)
            signode += templateNode


class ASTOperatorBuildIn(ASTBase):
    def __init__(self, op):
        self.op = op

    def is_operator(self):
        return True

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

    def describe_signature(self, signode, mode, env, prefix, symbol):
        _verify_description_mode(mode)
        identifier = text_type(self)
        if mode == 'lastIsName':
            signode += addnodes.desc_name(identifier, identifier)
        else:
            signode += addnodes.desc_addname(identifier, identifier)


class ASTOperatorType(ASTBase):
    def __init__(self, type):
        self.type = type

    def is_operator(self):
        return True

    def get_id_v1(self):
        return u'castto-%s-operator' % self.type.get_id_v1()

    def get_id_v2(self):
        return u'cv' + self.type.get_id_v2()

    def __unicode__(self):
        return u''.join(['operator ', text_type(self.type)])

    def get_name_no_template(self):
        return text_type(self)

    def describe_signature(self, signode, mode, env, prefix, symbol):
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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        signode += nodes.Text(text_type(self))


class ASTTemplateArgs(ASTBase):
    def __init__(self, args):
        assert args is not None
        assert len(args) > 0
        self.args = args

    def get_id_v1(self):
        res = []
        res.append(':')
        res.append(u'.'.join(a.get_id_v1() for a in self.args))
        res.append(':')
        return u''.join(res)

    def get_id_v2(self):
        res = []
        res.append('I')
        for a in self.args:
            res.append(a.get_id_v2())
        res.append('E')
        return u''.join(res)

    def __unicode__(self):
        res = ', '.join(text_type(a) for a in self.args)
        return '<' + res + '>'

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        signode += nodes.Text('<')
        first = True
        for a in self.args:
            if not first:
                signode += nodes.Text(', ')
            first = False
            a.describe_signature(signode, 'markType', env, symbol=symbol)
        signode += nodes.Text('>')


class ASTNestedNameElement(ASTBase):
    def __init__(self, identifier, templateArgs):
        self.identifier = identifier
        self.templateArgs = templateArgs

    def is_operator(self):
        return False

    def get_id_v1(self):
        res = self.identifier.get_id_v1()
        if self.templateArgs:
            res += self.templateArgs.get_id_v1()
        return res

    def get_id_v2(self):
        res = self.identifier.get_id_v2()
        if self.templateArgs:
            res += self.templateArgs.get_id_v2()
        return res

    def __unicode__(self):
        res = text_type(self.identifier)
        if self.templateArgs:
            res += text_type(self.templateArgs)
        return res

    def describe_signature(self, signode, mode, env, prefix, symbol):
        self.identifier.describe_signature(signode, mode, env, prefix, symbol)
        if self.templateArgs:
            self.templateArgs.describe_signature(signode, mode, env, symbol)


class ASTNestedName(ASTBase):
    def __init__(self, names, rooted):
        assert len(names) > 0
        self.names = names
        self.rooted = rooted
        for i in range(len(names) - 1):
            assert not names[i].is_operator()

    @property
    def name(self):
        return self

    def num_templates(self):
        count = 0
        for n in self.names:
            if n.is_operator():
                continue
            if n.templateArgs:
                count += 1
        return count

    def get_id_v1(self):
        tt = text_type(self)
        if tt in _id_shorthands_v1:
            return _id_shorthands_v1[tt]
        else:
            return u'::'.join(n.get_id_v1() for n in self.names)

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

    def __unicode__(self):
        res = []
        if self.rooted:
            res.append('')
        for n in self.names:
            res.append(text_type(n))
        return '::'.join(res)

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        # just print the name part, with template args, not template params
        if mode == 'lastIsName':
            addname = []
            if self.rooted:
                addname.append('')
            for n in self.names[:-1]:
                addname.append(text_type(n))
            addname = '::'.join(addname)
            if len(self.names) > 1:
                addname += '::'
            signode += addnodes.desc_addname(addname, addname)
            self.names[-1].describe_signature(signode, mode, env, '', symbol)
        elif mode == 'noneIsName':
            signode += nodes.Text(text_type(self))
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
                    name.describe_signature(signode, mode, env, prefix, symbol)
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

    def describe_signature(self, signode, mode, env, symbol):
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

    def describe_signature(self, signode, mode, env, symbol):
        if self.prefix:
            signode += addnodes.desc_annotation(self.prefix, self.prefix)
            signode += nodes.Text(' ')
        self.nestedName.describe_signature(signode, mode, env, symbol=symbol)


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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        if self.ellipsis:
            signode += nodes.Text('...')
        else:
            self.arg.describe_signature(signode, mode, env, symbol=symbol)


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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        paramlist = addnodes.desc_parameterlist()
        for arg in self.args:
            param = addnodes.desc_parameter('', '', noemph=True)
            if mode == 'lastIsName':  # i.e., outer-function params
                arg.describe_signature(param, 'param', env, symbol=symbol)
            else:
                arg.describe_signature(param, 'markType', env, symbol=symbol)
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
    def __init__(self, storage, inline, virtual, explicit,
                 constexpr, volatile, const):
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
    def __init__(self, outer, leftSpecs, rightSpecs, trailing):
        # leftSpecs and rightSpecs are used for output
        # allSpecs are used for id generation
        self.outer = outer
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

    def __unicode__(self):
        res = []
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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        modifiers = []

        def _add(modifiers, text):
            if len(modifiers) > 0:
                modifiers.append(nodes.Text(' '))
            modifiers.append(addnodes.desc_annotation(text, text))

        self.leftSpecs.describe_signature(modifiers)

        for m in modifiers:
            signode += m
        if self.trailingTypeSpec:
            if len(modifiers) > 0:
                signode += nodes.Text(' ')
            self.trailingTypeSpec.describe_signature(signode, mode, env,
                                                     symbol=symbol)
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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        signode += nodes.Text("*")
        self.next.describe_signature(signode, mode, env, symbol)


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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        signode += nodes.Text("&")
        self.next.describe_signature(signode, mode, env, symbol)


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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        signode += nodes.Text("...")
        if self.next.name:
            signode += nodes.Text(' ')
        self.next.describe_signature(signode, mode, env, symbol)


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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        signode += nodes.Text('(')
        self.inner.describe_signature(signode, mode, env, symbol)
        signode += nodes.Text(')')
        self.next.describe_signature(signode, "noneIsName", env, symbol)


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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        if self.declId:
            self.declId.describe_signature(signode, mode, env, symbol)
        for op in self.arrayOps:
            op.describe_signature(signode, mode, env)
        if self.paramQual:
            self.paramQual.describe_signature(signode, mode, env, symbol)


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
        assert declSpecs
        assert decl
        self.declSpecs = declSpecs
        self.decl = decl

    @property
    def name(self):
        name = self.decl.name
        return name

    def get_id_v1(self, objectType=None, symbol=None):
        res = []
        if objectType:  # needs the name
            if objectType == 'function':  # also modifiers
                res.append(symbol.get_full_nested_name().get_id_v1())
                res.append(self.decl.get_param_id_v1())
                res.append(self.decl.get_modifiers_id_v1())
                if (self.declSpecs.leftSpecs.constexpr or
                        (self.declSpecs.rightSpecs and
                         self.declSpecs.rightSpecs.constexpr)):
                    res.append('CE')
            elif objectType == 'type':  # just the name
                res.append(symbol.get_full_nested_name().get_id_v1())
            else:
                print(objectType)
                assert False
        else:  # only type encoding
            if self.decl.is_function_type():
                raise NoOldIdError()
            res.append(self.declSpecs.get_id_v1())
            res.append(self.decl.get_ptr_suffix_id_v1())
            res.append(self.decl.get_param_id_v1())
        return u''.join(res)

    def get_id_v2(self, objectType=None, symbol=None):
        res = []
        if objectType:  # needs the name
            if objectType == 'function':  # also modifiers
                modifiers = self.decl.get_modifiers_id_v2()
                res.append(symbol.get_full_nested_name().get_id_v2(modifiers))
                res.append(self.decl.get_param_id_v2())
            elif objectType == 'type':  # just the name
                res.append(symbol.get_full_nested_name().get_id_v2())
            else:
                print(objectType)
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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        self.declSpecs.describe_signature(signode, 'markType', env, symbol)
        if (self.decl.require_space_after_declSpecs() and
                len(text_type(self.declSpecs)) > 0):
            signode += nodes.Text(' ')
        self.decl.describe_signature(signode, mode, env, symbol)


class ASTTypeWithInit(ASTBase):
    def __init__(self, type, init):
        self.type = type
        self.init = init

    @property
    def name(self):
        return self.type.name

    def get_id_v1(self, objectType=None, symbol=None):
        if objectType == 'member':
            return symbol.get_full_nested_name().get_id_v1() + u'__' \
                + self.type.get_id_v1()
        else:
            return self.type.get_id_v1(objectType)

    def get_id_v2(self, objectType=None, symbol=None):
        if objectType == 'member':
            return symbol.declaration.name.get_id_v2()
        else:
            return self.type.get_id_v2()

    def __unicode__(self):
        res = []
        res.append(text_type(self.type))
        if self.init:
            res.append(text_type(self.init))
        return u''.join(res)

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        self.type.describe_signature(signode, mode, env, symbol=symbol)
        if self.init:
            self.init.describe_signature(signode, mode)


class ASTTypeUsing(ASTBase):
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def get_id_v1(self, objectType=None, symbol=None):
        return None

    def get_id_v2(self, objectType=None, symbol=None):
        return symbol.get_full_nested_name().get_id_v2()

    def __unicode__(self):
        res = []
        res.append(text_type(self.name))
        if self.type:
            res.append(' = ')
            res.append(text_type(self.type))
        return u''.join(res)

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        self.name.describe_signature(signode, mode, env, symbol=symbol)
        if self.type:
            signode += nodes.Text(' = ')
            self.type.describe_signature(signode, 'markType', env, symbol=symbol)


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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        if self.visibility != 'private':
            signode += addnodes.desc_annotation(self.visibility,
                                                self.visibility)
            signode += nodes.Text(' ')
        self.name.describe_signature(signode, 'markType', env, symbol=symbol)


class ASTClass(ASTBase):
    def __init__(self, name, bases):
        self.name = name
        self.bases = bases

    def get_id_v1(self, objectType, symbol):
        return symbol.get_full_nested_name().get_id_v1()

    def get_id_v2(self, objectType, symbol):
        return symbol.get_full_nested_name().get_id_v2()

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

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        self.name.describe_signature(signode, mode, env, symbol=symbol)
        if len(self.bases) > 0:
            signode += nodes.Text(' : ')
            for b in self.bases:
                b.describe_signature(signode, mode, env, symbol=symbol)
                signode += nodes.Text(', ')
            signode.pop()


class ASTEnum(ASTBase):
    def __init__(self, name, scoped, underlyingType):
        self.name = name
        self.scoped = scoped
        self.underlyingType = underlyingType

    def get_id_v1(self, objectType, symbol):
        raise NoOldIdError()

    def get_id_v2(self, objectType, symbol):
        return symbol.get_full_nested_name().get_id_v2()

    def __unicode__(self):
        res = []
        if self.scoped:
            res.append(self.scoped)
            res.append(' ')
        res.append(text_type(self.name))
        if self.underlyingType:
            res.append(' : ')
            res.append(text_type(self.underlyingType))
        return u''.join(res)

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        # self.scoped has been done by the CPPEnumObject
        self.name.describe_signature(signode, mode, env, symbol=symbol)
        if self.underlyingType:
            signode += nodes.Text(' : ')
            self.underlyingType.describe_signature(signode, 'noneIsName',
                                                   env, symbol=symbol)


class ASTEnumerator(ASTBase):
    def __init__(self, name, init):
        self.name = name
        self.init = init

    def get_id_v1(self, objectType, symbol):
        raise NoOldIdError()

    def get_id_v2(self, objectType, symbol):
        return symbol.get_full_nested_name().get_id_v2()

    def __unicode__(self):
        res = []
        res.append(text_type(self.name))
        if self.init:
            res.append(text_type(self.init))
        return u''.join(res)

    def describe_signature(self, signode, mode, env, symbol):
        _verify_description_mode(mode)
        self.name.describe_signature(signode, mode, env, symbol=symbol)
        if self.init:
            self.init.describe_signature(signode, 'noneIsName')


class ASTDeclaration(ASTBase):
    def __init__(self, objectType, visibility, templatePrefix, declaration):
        self.objectType = objectType
        self.visibility = visibility
        self.templatePrefix = templatePrefix
        self.declaration = declaration

        self.symbol = None
        self.declarationScope = None  # set by Symbol.add_declaration

    @property
    def name(self):
        return self.declaration.name

    def get_id_v1(self):
        if self.templatePrefix:
            raise NoOldIdError()
        return self.declaration.get_id_v1(self.objectType, self.symbol)

    def get_id_v2(self, prefixed=True):
        if prefixed:
            res = [_id_prefix_v2]
        else:
            res = []
        if self.templatePrefix:
            res.append(self.templatePrefix.get_id_v2())
        res.append(self.declaration.get_id_v2(self.objectType, self.symbol))
        return u''.join(res)

    def get_newest_id(self):
        return self.get_id_v2()

    def __unicode__(self):
        res = []
        if self.visibility and self.visibility != "public":
            res.append(self.visibility)
            res.append(u' ')
        if self.templatePrefix:
            res.append(text_type(self.templatePrefix))
        res.append(text_type(self.declaration))
        return u''.join(res)

    def describe_signature(self, signode, mode, env):
        _verify_description_mode(mode)
        assert self.symbol
        if not self.declarationScope:
            raise NotImplementedError("hmm, a bug? %s" % text_type(self))
        assert self.declarationScope
        if self.visibility and self.visibility != "public":
            signode += addnodes.desc_annotation(self.visibility + " ",
                                                self.visibility + " ")
        if self.templatePrefix:
            self.templatePrefix.describe_signature(signode, mode, env,
                                                   symbol=self.symbol)
        if self.objectType == 'type':
            signode += addnodes.desc_annotation('type ', 'type ')
        elif self.objectType == 'member':
            pass
        elif self.objectType == 'function':
            pass
        elif self.objectType == 'class':
            signode += addnodes.desc_annotation('class ', 'class ')
        elif self.objectType == 'enum':
            prefix = 'enum '
            if self.scoped:
                prefix += self.scoped
                prefix += ' '
            signode += addnodes.desc_annotation(prefix, prefix)
        elif self.objectType == 'enumerator':
            signode += addnodes.desc_annotation('enumerator ', 'enumerator ')
        else:
            assert False
        self.declaration.describe_signature(signode, mode, env,
                                            symbol=self.symbol)


class ASTNamespace(ASTBase):
    def __init__(self, nestedName, templatePrefix):
        self.nestedName = nestedName
        self.templatePrefix = templatePrefix


class Symbol(object):
    def __init__(self, parent, identifier,
                 templateParams, templateArgs, declaration):
        if not parent:
            # parent == None means global scope, so declaration means a parent
            assert not identifier
            assert not templateParams
            assert not templateArgs
            assert not declaration
        else:
            if not identifier:
                # in case it's an operator
                assert declaration
        self.parent = parent
        self.identifier = identifier
        self.templateParams = templateParams  # template<templateParams>
        self.templateArgs = templateArgs  # identifier<templateArgs>
        self.declaration = declaration

        self.children = []
        if self.parent:
            self.parent.children.append(self)
        if self.declaration:
            self.declaration.symbol = self
        # add symbols for the template params
        # (do it after self.children has been initialised
        if self.templateParams:
            for p in self.templateParams.params:
                if not p.get_identifier():
                    continue
                decl = ASTDeclaration('templateParam', None, None, p)
                nne = ASTNestedNameElement(p.get_identifier(), None)
                nn = ASTNestedName([nne], rooted=False)
                self._add_symbols(nn, [], decl)

    def get_all_symbols(self):
        # assumed to be in post-order
        for sChild in self.children:
            for s in sChild.get_all_symbols():
                yield s
        yield self

    def get_lookup_key(self):
        if not self.parent:
            # specialise for the root
            return None
        symbols = []
        s = self
        while s.parent:
            symbols.append(s)
            s = s.parent
        symbols.reverse()
        key = []
        for s in symbols[:-1]:
            assert s.identifier
            nne = ASTNestedNameElement(s.identifier, s.templateArgs)
            key.append((nne, s.templateParams))
        s = symbols[-1]
        if s.identifier:
            nne = ASTNestedNameElement(s.identifier, s.templateArgs)
        else:
            assert self.declaration
            nne = s.declaration.name.names[-1]
        key.append((nne, s.templateParams))
        return key

    def get_full_nested_name(self):
        names = []
        for nne, templateParams in self.get_lookup_key():
            names.append(nne)
        return ASTNestedName(names, rooted=False)

    def _find_named_symbol(self, identifier, templateParams,
                           templateArgs, operator):
        assert (identifier is None) != (operator is None)
        for s in self.children:
            if s.identifier != identifier:
                continue
            if not s.identifier:
                if not s.declaration:
                    continue
                assert operator
                name = s.declaration.name.names[-1]
                if not name.is_operator():
                    continue
                if text_type(name) != text_type(operator):
                    continue
            if (s.templateParams is None) != (templateParams is None):
                continue
            if s.templateParams:
                # TODO: do better comparison
                if text_type(s.templateParams) != text_type(templateParams):
                    continue
            if (s.templateArgs is None) != (templateArgs is None):
                continue
            if s.templateArgs:
                # TODO: do better comparison
                if text_type(s.templateArgs) != text_type(templateArgs):
                    continue
            return s
        return None

    def _add_symbols(self, nestedName, templateDecls, declaration):
        # This condition should be checked at the parser level.
        # Each template argument list must have a template parameter list.
        # But to declare a template there must be an additional template parameter list.
        assert(nestedName.num_templates() == len(templateDecls) or
               nestedName.num_templates() + 1 == len(templateDecls))

        parentSymbol = self
        if nestedName.rooted:
            while parentSymbol.parent:
                parentSymbol = parentSymbol.parent
        declarationScope = parentSymbol
        names = nestedName.names
        iTemplateDecl = 0
        for iName in range(len(names)):
            name = names[iName]
            if iName + 1 == len(names):
                if name.is_operator():
                    identifier = None
                    templateArgs = None
                    operator = name
                else:
                    identifier = name.identifier
                    templateArgs = name.templateArgs
                    operator = None
                if iTemplateDecl < len(templateDecls):
                    if iTemplateDecl + 1 != len(templateDecls):
                        print(text_type(templateDecls))
                        print(text_type(nestedName))
                    assert iTemplateDecl + 1 == len(templateDecls)
                    templateParams = templateDecls[iTemplateDecl]
                else:
                    assert iTemplateDecl == len(templateDecls)
                    templateParams = None
                symbol = parentSymbol._find_named_symbol(identifier,
                                                         templateParams,
                                                         templateArgs,
                                                         operator)
                if symbol:
                    if not declaration:
                        # good, just a scope creation
                        return symbol
                    if not symbol.declaration:
                        # If someone first opened the scope, and then later
                        # declares it, e.g,
                        # .. namespace:: Test
                        # .. namespace:: nullptr
                        # .. class:: Test
                        symbol.declaration = declaration
                        declaration.symbol = symbol
                        declaration.declarationScope = declarationScope
                        return symbol
                    # it may simply be a functin overload
                    # TODO: it could be a duplicate but let's just insert anyway
                    # the id generation will warn about it
                    symbol = Symbol(parent=parentSymbol, identifier=identifier,
                                    templateParams=templateParams,
                                    templateArgs=templateArgs,
                                    declaration=declaration)
                    declaration.declarationScope = declarationScope
                else:
                    symbol = Symbol(parent=parentSymbol, identifier=identifier,
                                    templateParams=templateParams,
                                    templateArgs=templateArgs,
                                    declaration=declaration)
                    if declaration:
                        declaration.declarationScope = declarationScope
                return symbol
            else:
                # there shouldn't be anything inside an operator
                assert not name.is_operator()
                identifier = name.identifier
                templateArgs = name.templateArgs
                if templateArgs:
                    assert iTemplateDecl < len(templateDecls)
                    templateParams = templateDecls[iTemplateDecl]
                    iTemplateDecl += 1
                else:
                    templateParams = None
                symbol = parentSymbol._find_named_symbol(identifier,
                                                         templateParams,
                                                         templateArgs,
                                                         operator=None)
                if symbol is None:
                    symbol = Symbol(parent=parentSymbol, identifier=identifier,
                                    templateParams=templateParams,
                                    templateArgs=templateArgs, declaration=None)
            parentSymbol = symbol
        assert False  # should have returned in the loop

    def add_name(self, nestedName, templatePrefix=None):
        if templatePrefix:
            templateDecls = templatePrefix.templates
        else:
            templateDecls = []
        return self._add_symbols(nestedName, templateDecls, declaration=None)

    def add_declaration(self, declaration):
        nestedName = declaration.name
        if declaration.templatePrefix:
            templateDecls = declaration.templatePrefix.templates
        else:
            templateDecls = []
        return self._add_symbols(nestedName, templateDecls, declaration)

    def find_identifier(self, identifier):
        for s in self.children:
            if s.identifier and s.identifier == identifier:
                return s
        return None

    def direct_lookup(self, key):
        s = self
        for name, templateParams in key:
            if name.is_operator():
                identifier = None
                templateArgs = None
                operator = name
            else:
                identifier = name.identifier
                templateArgs = name.templateArgs
                operator = None
            s = s._find_named_symbol(identifier, templateParams,
                                     templateArgs, operator)
            if not s:
                return None
        return s

    def find_name(self, nestedName, templateDecls, specific_specialisation):
        # TODO: unify this with the _add_symbols
        # This condition should be checked at the parser level.
        # Each template argument list must have a template parameter list.
        # But to declare a template there must be an additional template parameter list.
        assert(nestedName.num_templates() == len(templateDecls) or
               nestedName.num_templates() + 1 == len(templateDecls))
        parentSymbol = self
        if nestedName.rooted:
            while parentSymbol.parent:
                parentSymbol = parentSymbol.parent
        names = nestedName.names

        # walk up until we find the first identifier
        firstName = names[0]
        if not firstName.is_operator():
            while parentSymbol.parent:
                if parentSymbol.find_identifier(firstName.identifier):
                    break
                parentSymbol = parentSymbol.parent

        iTemplateDecl = 0
        for iName in range(len(names)):
            name = names[iName]
            if iName + 1 == len(names):
                if name.is_operator():
                    identifier = None
                    templateArgs = None
                    operator = name
                else:
                    identifier = name.identifier
                    templateArgs = name.templateArgs
                    operator = None
                if iTemplateDecl < len(templateDecls):
                    assert iTemplateDecl + 1 == len(templateDecls)
                    templateParams = templateDecls[iTemplateDecl]
                else:
                    assert iTemplateDecl == len(templateDecls)
                    templateParams = None
                symbol = parentSymbol._find_named_symbol(identifier,
                                                         templateParams,
                                                         templateArgs,
                                                         operator)
                if symbol:
                    return symbol
                else:
                    # TODO: search for version without template args,
                    #       if not specific_specialisation
                    return None
            else:
                # there shouldn't be anything inside an operator
                assert not name.is_operator()
                identifier = name.identifier
                templateArgs = name.templateArgs
                if templateArgs:
                    assert iTemplateDecl < len(templateDecls)
                    templateParams = templateDecls[iTemplateDecl]
                    iTemplateDecl += 1
                else:
                    templateParams = None
                symbol = parentSymbol._find_named_symbol(identifier,
                                                         templateParams,
                                                         templateArgs,
                                                         operator=None)
                if symbol is None:
                    # TODO: maybe search without template args
                    return None
            parentSymbol = symbol
        assert False  # should have returned in the loop

    def dump(self, indent):
        res = ['\t'*indent]
        if self.identifier:
            if self.templateParams:
                res.append(text_type(self.templateParams))
                res.append('\n')
                res.append('\t'*indent)
            res.append(text_type(self.identifier))
            if self.templateArgs:
                res.append(text_type(self.templateArgs))
            if self.declaration:
                res.append(": ")
                res.append(text_type(self.declaration))
        else:
            res.append('::')
        res.append('\n')
        for c in self.children:
            res.append(c.dump(indent + 1))
        return ''.join(res)


class DefinitionParser(object):
    # those without signedness and size modifiers
    # see http://en.cppreference.com/w/cpp/language/types
    _simple_fundemental_types = (
        'void', 'bool', 'char', 'wchar_t', 'char16_t', 'char32_t', 'int',
        'float', 'double', 'auto'
    )

    _prefix_keys = ('class', 'struct', 'union', 'typename')

    def __init__(self, definition, warnEnv):
        self.definition = definition.strip()
        self.pos = 0
        self.end = len(self.definition)
        self.last_match = None
        self._previous_state = (0, None)

        self.warnEnv = warnEnv

    def fail(self, msg):
        indicator = '-' * self.pos + '^'
        raise DefinitionError(
            'Invalid definition: %s [error at %d]\n  %s\n  %s' %
            (msg, self.pos, self.definition, indicator))

    def warn(self, msg):
        if self.warnEnv:
            self.warnEnv.warn(msg)
        else:
            print("Warning: %s" % msg)
            print("In declaration:\n%s" % self.definition)

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
        rooted = False
        if self.skip_string('::'):
            rooted = True
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
                    templateArgs = ASTTemplateArgs(templateArgs)
                identifier = ASTIdentifier(identifier)
                names.append(ASTNestedNameElement(identifier, templateArgs))

            self.skip_ws()
            if not self.skip_string('::'):
                break
        return ASTNestedName(names, rooted)

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
                # TODO: parse default parameters # TODO: didn't we just do that?
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
            if outer not in ('type', 'member', 'function', 'templateParam'):
                raise Exception('Internal error, unknown outer "%s".' % outer)
        """
        storage-class-specifier function-specifier "constexpr"
        "volatile" "const" trailing-type-specifier

        storage-class-specifier ->
              "static" (only for member_object and function_object)
            | "register"

        function-specifier -> "inline" | "virtual" | "explicit" (only for
        function_object)

        "constexpr" (only for member_object and function_object)
        """
        leftSpecs = self._parse_decl_specs_simple(outer, typed)
        rightSpecs = None

        if typed:
            trailing = self._parse_trailing_type_spec()
            rightSpecs = self._parse_decl_specs_simple(outer, typed)
        else:
            trailing = None
        return ASTDeclSpecs(outer, leftSpecs, rightSpecs, trailing)

    def _parse_declarator_name_param_qual(self, named, paramMode, typed):
        # now we should parse the name, and then suffixes
        if named == 'maybe':
            try:
                declId = self._parse_nested_name()
            except DefinitionError:
                declId = None
        elif named == 'single':
            if self.match(_identifier_re):
                identifier = ASTIdentifier(self.matched_text)
                nne = ASTNestedNameElement(identifier, None)
                declId = ASTNestedName([nne], rooted=False)
            else:
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
            elif outer == 'templateParam':
                value = self._parse_expression(end=[',', '>'])
            elif outer is None:  # function parameter
                value = self._parse_expression(end=[',', ')'])
            else:
                self.fail("Internal error, initializer for outer '%s' not "
                          "implemented." % outer)
            return ASTInitializer(value)

    def _parse_type(self, named, outer=None):
        """
        named=False|'maybe'|True: 'maybe' is e.g., for function objects which
        doesn't need to name the arguments

        outer == operatorCast: annoying case, we should not take the params
        """
        if outer:  # always named
            if outer not in ('type', 'member', 'function',
                             'operatorCast', 'templateParam'):
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
            elif outer == 'templateParam':
                named = 'single'
            declSpecs = self._parse_decl_specs(outer=outer)
            decl = self._parse_declerator(named=named, paramMode=paramMode)
        return ASTType(declSpecs, decl)

    def _parse_type_with_init(self, named, outer):
        if outer:
            assert outer in ('type', 'member', 'function', 'templateParam')
        type = self._parse_type(outer=outer, named=named)
        init = self._parse_initializer(outer=outer)
        return ASTTypeWithInit(type, init)

    def _parse_type_using(self):
        name = self._parse_nested_name()
        self.skip_ws()
        if not self.skip_string('='):
            return ASTTypeUsing(name, None)
        type = self._parse_type(False, None)
        return ASTTypeUsing(name, type)

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

    def _parse_enum(self):
        scoped = None  # is set by CPPEnumObject
        self.skip_ws()
        name = self._parse_nested_name()
        self.skip_ws()
        underlyingType = None
        if self.skip_string(':'):
            underlyingType = self._parse_type(named=False)
        return ASTEnum(name, scoped, underlyingType)

    def _parse_enumerator(self):
        name = self._parse_nested_name()
        self.skip_ws()
        init = None
        if self.skip_string('='):
            self.skip_ws()
            init = ASTInitializer(self.read_rest())
        return ASTEnumerator(name, init)

    def _parse_template_parameter_list(self):
        # only: '<' parameter-list '>'
        # we assume that 'template' has just been parsed
        templateParams = []
        self.skip_ws()
        if not self.skip_string("<"):
            self.fail("Expected '<' after 'template'")
        while 1:
            extraError = ''
            self.skip_ws()
            if self.skip_word('template'):
                # declare a tenplate template parameter
                nestedParams = self._parse_template_parameter_list()
            else:
                nestedParams = None
            self.skip_ws()
            key = None
            if self.skip_word_and_ws('typename'):
                key = 'typename'
            elif self.skip_word_and_ws('class'):
                key = 'class'
            elif nestedParams:
                self.fail("Expected 'typename' or 'class' after "
                          "template template parameter list.")
            if key:
                # declare a type or template type parameter
                self.skip_ws()
                parameterPack = self.skip_string('...')
                self.skip_ws()
                if self.match(_identifier_re):
                    identifier = ASTIdentifier(self.matched_text)
                else:
                    identifier = None
                self.skip_ws()
                if not parameterPack and self.skip_string('='):
                    default = self._parse_type(named=False, outer=None)
                else:
                    default = None
                data = ASTTemplateKeyParamPackIdDefault(key, identifier,
                                                        parameterPack, default)
                if nestedParams:
                    # template type
                    param = ASTTemplateParamTemplateType(nestedParams, data)
                else:
                    # type
                    param = ASTTemplateParamType(data)
                templateParams.append(param)
            else:
                # declare a non-type parameter
                pos = self.pos
                try:
                    param = self._parse_type_with_init('maybe', 'templateParam')
                    templateParams.append(ASTTemplateParamNonType(param))
                except DefinitionError as e:
                    self.pos = pos
                    extraError = "Error if non-type template parameter: %s"
                    extraError = extraError % e.description
            self.skip_ws()
            if self.skip_string('>'):
                return ASTTemplateParams(templateParams)
            elif self.skip_string(','):
                continue
            else:
                msg = 'Expected "=", ",", or ">" in template parameter list.'
                if len(extraError) > 0:
                    msg += '\n%s' % extraError
                self.fail(msg)

    def _parse_template_declaration_prefix(self):
        templates = []
        while 1:
            self.skip_ws()
            if not self.skip_word("template"):
                break
            params = self._parse_template_parameter_list()
            templates.append(params)
        if len(templates) == 0:
            return None
        else:
            return ASTTemplateDeclarationPrefix(templates)

    def _check_template_consistency(self, nestedName, templatePrefix):
        numArgs = nestedName.num_templates()
        if not templatePrefix:
            numParams = 0
        else:
            numParams = len(templatePrefix.templates)
        if numArgs + 1 < numParams:
            self.fail("Too few template argument lists comapred to parameter"
                      " lists. Argument lists: %d, Parameter lists: %d."
                      % (numArgs, numParams))
        if numArgs > numParams:
            numExtra = numArgs - numParams
            self.warn("Too many template argument lists compared to parameter"
                      " lists. Argument lists: %d, Parameter lists: %d,"
                      " Extra empty parameters lists prepended: %d."
                      % (numArgs, numParams, numExtra))
            newTemplates = []
            for i in range(numExtra):
                newTemplates.append(ASTTemplateParams([]))
            if templatePrefix:
                newTemplates.extend(templatePrefix.templates)
            templatePrefix = ASTTemplateDeclarationPrefix(newTemplates)
        return templatePrefix

    def parse_declaration(self, objectType):
        if objectType not in ('type', 'member',
                              'function', 'class', 'enum', 'enumerator'):
            raise Exception('Internal error, unknown objectType "%s".' % objectType)
        visibility = None
        templatePrefix = None
        declaration = None

        self.skip_ws()
        if self.match(_visibility_re):
            visibility = self.matched_text

        if objectType in ('type', 'member', 'function', 'class'):
            templatePrefix = self._parse_template_declaration_prefix()

        if objectType == 'type':
            error = None
            try:
                if not templatePrefix:
                    declaration = self._parse_type(named=True, outer='type')
            except DefinitionError as e:
                error = e.description
            try:
                if not declaration:
                    declaration = self._parse_type_using()
            except DefinitionError as e:
                if error:
                    msg = "Error if typedef:\n%s\n" \
                          "Error if type alias or template alias:\n%s" \
                          % (error, e.description)
                    raise DefinitionError(msg)
                else:
                    raise e
        elif objectType == 'member':
            declaration = self._parse_type_with_init(named=True, outer='member')
        elif objectType == 'function':
            declaration = self._parse_type(named=True, outer='function')
        elif objectType == 'class':
            declaration = self._parse_class()
        elif objectType == 'enum':
            declaration = self._parse_enum()
        elif objectType == 'enumerator':
            declaration = self._parse_enumerator()
        else:
            assert False
        templatePrefix = self._check_template_consistency(declaration.name,
                                                          templatePrefix)
        return ASTDeclaration(objectType, visibility,
                              templatePrefix, declaration)

    def parse_namespace_object(self):
        templatePrefix = self._parse_template_declaration_prefix()
        name = self._parse_nested_name()
        templatePrefix = self._check_template_consistency(name, templatePrefix)
        res = ASTNamespace(name, templatePrefix)
        res.objectType = 'namespace'
        return res

    def parse_xref_object(self):
        templatePrefix = self._parse_template_declaration_prefix()
        name = self._parse_nested_name()
        templatePrefix = self._check_template_consistency(name, templatePrefix)
        res = ASTNamespace(name, templatePrefix)
        res.objectType = 'xref'
        return res


def _make_phony_error_name():
    nne = ASTNestedNameElement(ASTIdentifier("PhonyNameDueToError"), None)
    return ASTNestedName([nne], rooted=False)


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

    def warn(self, msg):
        self.state_machine.reporter.warning(msg, lineno=self.lineno)

    def _add_enumerator_to_parent(self, ast):
        assert ast.objectType == 'enumerator'
        # find the parent, if it exists && is an enum
        #                     && it's unscoped,
        #                  then add the name to the parent scope
        symbol = ast.symbol
        assert symbol
        assert symbol.identifier is not None
        assert symbol.templateParams is None
        assert symbol.templateArgs is None
        parentSymbol = symbol.parent
        assert parentSymbol
        if parentSymbol.parent is None:
            # TODO: we could warn, but it is somewhat equivalent to unscoped
            # enums, without the enum
            return  # no parent
        parentDecl = parentSymbol.declaration
        if parentDecl is None:
            # the parent is not explicitly declared
            # TODO: we could warn, but it could be a style to just assume
            # enumerator parnets to be scoped
            return
        if parentDecl.objectType != 'enum':
            # TODO: maybe issue a warning, enumerators in non-enums is weird,
            # but it is somewhat equivalent to unscoped enums, without the enum
            return
        if parentDecl.scoped:
            return

        targetSymbol = parentSymbol.parent
        s = targetSymbol.find_identifier(symbol.identifier)
        if s is not None:
            # something is already declared with that name
            return
        Symbol(parent=targetSymbol, identifier=symbol.identifier,
               templateParams=None, templateArgs=None,
               declaration=symbol.declaration.clone())

    def add_target_and_index(self, ast, sig, signode):
        # general note: name must be lstrip(':')'ed, to remove "::"
        try:
            id_v1 = ast.get_id_v1()
        except NoOldIdError:
            id_v1 = None
        id_v2 = ast.get_id_v2()
        # store them in reverse order, so the newest is first
        ids  = [id_v2, id_v1]

        newestId = ids[0]
        assert newestId  # shouldn't be None
        if not re.compile(r'^[a-zA-Z0-9_]*$').match(newestId):
            self.warn('Index id generation for C++ object "%s" failed, please '
                      'report as bug (id=%s).' % (text_type(ast), newestId))

        name = text_type(ast.symbol.get_full_nested_name()).lstrip(':')
        indexText = self.get_index_text(name)
        self.indexnode['entries'].append(('single', indexText, newestId, ''))

        if newestId not in self.state.document.ids:
            # if the name is not unique, the first one will win
            names = self.env.domaindata['cpp']['names']
            if name not in names:
                names[name] = ast.symbol.docname
                signode['names'].append(name)
            else:
                # print("[CPP] non-unique name:", name)
                pass
            for id in ids:
                if id:  # is None when the element didn't exist in that version
                    signode['ids'].append(id)
            signode['first'] = (not self.names)  # hmm, what is this abound?
            self.state.document.note_explicit_target(signode)

    def parse_definition(self, parser):
        raise NotImplementedError()

    def describe_signature(self, signode, ast, parentScope):
        raise NotImplementedError()

    def handle_signature(self, sig, signode):
        if 'cpp:parentSymbol' not in self.env.ref_context:
            root = self.env.domaindata['cpp']['rootSymbol']
            self.env.ref_context['cpp:parentSymbol'] = root
        parentSymbol = self.env.ref_context['cpp:parentSymbol']

        parser = DefinitionParser(sig, self)
        try:
            ast = self.parse_definition(parser)
            parser.assert_end()
        except DefinitionError as e:
            self.warn(e.description)
            # It is easier to assume some phony name than handling the error in
            # the possibly inner declarations.
            name = _make_phony_error_name()
            symbol = parentSymbol.add_name(name)
            self.env.ref_context['cpp:lastSymbol'] = symbol
            raise ValueError
        symbol = parentSymbol.add_declaration(ast)
        self.env.ref_context['cpp:lastSymbol'] = symbol
        symbol.docname = self.env.docname

        if ast.objectType == 'enumerator':
            self._add_enumerator_to_parent(ast)

        self.describe_signature(signode, ast)
        return ast


class CPPTypeObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ type)') % name

    def parse_definition(self, parser):
        return parser.parse_declaration("type")

    def describe_signature(self, signode, ast):
        ast.describe_signature(signode, 'lastIsName', self.env)


class CPPMemberObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ member)') % name

    def parse_definition(self, parser):
        return parser.parse_declaration("member")

    def describe_signature(self, signode, ast):
        ast.describe_signature(signode, 'lastIsName', self.env)


class CPPFunctionObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ function)') % name

    def parse_definition(self, parser):
        return parser.parse_declaration("function")

    def describe_signature(self, signode, ast):
        ast.describe_signature(signode, 'lastIsName', self.env)


class CPPClassObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ class)') % name

    def before_content(self):
        lastSymbol = self.env.ref_context['cpp:lastSymbol']
        assert lastSymbol
        self.oldParentSymbol = self.env.ref_context['cpp:parentSymbol']
        self.env.ref_context['cpp:parentSymbol'] = lastSymbol

    def after_content(self):
        self.env.ref_context['cpp:parentSymbol'] = self.oldParentSymbol

    def parse_definition(self, parser):
        return parser.parse_declaration("class")

    def describe_signature(self, signode, ast):
        ast.describe_signature(signode, 'lastIsName', self.env)


class CPPEnumObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ enum)') % name

    def before_content(self):
        lastSymbol = self.env.ref_context['cpp:lastSymbol']
        assert lastSymbol
        self.oldParentSymbol = self.env.ref_context['cpp:parentSymbol']
        self.env.ref_context['cpp:parentSymbol'] = lastSymbol

    def after_content(self):
        self.env.ref_context['cpp:parentSymbol'] = self.oldParentSymbol

    def parse_definition(self, parser):
        ast = parser.parse_declaration("enum")
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

    def describe_signature(self, signode, ast):
        ast.describe_signature(signode, 'lastIsName', self.env)


class CPPEnumeratorObject(CPPObject):
    def get_index_text(self, name):
        return _('%s (C++ enumerator)') % name

    def parse_definition(self, parser):
        return parser.parse_declaration("enumerator")

    def describe_signature(self, signode, ast):
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

    def warn(self, msg):
        self.state_machine.reporter.warning(msg, lineno=self.lineno)

    def run(self):
        env = self.state.document.settings.env
        rootSymbol = env.domaindata['cpp']['rootSymbol']
        if self.arguments[0].strip() in ('NULL', '0', 'nullptr'):
            env.ref_context['cpp:parentSymbol'] = rootSymbol
        else:
            parser = DefinitionParser(self.arguments[0], self)
            try:
                ast = parser.parse_namespace_object()
                parser.assert_end()
            except DefinitionError as e:
                self.state_machine.reporter.warning(e.description,
                                                    line=self.lineno)
                name = _make_phony_error_name()
                ast = ASTNamespace(name, None)
            s = rootSymbol.add_name(ast.nestedName, ast.templatePrefix)
            env.ref_context['cpp:parentSymbol'] = s
        return []


class CPPXRefRole(XRefRole):
    def process_link(self, env, refnode, has_explicit_title, title, target):
        parent = env.ref_context.get('cpp:parentSymbol', None)
        if parent:
            refnode['cpp:parentKey'] = parent.get_lookup_key()
        # TODO: should this really be here?
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
        'rootSymbol': Symbol(None, None, None, None, None),
        'names': {}  # full name for indexing -> docname
    }

    def clear_doc(self, docname):
        rootSymbol = self.data['rootSymbol']
        for symbol in rootSymbol.get_all_symbols():
            if not symbol.declaration:
                continue
            try:
                sDocname = symbol.docname
            except AttributeError:
                # it's a template parameter
                # the symbols are yielded in post-order, so this should be fine
                assert symbol.parent
                sDocname = symbol.parent.docname
            if sDocname != docname:
                continue
            symbol.declaration = None
            symbol.docname = None
        for name, nDocname in list(self.data['names'].items()):
            if nDocname == docname:
                del self.data['names'][name]

    def process_doc(self, env, docname, document):
        # just for debugging
        # print(self.data['rootSymbol'].dump(0))
        pass

    # def merge_domaindata(self, docnames, otherdata):
    #    # TODO: merge rootSymbol

    def _resolve_xref_inner(self, env, fromdocname, builder,
                            target, node, contnode, warn=True):
        parser = DefinitionParser(target, env)
        try:
            ast = parser.parse_xref_object()
            parser.skip_ws()
            if not parser.eof:
                raise DefinitionError('')
        except DefinitionError:
            if warn:
                env.warn_node('Unparseable C++ cross-reference: %r' % target, node)
            return None, None
        parentKey = node.get("cpp:parentKey", None)
        rootSymbol = self.data['rootSymbol']
        if parentKey:
            parentSymbol = rootSymbol.direct_lookup(parentKey)
            if not parentSymbol:
                print("Target: ", target)
                print("ParentKey: ", parentKey)
            assert parentSymbol  # should be there
        else:
            parentSymbol = rootSymbol

        name = ast.nestedName
        if ast.templatePrefix:
            templateDecls = ast.templatePrefix.templates
        else:
            templateDecls = []
        s = parentSymbol.find_name(name, templateDecls,
                                   specific_specialisation=False)
        if s is None or s.declaration is None:
            return None, None
        declaration = s.declaration
        fullNestedName = s.get_full_nested_name()
        name = text_type(fullNestedName).lstrip(':')
        try:
            docname = s.docname
        except AttributeError:
            # it's a template parameter
            assert s.parent
            docname = s.parent.docname
        return make_refnode(builder, fromdocname, docname,
                            declaration.get_newest_id(), contnode, name
                            ), declaration.objectType

    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):
        return self._resolve_xref_inner(env, fromdocname, builder, target,
                                        node, contnode)[0]

    def resolve_any_xref(self, env, fromdocname, builder, target,
                         node, contnode):
        node, objtype = self._resolve_xref_inner(env, fromdocname, builder,
                                                 target, node, contnode,
                                                 warn=False)
        if node:
            return [('cpp:' + self.role_for_objtype(objtype), node)]
        return []

    def get_objects(self):
        rootSymbol = self.data['rootSymbol']
        for symbol in rootSymbol.get_all_symbols():
            if not symbol.declaration:
                continue
            name = text_type(symbol.get_full_nested_name()).lstrip(':')
            objectType = symbol.declaration.objectType
            try:
                docname = symbol.docname
            except AttributeError:
                continue
            newestId = symbol.declaration.get_newest_id()
            yield (name, name, objectType, docname, newestId, 1)
