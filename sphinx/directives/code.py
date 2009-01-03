# -*- coding: utf-8 -*-
"""
    sphinx.directives.code
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007-2009 by Georg Brandl.
    :license: BSD, see LICENSE for details.
"""

import sys
import codecs
from os import path

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.util import parselinenos


# ------ highlight directive --------------------------------------------------------

def highlightlang_directive(name, arguments, options, content, lineno,
                            content_offset, block_text, state, state_machine):
    if 'linenothreshold' in options:
        try:
            linenothreshold = int(options['linenothreshold'])
        except Exception:
            linenothreshold = 10
    else:
        linenothreshold = sys.maxint
    return [addnodes.highlightlang(lang=arguments[0].strip(),
                                   linenothreshold=linenothreshold)]

highlightlang_directive.content = 0
highlightlang_directive.arguments = (1, 0, 0)
highlightlang_directive.options = {'linenothreshold': directives.unchanged}
directives.register_directive('highlight', highlightlang_directive)
directives.register_directive('highlightlang', highlightlang_directive) # old name


# ------ code-block directive -------------------------------------------------------

def codeblock_directive(name, arguments, options, content, lineno,
                        content_offset, block_text, state, state_machine):
    code = u'\n'.join(content)
    literal = nodes.literal_block(code, code)
    literal['language'] = arguments[0]
    literal['linenos'] = 'linenos' in options
    return [literal]

codeblock_directive.content = 1
codeblock_directive.arguments = (1, 0, 0)
codeblock_directive.options = {'linenos': directives.flag}
directives.register_directive('code-block', codeblock_directive)
directives.register_directive('sourcecode', codeblock_directive)


# ------ literalinclude directive ---------------------------------------------------

def literalinclude_directive(name, arguments, options, content, lineno,
                             content_offset, block_text, state, state_machine):
    """Like .. include:: :literal:, but only warns if the include file is not found."""
    if not state.document.settings.file_insertion_enabled:
        return [state.document.reporter.warning('File insertion disabled', line=lineno)]
    env = state.document.settings.env
    rel_fn = arguments[0]
    source_dir = path.dirname(path.abspath(state_machine.input_lines.source(
        lineno - state_machine.input_offset - 1)))
    fn = path.normpath(path.join(source_dir, rel_fn))

    if 'pyobject' in options and 'lines' in options:
        return [state.document.reporter.warning(
            'Cannot use both "pyobject" and "lines" options', line=lineno)]

    encoding = options.get('encoding', env.config.source_encoding)
    try:
        f = codecs.open(fn, 'r', encoding)
        lines = f.readlines()
        f.close()
    except (IOError, OSError):
        return [state.document.reporter.warning(
            'Include file %r not found or reading it failed' % arguments[0],
            line=lineno)]
    except UnicodeError:
        return [state.document.reporter.warning(
            'Encoding %r used for reading included file %r seems to '
            'be wrong, try giving an :encoding: option' %
            (encoding, arguments[0]))]

    objectname = options.get('pyobject')
    if objectname is not None:
        from sphinx.pycode import ModuleAnalyzer
        analyzer = ModuleAnalyzer.for_file(fn, '')
        tags = analyzer.find_tags()
        if objectname not in tags:
            return [state.document.reporter.warning(
                'Object named %r not found in include file %r' %
                (objectname, arguments[0]), line=lineno)]
        else:
            lines = lines[tags[objectname][1] - 1 : tags[objectname][2] - 1]

    linespec = options.get('lines')
    if linespec is not None:
        try:
            linelist = parselinenos(linespec, len(lines))
        except ValueError, err:
            return [state.document.reporter.warning(str(err), line=lineno)]
        lines = [lines[i] for i in linelist]

    startafter = options.get('start-after')
    endbefore = options.get('end-before')
    if startafter is not None or endbefore is not None:
        use = not startafter
        res = []
        for line in lines:
            if not use and startafter in line:
                use = True
            elif use and endbefore in line:
                use = False
                break
            elif use:
                res.append(line)
        lines = res

    text = ''.join(lines)
    retnode = nodes.literal_block(text, text, source=fn)
    retnode.line = 1
    if options.get('language', ''):
        retnode['language'] = options['language']
    if 'linenos' in options:
        retnode['linenos'] = True
    state.document.settings.env.note_dependency(rel_fn)
    return [retnode]

literalinclude_directive.options = {'linenos': directives.flag,
                                    'language': directives.unchanged_required,
                                    'encoding': directives.encoding,
                                    'pyobject': directives.unchanged_required,
                                    'lines': directives.unchanged_required,
                                    'start-after': directives.unchanged_required,
                                    'end-before': directives.unchanged_required,
                                    }
literalinclude_directive.content = 0
literalinclude_directive.arguments = (1, 0, 0)
directives.register_directive('literalinclude', literalinclude_directive)
