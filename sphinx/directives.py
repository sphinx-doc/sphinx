# -*- coding: utf-8 -*-
"""
    sphinx.directives
    ~~~~~~~~~~~~~~~~~

    Handlers for additional ReST directives.

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""
from __future__ import with_statement

import re
import string
from os import path

from docutils import nodes
from docutils.parsers.rst import directives, roles
from docutils.parsers.rst.directives import admonitions

from . import addnodes

# ------ index markup --------------------------------------------------------------

entrytypes = [
    'single', 'pair', 'triple', 'quadruple',
    'module', 'keyword', 'operator', 'object', 'exception', 'statement', 'builtin',
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
    indexnode['entries'] = arguments
    for entry in arguments:
        try:
            type, string = entry.split(':', 1)
            env.note_index_entry(type.strip(), string.strip(),
                                 targetid, string.strip())
        except ValueError:
            continue
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

def parse_py_signature(signode, sig, desctype, currclass):
    """
    Transform a python signature into RST nodes. Returns (signode, fullname).
    Return the fully qualified name of the thing.

    If inside a class, the current class name is handled intelligently:
    * it is stripped from the displayed name if present
    * it is added to the full name (return value) if not present
    """
    m = py_sig_re.match(sig)
    if m is None: raise ValueError
    classname, name, arglist = m.groups()

    if currclass:
        if classname and classname.startswith(currclass):
            fullname = classname + name
            classname = classname[len(currclass):].lstrip('.')
        elif classname:
            fullname = currclass + '.' + classname + name
        else:
            fullname = currclass + '.' + name
    else:
        fullname = classname + name if classname else name

    if classname:
        signode += addnodes.desc_classname(classname, classname)
    signode += addnodes.desc_name(name, name)
    if not arglist:
        if desctype in ('function', 'method'):
            # for callables, add an empty parameter list
            signode += addnodes.desc_parameterlist()
        return fullname
    signode += addnodes.desc_parameterlist()

    stack = [signode[-1]]
    arglist = arglist.replace('`', '').replace(r'\ ', '') # remove markup
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
    return fullname


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

    parse_c_type(signode, rettype)
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

def parse_opcode_signature(signode, sig, desctype):
    """Transform an opcode signature into RST nodes."""
    m = opcode_sig_re.match(sig)
    if m is None: raise ValueError
    opname, arglist = m.groups()
    signode += addnodes.desc_name(opname, opname)
    paramlist = addnodes.desc_parameterlist()
    signode += paramlist
    paramlist += addnodes.desc_parameter(arglist, arglist)
    return opname.strip()


def add_refcount_annotation(env, node, name):
    """Add a reference count annotation. Return None."""
    entry = env.refcounts.get(name)
    if not entry:
        return
    elif entry.result_type not in ("PyObject*", "PyVarObject*"):
        return
    rc = 'Return value: '
    if entry.result_refs is None:
        rc += "Always NULL."
    else:
        rc += ("New" if entry.result_refs else "Borrowed") + " reference."
    node += addnodes.refcount(rc, rc)


def desc_directive(desctype, arguments, options, content, lineno,
                   content_offset, block_text, state, state_machine):
    env = state.document.settings.env
    node = addnodes.desc()
    node['desctype'] = desctype

    noindex = ('noindex' in options)
    signatures = map(lambda s: s.strip(), arguments[0].split('\n'))
    names = []
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
                name = parse_py_signature(signode, sig, desctype, env.currclass)
            elif desctype in ('cfunction', 'cmember', 'cmacro', 'ctype', 'cvar'):
                name = parse_c_signature(signode, sig, desctype)
            elif desctype == 'opcode':
                name = parse_opcode_signature(signode, sig, desctype)
            else:
                # describe: use generic fallback
                raise ValueError
        except ValueError, err:
            signode.clear()
            signode += addnodes.desc_name(sig, sig)
            continue             # we don't want an index entry here
        # only add target and index entry if this is the first description of the
        # function name in this desc block
        if not noindex and name not in names:
            fullname = (env.currmodule + '.' if env.currmodule else '') + name
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
    if desctype == 'cfunction':
        add_refcount_annotation(env, subnode, name)
    # needed for automatic qualification of members
    if desctype == 'class' and names:
        env.currclass = names[0]
    # needed for association of version{added,changed} directives
    if names:
        env.currdesc = names[0]
    state.nested_parse(content, content_offset, subnode)
    if desctype == 'class':
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
    # the generic one
    'describe',
]

for name in desctypes:
    directives.register_directive(name, desc_directive)


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
    env.note_versionchange(node['type'], node['version'], node)
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
        addnodes.seealso, name, ['See also:'], options, content,
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
            env.note_token(subnode['tokenname'])
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
    env.note_module(modname, options.get('synopsis', ''), options.get('platform', ''))
    ret = []
    targetnode = nodes.target('', '', ids=['module-' + modname])
    state.document.note_explicit_target(targetnode)
    ret.append(targetnode)
    if 'platform' in options:
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
                            'synopsis': lambda x: x}
directives.register_directive('module', module_directive)


def author_directive(name, arguments, options, content, lineno,
                     content_offset, block_text, state, state_machine):
    # The author directives aren't included in the built document
    return []

author_directive.arguments = (1, 0, 1)
directives.register_directive('sectionauthor', author_directive)
directives.register_directive('moduleauthor', author_directive)


# ------ toctree directive ---------------------------------------------------------

def toctree_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    env = state.document.settings.env
    dirname = path.dirname(env.filename)

    subnode = addnodes.toctree()
    includefiles = filter(None, content)
    # absolutize filenames
    includefiles = map(lambda x: path.normpath(path.join(dirname, x)), includefiles)
    subnode['includefiles'] = includefiles
    subnode['maxdepth'] = options.get('maxdepth', -1)
    return [subnode]

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
        with open(fn) as f:
            text = f.read()
    except (IOError, OSError):
        retnode = state.document.reporter.warning('Include file %r not found' %
                                                  arguments[0], line=lineno)
    else:
        retnode = nodes.literal_block(text, text, source=fn)
        retnode.line = 1
    return [retnode]

literalinclude_directive.content = 0
literalinclude_directive.arguments = (1, 0, 0)
directives.register_directive('literalinclude', literalinclude_directive)
