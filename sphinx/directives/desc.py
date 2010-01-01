# -*- coding: utf-8 -*-
"""
    sphinx.directives.desc
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import string

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.util import ws_re
from sphinx.util.compat import Directive, directive_dwim


def _is_only_paragraph(node):
    """True if the node only contains one paragraph (and system messages)."""
    if len(node) == 0:
        return False
    elif len(node) > 1:
        for subnode in node[1:]:
            if not isinstance(subnode, nodes.system_message):
                return False
    if isinstance(node[0], nodes.paragraph):
        return True
    return False


# REs for Python signatures
py_sig_re = re.compile(
    r'''^ ([\w.]*\.)?            # class name(s)
          (\w+)  \s*             # thing name
          (?: \((.*)\)           # optional: arguments
           (?:\s* -> \s* (.*))?  #           return annotation
          )? $                   # and nothing more
          ''', re.VERBOSE)

py_paramlist_re = re.compile(r'([\[\],])')  # split at '[', ']' and ','

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

# RE for option descriptions
option_desc_re = re.compile(
    r'((?:/|-|--)[-_a-zA-Z0-9]+)(\s*.*?)(?=,\s+(?:/|-|--)|$)')

# RE to split at word boundaries
wsplit_re = re.compile(r'(\W+)')

# RE to strip backslash escapes
strip_backslash_re = re.compile(r'\\(?=[^\\])')


class DescDirective(Directive):
    """
    Directive to describe a class, function or similar object.  Not used
    directly, but subclassed to add custom behavior.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'noindex': directives.flag,
        'module': directives.unchanged,
    }

    _ = lambda x: x  # make gettext extraction in constants possible

    doc_fields_with_arg = {
        'param': '%param',
        'parameter': '%param',
        'arg': '%param',
        'argument': '%param',
        'keyword': '%param',
        'kwarg': '%param',
        'kwparam': '%param',
        'type': '%type',
        'raises': _('Raises'),
        'raise': 'Raises',
        'exception': 'Raises',
        'except': 'Raises',
        'var': _('Variable'),
        'ivar': 'Variable',
        'cvar': 'Variable',
        'returns': _('Returns'),
        'return': 'Returns',
    }

    doc_fields_with_linked_arg = ('raises', 'raise', 'exception', 'except')

    doc_fields_without_arg = {
        'returns': 'Returns',
        'return': 'Returns',
        'rtype': _('Return type'),
    }

    def handle_doc_fields(self, node):
        """
        Convert field lists with known keys inside the description content into
        better-looking equivalents.
        """
        # don't traverse, only handle field lists that are immediate children
        for child in node.children:
            if not isinstance(child, nodes.field_list):
                continue
            params = []
            pfield = None
            param_nodes = {}
            param_types = {}
            new_list = nodes.field_list()
            for field in child:
                fname, fbody = field
                try:
                    typ, obj = fname.astext().split(None, 1)
                    typdesc = _(self.doc_fields_with_arg[typ])
                    if _is_only_paragraph(fbody):
                        children = fbody.children[0].children
                    else:
                        children = fbody.children
                    if typdesc == '%param':
                        if not params:
                            # add the field that later gets all the parameters
                            pfield = nodes.field()
                            new_list += pfield
                        dlitem = nodes.list_item()
                        dlpar = nodes.paragraph()
                        dlpar += nodes.emphasis(obj, obj)
                        dlpar += nodes.Text(' -- ', ' -- ')
                        dlpar += children
                        param_nodes[obj] = dlpar
                        dlitem += dlpar
                        params.append(dlitem)
                    elif typdesc == '%type':
                        typenodes = fbody.children
                        if _is_only_paragraph(fbody):
                            typenodes = ([nodes.Text(' (')] +
                                         typenodes[0].children +
                                         [nodes.Text(')')])
                        param_types[obj] = typenodes
                    else:
                        fieldname = typdesc + ' '
                        nfield = nodes.field()
                        nfieldname = nodes.field_name(fieldname, fieldname)
                        nfield += nfieldname
                        node = nfieldname
                        if typ in self.doc_fields_with_linked_arg:
                            node = addnodes.pending_xref(
                                obj, reftype='obj', refcaption=False,
                                reftarget=obj, modname=self.env.currmodule,
                                classname=self.env.currclass)
                            nfieldname += node
                        node += nodes.Text(obj, obj)
                        nfield += nodes.field_body()
                        nfield[1] += fbody.children
                        new_list += nfield
                except (KeyError, ValueError):
                    fnametext = fname.astext()
                    try:
                        typ = _(self.doc_fields_without_arg[fnametext])
                    except KeyError:
                        # at least capitalize the field name
                        typ = fnametext.capitalize()
                    fname[0] = nodes.Text(typ)
                    new_list += field
            if params:
                if len(params) == 1:
                    pfield += nodes.field_name('', _('Parameter'))
                    pfield += nodes.field_body()
                    pfield[1] += params[0][0]
                else:
                    pfield += nodes.field_name('', _('Parameters'))
                    pfield += nodes.field_body()
                    pfield[1] += nodes.bullet_list()
                    pfield[1][0].extend(params)

            for param, type in param_types.iteritems():
                if param in param_nodes:
                    param_nodes[param][1:1] = type
            child.replace_self(new_list)

    def get_signatures(self):
        """
        Retrieve the signatures to document from the directive arguments.
        """
        # remove backslashes to support (dummy) escapes; helps Vim highlighting
        return [strip_backslash_re.sub('', sig.strip())
                for sig in self.arguments[0].split('\n')]

    def parse_signature(self, sig, signode):
        """
        Parse the signature *sig* into individual nodes and append them to
        *signode*. If ValueError is raised, parsing is aborted and the whole
        *sig* is put into a single desc_name node.
        """
        raise ValueError

    def add_target_and_index(self, name, sig, signode):
        """
        Add cross-reference IDs and entries to self.indexnode, if applicable.
        """
        return  # do nothing by default

    def before_content(self):
        """
        Called before parsing content. Used to set information about the current
        directive context on the build environment.
        """
        pass

    def after_content(self):
        """
        Called after parsing content. Used to reset information about the
        current directive context on the build environment.
        """
        pass

    def run(self):
        self.desctype = self.name
        self.env = self.state.document.settings.env
        self.indexnode = addnodes.index(entries=[])

        node = addnodes.desc()
        node.document = self.state.document
        node['desctype'] = self.desctype
        node['noindex'] = noindex = ('noindex' in self.options)

        self.names = []
        signatures = self.get_signatures()
        for i, sig in enumerate(signatures):
            # add a signature node for each signature in the current unit
            # and add a reference target for it
            signode = addnodes.desc_signature(sig, '')
            signode['first'] = False
            node.append(signode)
            try:
                # name can also be a tuple, e.g. (classname, objname)
                name = self.parse_signature(sig, signode)
            except ValueError, err:
                # signature parsing failed
                signode.clear()
                signode += addnodes.desc_name(sig, sig)
                continue  # we don't want an index entry here
            if not noindex and name not in self.names:
                # only add target and index entry if this is the first
                # description of the object with this name in this desc block
                self.names.append(name)
                self.add_target_and_index(name, sig, signode)

        contentnode = addnodes.desc_content()
        node.append(contentnode)
        if self.names:
            # needed for association of version{added,changed} directives
            self.env.currdesc = self.names[0]
        self.before_content()
        self.state.nested_parse(self.content, self.content_offset, contentnode)
        self.handle_doc_fields(contentnode)
        self.env.currdesc = None
        self.after_content()
        return [self.indexnode, node]


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
                    return '%s() (in module %s)' % (name, modname)
                else:
                    return '%s()' % name
            if modname:
                return '%s() (%s.%s class method)' % (methname, modname,
                                                      clsname)
            else:
                return '%s() (%s class method)' % (methname, clsname)
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


