from __future__ import annotations

import re
from os.path import relpath
from pathlib import Path
from typing import TYPE_CHECKING

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.misc import Class
from docutils.parsers.rst.directives.misc import Include as BaseInclude
from docutils.statemachine import StateMachine

from sphinx import addnodes
from sphinx.domains.std import StandardDomain
from sphinx.locale import _, __
from sphinx.util import docname_join, logging, url_re
from sphinx.util.docutils import SphinxDirective
from sphinx.util.matching import Matcher, patfilter
from sphinx.util.nodes import explicit_title_re

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import ClassVar

    from docutils.nodes import Element, Node

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata, OptionSpec


glob_re = re.compile(r'.*[*?\[].*')
logger = logging.getLogger(__name__)


def int_or_nothing(argument: str) -> int:
    if not argument:
        return 999
    return int(argument)


class TocTree(SphinxDirective):
    """Directive to notify Sphinx about the hierarchical structure of the docs,
    and to include a table-of-contents like tree in the current document.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'maxdepth': int,
        'name': directives.unchanged,
        'class': directives.class_option,
        'caption': directives.unchanged_required,
        'glob': directives.flag,
        'hidden': directives.flag,
        'includehidden': directives.flag,
        'numbered': int_or_nothing,
        'titlesonly': directives.flag,
        'reversed': directives.flag,
    }

    def run(self) -> list[Node]:
        subnode = addnodes.toctree()
        subnode['parent'] = self.env.current_document.docname

        # (title, ref) pairs, where ref may be a document, or an external link,
        # and title may be None if the document's title is to be used
        subnode['entries'] = []
        subnode['includefiles'] = []
        subnode['maxdepth'] = self.options.get('maxdepth', -1)
        subnode['caption'] = self.options.get('caption')
        subnode['glob'] = 'glob' in self.options
        subnode['hidden'] = 'hidden' in self.options
        subnode['includehidden'] = 'includehidden' in self.options
        subnode['numbered'] = self.options.get('numbered', 0)
        subnode['titlesonly'] = 'titlesonly' in self.options
        self.set_source_info(subnode)
        self.parse_content(subnode)

        wrappernode = nodes.compound(
            classes=['toctree-wrapper', *self.options.get('class', ())],
        )
        wrappernode.append(subnode)
        self.add_name(wrappernode)
        return [wrappernode]

    def parse_content(self, toctree: addnodes.toctree) -> None:
        """Populate ``toctree['entries']`` and ``toctree['includefiles']`` from content."""
        generated_docnames = frozenset(StandardDomain._virtual_doc_names)
        suffixes = self.config.source_suffix
        current_docname = self.env.current_document.docname
        glob = toctree['glob']

        # glob target documents
        all_docnames = self.env.found_docs.copy() | generated_docnames
        all_docnames.remove(current_docname)  # remove current document
        frozen_all_docnames = frozenset(all_docnames)

        excluded = Matcher(self.config.exclude_patterns)
        for entry in self.content:
            if not entry:
                continue

            # look for explicit titles ("Some Title <document>")
            explicit = explicit_title_re.match(entry)
            url_match = url_re.match(entry) is not None
            if glob and glob_re.match(entry) and not explicit and not url_match:
                pat_name = docname_join(current_docname, entry)
                doc_names = sorted(
                    docname
                    for docname in patfilter(all_docnames, pat_name)
                    # don't include generated documents in globs
                    if docname not in generated_docnames
                )
                if not doc_names:
                    logger.warning(
                        __("toctree glob pattern %r didn't match any documents"),
                        entry,
                        location=toctree,
                        subtype='empty_glob',
                    )

                for docname in doc_names:
                    all_docnames.remove(docname)  # don't include it again
                    toctree['entries'].append((None, docname))
                    toctree['includefiles'].append(docname)
                continue

            if explicit:
                ref = explicit.group(2)
                title = explicit.group(1)
                docname = ref
            else:
                ref = docname = entry
                title = None

            # remove suffixes (backwards compatibility)
            for suffix in suffixes:
                if docname.endswith(suffix):
                    docname = docname.removesuffix(suffix)
                    break

            # absolutise filenames
            docname = docname_join(current_docname, docname)
            if url_match or ref == 'self':
                toctree['entries'].append((title, ref))
                continue

            if docname not in frozen_all_docnames:
                if excluded(str(self.env.doc2path(docname, False))):
                    msg = __('toctree contains reference to excluded document %r')
                    subtype = 'excluded'
                else:
                    msg = __('toctree contains reference to nonexisting document %r')
                    subtype = 'not_readable'

                logger.warning(
                    msg, docname, location=toctree, type='toc', subtype=subtype
                )
                self.env.note_reread()
                continue

            if docname in all_docnames:
                all_docnames.remove(docname)
            else:
                logger.warning(
                    __('duplicated entry found in toctree: %s'),
                    docname,
                    location=toctree,
                    type='toc',
                    subtype='duplicate_entry',
                )

            toctree['entries'].append((title, docname))
            toctree['includefiles'].append(docname)

        # entries contains all entries (self references, external links etc.)
        if 'reversed' in self.options:
            toctree['entries'] = list(reversed(toctree['entries']))
            toctree['includefiles'] = list(reversed(toctree['includefiles']))


class Author(SphinxDirective):
    """Directive to give the name of the author of the current document
    or section. Shown in the output only if the show_authors option is on.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec: ClassVar[OptionSpec] = {}

    def run(self) -> list[Node]:
        if not self.config.show_authors:
            return []
        para: Element = nodes.paragraph(translatable=False)
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
        emph += nodes.Text(text)
        inodes, messages = self.parse_inline(self.arguments[0])
        emph.extend(inodes)

        ret: list[Node] = [para]
        ret += messages
        return ret


