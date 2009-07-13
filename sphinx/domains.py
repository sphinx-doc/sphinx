# -*- coding: utf-8 -*-
"""
    sphinx.domains
    ~~~~~~~~~~~~~~

    Support for domains, which are groupings of description directives
    and roles describing e.g. constructs of one programming language.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from sphinx import addnodes
from sphinx.roles import XRefRole
from sphinx.directives import DescDirective


class Domain(object):
    name = ''
    directives = {}
    roles = {}
    label = ''

    def __init__(self):
        self._role_cache = {}
        self._directive_cache = {}

    def __getstate__(self):
        # can't pickle the adapter caches
        state = self.__dict__.copy()
        state['_role_cache'] = {}
        state['_directive_cache'] = {}
        return state

    def role(self, name):
        """
        Return a role adapter function that always gives the registered
        role its full name ('domain:name') as the first argument.
        """
        if name in self._role_cache:
            return self._role_cache[name]
        if name not in self.roles:
            return None
        fullname = '%s:%s' % (self.name, name)
        def role_adapter(typ, rawtext, text, lineno, inliner,
                         options={}, content=[]):
            return self.roles[name](fullname, rawtext, text, lineno,
                                    inliner, options, content)
        self._role_cache[name] = role_adapter
        return role_adapter
        
    def directive(self, name):
        """
        Return a directive adapter class that always gives the registered
        directive its full name ('domain:name') as ``self.name``.
        """
        if name in self._directive_cache:
            return self._directive_cache[name]
        if name not in self.directives:
            return None
        fullname = '%s:%s' % (self.name, name)
        BaseDirective = self.directives[name]
        class DirectiveAdapter(BaseDirective):
            def run(self):
                self.name = fullname
                return BaseDirective.run(self)
        self._directive_cache[name] = DirectiveAdapter
        return DirectiveAdapter

    def resolve_xref(self, typ, target, node, contnode):
        pass


# REs for Python signatures
py_sig_re = re.compile(
    r'''^ ([\w.]*\.)?            # class name(s)
          (\w+)  \s*             # thing name
          (?: \((.*)\)           # optional: arguments
           (?:\s* -> \s* (.*))?  #           return annotation
          )? $                   # and nothing more
          ''', re.VERBOSE)

py_paramlist_re = re.compile(r'([\[\],])')  # split at '[', ']' and ','


class PythonDesc(DescDirective):
    """
    Description of a general Python object.
    """

    def get_signature_prefix(self, sig):
        """
        May return a prefix to put before the object name in the signature.
        """
        return ''

    def needs_arglist(self):
        """
        May return true if an empty argument list is to be generated even if
        the document contains none.
        """
        return False

    def parse_signature(self, sig, signode):
        """
        Transform a Python signature into RST nodes.
        Returns (fully qualified name of the thing, classname if any).

        If inside a class, the current class name is handled intelligently:
        * it is stripped from the displayed name if present
        * it is added to the full name (return value) if not present
        """
        m = py_sig_re.match(sig)
        if m is None:
            raise ValueError
        classname, name, arglist, retann = m.groups()

        if self.env.currclass:
            add_module = False
            if classname and classname.startswith(self.env.currclass):
                fullname = classname + name
                # class name is given again in the signature
                classname = classname[len(self.env.currclass):].lstrip('.')
            elif classname:
                # class name is given in the signature, but different
                # (shouldn't happen)
                fullname = self.env.currclass + '.' + classname + name
            else:
                # class name is not given in the signature
                fullname = self.env.currclass + '.' + name
        else:
            add_module = True
            fullname = classname and classname + name or name

        prefix = self.get_signature_prefix(sig)
        if prefix:
            signode += addnodes.desc_annotation(prefix, prefix)

        if classname:
            signode += addnodes.desc_addname(classname, classname)
        # exceptions are a special case, since they are documented in the
        # 'exceptions' module.
        elif add_module and self.env.config.add_module_names:
            modname = self.options.get('module', self.env.currmodule)
            if modname and modname != 'exceptions':
                nodetext = modname + '.'
                signode += addnodes.desc_addname(nodetext, nodetext)

        signode += addnodes.desc_name(name, name)
        if not arglist:
            if self.needs_arglist():
                # for callables, add an empty parameter list
                signode += addnodes.desc_parameterlist()
            if retann:
                signode += addnodes.desc_returns(retann, retann)
            return fullname, classname
        signode += addnodes.desc_parameterlist()

        stack = [signode[-1]]
        for token in py_paramlist_re.split(arglist):
            if token == '[':
                opt = addnodes.desc_optional()
                stack[-1] += opt
                stack.append(opt)
            elif token == ']':
                try:
                    stack.pop()
                except IndexError:
                    raise ValueError
            elif not token or token == ',' or token.isspace():
                pass
            else:
                token = token.strip()
                stack[-1] += addnodes.desc_parameter(token, token)
        if len(stack) != 1:
            raise ValueError
        if retann:
            signode += addnodes.desc_returns(retann, retann)
        return fullname, classname

    def get_index_text(self, modname, name):
        """
        Return the text for the index entry of the object.
        """
        raise NotImplementedError('must be implemented in subclasses')

    def add_target_and_index(self, name_cls, sig, signode):
        modname = self.options.get('module', self.env.currmodule)
        fullname = (modname and modname + '.' or '') + name_cls[0]
        # note target
        if fullname not in self.state.document.ids:
            signode['names'].append(fullname)
            signode['ids'].append(fullname)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            self.env.note_descref(fullname, self.desctype, self.lineno)

        indextext = self.get_index_text(modname, name_cls)
        if indextext:
            self.indexnode['entries'].append(('single', indextext,
                                              fullname, fullname))

    def before_content(self):
        # needed for automatic qualification of members (reset in subclasses)
        self.clsname_set = False

    def after_content(self):
        if self.clsname_set:
            self.env.currclass = None


class ModulelevelDesc(PythonDesc):
    """
    Description of an object on module level (functions, data).
    """

    def needs_arglist(self):
        return self.desctype == 'function'

    def get_index_text(self, modname, name_cls):
        if self.desctype == 'function':
            if not modname:
                return _('%s() (built-in function)') % name_cls[0]
            return _('%s() (in module %s)') % (name_cls[0], modname)
        elif self.desctype == 'data':
            if not modname:
                return _('%s (built-in variable)') % name_cls[0]
            return _('%s (in module %s)') % (name_cls[0], modname)
        else:
            return ''


class ClasslikeDesc(PythonDesc):
    """
    Description of a class-like object (classes, interfaces, exceptions).
    """

    def get_signature_prefix(self, sig):
        return self.desctype + ' '

    def get_index_text(self, modname, name_cls):
        if self.desctype == 'class':
            if not modname:
                return _('%s (built-in class)') % name_cls[0]
            return _('%s (class in %s)') % (name_cls[0], modname)
        elif self.desctype == 'exception':
            return name_cls[0]
        else:
            return ''

    def before_content(self):
        PythonDesc.before_content(self)
        if self.names:
            self.env.currclass = self.names[0][0]
            self.clsname_set = True


class ClassmemberDesc(PythonDesc):
    """
    Description of a class member (methods, attributes).
    """

    def needs_arglist(self):
        return self.desctype.endswith('method')

    def get_signature_prefix(self, sig):
        if self.desctype == 'staticmethod':
            return 'static '
        elif self.desctype == 'classmethod':
            return 'classmethod '
        return ''

    def get_index_text(self, modname, name_cls):
        name, cls = name_cls
        add_modules = self.env.config.add_module_names
        if self.desctype == 'method':
            try:
                clsname, methname = name.rsplit('.', 1)
            except ValueError:
                if modname:
                    return _('%s() (in module %s)') % (name, modname)
                else:
                    return '%s()' % name
            if modname and add_modules:
                return _('%s() (%s.%s method)') % (methname, modname, clsname)
            else:
                return _('%s() (%s method)') % (methname, clsname)
        elif self.desctype == 'staticmethod':
            try:
                clsname, methname = name.rsplit('.', 1)
            except ValueError:
                if modname:
                    return _('%s() (in module %s)') % (name, modname)
                else:
                    return '%s()' % name
            if modname and add_modules:
                return _('%s() (%s.%s static method)') % (methname, modname,
                                                          clsname)
            else:
                return _('%s() (%s static method)') % (methname, clsname)
        elif self.desctype == 'classmethod':
            try:
                clsname, methname = name.rsplit('.', 1)
            except ValueError:
                if modname:
                    return _('%s() (in module %s)') % (name, modname)
                else:
                    return '%s()' % name
            if modname:
                return _('%s() (%s.%s class method)') % (methname, modname,
                                                         clsname)
            else:
                return _('%s() (%s class method)') % (methname, clsname)
        elif self.desctype == 'attribute':
            try:
                clsname, attrname = name.rsplit('.', 1)
            except ValueError:
                if modname:
                    return _('%s (in module %s)') % (name, modname)
                else:
                    return name
            if modname and add_modules:
                return _('%s (%s.%s attribute)') % (attrname, modname, clsname)
            else:
                return _('%s (%s attribute)') % (attrname, clsname)
        else:
            return ''

    def before_content(self):
        PythonDesc.before_content(self)
        if self.names and self.names[-1][1] and not self.env.currclass:
            self.env.currclass = self.names[-1][1].strip('.')
            self.clsname_set = True


class PyXRefRole(XRefRole):
    def process_link(self, env, pnode, has_explicit_title, title, target):
        pnode['modname'] = env.currmodule
        pnode['classname'] = env.currclass
        if not has_explicit_title:
            title = title.lstrip('.')   # only has a meaning for the target
            target = target.lstrip('~') # only has a meaning for the title
            # if the first character is a tilde, don't display the module/class
            # parts of the contents
            if title[0:1] == '~':
                title = title[1:]
                dot = title.rfind('.')
                if dot != -1:
                    title = title[dot+1:]
        # if the first character is a dot, search more specific namespaces first
        # else search builtins first
        if target[0:1] == '.':
            target = target[1:]
            pnode['refspecific'] = True
        return title, target


class PythonDomain(Domain):
    """Python language domain."""
    name = 'py'
    label = 'Python'
    directives = {
        'function': ModulelevelDesc,
        'data': ModulelevelDesc,
        'class': ClasslikeDesc,
        'exception': ClasslikeDesc,
        'method': ClassmemberDesc,
        'classmethod': ClassmemberDesc,
        'staticmethod': ClassmemberDesc,
        'attribute': ClassmemberDesc,
    }
    roles = {
        'data': PyXRefRole(),
        'exc': PyXRefRole(),
        'func': PyXRefRole(fix_parens=True),
        'class': PyXRefRole(),
        'const': PyXRefRole(),
        'attr': PyXRefRole(),
        'meth': PyXRefRole(fix_parens=True),
        'mod': PyXRefRole(),
        'obj': PyXRefRole(),
    }

    def find_desc(self, env, modname, classname, name, type, searchorder=0):
        """Find a description node matching "name", perhaps using
           the given module and/or classname."""
        # skip parens
        if name[-2:] == '()':
            name = name[:-2]

        if not name:
            return None, None

        # don't add module and class names for C things
        if type[0] == 'c' and type not in ('class', 'const'):
            # skip trailing star and whitespace
            name = name.rstrip(' *')
            if name in env.descrefs and env.descrefs[name][1][0] == 'c':
                return name, env.descrefs[name]
            return None, None

        newname = None
        if searchorder == 1:
            if modname and classname and \
                   modname + '.' + classname + '.' + name in env.descrefs:
                newname = modname + '.' + classname + '.' + name
            elif modname and modname + '.' + name in env.descrefs:
                newname = modname + '.' + name
            elif name in env.descrefs:
                newname = name
        else:
            if name in env.descrefs:
                newname = name
            elif modname and modname + '.' + name in env.descrefs:
                newname = modname + '.' + name
            elif modname and classname and \
                     modname + '.' + classname + '.' + name in env.descrefs:
                newname = modname + '.' + classname + '.' + name
            # special case: builtin exceptions have module "exceptions" set
            elif type == 'exc' and '.' not in name and \
                 'exceptions.' + name in env.descrefs:
                newname = 'exceptions.' + name
            # special case: object methods
            elif type in ('func', 'meth') and '.' not in name and \
                 'object.' + name in env.descrefs:
                newname = 'object.' + name
        if newname is None:
            return None, None
        return newname, env.descrefs[newname]

    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):

        if typ == 'mod' or \
           typ == 'obj' and target in env.modules:
            docname, synopsis, platform, deprecated = \
                env.modules.get(target, ('','','', ''))
            if not docname:
                newnode = builder.app.emit_firstresult(
                    'missing-reference', env, node, contnode)
                if not newnode:
                    newnode = contnode
            elif docname == fromdocname:
                # don't link to self
                newnode = contnode
            else:
                newnode = nodes.reference('', '')
                newnode['refuri'] = builder.get_relative_uri(
                    fromdocname, docname) + '#module-' + target
                newnode['reftitle'] = '%s%s%s' % (
                    (platform and '(%s) ' % platform),
                    synopsis, (deprecated and ' (deprecated)' or ''))
                newnode.append(contnode)
        elif typ in env.descroles:
            # "descrefs"
            modname = node['modname']
            clsname = node['classname']
            searchorder = node.hasattr('refspecific') and 1 or 0
            name, desc = self.find_desc(env, modname, clsname,
                                        target, typ, searchorder)
            if not desc:
                newnode = builder.app.emit_firstresult(
                    'missing-reference', env, node, contnode)
                if not newnode:
                    newnode = contnode
            else:
                newnode = nodes.reference('', '')
                if desc[0] == fromdocname:
                    newnode['refid'] = name
                else:
                    newnode['refuri'] = (
                        builder.get_relative_uri(fromdocname, desc[0])
                        + '#' + name)
                newnode['reftitle'] = name
                newnode.append(contnode)



# RE to split at word boundaries
wsplit_re = re.compile(r'(\W+)')

# REs for C signatures
c_sig_re = re.compile(
    r'''^([^(]*?)          # return type
        ([\w:]+)  \s*      # thing name (colon allowed for C++ class names)
        (?: \((.*)\) )?    # optionally arguments
        (\s+const)? $      # const specifier
    ''', re.VERBOSE)
c_funcptr_sig_re = re.compile(
    r'''^([^(]+?)          # return type
        (\( [^()]+ \)) \s* # name in parentheses
        \( (.*) \)         # arguments
        (\s+const)? $      # const specifier
    ''', re.VERBOSE)
c_funcptr_name_re = re.compile(r'^\(\s*\*\s*(.*?)\s*\)$')


class CDesc(DescDirective):
    """
    Description of a C language object.
    """

    # These C types aren't described anywhere, so don't try to create
    # a cross-reference to them
    stopwords = set(('const', 'void', 'char', 'int', 'long', 'FILE', 'struct'))

    def _parse_type(self, node, ctype):
        # add cross-ref nodes for all words
        for part in filter(None, wsplit_re.split(ctype)):
            tnode = nodes.Text(part, part)
            if part[0] in string.ascii_letters+'_' and \
                   part not in self.stopwords:
                pnode = addnodes.pending_xref(
                    '', reftype='ctype', reftarget=part,
                    modname=None, classname=None)
                pnode += tnode
                node += pnode
            else:
                node += tnode

    def parse_signature(self, sig, signode):
        """Transform a C (or C++) signature into RST nodes."""
        # first try the function pointer signature regex, it's more specific
        m = c_funcptr_sig_re.match(sig)
        if m is None:
            m = c_sig_re.match(sig)
        if m is None:
            raise ValueError('no match')
        rettype, name, arglist, const = m.groups()

        signode += addnodes.desc_type('', '')
        self._parse_type(signode[-1], rettype)
        try:
            classname, funcname = name.split('::', 1)
            classname += '::'
            signode += addnodes.desc_addname(classname, classname)
            signode += addnodes.desc_name(funcname, funcname)
            # name (the full name) is still both parts
        except ValueError:
            signode += addnodes.desc_name(name, name)
        # clean up parentheses from canonical name
        m = c_funcptr_name_re.match(name)
        if m:
            name = m.group(1)
        if not arglist:
            if self.desctype == 'cfunction':
                # for functions, add an empty parameter list
                signode += addnodes.desc_parameterlist()
            if const:
                signode += addnodes.desc_addname(const, const)
            return name

        paramlist = addnodes.desc_parameterlist()
        arglist = arglist.replace('`', '').replace('\\ ', '') # remove markup
        # this messes up function pointer types, but not too badly ;)
        args = arglist.split(',')
        for arg in args:
            arg = arg.strip()
            param = addnodes.desc_parameter('', '', noemph=True)
            try:
                ctype, argname = arg.rsplit(' ', 1)
            except ValueError:
                # no argument name given, only the type
                self._parse_type(param, arg)
            else:
                self._parse_type(param, ctype)
                param += nodes.emphasis(' '+argname, ' '+argname)
            paramlist += param
        signode += paramlist
        if const:
            signode += addnodes.desc_addname(const, const)
        return name

    def get_index_text(self, name):
        if self.desctype == 'cfunction':
            return _('%s (C function)') % name
        elif self.desctype == 'cmember':
            return _('%s (C member)') % name
        elif self.desctype == 'cmacro':
            return _('%s (C macro)') % name
        elif self.desctype == 'ctype':
            return _('%s (C type)') % name
        elif self.desctype == 'cvar':
            return _('%s (C variable)') % name
        else:
            return ''

    def add_target_and_index(self, name, sig, signode):
        # note target
        if name not in self.state.document.ids:
            signode['names'].append(name)
            signode['ids'].append(name)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            self.env.note_descref(name, self.desctype, self.lineno)

        indextext = self.get_index_text(name)
        if indextext:
            self.indexnode['entries'].append(('single', indextext, name, name))


class CDomain(Domain):
    """C language domain."""
    name = 'c'
    label = 'C'
    directives = {
        'function': CDesc,
        'member': CDesc,
        'macro': CDesc,
        'type': CDesc,
        'var': CDesc,
    }
    roles = {
        'member': XRefRole(),
        'macro': XRefRole(),
        'func' : XRefRole(fix_parens=True),
        'data': XRefRole(),
        'type': XRefRole(),
    }


# this contains all registered domains
all_domains = {
    'py': PythonDomain,
    'c': CDomain,
}