class CmdoptionDesc(DescDirective):
    """
    Description of a command-line option (.. cmdoption).
    """

    def parse_signature(self, sig, signode):
        """Transform an option description into RST nodes."""
        count = 0
        firstname = ''
        for m in option_desc_re.finditer(sig):
            optname, args = m.groups()
            if count:
                signode += addnodes.desc_addname(', ', ', ')
            signode += addnodes.desc_name(optname, optname)
            signode += addnodes.desc_addname(args, args)
            if not count:
                firstname = optname
            count += 1
        if not firstname:
            raise ValueError
        return firstname

    def add_target_and_index(self, name, sig, signode):
        targetname = name.replace('/', '-')
        if self.env.currprogram:
            targetname = '-' + self.env.currprogram + targetname
        targetname = 'cmdoption' + targetname
        signode['ids'].append(targetname)
        self.state.document.note_explicit_target(signode)
        self.indexnode['entries'].append(
            ('pair', _('%scommand line option; %s') %
             ((self.env.currprogram and
               self.env.currprogram + ' ' or ''), sig),
             targetname, targetname))
        self.env.note_progoption(name, targetname)


class GenericDesc(DescDirective):
    """
    A generic x-ref directive registered with Sphinx.add_description_unit().
    """

    def parse_signature(self, sig, signode):
        parse_node = additional_xref_types[self.desctype][2]
        if parse_node:
            name = parse_node(self.env, sig, signode)
        else:
            signode.clear()
            signode += addnodes.desc_name(sig, sig)
            # normalize whitespace like xfileref_role does
            name = ws_re.sub('', sig)
        return name

    def add_target_and_index(self, name, sig, signode):
        rolename, indextemplate = additional_xref_types[self.desctype][:2]
        targetname = '%s-%s' % (rolename, name)
        signode['ids'].append(targetname)
        self.state.document.note_explicit_target(signode)
        if indextemplate:
            indexentry = _(indextemplate) % (name,)
            indextype = 'single'
            colon = indexentry.find(':')
            if colon != -1:
                indextype = indexentry[:colon].strip()
                indexentry = indexentry[colon+1:].strip()
            self.indexnode['entries'].append((indextype, indexentry,
                                              targetname, targetname))
        self.env.note_reftarget(rolename, name, targetname)


