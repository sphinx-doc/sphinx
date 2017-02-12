# -*- coding: utf-8 -*-
"""
    sphinx.directives.code
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import codecs
from difflib import unified_diff

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList

from sphinx import addnodes
from sphinx.locale import _
from sphinx.util import parselinenos
from sphinx.util.nodes import set_source_info

if False:
    # For type annotation
    from typing import Any, Tuple  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.config import Config  # NOQA


class Highlight(Directive):
    """
    Directive to set the highlighting language for code blocks, as well
    as the threshold for line numbers.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'linenothreshold': directives.unchanged,
    }

    def run(self):
        # type: () -> List[nodes.Node]
        if 'linenothreshold' in self.options:
            try:
                linenothreshold = int(self.options['linenothreshold'])
            except Exception:
                linenothreshold = 10
        else:
            linenothreshold = sys.maxsize
        return [addnodes.highlightlang(lang=self.arguments[0].strip(),
                                       linenothreshold=linenothreshold)]


def dedent_lines(lines, dedent):
    # type: (List[unicode], int) -> List[unicode]
    if not dedent:
        return lines

    new_lines = []
    for line in lines:
        new_line = line[dedent:]
        if line.endswith('\n') and not new_line:
            new_line = '\n'  # keep CRLF
        new_lines.append(new_line)

    return new_lines


def container_wrapper(directive, literal_node, caption):
    # type: (Directive, nodes.Node, unicode) -> nodes.container
    container_node = nodes.container('', literal_block=True,
                                     classes=['literal-block-wrapper'])
    parsed = nodes.Element()
    directive.state.nested_parse(ViewList([caption], source=''),
                                 directive.content_offset, parsed)
    if isinstance(parsed[0], nodes.system_message):
        msg = _('Invalid caption: %s' % parsed[0].astext())
        raise ValueError(msg)
    caption_node = nodes.caption(parsed[0].rawsource, '',
                                 *parsed[0].children)
    caption_node.source = literal_node.source
    caption_node.line = literal_node.line
    container_node += caption_node
    container_node += literal_node
    return container_node


