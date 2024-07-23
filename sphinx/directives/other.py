from __future__ import annotations

import re
from os.path import abspath, relpath
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.admonitions import BaseAdmonition
from docutils.parsers.rst.directives.misc import Class
from docutils.parsers.rst.directives.misc import Include as BaseInclude
from docutils.statemachine import StateMachine

from sphinx import addnodes
from sphinx.domains.changeset import VersionChange  # NoQA: F401  # for compatibility
from sphinx.domains.std import StandardDomain
from sphinx.locale import _, __
from sphinx.util import docname_join, logging, url_re
from sphinx.util.docutils import SphinxDirective
from sphinx.util.matching import Matcher, patfilter
from sphinx.util.nodes import explicit_title_re

if TYPE_CHECKING:
    from collections.abc import Sequence

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
        subnode['parent'] = self.env.docname

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
        wrappernode = nodes.compound(
            classes=['toctree-wrapper', *self.options.get('class', ())],
        )
        wrappernode.append(subnode)
        self.add_name(wrappernode)

        ret = self.parse_content(subnode)
        ret.append(wrappernode)
        return ret

    def parse_content(self, toctree: addnodes.toctree) -> list[Node]:
        generated_docnames = frozenset(StandardDomain._virtual_doc_names)
        suffixes = self.config.source_suffix
        current_docname = self.env.docname
        glob = toctree['glob']

        # glob target documents
        all_docnames = self.env.found_docs.copy() | generated_docnames
        all_docnames.remove(current_docname)  # remove current document
        frozen_all_docnames = frozenset(all_docnames)

        ret: list[Node] = []
        excluded = Matcher(self.config.exclude_patterns)
        for entry in self.content:
            if not entry:
                continue

            # look for explicit titles ("Some Title <document>")
            explicit = explicit_title_re.match(entry)
            url_match = url_re.match(entry) is not None
            if glob and glob_re.match(entry) and not explicit and not url_match:
                pat_name = docname_join(current_docname, entry)
                doc_names = sorted(patfilter(all_docnames, pat_name))
                for docname in doc_names:
                    if docname in generated_docnames:
                        # don't include generated documents in globs
                        continue
                    all_docnames.remove(docname)  # don't include it again
                    toctree['entries'].append((None, docname))
                    toctree['includefiles'].append(docname)
                if not doc_names:
                    logger.warning(__("toctree glob pattern %r didn't match any documents"),
                                   entry, location=toctree)
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
                if excluded(self.env.doc2path(docname, False)):
                    message = __('toctree contains reference to excluded document %r')
                    subtype = 'excluded'
                else:
                    message = __('toctree contains reference to nonexisting document %r')
                    subtype = 'not_readable'

                logger.warning(message, docname, type='toc', subtype=subtype,
                               location=toctree)
                self.env.note_reread()
                continue

            if docname in all_docnames:
                all_docnames.remove(docname)
            else:
                logger.warning(__('duplicated entry found in toctree: %s'), docname,
                               location=toctree)

            toctree['entries'].append((title, docname))
            toctree['includefiles'].append(docname)

        # entries contains all entries (self references, external links etc.)
        if 'reversed' in self.options:
            toctree['entries'] = list(reversed(toctree['entries']))
            toctree['includefiles'] = list(reversed(toctree['includefiles']))

        return ret


class Author(SphinxDirective):
    """
    Directive to give the name of the author of the current document
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


class SeeAlso(BaseAdmonition):  # type: ignore[misc]
    """
    An admonition mentioning things to look at as reference.
    """

    node_class = addnodes.seealso


class TabularColumns(SphinxDirective):
    """
    Directive to give an explicit tabulary column definition to LaTeX.
    """

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
    """
    Directive to create a centered line of bold text.
    """

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
    """
    Directive for a list of names.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec: ClassVar[OptionSpec] = {}

    def run(self) -> list[Node]:
        children = self.parse_content_to_nodes()
        if len(children) != 1 or not isinstance(children[0], nodes.bullet_list):
            logger.warning(__('.. acks content is not a list'),
                           location=(self.env.docname, self.lineno))
            return []
        return [addnodes.acks('', *children)]


