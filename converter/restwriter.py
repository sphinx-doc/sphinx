# -*- coding: utf-8 -*-
"""
    Python documentation ReST writer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    How the converter works
    =======================

    A LaTeX document is tokenized by a `Tokenizer`.  The tokens are processed by
    the `DocParser` class which emits a tree of `DocNode`\s. The `RestWriter`
    now walks this node tree and generates ReST from that.

    There are some intricacies while writing ReST:

    - Paragraph text must be rewrapped in order to avoid ragged lines. The
      `textwrap` module does that nicely, but it must obviously operate on a
      whole paragraph at a time. Therefore the contents of the current paragraph
      are cached in `self.curpar`. Every time a block level element is
      encountered, its node handler calls `self.flush_par()` which writes out a
      paragraph. Because this can be detrimental for the markup at several
      stages, the `self.noflush` context manager can be used to forbid paragraph
      flushing temporarily, which means that no block level nodes can be
      processed.

    - There are no inline comments in ReST. Therefore comments are stored in
      `self.comments` and written out every time the paragraph is flushed.

    - A similar thing goes for footnotes: `self.footnotes`.

    - Some inline markup cannot contain nested markup. Therefore the function
      `textonly()` exists which returns a node similar to its argument, but
      stripped of inline markup.

    - Some constructs need to format non-block-level nodes, but without writing
      the result to the current paragraph. These use `self.get_node_text()`
      which writes to a temporary paragraph and returns the resulting markup.

    - Indentation is important. The `self.indent` context manager helps keeping
      track of indentation levels.

    - Some blocks, like lists, need to prevent the first line from being
      indented because the indentation space is already filled (e.g. by a
      bullet). Therefore the `self.indent` context manager accepts a
      `firstline` flag which can be set to ``False``, resulting in the first
      line not being indented.


    There are some restrictions on markup compared to LaTeX:

    - Table cells may not contain blocks.

    - Hard line breaks don't exist.

    - Block level markup inside "alltt" environments doesn't work.

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""

# yay!
from __future__ import with_statement

import re
import StringIO
import textwrap

WIDTH = 80
INDENT = 3

new_wordsep_re = re.compile(
        r'(\s+|'                                  # any whitespace
        r'(?<=\s)(?::[a-z-]+:)?`\S+|'             # interpreted text start
        r'[^\s\w]*\w+[a-zA-Z]-(?=\w+[a-zA-Z])|'   # hyphenated words
        r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash

import textwrap
# monkey-patch...
textwrap.TextWrapper.wordsep_re = new_wordsep_re
wrapper = textwrap.TextWrapper(width=WIDTH, break_long_words=False)

from .docnodes import RootNode, TextNode, NodeList, InlineNode, \
     CommentNode, EmptyNode
from .util import fixup_text, empty, text, my_make_id, \
     repair_bad_inline_markup
from .filenamemap import includes_mapping

class WriterError(Exception):
    pass


class Indenter(object):
    """ Context manager factory for indentation. """
    def __init__(self, writer):
        class IndenterManager(object):
            def __init__(self, indentlevel, flush, firstline):
                self.indentlevel = indentlevel
                self.flush = flush
                self.firstline = firstline

            def __enter__(self):
                writer.indentation += (self.indentlevel * ' ')
                writer.indentfirstline = self.firstline
                return self

            def __exit__(self, *ignored):
                if self.flush:
                    writer.flush_par()
                writer.indentation = writer.indentation[:-self.indentlevel]

        self.manager = IndenterManager

    def __call__(self, indentlevel=INDENT, flush=True, firstline=True):
        return self.manager(indentlevel, flush, firstline)


class NoFlush(object):
    """ Convenience context manager. """
    def __init__(self, writer):
        self.writer = writer

    def __enter__(self):
        self.writer.no_flushing += 1

    def __exit__(self, *ignored):
        self.writer.no_flushing -= 1


class SectionMeta(object):
    def __init__(self):
        self.modname = ''
        self.platform = ''
        self.synopsis = []
        self.modauthors = []
        self.sectauthors = []


class RestWriter(object):
    """ Write ReST from a node tree. """

    def __init__(self, fp, splitchap=False, toctree=None, deflang=None, labelprefix=''):
        self.splitchap = splitchap      # split output at chapters?
        if splitchap:
            self.fp = StringIO.StringIO() # dummy one
            self.chapters = [self.fp]
        else:
            self.fp = fp                # file pointer
        self.toctree = toctree          # entries for the TOC tree
        self.deflang = deflang          # default highlighting language
        self.labelprefix = labelprefix  # prefix for all label names

        # indentation tools
        self.indentation = ''           # current indentation string
        self.indentfirstline = True     # indent the first line of next paragraph?
        self.indented = Indenter(self)  # convenience context manager

        # paragraph flushing tools
        self.flush_cb = None            # callback run on next paragraph flush, used
                                        # for properly separating field lists from
                                        # the following paragraph
        self.no_flushing = 0            # raise an error on paragraph flush?
        self.noflush = NoFlush(self)    # convenience context manager

        # collected items to output later
        self.curpar = []                # text in current paragraph
        self.comments = []              # comments to be output after flushing
        self.indexentries = []          # indexentries to be output before flushing
        self.footnotes = []             # footnotes to be output at document end
        self.warnings = []              # warnings while writing

        # specials
        self.sectionlabel = ''          # most recent \label command
        self.thisclass = ''             # most recent classdesc name
        self.sectionmeta = None         # current section metadata
        self.noescape = 0               # don't escape text nodes
        self.indexsubitem = ''          # current \withsubitem text

    def write_document(self, rootnode):
        """ Write a document, represented by a RootNode. """
        assert type(rootnode) is RootNode

        if self.deflang:
            self.write_directive('highlightlang', self.deflang)

        self.visit_node(rootnode)
        self.write_footnotes()

    def new_chapter(self):
        """ Called if self.splitchap is True. Create a new file pointer
            and set self.fp to it. """
        new_fp = StringIO.StringIO()
        self.chapters.append(new_fp)
        self.fp = new_fp

    def write(self, text='', nl=True, first=False):
        """ Write a string to the output file. """
        if first:
            self.fp.write((self.indentation if self.indentfirstline else '') + text)
            self.indentfirstline = True
        elif text: # don't write indentation only
            self.fp.write(self.indentation + text)
        if nl:
            self.fp.write('\n')

    def write_footnotes(self):
        """ Write the current footnotes, if any. """
        self.flush_par()
        if self.footnotes:
            self.write('.. rubric:: Footnotes\n')
            footnotes = self.footnotes
            self.footnotes = [] # first clear since indented() will flush
            for footnode in footnotes:
                self.write('.. [#] ', nl=False)
                with self.indented(3, firstline=False):
                    self.visit_node(footnode)

    def write_directive(self, name, args='', node=None, spabove=False, spbelow=True):
        """ Helper to write a ReST directive. """
        if spabove:
            self.write()
        self.write('.. %s::%s' % (name, args and ' '+args))
        if spbelow:
            self.write()
        with self.indented():
            if node is not None:
                self.visit_node(node)

    def write_sectionmeta(self):
        mod = self.sectionmeta
        self.sectionmeta = None
        if not mod:
            return
        if mod.modname:
            self.write('.. module:: %s' % mod.modname)
            if mod.platform:
                self.write('   :platform: %s' % mod.platform)
            if mod.synopsis:
                self.write('   :synopsis: %s' % mod.synopsis[0])
                for line in mod.synopsis[1:]:
                    self.write('              %s' % line)
        if mod.modauthors:
            for author in mod.modauthors:
                self.write('.. moduleauthor:: %s' % author)
        if mod.sectauthors:
            for author in mod.sectauthors:
                self.write('.. sectionauthor:: %s' % author)
        self.write()
        self.write()

    indexentry_mapping = {
        'index': 'single',
        'indexii': 'pair',
        'indexiii': 'triple',
        'indexiv': 'quadruple',
        'stindex': 'statement',
        'ttindex': 'single',
        'obindex': 'object',
        'opindex': 'operator',
        'kwindex': 'keyword',
        'exindex': 'exception',
        'bifuncindex': 'builtin',
        'refmodindex': 'module',
        'refbimodindex': 'module',
        'refexmodindex': 'module',
        'refstmodindex': 'module',
    }

    def get_indexentries(self, entries):
        """ Return a list of lines for the index entries. """
        def format_entry(cmdname, args, subitem):
            textargs = []
            for arg in args:
                if isinstance(arg, TextNode):
                    textarg = text(arg)
                else:
                    textarg = self.get_node_text(self.get_textonly_node(arg, warn=0))
                if ';' in textarg:
                    raise WriterError("semicolon in index args: " + textarg)
                textarg += subitem
                textarg = textarg.replace('!', '; ')
                textargs.append(textarg)
            return '%s: %s' % (self.indexentry_mapping[cmdname],
                               '; '.join(textarg for textarg in textargs
                                         if not empty(arg)))

        ret = []
        if len(entries) == 1:
            ret.append('.. index:: %s' % format_entry(*entries[0]))
        else:
            ret.append('.. index::')
            for entry in entries:
                ret.append('   %s' % format_entry(*entry))
        return ret

    def get_par(self, wrap, width=None):
        """ Get the contents of the current paragraph.
            Returns a list if wrap and not indent, else a string. """
        if not self.curpar:
            if wrap:
                return []
            else:
                return ''
        text = ''.join(self.curpar).lstrip()
        text = repair_bad_inline_markup(text)
        self.curpar = []
        if wrap:
            # returns a list!
            wrapper.width = width or WIDTH
            return wrapper.wrap(text)
        else:
            return text

    no_warn_textonly = set((
        'var', 'code', 'textrm', 'emph', 'keyword', 'textit', 'programopt',
        'cfunction', 'texttt', 'email', 'constant',
    ))

    def get_textonly_node(self, node, cmd='', warn=1):
        """ Return a similar Node or NodeList that only has TextNode subnodes.

            Warning values:
             - 0: never warn
             - 1: warn for markup losing information
        """
        if cmd == 'code':
            warn = 0
        def do(subnode):
            if isinstance(subnode, TextNode):
                return subnode
            if isinstance(subnode, NodeList):
                return NodeList(do(subsubnode) for subsubnode in subnode)
            if isinstance(subnode, CommentNode):
                # loses comments, but huh
                return EmptyNode()
            if isinstance(subnode, InlineNode):
                if subnode.cmdname in ('filevar', 'envvar'):
                    return NodeList([TextNode('{'), do(subnode.args[0]), TextNode('}')])
                if subnode.cmdname == 'optional':
                    # this is not mapped to ReST markup
                    return subnode
                if len(subnode.args) == 1:
                    if warn == 1 and subnode.cmdname not in self.no_warn_textonly:
                        self.warnings.append('%r: Discarding %s markup in %r' %
                                             (cmd, subnode.cmdname, node))
                    return do(subnode.args[0])
                elif len(subnode.args) == 0:
                    # should only happen for IndexNodes which stay in
                    return subnode
                elif len(subnode.args) == 2 and subnode.cmdname == 'refmodule':
                    if not warn:
                        return do(subnode.args[1])
            raise WriterError('get_textonly_node() failed for %r' % subnode)
        return do(node)

    def get_node_text(self, node, wrap=False, width=None):
        """ Write the node to a temporary paragraph and return the result
            as a string. """
        with self.noflush:
            self._old_curpar = self.curpar
            self.curpar = []
            self.visit_node(node)
            ret = self.get_par(wrap, width=width)
            self.curpar = self._old_curpar
        return ret

    def flush_par(self, nocb=False, nocomments=False):
        """ Write the current paragraph to the output file.
            Prepend index entries, append comments and footnotes. """
        if self.no_flushing:
            raise WriterError('called flush_par() while noflush active')
        if self.indexentries:
            for line in self.get_indexentries(self.indexentries):
                self.write(line)
            self.write()
            self.indexentries = []
        if self.flush_cb and not nocb:
            self.flush_cb()
            self.flush_cb = None
        par = self.get_par(wrap=True)
        if par:
            for i, line in enumerate(par):
                self.write(line, first=(i==0))
            self.write()
        if self.comments and not nocomments:
            for comment in self.comments:
                self.write('.. % ' + comment)
            self.write()
            self.comments = []

    def visit_wrapped(self, pre, node, post, noescape=False):
        """ Write a node within a paragraph, wrapped with pre and post strings. """
        if noescape:
            self.noescape += 1
        self.curpar.append(pre)
        with self.noflush:
            self.visit_node(node)
        self.curpar.append(post)
        if noescape:
            self.noescape -= 1

    def visit_node(self, node):
        """ "Write" a node (appends to curpar or writes something). """
        visitfunc = getattr(self, 'visit_' + node.__class__.__name__, None)
        if not visitfunc:
            raise WriterError('no visit function for %s node' % node.__class__)
        visitfunc(node)

    # ------------------------- node handlers -----------------------------

    def visit_RootNode(self, node):
        if node.params.get('title'):
            title = self.get_node_text(node.params['title'])
            hl = len(title)
            self.write('*' * (hl+4))
            self.write('  %s  ' % title)
            self.write('*' * (hl+4))
            self.write()

            if node.params.get('author'):
                self.write(':Author: %s%s' %
                           (self.get_node_text(node.params['author']),
                            (' <%s>' % self.get_node_text(node.params['authoremail'])
                             if 'authoremail' in node.params else '')))
                self.write()

            if node.params.get('date'):
                self.write(':Date: %s' % self.get_node_text(node.params['date']))
                self.write()

            if node.params.get('release'):
                self.write('.. |release| replace:: %s' %
                           self.get_node_text(node.params['release']))
                self.write()

        self.visit_NodeList(node.children)

    def visit_NodeList(self, nodelist):
        for node in nodelist:
            self.visit_node(node)

    def visit_CommentNode(self, node):
        # no inline comments -> they are all output at the start of a new paragraph
        self.comments.append(node.comment.strip())

    sectchars = {
        'chapter': '*',
        'chapter*': '*',
        'section': '=',
        'subsection': '-',
        'subsubsection': '^',
        'paragraph': '"',
    }

    sectdoubleline = [
        'chapter',
        'chapter*',
    ]

    def visit_SectioningNode(self, node):
        self.flush_par()
        self.sectionlabel = ''
        self.thisclass = ''
        self.write()

        if self.splitchap and node.cmdname.startswith('chapter'):
            self.write_footnotes()
            self.new_chapter()

        heading = self.get_node_text(node.args[0]).strip()
        if self.sectionlabel:
            self.write('.. _%s:\n' % self.sectionlabel)
        hl = len(heading)
        if node.cmdname in self.sectdoubleline:
            self.write(self.sectchars[node.cmdname] * hl)
        self.write(heading)
        self.write(self.sectchars[node.cmdname] * hl)
        self.write()

    def visit_EnvironmentNode(self, node):
        self.flush_par()
        envname = node.envname
        if envname == 'notice':
            type = text(node.args[0]) or 'note'
            self.write_directive(type, '', node.content)
        elif envname in ('seealso', 'seealso*'):
            self.write_directive('seealso', '', node.content, spabove=True)
        elif envname == 'abstract':
            self.write_directive('topic', 'Abstract', node.content, spabove=True)
        elif envname == 'quote':
            with self.indented():
                self.visit_node(node.content)
            self.write()
        elif envname == 'quotation':
            self.write_directive('epigraph', '', node.content, spabove=True)
        else:
            raise WriterError('no handler for %s environment' % envname)

    descmap = {
        'funcdesc': ('function', '0(1)'),
        'funcdescni': ('function', '0(1)'),
        'classdesc': ('class', '0(1)'),
        'classdesc*': ('class', '0'),
        'methoddesc': ('method', '0.1(2)'),
        'methoddescni': ('method', '0.1(2)'),
        'excdesc': ('exception', '0'),
        'excclassdesc': ('exception', '0(1)'),
        'datadesc': ('data', '0'),
        'datadescni': ('data', '0'),
        'memberdesc': ('attribute', '0.1'),
        'memberdescni': ('attribute', '0.1'),
        'opcodedesc': ('opcode', '0 (1)'),

        'cfuncdesc': ('cfunction', '0 1(2)'),
        'cmemberdesc': ('cmember', '1 0.2'),
        'csimplemacrodesc': ('cmacro', '0'),
        'ctypedesc': ('ctype', '1'),
        'cvardesc': ('cvar', '0 1'),
    }

    def _write_sig(self, spec, args):
        # don't escape "*" in signatures
        self.noescape += 1
        for c in spec:
            if c.isdigit():
                self.visit_node(self.get_textonly_node(args[int(c)]))
            else:
                self.curpar.append(c)
        self.noescape -= 1

    def visit_DescEnvironmentNode(self, node):
        envname = node.envname
        if envname not in self.descmap:
            raise WriterError('no handler for %s environment' % envname)

        self.flush_par()
        # automatically fill in the class name if not given
        if envname[:9] == 'classdesc' or envname[:12] == 'excclassdesc':
            self.thisclass = text(node.args[0])
        elif envname[:10] in ('methoddesc', 'memberdesc') and not \
                 text(node.args[0]):
            if not self.thisclass:
                raise WriterError('No current class for %s member' %
                                  text(node.args[1]))
            node.args[0] = TextNode(self.thisclass)
        directivename, sigspec = self.descmap[envname]
        self._write_sig(sigspec, node.args)
        signature = self.get_par(wrap=False)
        self.write()
        self.write('.. %s:: %s' % (directivename, signature))
        if node.additional:
            for cmdname, add in node.additional:
                entry = self.descmap[cmdname.replace('line', 'desc')]
                if envname[:10] in ('methoddesc', 'memberdesc') and not \
                   text(add[0]):
                    if not self.thisclass:
                        raise WriterError('No current class for %s member' %
                                          text(add[1]))
                    add[0] = TextNode(self.thisclass)
                self._write_sig(entry[1], add)
                signature = self.get_par(wrap=False)
                self.write('        %s%s' % (' ' * (len(directivename) - 2),
                                             signature))
        if envname.endswith('ni'):
            self.write('   :noindex:')
        self.write()
        with self.indented():
            self.visit_node(node.content)


    def visit_CommandNode(self, node):
        cmdname = node.cmdname
        if cmdname == 'label':
            labelname = self.labelprefix + text(node.args[0]).lower()
            if self.no_flushing:
                # in section
                self.sectionlabel = labelname
            else:
                self.flush_par()
                self.write('.. _%s:\n' % labelname)
            return

        elif cmdname in ('declaremodule', 'modulesynopsis',
                       'moduleauthor', 'sectionauthor', 'platform'):
            self.flush_par(nocb=True, nocomments=True)
            if not self.sectionmeta:
                self.sectionmeta = SectionMeta()
            if cmdname == 'declaremodule':
                self.sectionmeta.modname = text(node.args[2])
            elif cmdname == 'modulesynopsis':
                self.sectionmeta.synopsis = self.get_node_text(
                    self.get_textonly_node(node.args[0], warn=0), wrap=True)
            elif cmdname == 'moduleauthor':
                email = text(node.args[1])
                self.sectionmeta.modauthors.append(
                    '%s%s' % (text(node.args[0]), (email and ' <%s>' % email)))
            elif cmdname == 'sectionauthor':
                email = text(node.args[1])
                self.sectionmeta.sectauthors.append(
                    '%s%s' % (text(node.args[0]), (email and ' <%s>' % email)))
            elif cmdname == 'platform':
                self.sectionmeta.platform = text(node.args[0])
            self.flush_cb = lambda: self.write_sectionmeta()
            return

        self.flush_par()
        if cmdname.startswith('see'):
            i = 2
            if cmdname == 'seemodule':
                self.write('Module :mod:`%s`' % text(node.args[1]))
            elif cmdname == 'seelink':
                linktext = self.get_node_text(node.args[1])
                self.write('`%s <%s>`_' % (linktext, text(node.args[0])))
            elif cmdname == 'seepep':
                self.write(':pep:`%s` - %s' % (text(node.args[0]),
                                               self.get_node_text(node.args[1])))
            elif cmdname == 'seerfc':
                self.write(':rfc:`%s` - %s' % (text(node.args[0]),
                                               text(node.args[1])))
            elif cmdname == 'seetitle':
                if empty(node.args[0]):
                    self.write('%s' % text(node.args[1]))
                else:
                    self.write('`%s <%s>`_' % (text(node.args[1]),
                                                text(node.args[0])))
            elif cmdname == 'seeurl':
                i = 1
                self.write('%s' % text(node.args[0]))
            elif cmdname == 'seetext':
                self.visit_node(node.args[0])
                return
            with self.indented():
                self.visit_node(node.args[i])
        elif cmdname in ('versionchanged', 'versionadded'):
            self.write('.. %s:: %s' % (cmdname, text(node.args[1])))
            if not empty(node.args[0]):
                with self.indented():
                    self.visit_node(node.args[0])
                    self.curpar.append('.')
            else:
                self.write()
        elif cmdname == 'deprecated':
            self.write_directive('deprecated', text(node.args[0]), node.args[1],
                                 spbelow=False)
        elif cmdname == 'localmoduletable':
            if self.toctree is not None:
                self.write_directive('toctree', '', spbelow=True, spabove=True)
                with self.indented():
                    for entry in self.toctree:
                        self.write(entry + '.rst')
            else:
                self.warnings.append('no toctree given, but \\localmoduletable in file')
        elif cmdname == 'verbatiminput':
            inclname = text(node.args[0])
            newname = includes_mapping.get(inclname, '../includes/' + inclname)
            if newname is None:
                self.write()
                self.write('.. XXX includefile %s' % inclname)
                return
            self.write()
            self.write('.. include:: %s' % newname)
            self.write('   :literal:')
            self.write()
        elif cmdname == 'input':
            inclname = text(node.args[0])
            newname = includes_mapping.get(inclname, None)
            if newname is None:
                self.write('X' 'XX: input{%s} :XX' 'X' % inclname)
                return
            self.write_directive('include', newname, spabove=True)
        elif cmdname == 'centerline':
            self.write_directive('centered', self.get_node_text(node.args[0]),
                                 spabove=True, spbelow=True)
        elif cmdname == 'XX' 'X':
            self.visit_wrapped(r'**\*\*** ', node.args[0], ' **\*\***')
        else:
            raise WriterError('no handler for %s command' % cmdname)

    def visit_DescLineCommandNode(self, node):
        # these have already been written as arguments of the corresponding
        # DescEnvironmentNode
        pass

    def visit_ParaSepNode(self, node):
        self.flush_par()

    def visit_VerbatimNode(self, node):
        if self.comments:
            # these interfer with the literal block
            self.flush_par()
        if self.curpar:
            last = self.curpar[-1].rstrip(' ')
            if last.endswith(':'):
                self.curpar[-1] = last + ':'
            else:
                self.curpar.append(' ::')
        else:
            self.curpar.append('::')
        self.flush_par()
        with self.indented():
            if isinstance(node.content, TextNode):
                # verbatim
                lines = textwrap.dedent(text(node.content).lstrip('\n')).split('\n')
                if not lines:
                    return
            else:
                # alltt, possibly with inline formats
                lines = self.get_node_text(self.get_textonly_node(
                    node.content, warn=0)).split('\n') + ['']
            # discard leading blank links
            while not lines[0].strip():
                del lines[0]
            for line in lines:
                self.write(line)

    note_re = re.compile('^\(\d\)$')

    def visit_TableNode(self, node):
        self.flush_par()
        lines = node.lines[:]
        lines.insert(0, node.headings)
        fmted_rows = []
        width = WIDTH - len(self.indentation)
        realwidths = [0] * node.numcols
        colwidth = (width / node.numcols) + 5
        # don't allow paragraphs in table cells for now
        with self.noflush:
            for line in lines:
                cells = []
                for i, cell in enumerate(line):
                    par = self.get_node_text(cell, wrap=True, width=colwidth)
                    if len(par) == 1 and self.note_re.match(par[0].strip()):
                        # special case: escape "(1)" to avoid enumeration
                        par[0] = '\\' + par[0]
                    maxwidth = max(map(len, par)) if par else 0
                    realwidths[i] = max(realwidths[i], maxwidth)
                    cells.append(par)
                fmted_rows.append(cells)

        def writesep(char='-'):
            out = ['+']
            for width in realwidths:
                out.append(char * (width+2))
                out.append('+')
            self.write(''.join(out))

        def writerow(row):
            lines = map(None, *row)
            for line in lines:
                out = ['|']
                for i, cell in enumerate(line):
                    if cell:
                        out.append(' ' + cell.ljust(realwidths[i]+1))
                    else:
                        out.append(' ' * (realwidths[i] + 2))
                    out.append('|')
                self.write(''.join(out))

        writesep('-')
        writerow(fmted_rows[0])
        writesep('=')
        for row in fmted_rows[1:]:
            writerow(row)
            writesep('-')
        self.write()

    def visit_ItemizeNode(self, node):
        self.flush_par()
        for title, content in node.items:
            if not empty(title):
                # do it like in a description list
                self.write(self.get_node_text(title))
                with self.indented():
                    self.visit_node(content)
            else:
                self.curpar.append('* ')
                with self.indented(2, firstline=False):
                    self.visit_node(content)

    def visit_EnumerateNode(self, node):
        self.flush_par()
        for title, content in node.items:
            assert empty(title)
            self.curpar.append('#. ')
            with self.indented(3, firstline=False):
                self.visit_node(content)

    def visit_DescriptionNode(self, node):
        self.flush_par()
        for title, content in node.items:
            self.write(self.get_node_text(title))
            with self.indented():
                self.visit_node(content)

    visit_DefinitionsNode = visit_DescriptionNode

    def visit_ProductionListNode(self, node):
        self.flush_par()
        arg = text(node.arg)
        self.write('.. productionlist::%s' % (' '+arg if arg else ''))
        with self.indented():
            for item in node.items:
                if not empty(item[0]):
                    lasttext = text(item[0])
                self.write('%s: %s' % (
                    text(item[0]).ljust(len(lasttext)),
                    self.get_node_text(item[1])))
        self.write()

    def visit_EmptyNode(self, node):
        pass

    def visit_TextNode(self, node):
        if self.noescape:
            self.curpar.append(node.text)
        else:
            self.curpar.append(fixup_text(node.text))

    visit_NbspNode = visit_TextNode
    visit_SimpleCmdNode = visit_TextNode

    def visit_BreakNode(self, node):
        # XXX: linebreaks in ReST?
        self.curpar.append(' --- ')

    def visit_IndexNode(self, node):
        if node.cmdname == 'withsubitem':
            self.indexsubitem = ' ' + text(node.indexargs[0])
            self.visit_node(node.indexargs[1])
            self.indexsubitem = ''
        else:
            self.indexentries.append((node.cmdname, node.indexargs,
                                      self.indexsubitem))

    # maps argumentless commands to text
    simplecmd_mapping = {
        'NULL': '*NULL*',
        'shortversion': '|version|',
        'version': '|release|',
        'today': '|today|',
    }

    # map LaTeX command names to roles: shorter names!
    role_mapping = {
        'cfunction': 'cfunc',
        'constant': 'const',
        'csimplemacro': 'cmacro',
        'exception': 'exc',
        'function': 'func',
        'grammartoken': 'token',
        'member': 'attr',
        'method': 'meth',
        'module': 'mod',
        'programopt': 'option',
        'filenq': 'file',
        # these mean: no change
        'cdata': '',
        'class': '',
        'command': '',
        'ctype': '',
        'data': '',           # NEW
        'dfn': '',
        'envvar': '',
        'file': '',
        'guilabel': '',
        'kbd': '',
        'keyword': '',
        'mailheader': '',
        'makevar': '',
        'menuselection': '',
        'mimetype': '',
        'newsgroup': '',
        'option': '',
        'pep': '',
        'program': '',
        'ref': '',
        'rfc': '',
    }

    # do not warn about nested inline markup in these roles
    role_no_warn = set((
        'cdata', 'cfunction', 'class', 'constant', 'csimplemacro', 'ctype',
        'data', 'exception', 'function', 'member', 'method', 'module',
    ))

    def visit_InlineNode(self, node):
        # XXX: no nested markup -- docutils doesn't support it
        cmdname = node.cmdname
        if not node.args:
            self.curpar.append(self.simplecmd_mapping[cmdname])
            return
        content = node.args[0]
        if cmdname in ('code', 'bfcode', 'samp', 'texttt', 'regexp'):
            self.visit_wrapped('``', self.get_textonly_node(content, 'code',
                                                            warn=1), '``', noescape=True)
        elif cmdname in ('emph', 'textit', 'var'):
            self.visit_wrapped('*', self.get_textonly_node(content, 'emph',
                                                           warn=1), '*')
        elif cmdname in ('strong', 'textbf'):
            self.visit_wrapped('**', self.get_textonly_node(content, 'strong',
                                                            warn=1), '**')
        elif cmdname in ('b', 'textrm', 'email'):
            self.visit_node(content)
        elif cmdname == 'token':
            # \token appears in productionlists only
            self.visit_wrapped('`', self.get_textonly_node(content, 'var',
                                                           warn=1), '`')
        elif cmdname == 'ref':
            self.curpar.append(':ref:`%s%s`' % (self.labelprefix,
                                                text(node.args[0]).lower()))
        elif cmdname == 'refmodule':
            self.visit_wrapped(':mod:`', node.args[1], '`', noescape=True)
        elif cmdname == 'optional':
            self.visit_wrapped('[', content, ']')
        elif cmdname == 'url':
            self.visit_node(content)
        elif cmdname == 'ulink':
            target = text(node.args[1])
            if target.startswith('..'):
                self.visit_wrapped('', content, ' (X' + 'XX reference: %s)' % target)
            elif not target.startswith(('http:', 'mailto:')):
                #self.warnings.append('Local \\ulink to %s, use \\ref instead' % target)
                self.visit_wrapped('', content, ' (X' 'XX reference: %s)' % target)
            else:
                self.visit_wrapped('`', self.get_textonly_node(content, 'ulink', warn=1),
                                   ' <%s>`_' % target)
        elif cmdname == 'citetitle':
            target = text(content)
            if not target:
                self.visit_node(node.args[1])
            elif target.startswith('..'):
                self.visit_wrapped('', node.args[1],
                                   ' (X' + 'XX reference: %s)' % target)
            else:
                self.visit_wrapped('`', self.get_textonly_node(node.args[1],
                                                               'citetitle', warn=1),
                                   ' <%s>`_' % target)
        elif cmdname == 'character':
            # ``'a'`` is not longer than :character:`a`
            self.visit_wrapped("``'", content, "'``", noescape=True)
        elif cmdname == 'manpage':
            self.curpar.append(':manpage:`')
            self.visit_node(self.get_textonly_node(content, warn=0))
            self.visit_wrapped('(', self.get_textonly_node(node.args[1], warn=0), ')')
            self.curpar.append('`')
        elif cmdname == 'footnote':
            self.curpar.append(' [#]_')
            self.footnotes.append(content)
        elif cmdname == 'frac':
            self.visit_wrapped('(', node.args[0], ')/')
            self.visit_wrapped('(', node.args[1], ')')
        elif cmdname == 'longprogramopt':
            self.visit_wrapped(':option:`--', content, '`')
        elif cmdname == 'filevar':
            self.visit_wrapped(':file:`{', content, '}`')
        elif cmdname == '':
            self.visit_node(content)
        # stray commands from distutils
        elif cmdname in ('argument name', 'value', 'attribute', 'option name'):
            self.visit_wrapped('*', content, '*')
        else:
            self.visit_wrapped(':%s:`' % (self.role_mapping[cmdname] or cmdname),
                               self.get_textonly_node(
                content, cmdname, warn=(cmdname not in self.role_no_warn)), '`')
