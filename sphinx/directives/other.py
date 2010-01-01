# -*- coding: utf-8 -*-
"""
    sphinx.directives.other
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.locale import pairindextypes
from sphinx.util import patfilter, ws_re, caption_ref_re, url_re, docname_join
from sphinx.util.compat import Directive, directive_dwim, make_admonition


class TocTree(Directive):
    """
    Directive to notify Sphinx about the hierarchical structure of the docs,
    and to include a table-of-contents like tree in the current document.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'maxdepth': int,
        'glob': directives.flag,
        'hidden': directives.flag,
        'numbered': directives.flag,
    }

    def run(self):
        env = self.state.document.settings.env
        suffix = env.config.source_suffix
        glob = 'glob' in self.options

        ret = []
        # (title, ref) pairs, where ref may be a document, or an external link,
        # and title may be None if the document's title is to be used
        entries = []
        includefiles = []
        includetitles = {}
        all_docnames = env.found_docs.copy()
        # don't add the currently visited file in catch-all patterns
        all_docnames.remove(env.docname)
        for entry in self.content:
            if not entry:
                continue
            if not glob:
                # look for explicit titles ("Some Title <document>")
                m = caption_ref_re.match(entry)
                if m:
                    ref = m.group(2)
                    title = m.group(1)
                    docname = ref
                else:
                    ref = docname = entry
                    title = None
                # remove suffixes (backwards compatibility)
                if docname.endswith(suffix):
                    docname = docname[:-len(suffix)]
                # absolutize filenames
                docname = docname_join(env.docname, docname)
                if url_re.match(ref) or ref == 'self':
                    entries.append((title, ref))
                elif docname not in env.found_docs:
                    ret.append(self.state.document.reporter.warning(
                        'toctree references unknown document %r' % docname,
                        line=self.lineno))
                else:
                    entries.append((title, docname))
                    includefiles.append(docname)
            else:
                patname = docname_join(env.docname, entry)
                docnames = sorted(patfilter(all_docnames, patname))
                for docname in docnames:
                    all_docnames.remove(docname) # don't include it again
                    entries.append((None, docname))
                    includefiles.append(docname)
                if not docnames:
                    ret.append(self.state.document.reporter.warning(
                        'toctree glob pattern %r didn\'t match any documents'
                        % entry, line=self.lineno))
        subnode = addnodes.toctree()
        subnode['parent'] = env.docname
        # entries contains all entries (self references, external links etc.)
        subnode['entries'] = entries
        # includefiles only entries that are documents
        subnode['includefiles'] = includefiles
        subnode['maxdepth'] = self.options.get('maxdepth', -1)
        subnode['glob'] = glob
        subnode['hidden'] = 'hidden' in self.options
        subnode['numbered'] = 'numbered' in self.options
        ret.append(subnode)
        return ret


class Module(Directive):
    """
    Directive to mark description of a new module.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'platform': lambda x: x,
        'synopsis': lambda x: x,
        'noindex': directives.flag,
        'deprecated': directives.flag,
    }

    def run(self):
        env = self.state.document.settings.env
        modname = self.arguments[0].strip()
        noindex = 'noindex' in self.options
        env.currmodule = modname
        env.note_module(modname, self.options.get('synopsis', ''),
                        self.options.get('platform', ''),
                        'deprecated' in self.options)
        modulenode = addnodes.module()
        modulenode['modname'] = modname
        modulenode['synopsis'] = self.options.get('synopsis', '')
        targetnode = nodes.target('', '', ids=['module-' + modname], ismod=True)
        self.state.document.note_explicit_target(targetnode)
        ret = [modulenode, targetnode]
        if 'platform' in self.options:
            platform = self.options['platform']
            modulenode['platform'] = platform
            node = nodes.paragraph()
            node += nodes.emphasis('', _('Platforms: '))
            node += nodes.Text(platform, platform)
            ret.append(node)
        # the synopsis isn't printed; in fact, it is only used in the
        # modindex currently
        if not noindex:
            indextext = _('%s (module)') % modname
            inode = addnodes.index(entries=[('single', indextext,
                                             'module-' + modname, modname)])
            ret.insert(0, inode)
        return ret


class CurrentModule(Directive):
    """
    This directive is just to tell Sphinx that we're documenting
    stuff in module foo, but links to module foo won't lead here.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        modname = self.arguments[0].strip()
        if modname == 'None':
            env.currmodule = None
        else:
            env.currmodule = modname
        return []