class CodeBlock(Directive):
    """
    Directive for a code block with special highlighting or line numbering
    settings.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'linenos': directives.flag,
        'dedent': int,
        'lineno-start': int,
        'emphasize-lines': directives.unchanged_required,
        'caption': directives.unchanged_required,
        'class': directives.class_option,
        'name': directives.unchanged,
    }

    def run(self):
        # type: () -> List[nodes.Node]
        document = self.state.document
        code = u'\n'.join(self.content)

        linespec = self.options.get('emphasize-lines')
        if linespec:
            try:
                nlines = len(self.content)
                hl_lines = [x + 1 for x in parselinenos(linespec, nlines)]
            except ValueError as err:
                return [document.reporter.warning(str(err), line=self.lineno)]
        else:
            hl_lines = None

        if 'dedent' in self.options:
            lines = code.split('\n')
            lines = dedent_lines(lines, self.options['dedent'])
            code = '\n'.join(lines)

        literal = nodes.literal_block(code, code)
        literal['language'] = self.arguments[0]
        literal['linenos'] = 'linenos' in self.options or \
                             'lineno-start' in self.options
        literal['classes'] += self.options.get('class', [])
        extra_args = literal['highlight_args'] = {}
        if hl_lines is not None:
            extra_args['hl_lines'] = hl_lines
        if 'lineno-start' in self.options:
            extra_args['linenostart'] = self.options['lineno-start']
        set_source_info(self, literal)

        caption = self.options.get('caption')
        if caption:
            try:
                literal = container_wrapper(self, literal, caption)
            except ValueError as exc:
                return [document.reporter.warning(str(exc), line=self.lineno)]

        # literal will be note_implicit_target that is linked from caption and numref.
        # when options['name'] is provided, it should be primary ID.
        self.add_name(literal)

        return [literal]


class LiteralIncludeReader(object):
    INVALID_OPTIONS_PAIR = [
        ('pyobject', 'lines'),
        ('lineno-match', 'lineno-start'),
        ('lineno-match', 'append'),
        ('lineno-match', 'prepend'),
        ('start-after', 'start-at'),
        ('end-before', 'end-at'),
        ('diff', 'pyobject'),
        ('diff', 'lineno-start'),
        ('diff', 'lineno-match'),
        ('diff', 'lines'),
        ('diff', 'start-after'),
        ('diff', 'end-before'),
        ('diff', 'start-at'),
        ('diff', 'end-at'),
    ]

    def __init__(self, filename, options, config):
        # type: (unicode, Dict, Config) -> None
        self.filename = filename
        self.options = options
        self.encoding = options.get('encoding', config.source_encoding)
        self.lineno_start = self.options.get('lineno-start', 1)

        self.parse_options()

    def parse_options(self):
        # type: () -> None
        for option1, option2 in self.INVALID_OPTIONS_PAIR:
            if option1 in self.options and option2 in self.options:
                raise ValueError(_('Cannot use both "%s" and "%s" options') %
                                 (option1, option2))

    def read_file(self, filename):
        # type: (unicode) -> List[unicode]
        try:
            with codecs.open(filename, 'r', self.encoding, errors='strict') as f:  # type: ignore  # NOQA
                text = f.read()  # type: unicode
                if 'tab-width' in self.options:
                    text = text.expandtabs(self.options['tab-width'])

                lines = text.splitlines(True)
                if 'dedent' in self.options:
                    return dedent_lines(lines, self.options.get('dedent'))
                else:
                    return lines
        except (IOError, OSError) as exc:
            raise IOError(_('Include file %r not found or reading it failed') % filename)
        except UnicodeError as exc:
            raise UnicodeError(_('Encoding %r used for reading included file %r seems to '
                                 'be wrong, try giving an :encoding: option') %
                               (self.encoding, filename))

    def read(self):
        # type: () -> Tuple[unicode, int]
        if 'diff' in self.options:
            lines = self.show_diff()
        else:
            filters = [self.pyobject_filter,
                       self.lines_filter,
                       self.start_filter,
                       self.end_filter,
                       self.prepend_filter,
                       self.append_filter]
            lines = self.read_file(self.filename)
            for func in filters:
                lines = func(lines)

        return ''.join(lines), len(lines)

    def show_diff(self):
        # type: () -> List[unicode]
        new_lines = self.read_file(self.filename)
        old_filename = self.options.get('diff')
        old_lines = self.read_file(old_filename)
        diff = unified_diff(old_lines, new_lines, old_filename, self.filename)  # type: ignore
        return list(diff)

    def pyobject_filter(self, lines):
        # type: (List[unicode]) -> List[unicode]
        pyobject = self.options.get('pyobject')
        if pyobject:
            from sphinx.pycode import ModuleAnalyzer
            analyzer = ModuleAnalyzer.for_file(self.filename, '')
            tags = analyzer.find_tags()
            if pyobject not in tags:
                raise ValueError(_('Object named %r not found in include file %r') %
                                 (pyobject, self.filename))
            else:
                start = tags[pyobject][1]
                end = tags[pyobject][2]
                lines = lines[start - 1:end - 1]
                if 'lineno-match' in self.options:
                    self.lineno_start = start

        return lines

    def lines_filter(self, lines):
        # type: (List[unicode]) -> List[unicode]
        linespec = self.options.get('lines')
        if linespec:
            linelist = parselinenos(linespec, len(lines))
            if 'lineno-match' in self.options:
                # make sure the line list is not "disjoint".
                first = linelist[0]
                if all(first + i == n for i, n in enumerate(linelist)):
                    self.lineno_start = linelist[0] + 1
                else:
                    raise ValueError(_('Cannot use "lineno-match" with a disjoint '
                                       'set of "lines"'))

            lines = [lines[n] for n in linelist]

        return lines

    def start_filter(self, lines):
        # type: (List[unicode]) -> List[unicode]
        if 'start-at' in self.options:
            start = self.options.get('start-at')
            inclusive = False
        elif 'start-after' in self.options:
            start = self.options.get('start-after')
            inclusive = True
        else:
            start = None

        if start:
            for lineno, line in enumerate(lines):
                if start in line:
                    if 'lineno-match' in self.options:
                        self.lineno_start += lineno + 1

                    if inclusive:
                        return lines[lineno + 1:]
                    else:
                        return lines[lineno:]

        return lines

    def end_filter(self, lines):
        # type: (List[unicode]) -> List[unicode]
        if 'end-at' in self.options:
            end = self.options.get('end-at')
            inclusive = True
        elif 'end-before' in self.options:
            end = self.options.get('end-before')
            inclusive = False
        else:
            end = None

        if end:
            for lineno, line in enumerate(lines):
                if end in line:
                    if 'lineno-match' in self.options:
                        self.lineno_start += lineno + 1

                    if inclusive:
                        return lines[:lineno + 1]
                    else:
                        if lineno == 0:
                            return []
                        else:
                            return lines[:lineno]

        return lines

    def prepend_filter(self, lines):
        # type: (List[unicode]) -> List[unicode]
        prepend = self.options.get('prepend')
        if prepend:
            lines.insert(0, prepend + '\n')

        return lines

    def append_filter(self, lines):
        # type: (List[unicode]) -> List[unicode]
        append = self.options.get('append')
        if append:
            lines.append(append + '\n')

        return lines


class LiteralInclude(Directive):
    """
    Like ``.. include:: :literal:``, but only warns if the include file is
    not found, and does not raise errors.  Also has several options for
    selecting what to include.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'dedent': int,
        'linenos': directives.flag,
        'lineno-start': int,
        'lineno-match': directives.flag,
        'tab-width': int,
        'language': directives.unchanged_required,
        'encoding': directives.encoding,
        'pyobject': directives.unchanged_required,
        'lines': directives.unchanged_required,
        'start-after': directives.unchanged_required,
        'end-before': directives.unchanged_required,
        'start-at': directives.unchanged_required,
        'end-at': directives.unchanged_required,
        'prepend': directives.unchanged_required,
        'append': directives.unchanged_required,
        'emphasize-lines': directives.unchanged_required,
        'caption': directives.unchanged,
        'class': directives.class_option,
        'name': directives.unchanged,
        'diff': directives.unchanged_required,
    }

    def run(self):
        # type: () -> List[nodes.Node]
        document = self.state.document
        if not document.settings.file_insertion_enabled:
            return [document.reporter.warning('File insertion disabled',
                                              line=self.lineno)]
        env = document.settings.env

        # convert options['diff'] to absolute path
        if 'diff' in self.options:
            _, path = env.relfn2path(self.options['diff'])
            self.options['diff'] = path

        try:
            rel_filename, filename = env.relfn2path(self.arguments[0])
            env.note_dependency(rel_filename)

            reader = LiteralIncludeReader(filename, self.options, env.config)
            text, lines = reader.read()

            retnode = nodes.literal_block(text, text, source=filename)
            set_source_info(self, retnode)
            if self.options.get('diff'):  # if diff is set, set udiff
                retnode['language'] = 'udiff'
            elif 'language' in self.options:
                retnode['language'] = self.options['language']
            retnode['linenos'] = ('linenos' in self.options or
                                  'lineno-start' in self.options or
                                  'lineno-match' in self.options)
            retnode['classes'] += self.options.get('class', [])
            extra_args = retnode['highlight_args'] = {}
            if 'empahsize-lines' in self.options:
                hl_lines = parselinenos(self.options['emphasize-lines'], lines)
                extra_args['hl_lines'] = [x + 1 for x in hl_lines]
            extra_args['linenostart'] = reader.lineno_start

            if 'caption' in self.options:
                caption = self.options['caption'] or self.arguments[0]
                retnode = container_wrapper(self, retnode, caption)

            # retnode will be note_implicit_target that is linked from caption and numref.
            # when options['name'] is provided, it should be primary ID.
            self.add_name(retnode)

            return [retnode]
        except Exception as exc:
            return [document.reporter.warning(str(exc), line=self.lineno)]


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    directives.register_directive('highlight', Highlight)
    directives.register_directive('highlightlang', Highlight)  # old
    directives.register_directive('code-block', CodeBlock)
    directives.register_directive('sourcecode', CodeBlock)
    directives.register_directive('literalinclude', LiteralInclude)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
