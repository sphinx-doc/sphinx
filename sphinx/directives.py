# -*- coding: utf-8 -*-
"""
    sphinx.directives
    ~~~~~~~~~~~~~~~~~

    Handlers for additional ReST directives.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import re
import string
import posixpath
from os import path

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import admonitions

from sphinx import addnodes

# ------ index markup --------------------------------------------------------------

entrytypes = [
    'single', 'pair', 'triple', 'module', 'keyword', 'operator',
    'object', 'exception', 'statement', 'builtin',
]

def index_directive(name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    arguments = arguments[0].split('\n')
    env = state.document.settings.env
    targetid = 'index-%s' % env.index_num
    env.index_num += 1
    targetnode = nodes.target('', '', ids=[targetid])
    state.document.note_explicit_target(targetnode)
    indexnode = addnodes.index()
    indexnode['entries'] = ne = []
    for entry in arguments:
        entry = entry.strip()
        for type in entrytypes:
            if entry.startswith(type+':'):
                value = entry[len(type)+1:].strip()
                env.note_index_entry(type, value, targetid, value)
                ne.append((type, value, targetid, value))
                break
        # shorthand notation for single entries
        else:
            for value in entry.split(','):
                env.note_index_entry('single', value.strip(), targetid, value.strip())
                ne.append(('single', value.strip(), targetid, value.strip()))
    return [indexnode, targetnode]

index_directive.arguments = (1, 0, 1)
directives.register_directive('index', index_directive)

# ------ information units ---------------------------------------------------------

def desc_index_text(desctype, currmodule, name):
    if desctype == 'function':
        if not currmodule:
            return '%s() (built-in function)' % name
        return '%s() (in module %s)' % (name, currmodule)
    elif desctype == 'data':
        if not currmodule:
            return '%s (built-in variable)' % name
        return '%s (in module %s)' % (name, currmodule)
    elif desctype == 'class':
        return '%s (class in %s)' % (name, currmodule)
    elif desctype == 'exception':
        return name
    elif desctype == 'method':
        try:
            clsname, methname = name.rsplit('.', 1)
        except:
            if currmodule:
                return '%s() (in module %s)' % (name, currmodule)
            else:
                return '%s()' % name
        if currmodule:
            return '%s() (%s.%s method)' % (methname, currmodule, clsname)
        else:
            return '%s() (%s method)' % (methname, clsname)
    elif desctype == 'attribute':
        try:
            clsname, attrname = name.rsplit('.', 1)
        except:
            if currmodule:
                return '%s (in module %s)' % (name, currmodule)
            else:
                return name
        if currmodule:
            return '%s (%s.%s attribute)' % (attrname, currmodule, clsname)
        else:
            return '%s (%s attribute)' % (attrname, clsname)
    elif desctype == 'opcode':
        return '%s (opcode)' % name
    elif desctype == 'cfunction':
        return '%s (C function)' % name
    elif desctype == 'cmember':
        return '%s (C member)' % name
    elif desctype == 'cmacro':
        return '%s (C macro)' % name
    elif desctype == 'ctype':
        return '%s (C type)' % name
    elif desctype == 'cvar':
        return '%s (C variable)' % name
    else:
        raise ValueError("unhandled descenv: %s" % desctype)


# ------ functions to parse a Python or C signature and create desc_* nodes.

py_sig_re = re.compile(r'''^([\w.]*\.)?        # class names
                           (\w+)  \s*          # thing name
                           (?: \((.*)\) )? $   # optionally arguments
                        ''', re.VERBOSE)

py_paramlist_re = re.compile(r'([\[\],])')  # split at '[', ']' and ','

def parse_py_signature(signode, sig, desctype, env):
    """
    Transform a python signature into RST nodes.
    Return (fully qualified name of the thing, classname if any).

    If inside a class, the current class name is handled intelligently:
    * it is stripped from the displayed name if present
    * it is added to the full name (return value) if not present
    """
    m = py_sig_re.match(sig)
    if m is None: raise ValueError
    classname, name, arglist = m.groups()

    if env.currclass:
        if classname and classname.startswith(env.currclass):
            fullname = classname + name
            classname = classname[len(env.currclass):].lstrip('.')
        elif classname:
            fullname = env.currclass + '.' + classname + name
        else:
            fullname = env.currclass + '.' + name
    else:
        fullname = classname and classname + name or name

    if classname:
        signode += addnodes.desc_classname(classname, classname)
    # exceptions are a special case, since they are documented in the
    # 'exceptions' module.
    elif env.config.add_module_names and \
           env.currmodule and env.currmodule != 'exceptions':
        nodetext = env.currmodule + '.'
        signode += addnodes.desc_classname(nodetext, nodetext)

    signode += addnodes.desc_name(name, name)
    if not arglist:
        if desctype in ('function', 'method'):
            # for callables, add an empty parameter list
            signode += addnodes.desc_parameterlist()
        return fullname, classname
    signode += addnodes.desc_parameterlist()

    stack = [signode[-1]]
    for token in py_paramlist_re.split(arglist):
        if token == '[':
            opt = addnodes.desc_optional()
            stack[-1] += opt
            stack.append(opt)
        elif token == ']':
            try: stack.pop()
            except IndexError: raise ValueError
        elif not token or token == ',' or token.isspace():
            pass
        else:
            token = token.strip()
            stack[-1] += addnodes.desc_parameter(token, token)
    if len(stack) != 1: raise ValueError
    return fullname, classname


c_sig_re = re.compile(
    r'''^([^(]*?)          # return type
        (\w+)  \s*         # thing name
        (?: \((.*)\) )? $  # optionally arguments
    ''', re.VERBOSE)
c_funcptr_sig_re = re.compile(
    r'''^([^(]+?)          # return type
        (\( [^()]+ \)) \s* # name in parentheses
        \( (.*) \) $       # arguments
    ''', re.VERBOSE)

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
    """Transform a C-language signature into RST nodes."""
    # first try the function pointer signature regex, it's more specific
    m = c_funcptr_sig_re.match(sig)
    if m is None:
        m = c_sig_re.match(sig)
    if m is None:
        raise ValueError('no match')
    rettype, name, arglist = m.groups()

    signode += addnodes.desc_type("", "")
    parse_c_type(signode[-1], rettype)
    signode += addnodes.desc_name(name, name)
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
    return name


opcode_sig_re = re.compile(r'(\w+(?:\+\d)?)\s*\((.*)\)')

def parse_opcode_signature(signode, sig):
    """Transform an opcode signature into RST nodes."""
    m = opcode_sig_re.match(sig)
    if m is None: raise ValueError
    opname, arglist = m.groups()
    signode += addnodes.desc_name(opname, opname)
    paramlist = addnodes.desc_parameterlist()
    signode += paramlist
    paramlist += addnodes.desc_parameter(arglist, arglist)
    return opname.strip()


option_desc_re = re.compile(r'([-/])([-_a-zA-Z0-9]+)(\s*.*)')

def parse_option_desc(signode, sig):
    """Transform an option description into RST nodes."""
    m = option_desc_re.match(sig)
    if m is None: raise ValueError
    prefix, optname, args = m.groups()
    signode += addnodes.desc_name(prefix+optname, prefix+optname)
    signode += addnodes.desc_classname(args, args)
    return optname


def desc_directive(desctype, arguments, options, content, lineno,
                   content_offset, block_text, state, state_machine):
    env = state.document.settings.env
    node = addnodes.desc()
    node['desctype'] = desctype

    noindex = ('noindex' in options)
    node['noindex'] = noindex
    # remove backslashes to support (dummy) escapes; helps Vim's highlighting
    signatures = map(lambda s: s.strip().replace('\\', ''), arguments[0].split('\n'))
    names = []
    clsname = None
    for i, sig in enumerate(signatures):
        # add a signature node for each signature in the current unit
        # and add a reference target for it
        sig = sig.strip()
        signode = addnodes.desc_signature(sig, '')
        signode['first'] = False
        node.append(signode)
        try:
            if desctype in ('function', 'data', 'class', 'exception',
                            'method', 'attribute'):
                name, clsname = parse_py_signature(signode, sig, desctype, env)
            elif desctype in ('cfunction', 'cmember', 'cmacro', 'ctype', 'cvar'):
                name = parse_c_signature(signode, sig, desctype)
            elif desctype == 'opcode':
                name = parse_opcode_signature(signode, sig)
            elif desctype == 'cmdoption':
                optname = parse_option_desc(signode, sig)
                if not noindex:
                    targetname = 'cmdoption-' + optname
                    signode['ids'].append(targetname)
                    state.document.note_explicit_target(signode)
                    env.note_index_entry('pair', 'command line option; %s' % sig,
                                         targetname, targetname)
                    env.note_reftarget('option', optname, targetname)
                continue
            elif desctype == 'describe':
                signode.clear()
                signode += addnodes.desc_name(sig, sig)
                continue
            else:
                # another registered generic x-ref directive
                rolename, indextext, parse_node = additional_xref_types[desctype]
                if parse_node:
                    parse_node(sig, signode)
                else:
                    signode.clear()
                    signode += addnodes.desc_name(sig, sig)
                if not noindex:
                    targetname = '%s-%s' % (rolename, sig)
                    signode['ids'].append(targetname)
                    state.document.note_explicit_target(signode)
                    if indextext:
                        env.note_index_entry('pair', '%s; %s' % (indextext, sig),
                                             targetname, targetname)
                    env.note_reftarget(rolename, sig, targetname)
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
            fullname = (env.currmodule and env.currmodule + '.' or '') + name
            # note target
            if fullname not in state.document.ids:
                signode['names'].append(fullname)
                signode['ids'].append(fullname)
                signode['first'] = (not names)
                state.document.note_explicit_target(signode)
                env.note_descref(fullname, desctype)
            names.append(name)

            env.note_index_entry('single',
                                 desc_index_text(desctype, env.currmodule, name),
                                 fullname, fullname)

    subnode = addnodes.desc_content()
    # needed for automatic qualification of members
    clsname_set = False
    if desctype == 'class' and names:
        env.currclass = names[0]
        clsname_set = True
    elif desctype in ('method', 'attribute') and clsname and not env.currclass:
        env.currclass = clsname.strip('.')
        clsname_set = True
    # needed for association of version{added,changed} directives
    if names:
        env.currdesc = names[0]
    state.nested_parse(content, content_offset, subnode)
    if clsname_set:
        env.currclass = None
    env.currdesc = None
    node.append(subnode)
    return [node]

desc_directive.content = 1
desc_directive.arguments = (1, 0, 1)
desc_directive.options = {'noindex': directives.flag}

desctypes = [
    # the Python ones
    'function',
    'data',
    'class',
    'method',
    'attribute',
    'exception',
    # the C ones
    'cfunction',
    'cmember',
    'cmacro',
    'ctype',
    'cvar',
    # the odd one
    'opcode',
    # for command line options
    'cmdoption',
    # the generic one
    'describe',
    'envvar',
]

for _name in desctypes:
    directives.register_directive(_name, desc_directive)

# Generic cross-reference types; they can be registered in the application
additional_xref_types = {
    # directive name: (role name, index text)
    'envvar': ('envvar', 'environment variable', None),
}


# ------ versionadded/versionchanged -----------------------------------------------

def version_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    node = addnodes.versionmodified()
    node['type'] = name
    node['version'] = arguments[0]
    if len(arguments) == 2:
        inodes, messages = state.inline_text(arguments[1], lineno+1)
        node.extend(inodes)
        if content:
            state.nested_parse(content, content_offset, node)
        ret = [node] + messages
    else:
        ret = [node]
    env = state.document.settings.env
    env.note_versionchange(node['type'], node['version'], node, lineno)
    return ret

version_directive.arguments = (1, 1, 1)
version_directive.content = 1

directives.register_directive('deprecated', version_directive)
directives.register_directive('versionadded', version_directive)
directives.register_directive('versionchanged', version_directive)


# ------ see also ------------------------------------------------------------------

def seealso_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    rv = admonitions.make_admonition(
        addnodes.seealso, name, ['See also'], options, content,
        lineno, content_offset, block_text, state, state_machine)
    return rv

seealso_directive.content = 1
seealso_directive.arguments = (0, 0, 0)
directives.register_directive('seealso', seealso_directive)


# ------ production list (for the reference) ---------------------------------------

token_re = re.compile('`([a-z_]+)`')

def token_xrefs(text, env):
    retnodes = []
    pos = 0
    for m in token_re.finditer(text):
        if m.start() > pos:
            txt = text[pos:m.start()]
            retnodes.append(nodes.Text(txt, txt))
        refnode = addnodes.pending_xref(m.group(1))
        refnode['reftype'] = 'token'
        refnode['reftarget'] = m.group(1)
        refnode['modname'] = env.currmodule
        refnode['classname'] = env.currclass
        refnode += nodes.literal(m.group(1), m.group(1), classes=['xref'])
        retnodes.append(refnode)
        pos = m.end()
    if pos < len(text):
        retnodes.append(nodes.Text(text[pos:], text[pos:]))
    return retnodes

def productionlist_directive(name, arguments, options, content, lineno,
                             content_offset, block_text, state, state_machine):
    env = state.document.settings.env
    node = addnodes.productionlist()
    messages = []
    i = 0

    for rule in arguments[0].split('\n'):
        if i == 0 and ':' not in rule:
            # production group
            continue
        i += 1
        try:
            name, tokens = rule.split(':', 1)
        except ValueError:
            break
        subnode = addnodes.production()
        subnode['tokenname'] = name.strip()
        if subnode['tokenname']:
            idname = 'grammar-token-%s' % subnode['tokenname']
            if idname not in state.document.ids:
                subnode['ids'].append(idname)
            state.document.note_implicit_target(subnode, subnode)
            env.note_reftarget('token', subnode['tokenname'], idname)
        subnode.extend(token_xrefs(tokens, env))
        node.append(subnode)
    return [node] + messages

productionlist_directive.content = 0
productionlist_directive.arguments = (1, 0, 1)
directives.register_directive('productionlist', productionlist_directive)

# ------ section metadata ----------------------------------------------------------

def module_directive(name, arguments, options, content, lineno,
                     content_offset, block_text, state, state_machine):
    env = state.document.settings.env
    modname = arguments[0].strip()
    env.currmodule = modname
    env.note_module(modname, options.get('synopsis', ''),
                    options.get('platform', ''),
                    'deprecated' in options)
    modulenode = addnodes.module()
    modulenode['modname'] = modname
    modulenode['synopsis'] = options.get('synopsis', '')
    targetnode = nodes.target('', '', ids=['module-' + modname])
    state.document.note_explicit_target(targetnode)
    ret = [modulenode, targetnode]
    if 'platform' in options:
        modulenode['platform'] = options['platform']
        node = nodes.paragraph()
        node += nodes.emphasis('Platforms: ', 'Platforms: ')
        node += nodes.Text(options['platform'], options['platform'])
        ret.append(node)
    # the synopsis isn't printed; in fact, it is only used in the modindex currently
    env.note_index_entry('single', '%s (module)' % modname, 'module-' + modname,
                         modname)
    return ret

module_directive.arguments = (1, 0, 0)
module_directive.options = {'platform': lambda x: x,
                            'synopsis': lambda x: x,
                            'deprecated': directives.flag}
directives.register_directive('module', module_directive)


def author_directive(name, arguments, options, content, lineno,
                     content_offset, block_text, state, state_machine):
    # Show authors only if the show_authors option is on
    env = state.document.settings.env
    if not env.config.show_authors:
        return []
    para = nodes.paragraph()
    emph = nodes.emphasis()
    para += emph
    if name == 'sectionauthor':
        text = 'Section author: '
    elif name == 'moduleauthor':
        text = 'Module author: '
    else:
        text = 'Author: '
    emph += nodes.Text(text, text)
    inodes, messages = state.inline_text(arguments[0], lineno)
    emph.extend(inodes)
    return [para] + messages

author_directive.arguments = (1, 0, 1)
directives.register_directive('sectionauthor', author_directive)
directives.register_directive('moduleauthor', author_directive)


# ------ toctree directive ---------------------------------------------------------

def toctree_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    env = state.document.settings.env
    suffix = env.config.source_suffix
    dirname = posixpath.dirname(env.docname)

    ret = []
    subnode = addnodes.toctree()
    includefiles = []
    for docname in content:
        if not docname:
            continue
        # absolutize filenames, remove suffixes
        if docname.endswith(suffix):
            docname = docname[:-len(suffix)]
        docname = posixpath.normpath(posixpath.join(dirname, docname))
        if docname not in env.found_docs:
            ret.append(state.document.reporter.warning(
                'toctree references unknown document %s' % docname, line=lineno))
        else:
            includefiles.append(docname)
    subnode['includefiles'] = includefiles
    subnode['maxdepth'] = options.get('maxdepth', -1)
    ret.append(subnode)
    return ret

toctree_directive.content = 1
toctree_directive.options = {'maxdepth': int}
directives.register_directive('toctree', toctree_directive)


# ------ centered directive ---------------------------------------------------------

def centered_directive(name, arguments, options, content, lineno,
                       content_offset, block_text, state, state_machine):
    if not arguments:
        return []
    subnode = addnodes.centered()
    inodes, messages = state.inline_text(arguments[0], lineno)
    subnode.extend(inodes)
    return [subnode] + messages

centered_directive.arguments = (1, 0, 1)
directives.register_directive('centered', centered_directive)


# ------ highlightlanguage directive ------------------------------------------------

def highlightlang_directive(name, arguments, options, content, lineno,
                            content_offset, block_text, state, state_machine):
    return [addnodes.highlightlang(lang=arguments[0].strip())]

highlightlang_directive.content = 0
highlightlang_directive.arguments = (1, 0, 0)
directives.register_directive('highlightlang', highlightlang_directive)


# ------ literalinclude directive ---------------------------------------------------

def literalinclude_directive(name, arguments, options, content, lineno,
                             content_offset, block_text, state, state_machine):
    """Like .. include:: :literal:, but only warns if the include file is not found."""
    if not state.document.settings.file_insertion_enabled:
        return [state.document.reporter.warning('File insertion disabled', line=lineno)]
    env = state.document.settings.env
    fn = arguments[0]
    source_dir = path.dirname(path.abspath(state_machine.input_lines.source(
        lineno - state_machine.input_offset - 1)))
    fn = path.normpath(path.join(source_dir, fn))

    try:
        f = open(fn)
        text = f.read()
        f.close()
    except (IOError, OSError):
        retnode = state.document.reporter.warning(
            'Include file %r not found or reading it failed' % arguments[0], line=lineno)
    else:
        retnode = nodes.literal_block(text, text, source=fn)
        retnode.line = 1
    return [retnode]

literalinclude_directive.content = 0
literalinclude_directive.arguments = (1, 0, 0)
directives.register_directive('literalinclude', literalinclude_directive)


# ------ glossary directive ---------------------------------------------------------

def glossary_directive(name, arguments, options, content, lineno,
                       content_offset, block_text, state, state_machine):
    """Glossary with cross-reference targets for :dfn: roles."""
    env = state.document.settings.env
    node = addnodes.glossary()
    state.nested_parse(content, content_offset, node)

    # the content should be definition lists
    dls = [child for child in node if isinstance(child, nodes.definition_list)]
    # now, extract definition terms to enable cross-reference creation
    for dl in dls:
        dl['classes'].append('glossary')
        for li in dl.children:
            if not li.children or not isinstance(li[0], nodes.term):
                continue
            termtext = li.children[0].astext()
            new_id = 'term-' + nodes.make_id(termtext)
            if new_id in env.gloss_entries:
                new_id = 'term-' + str(len(env.gloss_entries))
            env.gloss_entries.add(new_id)
            li[0]['names'].append(new_id)
            li[0]['ids'].append(new_id)
            state.document.settings.env.note_reftarget('term', termtext.lower(),
                                                       new_id)
    return [node]

glossary_directive.content = 1
glossary_directive.arguments = (0, 0, 0)
directives.register_directive('glossary', glossary_directive)


# ------ acks directive -------------------------------------------------------------

def acks_directive(name, arguments, options, content, lineno,
                   content_offset, block_text, state, state_machine):
    node = addnodes.acks()
    state.nested_parse(content, content_offset, node)
    if len(node.children) != 1 or not isinstance(node.children[0], nodes.bullet_list):
        return [state.document.reporter.warning('.. acks content is not a list',
                                                line=lineno)]
    return [node]

acks_directive.content = 1
acks_directive.arguments = (0, 0, 0)
directives.register_directive('acks', acks_directive)