class Author(Directive):
    """
    Directive to give the name of the author of the current document
    or section. Shown in the output only if the show_authors option is on.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        if not env.config.show_authors:
            return []
        para = nodes.paragraph()
        emph = nodes.emphasis()
        para += emph
        if self.name == 'sectionauthor':
            text = _('Section author: ')
        elif self.name == 'moduleauthor':
            text = _('Module author: ')
        else:
            text = _('Author: ')
        emph += nodes.Text(text, text)
        inodes, messages = self.state.inline_text(self.arguments[0],
                                                  self.lineno)
        emph.extend(inodes)
        return [para] + messages


class Program(Directive):
    """
    Directive to name the program for which options are documented.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        program = ws_re.sub('-', self.arguments[0].strip())
        if program == 'None':
            env.currprogram = None
        else:
            env.currprogram = program
        return []


class Index(Directive):
    """
    Directive to add entries to the index.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    indextypes = [
        'single', 'pair', 'double', 'triple',
    ]

    def run(self):
        arguments = self.arguments[0].split('\n')
        env = self.state.document.settings.env
        targetid = 'index-%s' % env.index_num
        env.index_num += 1
        targetnode = nodes.target('', '', ids=[targetid])
        self.state.document.note_explicit_target(targetnode)
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
                for type in self.indextypes:
                    if entry.startswith(type+':'):
                        value = entry[len(type)+1:].strip()
                        if type == 'double':
                            type = 'pair'
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


class VersionChange(Directive):
    """
    Directive to describe a change/addition/deprecation in a specific version.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        node = addnodes.versionmodified()
        node.document = self.state.document
        node['type'] = self.name
        node['version'] = self.arguments[0]
        if len(self.arguments) == 2:
            inodes, messages = self.state.inline_text(self.arguments[1],
                                                      self.lineno+1)
            node.extend(inodes)
            if self.content:
                self.state.nested_parse(self.content, self.content_offset, node)
            ret = [node] + messages
        else:
            ret = [node]
        env = self.state.document.settings.env
        env.note_versionchange(node['type'], node['version'], node, self.lineno)
        return ret


class SeeAlso(Directive):
    """
    An admonition mentioning things to look at as reference.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        ret = make_admonition(
            addnodes.seealso, self.name, [_('See also')], self.options,
            self.content, self.lineno, self.content_offset, self.block_text,
            self.state, self.state_machine)
        if self.arguments:
            argnodes, msgs = self.state.inline_text(self.arguments[0],
                                                    self.lineno)
            para = nodes.paragraph()
            para += argnodes
            para += msgs
            ret[0].insert(1, para)
        return ret


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

class ProductionList(Directive):
    """
    Directive to list grammar productions.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        node = addnodes.productionlist()
        messages = []
        i = 0

        for rule in self.arguments[0].split('\n'):
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
                if idname not in self.state.document.ids:
                    subnode['ids'].append(idname)
                self.state.document.note_implicit_target(subnode, subnode)
                env.note_reftarget('token', subnode['tokenname'], idname)
            subnode.extend(token_xrefs(tokens, env))
            node.append(subnode)
        return [node] + messages


