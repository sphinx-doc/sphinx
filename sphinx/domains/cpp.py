# -*- coding: utf-8 -*-
"""
    sphinx.domains.cpp
    ~~~~~~~~~~~~~~~~~~

    The C++ language domain.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import string

from docutils import nodes

from sphinx import addnodes
from sphinx.roles import XRefRole
from sphinx.locale import l_, _
from sphinx.domains import Domain, ObjType
from sphinx.directives import ObjectDescription
from sphinx.util.nodes import make_refnode
from sphinx.util.docfields import Field, TypedField


_identifier_re = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
_whitespace_re = re.compile(r'\s+(?u)')
_string_re = re.compile(r"[LuU8]?('([^'\\]*(?:\\.[^'\\]*)*)'"
                        r'|"([^"\\]*(?:\\.[^"\\]*)*)")', re.S)


class DefinitionError(ValueError):
    pass


class _DefExpr(object):

    def __unicode__(self):
        raise NotImplementedError()

    def split_owner(self):
        return None, self

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return '<defexpr %s>' % self


class _NameDefExpr(_DefExpr):

    def __init__(self, name):
        self.name = name

    def __unicode__(self):
        return unicode(self.name)


class _PathDefExpr(_DefExpr):

    def __init__(self, parts):
        self.path = parts

    def split_owner(self):
        if len(self.path) > 1:
            return _PathDefExpr(self.path[:-1]), self.path[-1]
        return _DefExpr.split_owner(self)

    def __unicode__(self):
        return u'::'.join(map(unicode, self.path))


class _TemplateDefExpr(_DefExpr):

    def __init__(self, typename, args):
        self.typename = typename
        self.args = args

    def __unicode__(self):
        return u'%s<%s>' % (self.typename, u', '.join(map(unicode, self.args)))


class _ArgumentDefExpr(_DefExpr):

    def __init__(self, type, name, default=None):
        self.type = type
        self.name = name
        self.default = default

    def __unicode__(self):
        return (self.type is not None and u'%s %s' % (self.type, self.name)
                or unicode(self.name)) + (self.default is not None and
                                          u'=%s' % self.default or u'')


class _FunctionDefExpr(_DefExpr):

    def __init__(self, name, signature, const, pure_virtual):
        self.name = name
        self.signature = signature
        self.const = const
        self.pure_virtual = pure_virtual

    def __unicode__(self):
        return u'%s(%s)%s%s' % (
            self.name,
            u', '.join(map(unicode, self.signature)),
            self.const and u' const' or u'',
            self.pure_virtual and ' = 0' or ''
        )


class DefinitionParser(object):

    def __init__(self, definition):
        self.definition = definition.strip()
        self.pos = 0
        self.end = len(self.definition)
        self.last_match = None
        self._previous_state = (0, None)

    def fail(self, msg):
        raise DefinitionError('Invalid definition: "%s", %s [error at %d]' %
            (self.definition, msg, self.pos))

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

    def skip_ws(self):
        return self.match(_whitespace_re) is not None

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

    def _parse_name(self):
        if not self.match(_identifier_re):
            self.fail('expected name')
        return _NameDefExpr(self.matched_text)

    def _parse_type_expr(self):
        typename = self._parse_name()
        self.skip_ws()
        if not self.skip_string('<'):
            return typename

        args = []
        while 1:
            self.skip_ws()
            if self.skip_string('>'):
                break
            if args:
                if not self.skip_string(','):
                    self.fail('"," or ">" in template expected')
                self.skip_ws()
            args.append(self._parse_type(True))
        return _TemplateDefExpr(typename, args)

    def _parse_type(self, in_template=False):
        result = []

        # if there is a leading :: or not, we don't care because we
        # treat them exactly the same
        self.skip_string('::')

        while 1:
            self.skip_ws()
            if (in_template and self.current_char in ',>') or \
               (result and not self.skip_string('::')) or \
               self.eof:
                break
            result.append(self._parse_type_expr())

        if not result:
            self.fail('expected type')
        if len(result) == 1:
            return result[0]
        return _PathDefExpr(result)

    def _parse_default_expr(self):
        self.skip_ws()
        if self.match(_string_re):
            return self.matched_text
        idx1 = self.definition.find(',', self.pos)
        idx2 = self.definition.find(')', self.pos)
        if idx1 < 0:
            idx = idx2
        elif idx2 < 0:
            idx = idx1
        else:
            idx = min(idx1, idx2)
        if idx < 0:
            self.fail('unexpected end in default expression')
        rv = self.definition[self.pos:idx]
        self.pos = idx
        return rv

    def _parse_signature(self):
        self.skip_ws()
        if not self.skip_string('('):
            self.fail('expected parentheses for function')

        args = []
        while 1:
            self.skip_ws()
            if self.eof:
                self.fail('missing closing parentheses')
            if self.skip_string(')'):
                break
            if args:
                if not self.skip_string(','):
                    self.fail('expected comma between arguments')
                self.skip_ws()

            argname = self._parse_type()
            argtype = default = None
            self.skip_ws()
            if self.skip_string('='):
                self.pos += 1
                default = self._parse_default_expr()
            elif self.current_char not in ',)':
                argtype = argname
                argname = self._parse_name()
                self.skip_ws()
                if self.skip_string('='):
                    default = self._parse_default_expr()

            args.append(_ArgumentDefExpr(argtype, argname, default))
        self.skip_ws()
        const = self.skip_string('const')
        if const:
            self.skip_ws()
        if self.skip_string('='):
            self.skip_ws()
            if not (self.skip_string('0') or \
                    self.skip_string('NULL') or \
                    self.skip_string('nullptr')):
                self.fail('pure virtual functions must be defined with '
                          'either 0, NULL or nullptr, other macros are '
                          'not allowed')
            pure_virtual = True
        else:
            pure_virtual = False
        return args, const, pure_virtual

    def parse_variable(self):
        type = self._parse_type()
        name = self._parse_type()
        return type, name

    def parse_function(self):
        rv = self._parse_type()
        name = self._parse_type()
        return rv, _FunctionDefExpr(name, *self._parse_signature())


class CPPObject(ObjectDescription):
    """Description of a C++ language object."""


class CPPDomain(Domain):
    """C++ language domain."""
    name = 'cpp'
    label = 'C++'
    object_types = {
        'class':    ObjType(l_('C++ class'),    'class'),
        'function': ObjType(l_('C++ function'), 'func'),
        'member':   ObjType(l_('C++ member'),   'member'),
        'macro':    ObjType(l_('C++ macro'),    'macro'),
        'type':     ObjType(l_('C++ type'),     'type'),
        'var':      ObjType(l_('C++ variable'), 'data'),
    }

    directives = {
        'class':    CPPObject,
        'function': CPPObject,
        'member':   CPPObject,
        'macro':    CPPObject,
        'type':     CPPObject,
        'var':      CPPObject,
    }
    roles = {
        'class':  XRefRole(),
        'func' :  XRefRole(fix_parens=True),
        'member': XRefRole(),
        'macro':  XRefRole(),
        'data':   XRefRole(),
        'type':   XRefRole(),
    }
    initial_data = {
        'objects': {},  # fullname -> docname, objtype
    }

    def clear_doc(self, docname):
        for fullname, (fn, _) in self.data['objects'].items():
            if fn == docname:
                del self.data['objects'][fullname]

    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):
        # strip pointer asterisk
        target = target.rstrip(' *')
        if target not in self.data['objects']:
            return None
        obj = self.data['objects'][target]
        return make_refnode(builder, fromdocname, obj[0], target,
                            contnode, target)

    def get_objects(self):
        for refname, (docname, type) in self.data['objects'].iteritems():
            yield (refname, type, docname, refname, 1)