class TabularColumns(SphinxDirective):
    """Directive to give an explicit tabulary column definition to LaTeX."""

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec: ClassVar[OptionSpec] = {}

    def run(self) -> list[Node]:
        node = addnodes.tabular_col_spec()
        node['spec'] = self.arguments[0]
        self.set_source_info(node)
        return [node]


class Centered(SphinxDirective):
    """Directive to create a centered line of bold text."""

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec: ClassVar[OptionSpec] = {}

    def run(self) -> list[Node]:
        if not self.arguments:
            return []
        subnode: Element = addnodes.centered()
        inodes, messages = self.parse_inline(self.arguments[0])
        subnode.extend(inodes)

        ret: list[Node] = [subnode]
        ret += messages
        return ret


class Acks(SphinxDirective):
    """Directive for a list of names."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec: ClassVar[OptionSpec] = {}

    def run(self) -> list[Node]:
        children = self.parse_content_to_nodes()
        if len(children) != 1 or not isinstance(children[0], nodes.bullet_list):
            logger.warning(
                __('.. acks content is not a list'),
                location=(self.env.current_document.docname, self.lineno),
            )
            return []
        return [addnodes.acks('', *children)]


class HList(SphinxDirective):
    """Directive for a list that gets compacted horizontally."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec: ClassVar[OptionSpec] = {
        'columns': int,
    }

    def run(self) -> list[Node]:
        ncolumns = self.options.get('columns', 2)
        children = self.parse_content_to_nodes()
        if len(children) != 1 or not isinstance(children[0], nodes.bullet_list):
            logger.warning(
                __('.. hlist content is not a list'),
                location=(self.env.current_document.docname, self.lineno),
            )
            return []
        fulllist = children[0]
        # create a hlist node where the items are distributed
        npercol, nmore = divmod(len(fulllist), ncolumns)
        index = 0
        newnode = addnodes.hlist()
        newnode['ncolumns'] = str(ncolumns)
        for column in range(ncolumns):
            endindex = index + ((npercol + 1) if column < nmore else npercol)
            bullet_list = nodes.bullet_list()
            bullet_list += fulllist.children[index:endindex]
            newnode += addnodes.hlistcol('', bullet_list)
            index = endindex
        return [newnode]


