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


_identifier_re = re.compile(r'(~?[a-zA-Z_][a-zA-Z0-9_]*)')
_whitespace_re = re.compile(r'\s+(?u)')
_string_re = re.compile(r"[LuU8]?('([^'\\]*(?:\\.[^'\\]*)*)'"
                        r'|"([^"\\]*(?:\\.[^"\\]*)*)")', re.S)
_operator_re = re.compile(r'''(?x)
        \[\s*\]
    |   \(\s*\)
    |   [!<>=/*%+-|&^]=?
    |   <<=? | >>=? | ~ | ^ | & | && | \| | \|\|
''')


class DefinitionError(Exception):
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


class _ModifierDefExpr(_DefExpr):

    def __init__(self, modifiers, typename):
        self.modifiers = modifiers
        self.typename = typename

    def __unicode__(self):
        return u' '.join(map(unicode, list(self.modifiers) + [self.typename]))


class _PtrDefExpr(_DefExpr):

    def __init__(self, typename):
        self.typename = typename

    def __unicode__(self):
        return u'%s*' % self.typename


class _RefDefExpr(_DefExpr):

    def __init__(self, typename):
        self.typename = typename

    def __unicode__(self):
        return u'%s&' % self.typename


class _CastOpDefExpr(_DefExpr):

    def __init__(self, typename):
        self.typename = typename

    def __unicode__(self):
        return u'operator %s' % self.typename


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

    # mapping of valid type modifiers.  if the set is None it means
    # the modifier can prefix all types, otherwise only the types
    # (actually more keywords) in the set.  Also check
    # _guess_typename when changing this
    _modifiers = {
        'volatile':     None,
        'register':     None,
        'const':        None,
        'mutable':      None,
        'typename':     None,
        'unsigned':     set(('char', 'int', 'long')),
        'signed':       set(('char', 'int', 'long')),
        'short':        set(('int', 'short')),
        'long':         set(('int', 'long'))
    }

    def __init__(self, definition):
        self.definition = definition.strip()
        self.pos = 0
        self.end = len(self.definition)
        self.last_match = None
        self._previous_state = (0, None)

    def fail(self, msg):
        raise DefinitionError('Invalid definition: %s [error at %d]\n  %s' %
            (msg, self.pos, self.definition))

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

    def _parse_operator(self):
        # thank god, a regular operator definition
        if self.match(_operator_re):
            return _NameDefExpr('operator' +
                                _whitespace_re.sub('', self.matched_text))

        # oh well, looks like a cast operator definition.
        # In that case, eat another type.
        type = self._parse_type()
        return _CastOpDefExpr(type)

    def _parse_name(self):
        if not self.match(_identifier_re):
            self.fail('expected name')
        identifier = self.matched_text

        # strictly speaking, operators are not regular identifiers
        # but because operator is a keyword, it might not be used
        # for variable names anyways, so we can safely parse the
        # operator here as identifier
        if identifier == 'operator':
            return self._parse_operator()

        return _NameDefExpr(identifier)

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

    def _guess_typename(self, path):
        if not path:
            return [], 'int'
        # for the long type, we don't want the int in there
        if 'long' in path:
            path = [x for x in path if x != 'int']
            # remove one long
            path.remove('long')
            return path, 'long'
        if path[-1] in ('int', 'char'):
            return path[:-1], path[-1]
        return path, 'int'

    def _attach_refptr(self, expr):
        self.skip_ws()
        if self.skip_string('*'):
            return _PtrDefExpr(expr)
        elif self.skip_string('&'):
            return _RefDefExpr(expr)
        return expr

    def _parse_builtin(self, modifier):
        path = [modifier]
        following = self._modifiers[modifier]
        while 1:
            self.skip_ws()
            if not self.match(_identifier_re):
                break
            identifier = self.matched_text
            if identifier in following:
                path.append(identifier)
                following = self._modifiers[modifier]
                assert following
            else:
                self.backout()
                break
        modifiers, typename = self._guess_typename(path)
        rv = _ModifierDefExpr(modifiers, _NameDefExpr(typename))
        return self._attach_refptr(rv)

    def _parse_type(self, in_template=False):
        result = []
        modifiers = []

        # if there is a leading :: or not, we don't care because we
        # treat them exactly the same.  Buf *if* there is one, we
        # don't have to check for type modifiers
        if not self.skip_string('::'):
            self.skip_ws()
            if self.match(_identifier_re):
                modifier = self.matched_text
                if modifier in self._modifiers:
                    following = self._modifiers[modifier]
                    # if the set is not none, there is a limited set
                    # of types that might follow.  It is technically
                    # impossible for a template to follow, so what
                    # we do is go to a different function that just
                    # eats types
                    if following is not None:
                        return self._parse_builtin(modifier)
                    modifiers.append(modifier)
                else:
                    self.backout()

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
            rv = result[0]
        else:
            rv = _PathDefExpr(result)
        if modifiers:
            rv = _ModifierDefExpr(modifiers, rv)
        return self._attach_refptr(rv)

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

    def parse_typename(self):
        return self._parse_type()

    def assert_end(self):
        self.skip_ws()
        if not self.eof:
            self.fail('expected end of definition, got %r' %
                      self.definition[self.pos:])