class Target(Directive):
    """
    Generic target for user-defined cross-reference types.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        rolename, indextemplate, foo = additional_xref_types[self.name]
        # normalize whitespace in fullname like xfileref_role does
        fullname = ws_re.sub('', self.arguments[0].strip())
        targetname = '%s-%s' % (rolename, fullname)
        node = nodes.target('', '', ids=[targetname])
        self.state.document.note_explicit_target(node)
        ret = [node]
        if indextemplate:
            indexentry = indextemplate % (fullname,)
            indextype = 'single'
            colon = indexentry.find(':')
            if colon != -1:
                indextype = indexentry[:colon].strip()
                indexentry = indexentry[colon+1:].strip()
            inode = addnodes.index(entries=[(indextype, indexentry,
                                             targetname, targetname)])
            ret.insert(0, inode)
        env.note_reftarget(rolename, fullname, targetname)
        return ret

# Note: the target directive is not registered here, it is used by the
# application when registering additional xref types.

_ = lambda x: x

# Generic cross-reference types; they can be registered in the application;
# the directives are either desc_directive or target_directive.
additional_xref_types = {
    # directive name: (role name, index text, function to parse the desc node)
    'envvar': ('envvar', _('environment variable; %s'), None),
}

del _


directives.register_directive('describe', directive_dwim(DescDirective))

directives.register_directive('function', directive_dwim(ModulelevelDesc))
directives.register_directive('data', directive_dwim(ModulelevelDesc))
directives.register_directive('class', directive_dwim(ClasslikeDesc))
directives.register_directive('exception', directive_dwim(ClasslikeDesc))
directives.register_directive('method', directive_dwim(ClassmemberDesc))
directives.register_directive('classmethod', directive_dwim(ClassmemberDesc))
directives.register_directive('staticmethod', directive_dwim(ClassmemberDesc))
directives.register_directive('attribute', directive_dwim(ClassmemberDesc))

directives.register_directive('cfunction', directive_dwim(CDesc))
directives.register_directive('cmember', directive_dwim(CDesc))
directives.register_directive('cmacro', directive_dwim(CDesc))
directives.register_directive('ctype', directive_dwim(CDesc))
directives.register_directive('cvar', directive_dwim(CDesc))

directives.register_directive('cmdoption', directive_dwim(CmdoptionDesc))
directives.register_directive('envvar', directive_dwim(GenericDesc))
