# -*- coding: utf-8 -*-
"""
    sphinx.directives.other
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from sphinx import addnodes
from sphinx.locale import pairindextypes, _
from sphinx.util import url_re, docname_join
from sphinx.util.nodes import explicit_title_re
from sphinx.util.compat import make_admonition
from sphinx.util.matching import patfilter


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
        'titlesonly': directives.flag,
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
        all_docnames = env.found_docs.copy()
        # don't add the currently visited file in catch-all patterns
        all_docnames.remove(env.docname)
        for entry in self.content:
            if not entry:
                continue
            if not glob:
                # look for explicit titles ("Some Title <document>")
                m = explicit_title_re.match(entry)
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
                        'toctree contains reference to nonexisting '
                        'document %r' % docname, line=self.lineno))
                    env.note_reread()
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
        subnode['titlesonly'] = 'titlesonly' in self.options
        wrappernode = nodes.compound(classes=['toctree-wrapper'])
        wrappernode.append(subnode)
        ret.append(wrappernode)
        return ret


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
        elif self.name == 'codeauthor':
            text = _('Code author: ')
        else:
            text = _('Author: ')
        emph += nodes.Text(text, text)
        inodes, messages = self.state.inline_text(self.arguments[0],
                                                  self.lineno)
        emph.extend(inodes)
        return [para] + messages


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
        targetid = 'index-%s' % env.new_serialno('index')
        targetnode = nodes.target('', '', ids=[targetid])
        self.state.document.note_explicit_target(targetnode)
        indexnode = addnodes.index()
        indexnode['entries'] = ne = []
        indexnode['inline'] = False
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
        node.line = self.lineno
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


from docutils.parsers.rst.directives.misc import Include as BaseInclude

class Include(BaseInclude):
    """
    Like the standard "Include" directive, but interprets absolute paths
    correctly.
    """

    def run(self):
        if self.arguments[0].startswith('/') or \
               self.arguments[0].startswith(os.sep):
            env = self.state.document.settings.env
            self.arguments[0] = os.path.join(env.srcdir, self.arguments[0][1:])
        return BaseInclude.run(self)


directives.register_directive('toctree', TocTree)
directives.register_directive('sectionauthor', Author)
directives.register_directive('moduleauthor', Author)
directives.register_directive('codeauthor', Author)
directives.register_directive('index', Index)
directives.register_directive('deprecated', VersionChange)
directives.register_directive('versionadded', VersionChange)
directives.register_directive('versionchanged', VersionChange)
directives.register_directive('seealso', SeeAlso)
directives.register_directive('tabularcolumns', TabularColumns)
directives.register_directive('centered', Centered)
directives.register_directive('acks', Acks)
directives.register_directive('hlist', HList)
directives.register_directive('only', Only)
directives.register_directive('include', Include)

# register the standard rst class directive under a different name
from docutils.parsers.rst.directives.misc import Class
# only for backwards compatibility now
directives.register_directive('cssclass', Class)
# new standard name when default-domain with "class" is in effect
directives.register_directive('rst-class', Class)
