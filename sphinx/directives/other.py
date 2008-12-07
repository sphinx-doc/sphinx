# -*- coding: utf-8 -*-
"""
    sphinx.directives.other
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import re
import posixpath

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.locale import pairindextypes
from sphinx.util import patfilter, ws_re, caption_ref_re
from sphinx.util.compat import make_admonition


# ------ the TOC tree ---------------------------------------------------------------

def toctree_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    env = state.document.settings.env
    suffix = env.config.source_suffix
    dirname = posixpath.dirname(env.docname)
    glob = 'glob' in options

    ret = []
    subnode = addnodes.toctree()
    includefiles = []
    includetitles = {}
    all_docnames = env.found_docs.copy()
    # don't add the currently visited file in catch-all patterns
    all_docnames.remove(env.docname)
    for entry in content:
        if not entry:
            continue
        if not glob:
            # look for explicit titles and documents ("Some Title <document>").
            m = caption_ref_re.match(entry)
            if m:
                docname = m.group(2)
                includetitles[docname] = m.group(1)
            else:
                docname = entry
            # remove suffixes (backwards compatibility)
            if docname.endswith(suffix):
                docname = docname[:-len(suffix)]
            # absolutize filenames
            docname = posixpath.normpath(posixpath.join(dirname, docname))
            if docname not in env.found_docs:
                ret.append(state.document.reporter.warning(
                    'toctree references unknown document %r' % docname, line=lineno))
            else:
                includefiles.append(docname)
        else:
            patname = posixpath.normpath(posixpath.join(dirname, entry))
            docnames = sorted(patfilter(all_docnames, patname))
            for docname in docnames:
                all_docnames.remove(docname) # don't include it again
                includefiles.append(docname)
            if not docnames:
                ret.append(state.document.reporter.warning(
                    'toctree glob pattern %r didn\'t match any documents' % entry,
                    line=lineno))
    subnode['includefiles'] = includefiles
    subnode['includetitles'] = includetitles
    subnode['maxdepth'] = options.get('maxdepth', -1)
    subnode['glob'] = glob
    ret.append(subnode)
    return ret

toctree_directive.content = 1
toctree_directive.options = {'maxdepth': int, 'glob': directives.flag}
directives.register_directive('toctree', toctree_directive)


# ------ section metadata ----------------------------------------------------------

def module_directive(name, arguments, options, content, lineno,
                     content_offset, block_text, state, state_machine):
    env = state.document.settings.env
    modname = arguments[0].strip()
    noindex = 'noindex' in options
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
        node += nodes.emphasis('', _('Platforms: '))
        node += nodes.Text(options['platform'], options['platform'])
        ret.append(node)
    # the synopsis isn't printed; in fact, it is only used in the modindex currently
    if not noindex:
        indextext = _('%s (module)') % modname
        inode = addnodes.index(entries=[('single', indextext,
                                         'module-' + modname, modname)])
        ret.insert(0, inode)
    return ret

module_directive.arguments = (1, 0, 0)
module_directive.options = {'platform': lambda x: x,
                            'synopsis': lambda x: x,
                            'noindex': directives.flag,
                            'deprecated': directives.flag}
directives.register_directive('module', module_directive)


def currentmodule_directive(name, arguments, options, content, lineno,
                            content_offset, block_text, state, state_machine):
    # This directive is just to tell people that we're documenting
    # stuff in module foo, but links to module foo won't lead here.
    env = state.document.settings.env
    modname = arguments[0].strip()
    if modname == 'None':
        env.currmodule = None
    else:
        env.currmodule = modname
    return []

currentmodule_directive.arguments = (1, 0, 0)
directives.register_directive('currentmodule', currentmodule_directive)


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
        text = _('Section author: ')
    elif name == 'moduleauthor':
        text = _('Module author: ')
    else:
        text = _('Author: ')
    emph += nodes.Text(text, text)
    inodes, messages = state.inline_text(arguments[0], lineno)
    emph.extend(inodes)
    return [para] + messages

author_directive.arguments = (1, 0, 1)
directives.register_directive('sectionauthor', author_directive)
directives.register_directive('moduleauthor', author_directive)


def program_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    env = state.document.settings.env
    program = ws_re.sub('-', arguments[0].strip())
    if program == 'None':
        env.currprogram = None
    else:
        env.currprogram = program
    return []

program_directive.arguments = (1, 0, 1)
directives.register_directive('program', program_directive)


# ------ index markup --------------------------------------------------------------

indextypes = [
    'single', 'pair', 'triple',
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
        for type in pairindextypes:
            if entry.startswith(type+':'):
                value = entry[len(type)+1:].strip()
                value = pairindextypes[type] + '; ' + value
                ne.append(('pair', value, targetid, value))
                break
        else:
            for type in indextypes:
                if entry.startswith(type+':'):
                    value = entry[len(type)+1:].strip()
                    ne.append((type, value, targetid, value))
                    break
            # shorthand notation for single entries
            else:
                for value in entry.split(','):
                    value = value.strip()
                    if not value:
                        continue
                    ne.append(('single', value, targetid, value))
    return [indexnode, targetnode]

index_directive.arguments = (1, 0, 1)
directives.register_directive('index', index_directive)

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
    ret = make_admonition(
        addnodes.seealso, name, [_('See also')], options, content,
        lineno, content_offset, block_text, state, state_machine)
    if arguments:
        argnodes, msgs = state.inline_text(arguments[0], lineno)
        para = nodes.paragraph()
        para += argnodes
        para += msgs
        ret[0].insert(1, para)
    return ret

seealso_directive.content = 1
seealso_directive.arguments = (0, 1, 1)
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


# ------ glossary directive ---------------------------------------------------------

def glossary_directive(name, arguments, options, content, lineno,
                       content_offset, block_text, state, state_machine):
    """Glossary with cross-reference targets for :term: roles."""
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
            # add an index entry too
            indexnode = addnodes.index()
            indexnode['entries'] = [('single', termtext, new_id, termtext)]
            li.insert(0, indexnode)
    return [node]

glossary_directive.content = 1
glossary_directive.arguments = (0, 0, 0)
directives.register_directive('glossary', glossary_directive)


# ------ miscellaneous markup -------------------------------------------------------

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


def tabularcolumns_directive(name, arguments, options, content, lineno,
                             content_offset, block_text, state, state_machine):
    # support giving explicit tabulary column definition to latex
    node = addnodes.tabular_col_spec()
    node['spec'] = arguments[0]
    return [node]

tabularcolumns_directive.content = 0
tabularcolumns_directive.arguments = (1, 0, 1)
directives.register_directive('tabularcolumns', tabularcolumns_directive)


# register the standard rst class directive under a different name

try:
    # docutils 0.4
    from docutils.parsers.rst.directives.misc import class_directive
    directives.register_directive('cssclass', class_directive)
except ImportError:
    try:
        # docutils 0.5
        from docutils.parsers.rst.directives.misc import Class
        directives.register_directive('cssclass', Class)
    except ImportError:
        # whatever :)
        pass