class Only(SphinxDirective):
    """Directive to only include text if the given tag(s) are enabled."""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec: ClassVar[OptionSpec] = {}

    def run(self) -> list[Node]:
        self.env._only_docs.add(self.env.docname)
        try:
            include_content = self.env._tags.eval_condition(self.arguments[0])
        except Exception as err:
            logger.warning(
                __('exception while evaluating only directive expression: %s'),
                err,
                location=self.get_location(),
            )
            include_content = True

        # Reparse enabled content in the document's active section context.
        # Keep the block's line count unchanged so the parser can reread it at
        # the original offset without shifting source locations.
        total_line_count = self.block_text.count('\n') + 1
        offset_end = self.state_machine.line_offset
        offset_start = offset_end - total_line_count + 1
        input_lines = self.state_machine.input_lines

        content_start = 0
        content_view = self.content
        while content_view is not input_lines:
            if content_view.parent is None or content_view.parent_offset is None:
                msg = 'only directive content is detached from parser input'
                raise RuntimeError(msg)
            content_start += content_view.parent_offset
            content_view = content_view.parent

        # Included and nested input may be a ViewList slice; update each parent.
        while input_lines is not None:
            input_lines.data[offset_start : offset_end + 1] = [''] * total_line_count
            if include_content:
                input_lines.data[content_start : content_start + len(self.content)] = (
                    self.content.data
                )

            if input_lines.parent_offset is not None:
                offset_start += input_lines.parent_offset
                offset_end += input_lines.parent_offset
                content_start += input_lines.parent_offset
            input_lines = input_lines.parent

        self.state_machine.next_line(1 - total_line_count)
        return []


class Include(BaseInclude, SphinxDirective):
    """Like the standard "Include" directive, but interprets absolute paths
    "correctly", i.e. relative to source directory.
    """

    def run(self) -> Sequence[Node]:
        # To properly emit "include-read" events from included RST text,
        # we must patch the ``StateMachine.insert_input()`` method.
        # In the future, docutils will hopefully offer a way for Sphinx
        # to provide the RST parser to use
        # when parsing RST text that comes in via Include directive.
        def _insert_input(include_lines: list[str], source: str) -> None:
            # First, we need to combine the lines back into text so that
            # we can send it with the include-read event.
            # In docutils 0.18 and later, there are two lines at the end
            # that act as markers.
            # We must preserve them and leave them out of the include-read event:
            text = '\n'.join(include_lines[:-2])

            path = Path(relpath(Path(source).resolve(), start=self.env.srcdir))
            docname = self.env.current_document.docname

            # Emit the "include-read" event
            arg = [text]
            self.env.events.emit('include-read', path, docname, arg)
            text = arg[0]

            # Split back into lines and reattach the two marker lines
            include_lines = text.splitlines() + include_lines[-2:]

            # Call the parent implementation.
            # Note that this snake does not eat its tail because we patch
            # the *Instance* method and this call is to the *Class* method.
            return StateMachine.insert_input(self.state_machine, include_lines, source)

        # Only enable this patch if there are listeners for 'include-read'.
        if self.env.events.listeners.get('include-read'):
            self.state_machine.insert_input = _insert_input  # type: ignore[assignment,method-assign]

        if self.arguments[0].startswith('<') and self.arguments[0].endswith('>'):
            # docutils "standard" includes, do not do path processing
            return super().run()
        _rel_filename, filename = self.env.relfn2path(self.arguments[0])
        self.arguments[0] = str(filename)
        self.env.note_included(filename)
        return super().run()


def setup(app: Sphinx) -> ExtensionMetadata:
    directives.register_directive('toctree', TocTree)
    directives.register_directive('sectionauthor', Author)
    directives.register_directive('moduleauthor', Author)
    directives.register_directive('codeauthor', Author)
    directives.register_directive('tabularcolumns', TabularColumns)
    directives.register_directive('centered', Centered)
    directives.register_directive('acks', Acks)
    directives.register_directive('hlist', HList)
    directives.register_directive('only', Only)
    directives.register_directive('include', Include)

    # register the standard rst class directive under a different name
    # only for backwards compatibility now
    directives.register_directive('cssclass', Class)
    # new standard name when default-domain with "class" is in effect
    directives.register_directive('rst-class', Class)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