class HList(SphinxDirective):
    """
    Directive for a list that gets compacted horizontally.
    """

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
            logger.warning(__('.. hlist content is not a list'),
                           location=(self.env.docname, self.lineno))
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
    """
    Directive to only include text if the given tag(s) are enabled.

    This directive functions somewhat akin to a pre-processor,
    as tag expressions are constant throughout the build.
    The ``only`` directive is the only one that is able to 'hoist'
    content in the section hierarchy, as the expected usage includes
    conditional inclusion of sections.

    At present, there is no supported mechanism to parse content that
    may contain section headings at a level equal to or greater than
    the section containing the ``only`` directive. Implementation of
    such a mechanism is possible, though complex. Prior to Sphinx 7.4,
    this approach was used to implement the ``only`` directive.

    The current implementation makes use of the ability to modify the
    input lines of the document being parsed, whilst parsing it. This
    is not encouraged. Given the nature of ``only`` as both a special
    case and akin to a pre-processor, this is considered acceptable.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec: ClassVar[OptionSpec] = {}

    def run(self) -> list[Node]:
        tags = self.env.app.builder.tags
        expr = self.arguments[0]

        try:
            keep_content = tags.eval_condition(expr)
        except Exception as err:
            logger.warning(
                __('exception while evaluating only directive expression: %s'),
                err,
                location=self.get_location())
            keep_content = True

        # Does the directive content end with a newline?
        trailing_newline = self.block_text[-1] == '\n'

        # Calculate line counts for the entire block, the content, and the preamble.
        total_line_count = self.block_text.count('\n') + 1
        content_line_count = len(self.content.data) + (1 * trailing_newline)
        preamble_line_count = total_line_count - content_line_count

        # Calculate the location of the directive content in the input lines.
        offset_end = self.state_machine.line_offset
        offset_start = offset_end - total_line_count + 1

        # Every copy of ``input_lines`` must be updated, so we propagate up
        # through the parent hierarchy.
        input_lines = self.state_machine.input_lines
        while input_lines is not None:
            if keep_content:
                blank_lines = [''] * preamble_line_count
                content = self.content.data + ([''] * trailing_newline)
                # Blank out the initial lines
                input_lines.data[offset_start:offset_start + preamble_line_count] = blank_lines
                # Replace the remaining lines with the unindented content
                input_lines.data[offset_start + preamble_line_count:offset_end + 1] = content
            else:
                blank_lines = [''] * total_line_count
                # Blank out every line
                input_lines.data[offset_start:offset_end + 1] = blank_lines

            # Update the offsets for the parent
            if input_lines.parent_offset is not None:
                offset_start += input_lines.parent_offset
                offset_end += input_lines.parent_offset
            input_lines = input_lines.parent

        # ``1 - directive_lines`` is from the offset_start calculation
        self.state_machine.next_line(1 - total_line_count)
        return []


class Include(BaseInclude, SphinxDirective):
    """
    Like the standard "Include" directive, but interprets absolute paths
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
            text = "\n".join(include_lines[:-2])

            path = Path(relpath(abspath(source), start=self.env.srcdir))
            docname = self.env.docname

            # Emit the "include-read" event
            arg = [text]
            self.env.app.events.emit('include-read', path, docname, arg)
            text = arg[0]

            # Split back into lines and reattach the two marker lines
            include_lines = text.splitlines() + include_lines[-2:]

            # Call the parent implementation.
            # Note that this snake does not eat its tail because we patch
            # the *Instance* method and this call is to the *Class* method.
            return StateMachine.insert_input(self.state_machine, include_lines, source)

        # Only enable this patch if there are listeners for 'include-read'.
        if self.env.app.events.listeners.get('include-read'):
            # See https://github.com/python/mypy/issues/2427 for details on the mypy issue
            self.state_machine.insert_input = _insert_input

        if self.arguments[0].startswith('<') and \
           self.arguments[0].endswith('>'):
            # docutils "standard" includes, do not do path processing
            return super().run()
        rel_filename, filename = self.env.relfn2path(self.arguments[0])
        self.arguments[0] = filename
        self.env.note_included(filename)
        return super().run()


def setup(app: Sphinx) -> ExtensionMetadata:
    directives.register_directive('toctree', TocTree)
    directives.register_directive('sectionauthor', Author)
    directives.register_directive('moduleauthor', Author)
    directives.register_directive('codeauthor', Author)
    directives.register_directive('seealso', SeeAlso)
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
