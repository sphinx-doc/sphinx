# -*- coding: utf-8 -*-
"""
    sphinx.directives.desc
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import re
import string

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.util import ws_re


# ------ information units ---------------------------------------------------------

def desc_index_text(desctype, module, name, add_modules):
    if desctype == 'function':
        if not module:
            return _('%s() (built-in function)') % name
        return _('%s() (in module %s)') % (name, module)
    elif desctype == 'data':
        if not module:
            return _('%s (built-in variable)') % name
        return _('%s (in module %s)') % (name, module)
    elif desctype == 'class':
        if not module:
            return _('%s (built-in class)') % name
        return _('%s (class in %s)') % (name, module)
    elif desctype == 'exception':
        return name
    elif desctype == 'method':
        try:
            clsname, methname = name.rsplit('.', 1)
        except ValueError:
            if module:
                return _('%s() (in module %s)') % (name, module)
            else:
                return '%s()' % name
        if module and add_modules:
            return _('%s() (%s.%s method)') % (methname, module, clsname)
        else:
            return _('%s() (%s method)') % (methname, clsname)
    elif desctype == 'staticmethod':
        try:
            clsname, methname = name.rsplit('.', 1)
        except ValueError:
            if module:
                return _('%s() (in module %s)') % (name, module)
            else:
                return '%s()' % name
        if module and add_modules:
            return _('%s() (%s.%s static method)') % (methname, module, clsname)
        else:
            return _('%s() (%s static method)') % (methname, clsname)
    elif desctype == 'attribute':
        try:
            clsname, attrname = name.rsplit('.', 1)
        except ValueError:
            if module:
                return _('%s (in module %s)') % (name, module)
            else:
                return name
        if module and add_modules:
            return _('%s (%s.%s attribute)') % (attrname, module, clsname)
        else:
            return _('%s (%s attribute)') % (attrname, clsname)
    elif desctype == 'cfunction':
        return _('%s (C function)') % name
    elif desctype == 'cmember':
        return _('%s (C member)') % name
    elif desctype == 'cmacro':
        return _('%s (C macro)') % name
    elif desctype == 'ctype':
        return _('%s (C type)') % name
    elif desctype == 'cvar':
        return _('%s (C variable)') % name
    else:
        raise ValueError('unhandled descenv: %s' % desctype)


# ------ make field lists (like :param foo:) in desc bodies prettier

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

doc_fields_without_arg = {
    'returns': 'Returns',
    'return': 'Returns',
    'rtype': _('Return type'),
}

del _

def handle_doc_fields(node):
    # don't traverse, only handle field lists that are immediate children
    for child in node.children:
        if not isinstance(child, nodes.field_list):
            continue
        params = None
        param_nodes = {}
        param_types = {}
        new_list = nodes.field_list()
        for field in child:
            fname, fbody = field
            try:
                typ, obj = fname.astext().split(None, 1)
                typ = _(doc_fields_with_arg[typ])
                if len(fbody.children) == 1 and \
                   isinstance(fbody.children[0], nodes.paragraph):
                    children = fbody.children[0].children
                else:
                    children = fbody.children
                if typ == '%param':
                    if not params:
                        pfield = nodes.field()
                        pfield += nodes.field_name('', _('Parameters'))
                        pfield += nodes.field_body()
                        params = nodes.bullet_list()
                        pfield[1] += params
                        new_list += pfield
                    dlitem = nodes.list_item()
                    dlpar = nodes.paragraph()
                    dlpar += nodes.emphasis(obj, obj)
                    dlpar += nodes.Text(' -- ', ' -- ')
                    dlpar += children
                    param_nodes[obj] = dlpar
                    dlitem += dlpar
                    params += dlitem
                elif typ == '%type':
                    param_types[obj] = fbody.astext()
                else:
                    fieldname = typ + ' ' + obj
                    nfield = nodes.field()
                    nfield += nodes.field_name(fieldname, fieldname)
                    nfield += nodes.field_body()
                    nfield[1] += fbody.children
                    new_list += nfield
            except (KeyError, ValueError):
                fnametext = fname.astext()
                try:
                    typ = _(doc_fields_without_arg[fnametext])
                except KeyError:
                    # at least capitalize the field name
                    typ = fnametext.capitalize()
                fname[0] = nodes.Text(typ)
                new_list += field
        for param, type in param_types.iteritems():
            if param in param_nodes:
                param_nodes[param].insert(1, nodes.Text(' (%s)' % type))
        child.replace_self(new_list)


# ------ functions to parse a Python or C signature and create desc_* nodes.

py_sig_re = re.compile(
    r'''^ ([\w.]*\.)?            # class name(s)
          (\w+)  \s*             # thing name
          (?: \((.*)\)           # optional arguments
          (\s* -> \s* .*)? )? $  # optional return annotation
          ''', re.VERBOSE)

py_paramlist_re = re.compile(r'([\[\],])')  # split at '[', ']' and ','

def parse_py_signature(signode, sig, desctype, module, env):
    """
    Transform a python signature into RST nodes.
    Return (fully qualified name of the thing, classname if any).

    If inside a class, the current class name is handled intelligently:
    * it is stripped from the displayed name if present
    * it is added to the full name (return value) if not present
    """
    m = py_sig_re.match(sig)
    if m is None:
        raise ValueError
    classname, name, arglist, retann = m.groups()

    if retann:
        retann = u' \N{RIGHTWARDS ARROW} ' + retann.strip()[2:]

    if env.currclass:
        add_module = False
        if classname and classname.startswith(env.currclass):
            fullname = classname + name
            # class name is given again in the signature
            classname = classname[len(env.currclass):].lstrip('.')
        elif classname:
            # class name is given in the signature, but different
            # (shouldn't happen)
            fullname = env.currclass + '.' + classname + name
        else:
            # class name is not given in the signature
            fullname = env.currclass + '.' + name
    else:
        add_module = True
        fullname = classname and classname + name or name

    if desctype == 'staticmethod':
        signode += addnodes.desc_annotation('static ', 'static ')

    if classname:
        signode += addnodes.desc_addname(classname, classname)
    # exceptions are a special case, since they are documented in the
    # 'exceptions' module.
    elif add_module and env.config.add_module_names and \
           module and module != 'exceptions':
        nodetext = module + '.'
        signode += addnodes.desc_addname(nodetext, nodetext)

    signode += addnodes.desc_name(name, name)
    if not arglist:
        if desctype in ('function', 'method', 'staticmethod'):
            # for callables, add an empty parameter list
            signode += addnodes.desc_parameterlist()
        if retann:
            signode += addnodes.desc_type(retann, retann)
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
        signode += addnodes.desc_type(retann, retann)
    return fullname, classname


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

# RE to split at word boundaries
wsplit_re = re.compile(r'(\W+)')

# These C types aren't described in the reference, so don't try to create
# a cross-reference to them
stopwords = set(('const', 'void', 'char', 'int', 'long', 'FILE', 'struct'))

def parse_c_type(node, ctype):
    # add cross-ref nodes for all words
    for part in filter(None, wsplit_re.split(ctype)):
        tnode = nodes.Text(part, part)
        if part[0] in string.letters+'_' and part not in stopwords:
            pnode = addnodes.pending_xref(
                '', reftype='ctype', reftarget=part, modname=None, classname=None)
            pnode += tnode
            node += pnode
        else:
            node += tnode

def parse_c_signature(signode, sig, desctype):
    """Transform a C (or C++) signature into RST nodes."""
    # first try the function pointer signature regex, it's more specific
    m = c_funcptr_sig_re.match(sig)
    if m is None:
        m = c_sig_re.match(sig)
    if m is None:
        raise ValueError('no match')
    rettype, name, arglist, const = m.groups()

    signode += addnodes.desc_type('', '')
    parse_c_type(signode[-1], rettype)
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
        if desctype == 'cfunction':
            # for functions, add an empty parameter list
            signode += addnodes.desc_parameterlist()
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
            parse_c_type(param, arg)
        else:
            parse_c_type(param, ctype)
            param += nodes.emphasis(' '+argname, ' '+argname)
        paramlist += param
    signode += paramlist
    if const:
        signode += addnodes.desc_addname(const, const)
    return name


option_desc_re = re.compile(
    r'((?:/|-|--)[-_a-zA-Z0-9]+)(\s*.*?)(?=,\s+(?:/|-|--)|$)')

def parse_option_desc(signode, sig):
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


def desc_directive(desctype, arguments, options, content, lineno,
                   content_offset, block_text, state, state_machine):
    env = state.document.settings.env
    inode = addnodes.index(entries=[])
    node = addnodes.desc()
    node['desctype'] = desctype

    noindex = ('noindex' in options)
    node['noindex'] = noindex
    # remove backslashes to support (dummy) escapes; helps Vim's highlighting
    signatures = map(lambda s: s.strip().replace('\\', ''), arguments[0].split('\n'))
    names = []
    clsname = None
    module = options.get('module', env.currmodule)
    for i, sig in enumerate(signatures):
        # add a signature node for each signature in the current unit
        # and add a reference target for it
        sig = sig.strip()
        signode = addnodes.desc_signature(sig, '')
        signode['first'] = False
        node.append(signode)
        try:
            if desctype in ('function', 'data', 'class', 'exception',
                            'method', 'staticmethod', 'attribute'):
                name, clsname = parse_py_signature(signode, sig, desctype, module, env)
            elif desctype in ('cfunction', 'cmember', 'cmacro', 'ctype', 'cvar'):
                name = parse_c_signature(signode, sig, desctype)
            elif desctype == 'cmdoption':
                optname = parse_option_desc(signode, sig)
                if not noindex:
                    targetname = optname.replace('/', '-')
                    if env.currprogram:
                        targetname = '-' + env.currprogram + targetname
                    targetname = 'cmdoption' + targetname
                    signode['ids'].append(targetname)
                    state.document.note_explicit_target(signode)
                    inode['entries'].append(
                        ('pair', _('%scommand line option; %s') %
                         ((env.currprogram and env.currprogram + ' ' or ''), sig),
                         targetname, targetname))
                    env.note_progoption(optname, targetname)
                continue
            elif desctype == 'describe':
                signode.clear()
                signode += addnodes.desc_name(sig, sig)
                continue
            else:
                # another registered generic x-ref directive
                rolename, indextemplate, parse_node = additional_xref_types[desctype]
                if parse_node:
                    fullname = parse_node(env, sig, signode)
                else:
                    signode.clear()
                    signode += addnodes.desc_name(sig, sig)
                    # normalize whitespace like xfileref_role does
                    fullname = ws_re.sub('', sig)
                if not noindex:
                    targetname = '%s-%s' % (rolename, fullname)
                    signode['ids'].append(targetname)
                    state.document.note_explicit_target(signode)
                    if indextemplate:
                        indexentry = _(indextemplate) % (fullname,)
                        indextype = 'single'
                        colon = indexentry.find(':')
                        if colon != -1:
                            indextype = indexentry[:colon].strip()
                            indexentry = indexentry[colon+1:].strip()
                        inode['entries'].append((indextype, indexentry,
                                                 targetname, targetname))
                    env.note_reftarget(rolename, fullname, targetname)
                # don't use object indexing below
                continue
        except ValueError, err:
            # signature parsing failed
            signode.clear()
            signode += addnodes.desc_name(sig, sig)
            continue             # we don't want an index entry here
        # only add target and index entry if this is the first description of the
        # function name in this desc block
        if not noindex and name not in names:
            fullname = (module and module + '.' or '') + name
            # note target
            if fullname not in state.document.ids:
                signode['names'].append(fullname)
                signode['ids'].append(fullname)
                signode['first'] = (not names)
                state.document.note_explicit_target(signode)
                env.note_descref(fullname, desctype, lineno)
            names.append(name)

            indextext = desc_index_text(desctype, module, name,
                                        env.config.add_module_names)
            inode['entries'].append(('single', indextext, fullname, fullname))

    subnode = addnodes.desc_content()
    # needed for automatic qualification of members
    clsname_set = False
    if desctype in ('class', 'exception') and names:
        env.currclass = names[0]
        clsname_set = True
    elif desctype in ('method', 'staticmethod', 'attribute') and \
             clsname and not env.currclass:
        env.currclass = clsname.strip('.')
        clsname_set = True
    # needed for association of version{added,changed} directives
    if names:
        env.currdesc = names[0]
    state.nested_parse(content, content_offset, subnode)
    handle_doc_fields(subnode)
    if clsname_set:
        env.currclass = None
    env.currdesc = None
    node.append(subnode)
    return [inode, node]

desc_directive.content = 1
desc_directive.arguments = (1, 0, 1)
desc_directive.options = {'noindex': directives.flag,
                          'module': directives.unchanged}

desctypes = [
    # the Python ones
    'function',
    'data',
    'class',
    'method',
    'staticmethod',
    'attribute',
    'exception',
    # the C ones
    'cfunction',
    'cmember',
    'cmacro',
    'ctype',
    'cvar',
    # for command line options
    'cmdoption',
    # the generic one
    'describe',
    'envvar',
]

for _name in desctypes:
    directives.register_directive(_name, desc_directive)

_ = lambda x: x

# Generic cross-reference types; they can be registered in the application;
# the directives are either desc_directive or target_directive
additional_xref_types = {
    # directive name: (role name, index text, function to parse the desc node)
    'envvar': ('envvar', _('environment variable; %s'), None),
}

del _


# ------ target --------------------------------------------------------------------

def target_directive(targettype, arguments, options, content, lineno,
                     content_offset, block_text, state, state_machine):
    """Generic target for user-defined cross-reference types."""
    env = state.document.settings.env
    rolename, indextemplate, foo = additional_xref_types[targettype]
    # normalize whitespace in fullname like xfileref_role does
    fullname = ws_re.sub('', arguments[0].strip())
    targetname = '%s-%s' % (rolename, fullname)
    node = nodes.target('', '', ids=[targetname])
    state.document.note_explicit_target(node)
    ret = [node]
    if indextemplate:
        indexentry = indextemplate % (fullname,)
        indextype = 'single'
        colon = indexentry.find(':')
        if colon != -1:
            indextype = indexentry[:colon].strip()
            indexentry = indexentry[colon+1:].strip()
        inode = addnodes.index(entries=[(indextype, indexentry, targetname, targetname)])
        ret.insert(0, inode)
    env.note_reftarget(rolename, fullname, targetname)
    return ret

target_directive.content = 0
target_directive.arguments = (1, 0, 1)

# note, the target directive is not registered here, it is used by the application
# when registering additional xref types