class TabularColumns(Directive):
    """
    Directive to give an explicit tabulary column definition to LaTeX.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        node = addnodes.tabular_col_spec()
        node['spec'] = self.arguments[0]
        return [node]


class Glossary(Directive):
    """
    Directive to create a glossary with cross-reference targets
    for :term: roles.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'sorted': directives.flag,
    }

    def run(self):
        env = self.state.document.settings.env
        node = addnodes.glossary()
        node.document = self.state.document
        self.state.nested_parse(self.content, self.content_offset, node)

        # the content should be definition lists
        dls = [child for child in node
               if isinstance(child, nodes.definition_list)]
        # now, extract definition terms to enable cross-reference creation
        new_dl = nodes.definition_list()
        new_dl['classes'].append('glossary')
        items = []
        for dl in dls:
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
                env.note_reftarget('term', termtext.lower(), new_id)
                # add an index entry too
                indexnode = addnodes.index()
                indexnode['entries'] = [('single', termtext, new_id, termtext)]
                li.insert(0, indexnode)
                items.append((termtext, li))
        if 'sorted' in self.options:
            items.sort(key=lambda x: x[0].lower())
        new_dl.extend(item[1] for item in items)
        node.children = [new_dl]
        return [node]


class Centered(Directive):
    """
    Directive to create a centered line of bold text.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        if not self.arguments:
            return []
        subnode = addnodes.centered()
        inodes, messages = self.state.inline_text(self.arguments[0],
                                                  self.lineno)
        subnode.extend(inodes)
        return [subnode] + messages



class Acks(Directive):
    """
    Directive for a list of names.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        node = addnodes.acks()
        node.document = self.state.document
        self.state.nested_parse(self.content, self.content_offset, node)
        if len(node.children) != 1 or not isinstance(node.children[0],
                                                     nodes.bullet_list):
            return [self.state.document.reporter.warning(
                '.. acks content is not a list', line=self.lineno)]
        return [node]


class HList(Directive):
    """
    Directive for a list that gets compacted horizontally.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'columns': int,
    }

    def run(self):
        ncolumns = self.options.get('columns', 2)
        node = nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(self.content, self.content_offset, node)
        if len(node.children) != 1 or not isinstance(node.children[0],
                                                     nodes.bullet_list):
            return [self.state.document.reporter.warning(
                '.. hlist content is not a list', line=self.lineno)]
        fulllist = node.children[0]
        # create a hlist node where the items are distributed
        npercol, nmore = divmod(len(fulllist), ncolumns)
        index = 0
        newnode = addnodes.hlist()
        for column in range(ncolumns):
            endindex = index + (column < nmore and (npercol+1) or npercol)
            col = addnodes.hlistcol()
            col += nodes.bullet_list()
            col[0] += fulllist.children[index:endindex]
            index = endindex
            newnode += col
        return [newnode]


class Only(Directive):
    """
    Directive to only include text if the given tag(s) are enabled.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        node = addnodes.only()
        node.document = self.state.document
        node.line = self.lineno
        node['expr'] = self.arguments[0]
        self.state.nested_parse(self.content, self.content_offset, node,
                                match_titles=1)
        return [node]


directives.register_directive('toctree', directive_dwim(TocTree))
directives.register_directive('module', directive_dwim(Module))
directives.register_directive('currentmodule', directive_dwim(CurrentModule))
directives.register_directive('sectionauthor', directive_dwim(Author))
directives.register_directive('moduleauthor', directive_dwim(Author))
directives.register_directive('program', directive_dwim(Program))
directives.register_directive('index', directive_dwim(Index))
directives.register_directive('deprecated', directive_dwim(VersionChange))
directives.register_directive('versionadded', directive_dwim(VersionChange))
directives.register_directive('versionchanged', directive_dwim(VersionChange))
directives.register_directive('seealso', directive_dwim(SeeAlso))
directives.register_directive('productionlist', directive_dwim(ProductionList))
directives.register_directive('tabularcolumns', directive_dwim(TabularColumns))
directives.register_directive('glossary', directive_dwim(Glossary))
directives.register_directive('centered', directive_dwim(Centered))
directives.register_directive('acks', directive_dwim(Acks))
directives.register_directive('hlist', directive_dwim(HList))
directives.register_directive('only', directive_dwim(Only))

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