class CPPObject(ObjectDescription):
    """Description of a C++ language object."""

    def _attach_type(self, node, type):
        # XXX: link? how could we do that
        text = unicode(type) + u' '
        pnode = addnodes.pending_xref(
            '', refdomain='cpp', reftype='type',
            reftarget=text, modname=None, classname=None)
        pnode += nodes.Text(text)
        node += pnode

    def handle_signature(self, sig, signode):
        """Transform a C++ signature into RST nodes."""
        parser = DefinitionParser(sig)
        typename = parser.parse_typename()
        parser.assert_end()

        signode += addnodes.desc_type('', '')
        self._attach_type(signode, typename)
        return unicode(typename)


class CPPTypedObject(CPPObject):

    def _attach_var(self, node, var):
        owner, name = var.name.split_owner()
        varname = unicode(name)
        if owner is not None:
            owner = unicode(owner) + '::'
            node += addnodes.desc_addname(owner, owner)
        node += addnodes.desc_name(varname, varname)

    def handle_signature(self, sig, signode):
        """Transform a C++ signature into RST nodes."""
        parser = DefinitionParser(sig)
        rv, var = parser.parse_variable()
        parser.assert_end()

        signode += addnodes.desc_type('', '')
        self._attach_type(signode, rv)
        self._attach_var(signode, var)
        return str(func.name)


class CPPFunctionObject(CPPTypedObject):

    def _attach_function(self, node, func):
        owner, name = func.name.split_owner()
        funcname = unicode(name)
        if owner is not None:
            owner = unicode(owner) + '::'
            node += addnodes.desc_addname(owner, owner)
        node += addnodes.desc_name(funcname, funcname)

        paramlist = addnodes.desc_parameterlist()
        for arg in func.signature:
            param = addnodes.desc_parameter('', '', noemph=True)
            if arg.type is not None:
                self._attach_type(param, arg.type)
            param += nodes.emphasis(unicode(arg.name), unicode(arg.name))
            if arg.default is not None:
                def_ = u'=' + unicode(arg.default)
                param += nodes.emphasis(def_, def_)
            paramlist += param

        node += paramlist
        if func.const:
            node += addnodes.desc_addname(' const', ' const')
        if func.pure_virtual:
            node += addnodes.desc_addname(' = 0', ' = 0')

    def handle_signature(self, sig, signode):
        """Transform a C++ signature into RST nodes."""
        parser = DefinitionParser(sig)
        rv, func = parser.parse_function()
        parser.assert_end()

        signode += addnodes.desc_type('', '')
        self._attach_type(signode, rv)
        self._attach_function(signode, func)
        return str(func.name)


class CPPDomain(Domain):
    """C++ language domain."""
    name = 'cpp'
    label = 'C++'
    object_types = {
        'class':    ObjType(l_('C++ class'),    'class'),
        'function': ObjType(l_('C++ function'), 'func'),
        'member':   ObjType(l_('C++ member'),   'member'),
        'type':     ObjType(l_('C++ type'),     'type'),
        'var':      ObjType(l_('C++ variable'), 'data'),
    }

    directives = {
        'class':    CPPObject,
        'function': CPPFunctionObject,
        'member':   CPPTypedObject,
        'type':     CPPTypedObject,
        'var':      CPPTypedObject,
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
