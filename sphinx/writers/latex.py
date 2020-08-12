"""
    sphinx.writers.latex
    ~~~~~~~~~~~~~~~~~~~~

    Custom docutils writer for LaTeX.

    Much of this code is adapted from Dave Kuhlman's "docpy" writer from his
    docutils sandbox.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import warnings
from collections import defaultdict
from os import path
from typing import Any, Dict, Iterable, Iterator, List, Tuple, Set, Union
from typing import cast

from docutils import nodes, writers
from docutils.nodes import Element, Node, Text

from sphinx import addnodes
from sphinx import highlighting
from sphinx.deprecation import (
    RemovedInSphinx40Warning, RemovedInSphinx50Warning, deprecated_alias
)
from sphinx.domains import IndexEntry
from sphinx.domains.std import StandardDomain
from sphinx.errors import SphinxError
from sphinx.locale import admonitionlabels, _, __
from sphinx.util import split_into, logging, texescape
from sphinx.util.docutils import SphinxTranslator
from sphinx.util.nodes import clean_astext, get_prev_node
from sphinx.util.template import LaTeXRenderer
from sphinx.util.texescape import tex_replace_map

try:
    from docutils.utils.roman import toRoman
except ImportError:
    # In Debain/Ubuntu, roman package is provided as roman, not as docutils.utils.roman
    from roman import toRoman  # type: ignore

if False:
    # For type annotation
    from sphinx.builders.latex import LaTeXBuilder
    from sphinx.builders.latex.theming import Theme


logger = logging.getLogger(__name__)

MAX_CITATION_LABEL_LENGTH = 8
LATEXSECTIONNAMES = ["part", "chapter", "section", "subsection",
                     "subsubsection", "paragraph", "subparagraph"]
ENUMERATE_LIST_STYLE = defaultdict(lambda: r'\arabic',
                                   {
                                       'arabic': r'\arabic',
                                       'loweralpha': r'\alph',
                                       'upperalpha': r'\Alph',
                                       'lowerroman': r'\roman',
                                       'upperroman': r'\Roman',
                                   })

EXTRA_RE = re.compile(r'^(.*\S)\s+\(([^()]*)\)\s*$')


class collected_footnote(nodes.footnote):
    """Footnotes that are collected are assigned this class."""


class UnsupportedError(SphinxError):
    category = 'Markup is unsupported in LaTeX'


class LaTeXWriter(writers.Writer):

    supported = ('sphinxlatex',)

    settings_spec = ('LaTeX writer options', '', (
        ('Document name', ['--docname'], {'default': ''}),
        ('Document class', ['--docclass'], {'default': 'manual'}),
        ('Author', ['--author'], {'default': ''}),
    ))
    settings_defaults = {}  # type: Dict

    output = None

    def __init__(self, builder: "LaTeXBuilder") -> None:
        super().__init__()
        self.builder = builder
        self.theme = None  # type: Theme

    def translate(self) -> None:
        try:
            visitor = self.builder.create_translator(self.document, self.builder, self.theme)
        except TypeError:
            warnings.warn('LaTeXTranslator now takes 3rd argument; "theme".',
                          RemovedInSphinx50Warning, stacklevel=2)
            visitor = self.builder.create_translator(self.document, self.builder)

        self.document.walkabout(visitor)
        self.output = cast(LaTeXTranslator, visitor).astext()


# Helper classes

class Table:
    """A table data"""

    def __init__(self, node: Element) -> None:
        self.header = []                        # type: List[str]
        self.body = []                          # type: List[str]
        self.align = node.get('align')
        self.colcount = 0
        self.colspec = None                     # type: str
        self.colwidths = []                     # type: List[int]
        self.has_problematic = False
        self.has_oldproblematic = False
        self.has_verbatim = False
        self.caption = None                     # type: List[str]
        self.stubs = []                         # type: List[int]

        # current position
        self.col = 0
        self.row = 0

        # for internal use
        self.classes = node.get('classes', [])  # type: List[str]
        self.cells = defaultdict(int)           # type: Dict[Tuple[int, int], int]
                                                # it maps table location to cell_id
                                                # (cell = rectangular area)
        self.cell_id = 0                        # last assigned cell_id

    def is_longtable(self) -> bool:
        """True if and only if table uses longtable environment."""
        return self.row > 30 or 'longtable' in self.classes

    def get_table_type(self) -> str:
        """Returns the LaTeX environment name for the table.

        The class currently supports:

        * longtable
        * tabular
        * tabulary
        """
        if self.is_longtable():
            return 'longtable'
        elif self.has_verbatim:
            return 'tabular'
        elif self.colspec:
            return 'tabulary'
        elif self.has_problematic or (self.colwidths and 'colwidths-given' in self.classes):
            return 'tabular'
        else:
            return 'tabulary'

    def get_colspec(self) -> str:
        """Returns a column spec of table.

        This is what LaTeX calls the 'preamble argument' of the used table environment.

        .. note:: the ``\\X`` and ``T`` column type specifiers are defined in ``sphinx.sty``.
        """
        if self.colspec:
            return self.colspec
        elif self.colwidths and 'colwidths-given' in self.classes:
            total = sum(self.colwidths)
            colspecs = ['\\X{%d}{%d}' % (width, total) for width in self.colwidths]
            return '{|%s|}\n' % '|'.join(colspecs)
        elif self.has_problematic:
            return '{|*{%d}{\\X{1}{%d}|}}\n' % (self.colcount, self.colcount)
        elif self.get_table_type() == 'tabulary':
            # sphinx.sty sets T to be J by default.
            return '{|' + ('T|' * self.colcount) + '}\n'
        elif self.has_oldproblematic:
            return '{|*{%d}{\\X{1}{%d}|}}\n' % (self.colcount, self.colcount)
        else:
            return '{|' + ('l|' * self.colcount) + '}\n'

    def add_cell(self, height: int, width: int) -> None:
        """Adds a new cell to a table.

        It will be located at current position: (``self.row``, ``self.col``).
        """
        self.cell_id += 1
        for col in range(width):
            for row in range(height):
                assert self.cells[(self.row + row, self.col + col)] == 0
                self.cells[(self.row + row, self.col + col)] = self.cell_id

    def cell(self, row: int = None, col: int = None) -> "TableCell":
        """Returns a cell object (i.e. rectangular area) containing given position.

        If no option arguments: ``row`` or ``col`` are given, the current position;
        ``self.row`` and ``self.col`` are used to get a cell object by default.
        """
        try:
            if row is None:
                row = self.row
            if col is None:
                col = self.col
            return TableCell(self, row, col)
        except IndexError:
            return None


class TableCell:
    """A cell data of tables."""

    def __init__(self, table: Table, row: int, col: int) -> None:
        if table.cells[(row, col)] == 0:
            raise IndexError

        self.table = table
        self.cell_id = table.cells[(row, col)]
        self.row = row
        self.col = col

        # adjust position for multirow/multicol cell
        while table.cells[(self.row - 1, self.col)] == self.cell_id:
            self.row -= 1
        while table.cells[(self.row, self.col - 1)] == self.cell_id:
            self.col -= 1

    @property
    def width(self) -> int:
        """Returns the cell width."""
        width = 0
        while self.table.cells[(self.row, self.col + width)] == self.cell_id:
            width += 1
        return width

    @property
    def height(self) -> int:
        """Returns the cell height."""
        height = 0
        while self.table.cells[(self.row + height, self.col)] == self.cell_id:
            height += 1
        return height


def escape_abbr(text: str) -> str:
    """Adjust spacing after abbreviations."""
    return re.sub(r'\.(?=\s|$)', r'.\@', text)


def rstdim_to_latexdim(width_str: str, scale: int = 100) -> str:
    """Convert `width_str` with rst length to LaTeX length."""
    match = re.match(r'^(\d*\.?\d*)\s*(\S*)$', width_str)
    if not match:
        raise ValueError
    res = width_str
    amount, unit = match.groups()[:2]
    if scale == 100:
        float(amount)  # validate amount is float
        if unit in ('', "px"):
            res = "%s\\sphinxpxdimen" % amount
        elif unit == 'pt':
            res = '%sbp' % amount  # convert to 'bp'
        elif unit == "%":
            res = "%.3f\\linewidth" % (float(amount) / 100.0)
    else:
        amount_float = float(amount) * scale / 100.0
        if unit in ('', "px"):
            res = "%.5f\\sphinxpxdimen" % amount_float
        elif unit == 'pt':
            res = '%.5fbp' % amount_float
        elif unit == "%":
            res = "%.5f\\linewidth" % (amount_float / 100.0)
        else:
            res = "%.5f%s" % (amount_float, unit)
    return res


class LaTeXTranslator(SphinxTranslator):
    builder = None  # type: LaTeXBuilder

    secnumdepth = 2  # legacy sphinxhowto.cls uses this, whereas article.cls
    # default is originally 3. For book/report, 2 is already LaTeX default.
    ignore_missing_images = False

    # sphinx specific document classes
    docclasses = ('howto', 'manual')

    def __init__(self, document: nodes.document, builder: "LaTeXBuilder",
                 theme: "Theme" = None) -> None:
        super().__init__(document, builder)
        self.body = []  # type: List[str]
        self.theme = theme

        if theme is None:
            warnings.warn('LaTeXTranslator now takes 3rd argument; "theme".',
                          RemovedInSphinx50Warning, stacklevel=2)

        # flags
        self.in_title = 0
        self.in_production_list = 0
        self.in_footnote = 0
        self.in_caption = 0
        self.in_term = 0
        self.needs_linetrimming = 0
        self.in_minipage = 0
        self.no_latex_floats = 0
        self.first_document = 1
        self.this_is_the_title = 1
        self.literal_whitespace = 0
        self.in_parsed_literal = 0
        self.compact_list = 0
        self.first_param = 0

        sphinxpkgoptions = []

        # sort out some elements
        self.elements = self.builder.context.copy()

        # initial section names
        self.sectionnames = LATEXSECTIONNAMES[:]

        if self.theme:
            # new style: control sectioning via theme's setting
            #
            # .. note:: template variables(elements) are already assigned in builder
            docclass = self.theme.docclass
            if self.theme.toplevel_sectioning == 'section':
                self.sectionnames.remove('chapter')
        else:
            # old style: sectioning control is hard-coded
            # but some have other interface in config file
            self.elements['wrapperclass'] = self.format_docclass(self.settings.docclass)

            # we assume LaTeX class provides \chapter command except in case
            # of non-Japanese 'howto' case
            if document.get('docclass') == 'howto':
                docclass = self.config.latex_docclass.get('howto', 'article')
                if docclass[0] == 'j':  # Japanese class...
                    pass
                else:
                    self.sectionnames.remove('chapter')
            else:
                docclass = self.config.latex_docclass.get('manual', 'report')
            self.elements['docclass'] = docclass

        # determine top section level
        self.top_sectionlevel = 1
        if self.config.latex_toplevel_sectioning:
            try:
                self.top_sectionlevel = \
                    self.sectionnames.index(self.config.latex_toplevel_sectioning)
            except ValueError:
                logger.warning(__('unknown %r toplevel_sectioning for class %r') %
                               (self.config.latex_toplevel_sectioning, docclass))

        if self.config.numfig:
            self.numfig_secnum_depth = self.config.numfig_secnum_depth
            if self.numfig_secnum_depth > 0:  # default is 1
                # numfig_secnum_depth as passed to sphinx.sty indices same names as in
                # LATEXSECTIONNAMES but with -1 for part, 0 for chapter, 1 for section...
                if len(self.sectionnames) < len(LATEXSECTIONNAMES) and \
                   self.top_sectionlevel > 0:
                    self.numfig_secnum_depth += self.top_sectionlevel
                else:
                    self.numfig_secnum_depth += self.top_sectionlevel - 1
                # this (minus one) will serve as minimum to LaTeX's secnumdepth
                self.numfig_secnum_depth = min(self.numfig_secnum_depth,
                                               len(LATEXSECTIONNAMES) - 1)
                # if passed key value is < 1 LaTeX will act as if 0; see sphinx.sty
                sphinxpkgoptions.append('numfigreset=%s' % self.numfig_secnum_depth)
            else:
                sphinxpkgoptions.append('nonumfigreset')

        if self.config.numfig and self.config.math_numfig:
            sphinxpkgoptions.append('mathnumfig')

        if (self.config.language not in {None, 'en', 'ja'} and
                'fncychap' not in self.config.latex_elements):
            # use Sonny style if any language specified (except English)
            self.elements['fncychap'] = ('\\usepackage[Sonny]{fncychap}\n'
                                         '\\ChNameVar{\\Large\\normalfont'
                                         '\\sffamily}\n\\ChTitleVar{\\Large'
                                         '\\normalfont\\sffamily}')

        self.babel = self.builder.babel
        if self.config.language and not self.babel.is_supported_language():
            # emit warning if specified language is invalid
            # (only emitting, nothing changed to processing)
            logger.warning(__('no Babel option known for language %r'),
                           self.config.language)

        minsecnumdepth = self.secnumdepth  # 2 from legacy sphinx manual/howto
        if self.document.get('tocdepth'):
            # reduce tocdepth if `part` or `chapter` is used for top_sectionlevel
            #   tocdepth = -1: show only parts
            #   tocdepth =  0: show parts and chapters
            #   tocdepth =  1: show parts, chapters and sections
            #   tocdepth =  2: show parts, chapters, sections and subsections
            #   ...
            tocdepth = self.document.get('tocdepth', 999) + self.top_sectionlevel - 2
            if len(self.sectionnames) < len(LATEXSECTIONNAMES) and \
               self.top_sectionlevel > 0:
                tocdepth += 1  # because top_sectionlevel is shifted by -1
            if tocdepth > len(LATEXSECTIONNAMES) - 2:  # default is 5 <-> subparagraph
                logger.warning(__('too large :maxdepth:, ignored.'))
                tocdepth = len(LATEXSECTIONNAMES) - 2

            self.elements['tocdepth'] = '\\setcounter{tocdepth}{%d}' % tocdepth
            minsecnumdepth = max(minsecnumdepth, tocdepth)

        if self.config.numfig and (self.config.numfig_secnum_depth > 0):
            minsecnumdepth = max(minsecnumdepth, self.numfig_secnum_depth - 1)

        if minsecnumdepth > self.secnumdepth:
            self.elements['secnumdepth'] = '\\setcounter{secnumdepth}{%d}' %\
                                           minsecnumdepth

        contentsname = document.get('contentsname')
        if contentsname:
            self.elements['contentsname'] = self.babel_renewcommand('\\contentsname',
                                                                    contentsname)

        if self.elements['maxlistdepth']:
            sphinxpkgoptions.append('maxlistdepth=%s' % self.elements['maxlistdepth'])
        if sphinxpkgoptions:
            self.elements['sphinxpkgoptions'] = '[,%s]' % ','.join(sphinxpkgoptions)
        if self.elements['sphinxsetup']:
            self.elements['sphinxsetup'] = ('\\sphinxsetup{%s}' %
                                            self.elements['sphinxsetup'])
        if self.elements['extraclassoptions']:
            self.elements['classoptions'] += ',' + \
                                             self.elements['extraclassoptions']

        self.highlighter = highlighting.PygmentsBridge('latex', self.config.pygments_style,
                                                       latex_engine=self.config.latex_engine)
        self.context = []                   # type: List[Any]
        self.descstack = []                 # type: List[str]
        self.tables = []                    # type: List[Table]
        self.next_table_colspec = None      # type: str
        self.bodystack = []                 # type: List[List[str]]
        self.footnote_restricted = None     # type: nodes.Element
        self.pending_footnotes = []         # type: List[nodes.footnote_reference]
        self.curfilestack = []              # type: List[str]
        self.handled_abbrs = set()          # type: Set[str]

    def pushbody(self, newbody: List[str]) -> None:
        self.bodystack.append(self.body)
        self.body = newbody

    def popbody(self) -> List[str]:
        body = self.body
        self.body = self.bodystack.pop()
        return body

    def format_docclass(self, docclass: str) -> str:
        """ prepends prefix to sphinx document classes
        """
        warnings.warn('LaTeXWriter.format_docclass() is deprecated.',
                      RemovedInSphinx50Warning, stacklevel=2)
        if docclass in self.docclasses:
            docclass = 'sphinx' + docclass
        return docclass

    def astext(self) -> str:
        self.elements.update({
            'body': ''.join(self.body),
            'indices': self.generate_indices()
        })
        return self.render('latex.tex_t', self.elements)

    def hypertarget(self, id: str, withdoc: bool = True, anchor: bool = True) -> str:
        if withdoc:
            id = self.curfilestack[-1] + ':' + id
        return ('\\phantomsection' if anchor else '') + \
            '\\label{%s}' % self.idescape(id)

    def hypertarget_to(self, node: Element, anchor: bool = False) -> str:
        labels = ''.join(self.hypertarget(node_id, anchor=False) for node_id in node['ids'])
        if anchor:
            return r'\phantomsection' + labels
        else:
            return labels

    def hyperlink(self, id: str) -> str:
        return '{\\hyperref[%s]{' % self.idescape(id)

    def hyperpageref(self, id: str) -> str:
        return '\\autopageref*{%s}' % self.idescape(id)

    def escape(self, s: str) -> str:
        return texescape.escape(s, self.config.latex_engine)

    def idescape(self, id: str) -> str:
        return '\\detokenize{%s}' % str(id).translate(tex_replace_map).\
            encode('ascii', 'backslashreplace').decode('ascii').\
            replace('\\', '_')

    def babel_renewcommand(self, command: str, definition: str) -> str:
        if self.elements['multilingual']:
            prefix = '\\addto\\captions%s{' % self.babel.get_language()
            suffix = '}'
        else:  # babel is disabled (mainly for Japanese environment)
            prefix = ''
            suffix = ''

        return ('%s\\renewcommand{%s}{%s}%s\n' % (prefix, command, definition, suffix))

    def generate_indices(self) -> str:
        def generate(content: List[Tuple[str, List[IndexEntry]]], collapsed: bool) -> None:
            ret.append('\\begin{sphinxtheindex}\n')
            ret.append('\\let\\bigletter\\sphinxstyleindexlettergroup\n')
            for i, (letter, entries) in enumerate(content):
                if i > 0:
                    ret.append('\\indexspace\n')
                ret.append('\\bigletter{%s}\n' % self.escape(letter))
                for entry in entries:
                    if not entry[3]:
                        continue
                    ret.append('\\item\\relax\\sphinxstyleindexentry{%s}' %
                               self.encode(entry[0]))
                    if entry[4]:
                        # add "extra" info
                        ret.append('\\sphinxstyleindexextra{%s}' % self.encode(entry[4]))
                    ret.append('\\sphinxstyleindexpageref{%s:%s}\n' %
                               (entry[2], self.idescape(entry[3])))
            ret.append('\\end{sphinxtheindex}\n')

        ret = []
        # latex_domain_indices can be False/True or a list of index names
        indices_config = self.builder.config.latex_domain_indices
        if indices_config:
            for domain in self.builder.env.domains.values():
                for indexcls in domain.indices:
                    indexname = '%s-%s' % (domain.name, indexcls.name)
                    if isinstance(indices_config, list):
                        if indexname not in indices_config:
                            continue
                    content, collapsed = indexcls(domain).generate(
                        self.builder.docnames)
                    if not content:
                        continue
                    ret.append('\\renewcommand{\\indexname}{%s}\n' %
                               indexcls.localname)
                    generate(content, collapsed)

        return ''.join(ret)

    def render(self, template_name: str, variables: Dict) -> str:
        renderer = LaTeXRenderer(latex_engine=self.config.latex_engine)
        for template_dir in self.builder.config.templates_path:
            template = path.join(self.builder.confdir, template_dir,
                                 template_name)
            if path.exists(template):
                return renderer.render(template, variables)

        return renderer.render(template_name, variables)

    @property
    def table(self) -> Table:
        """Get current table."""
        if self.tables:
            return self.tables[-1]
        else:
            return None

    def visit_document(self, node: Element) -> None:
        self.curfilestack.append(node.get('docname', ''))
        if self.first_document == 1:
            # the first document is all the regular content ...
            self.first_document = 0
        elif self.first_document == 0:
            # ... and all others are the appendices
            self.body.append('\n\\appendix\n')
            self.first_document = -1
        if 'docname' in node:
            self.body.append(self.hypertarget(':doc'))
        # "- 1" because the level is increased before the title is visited
        self.sectionlevel = self.top_sectionlevel - 1

    def depart_document(self, node: Element) -> None:
        pass

    def visit_start_of_file(self, node: Element) -> None:
        self.curfilestack.append(node['docname'])

    def depart_start_of_file(self, node: Element) -> None:
        self.curfilestack.pop()

    def visit_section(self, node: Element) -> None:
        if not self.this_is_the_title:
            self.sectionlevel += 1
        self.body.append('\n\n')

    def depart_section(self, node: Element) -> None:
        self.sectionlevel = max(self.sectionlevel - 1,
                                self.top_sectionlevel - 1)

    def visit_problematic(self, node: Element) -> None:
        self.body.append(r'{\color{red}\bfseries{}')

    def depart_problematic(self, node: Element) -> None:
        self.body.append('}')

    def visit_topic(self, node: Element) -> None:
        self.in_minipage = 1
        self.body.append('\n\\begin{sphinxShadowBox}\n')

    def depart_topic(self, node: Element) -> None:
        self.in_minipage = 0
        self.body.append('\\end{sphinxShadowBox}\n')
    visit_sidebar = visit_topic
    depart_sidebar = depart_topic

    def visit_glossary(self, node: Element) -> None:
        pass

    def depart_glossary(self, node: Element) -> None:
        pass

    def visit_productionlist(self, node: Element) -> None:
        self.body.append('\n\n\\begin{productionlist}\n')
        self.in_production_list = 1

    def depart_productionlist(self, node: Element) -> None:
        self.body.append('\\end{productionlist}\n\n')
        self.in_production_list = 0

    def visit_production(self, node: Element) -> None:
        if node['tokenname']:
            tn = node['tokenname']
            self.body.append(self.hypertarget('grammar-token-' + tn))
            self.body.append('\\production{%s}{' % self.encode(tn))
        else:
            self.body.append('\\productioncont{')

    def depart_production(self, node: Element) -> None:
        self.body.append('}\n')

    def visit_transition(self, node: Element) -> None:
        self.body.append(self.elements['transition'])

    def depart_transition(self, node: Element) -> None:
        pass

    def visit_title(self, node: Element) -> None:
        parent = node.parent
        if isinstance(parent, addnodes.seealso):
            # the environment already handles this
            raise nodes.SkipNode
        elif isinstance(parent, nodes.section):
            if self.this_is_the_title:
                if len(node.children) != 1 and not isinstance(node.children[0],
                                                              nodes.Text):
                    logger.warning(__('document title is not a single Text node'),
                                   location=node)
                if not self.elements['title']:
                    # text needs to be escaped since it is inserted into
                    # the output literally
                    self.elements['title'] = self.escape(node.astext())
                self.this_is_the_title = 0
                raise nodes.SkipNode
            else:
                short = ''
                if node.traverse(nodes.image):
                    short = ('[%s]' % self.escape(' '.join(clean_astext(node).split())))

                try:
                    self.body.append(r'\%s%s{' % (self.sectionnames[self.sectionlevel], short))
                except IndexError:
                    # just use "subparagraph", it's not numbered anyway
                    self.body.append(r'\%s%s{' % (self.sectionnames[-1], short))
                self.context.append('}\n' + self.hypertarget_to(node.parent))
        elif isinstance(parent, nodes.topic):
            self.body.append(r'\sphinxstyletopictitle{')
            self.context.append('}\n')
        elif isinstance(parent, nodes.sidebar):
            self.body.append(r'\sphinxstylesidebartitle{')
            self.context.append('}\n')
        elif isinstance(parent, nodes.Admonition):
            self.body.append('{')
            self.context.append('}\n')
        elif isinstance(parent, nodes.table):
            # Redirect body output until title is finished.
            self.pushbody([])
        else:
            logger.warning(__('encountered title node not in section, topic, table, '
                              'admonition or sidebar'),
                           location=node)
            self.body.append('\\sphinxstyleothertitle{')
            self.context.append('}\n')
        self.in_title = 1

    def depart_title(self, node: Element) -> None:
        self.in_title = 0
        if isinstance(node.parent, nodes.table):
            self.table.caption = self.popbody()
        else:
            self.body.append(self.context.pop())

    def visit_subtitle(self, node: Element) -> None:
        if isinstance(node.parent, nodes.sidebar):
            self.body.append('\\sphinxstylesidebarsubtitle{')
            self.context.append('}\n')
        else:
            self.context.append('')

    def depart_subtitle(self, node: Element) -> None:
        self.body.append(self.context.pop())

    def visit_desc(self, node: Element) -> None:
        self.body.append('\n\n\\begin{fulllineitems}\n')
        if self.table:
            self.table.has_problematic = True

    def depart_desc(self, node: Element) -> None:
        self.body.append('\n\\end{fulllineitems}\n\n')

    def _visit_signature_line(self, node: Element) -> None:
        for child in node:
            if isinstance(child, addnodes.desc_parameterlist):
                self.body.append(r'\pysiglinewithargsret{')
                break
        else:
            self.body.append(r'\pysigline{')

    def _depart_signature_line(self, node: Element) -> None:
        self.body.append('}')

    def visit_desc_signature(self, node: Element) -> None:
        if node.parent['objtype'] != 'describe' and node['ids']:
            hyper = self.hypertarget(node['ids'][0])
        else:
            hyper = ''
        self.body.append(hyper)
        if not node.get('is_multiline'):
            self._visit_signature_line(node)
        else:
            self.body.append('%\n\\pysigstartmultiline\n')

    def depart_desc_signature(self, node: Element) -> None:
        if not node.get('is_multiline'):
            self._depart_signature_line(node)
        else:
            self.body.append('%\n\\pysigstopmultiline')

    def visit_desc_signature_line(self, node: Element) -> None:
        self._visit_signature_line(node)

    def depart_desc_signature_line(self, node: Element) -> None:
        self._depart_signature_line(node)

    def visit_desc_addname(self, node: Element) -> None:
        self.body.append(r'\sphinxcode{\sphinxupquote{')
        self.literal_whitespace += 1

    def depart_desc_addname(self, node: Element) -> None:
        self.body.append('}}')
        self.literal_whitespace -= 1

    def visit_desc_type(self, node: Element) -> None:
        pass

    def depart_desc_type(self, node: Element) -> None:
        pass

    def visit_desc_returns(self, node: Element) -> None:
        self.body.append(r'{ $\rightarrow$ ')

    def depart_desc_returns(self, node: Element) -> None:
        self.body.append(r'}')

    def visit_desc_name(self, node: Element) -> None:
        self.body.append(r'\sphinxbfcode{\sphinxupquote{')
        self.literal_whitespace += 1

    def depart_desc_name(self, node: Element) -> None:
        self.body.append('}}')
        self.literal_whitespace -= 1

    def visit_desc_parameterlist(self, node: Element) -> None:
        # close name, open parameterlist
        self.body.append('}{')
        self.first_param = 1

    def depart_desc_parameterlist(self, node: Element) -> None:
        # close parameterlist, open return annotation
        self.body.append('}{')

    def visit_desc_parameter(self, node: Element) -> None:
        if not self.first_param:
            self.body.append(', ')
        else:
            self.first_param = 0
        if not node.hasattr('noemph'):
            self.body.append(r'\emph{')

    def depart_desc_parameter(self, node: Element) -> None:
        if not node.hasattr('noemph'):
            self.body.append('}')

    def visit_desc_optional(self, node: Element) -> None:
        self.body.append(r'\sphinxoptional{')

    def depart_desc_optional(self, node: Element) -> None:
        self.body.append('}')

    def visit_desc_annotation(self, node: Element) -> None:
        self.body.append(r'\sphinxbfcode{\sphinxupquote{')

    def depart_desc_annotation(self, node: Element) -> None:
        self.body.append('}}')

    def visit_desc_content(self, node: Element) -> None:
        if node.children and not isinstance(node.children[0], nodes.paragraph):
            # avoid empty desc environment which causes a formatting bug
            self.body.append('~')

    def depart_desc_content(self, node: Element) -> None:
        pass

    def visit_seealso(self, node: Element) -> None:
        self.body.append('\n\n\\sphinxstrong{%s:}\n\n' % admonitionlabels['seealso'])

    def depart_seealso(self, node: Element) -> None:
        self.body.append("\n\n")

    def visit_rubric(self, node: Element) -> None:
        if len(node) == 1 and node.astext() in ('Footnotes', _('Footnotes')):
            raise nodes.SkipNode
        self.body.append('\\subsubsection*{')
        self.context.append('}\n')
        self.in_title = 1

    def depart_rubric(self, node: Element) -> None:
        self.in_title = 0
        self.body.append(self.context.pop())

    def visit_footnote(self, node: Element) -> None:
        self.in_footnote += 1
        label = cast(nodes.label, node[0])
        if self.in_parsed_literal:
            self.body.append('\\begin{footnote}[%s]' % label.astext())
        else:
            self.body.append('%%\n\\begin{footnote}[%s]' % label.astext())
        self.body.append('\\sphinxAtStartFootnote\n')

    def depart_footnote(self, node: Element) -> None:
        if self.in_parsed_literal:
            self.body.append('\\end{footnote}')
        else:
            self.body.append('%\n\\end{footnote}')
        self.in_footnote -= 1

    def visit_label(self, node: Element) -> None:
        raise nodes.SkipNode

    def visit_tabular_col_spec(self, node: Element) -> None:
        self.next_table_colspec = node['spec']
        raise nodes.SkipNode

    def visit_table(self, node: Element) -> None:
        if len(self.tables) == 1:
            if self.table.get_table_type() == 'longtable':
                raise UnsupportedError(
                    '%s:%s: longtable does not support nesting a table.' %
                    (self.curfilestack[-1], node.line or ''))
            else:
                # change type of parent table to tabular
                # see https://groups.google.com/d/msg/sphinx-users/7m3NeOBixeo/9LKP2B4WBQAJ
                self.table.has_problematic = True
        elif len(self.tables) > 2:
            raise UnsupportedError(
                '%s:%s: deeply nested tables are not implemented.' %
                (self.curfilestack[-1], node.line or ''))

        self.tables.append(Table(node))
        if self.next_table_colspec:
            self.table.colspec = '{%s}\n' % self.next_table_colspec
            if 'colwidths-given' in node.get('classes', []):
                logger.info(__('both tabularcolumns and :widths: option are given. '
                               ':widths: is ignored.'), location=node)
        self.next_table_colspec = None

    def depart_table(self, node: Element) -> None:
        labels = self.hypertarget_to(node)
        table_type = self.table.get_table_type()
        table = self.render(table_type + '.tex_t',
                            dict(table=self.table, labels=labels))
        self.body.append("\n\n")
        self.body.append(table)
        self.body.append("\n")

        self.tables.pop()

    def visit_colspec(self, node: Element) -> None:
        self.table.colcount += 1
        if 'colwidth' in node:
            self.table.colwidths.append(node['colwidth'])
        if 'stub' in node:
            self.table.stubs.append(self.table.colcount - 1)

    def depart_colspec(self, node: Element) -> None:
        pass

    def visit_tgroup(self, node: Element) -> None:
        pass

    def depart_tgroup(self, node: Element) -> None:
        pass

    def visit_thead(self, node: Element) -> None:
        # Redirect head output until header is finished.
        self.pushbody(self.table.header)

    def depart_thead(self, node: Element) -> None:
        self.popbody()

    def visit_tbody(self, node: Element) -> None:
        # Redirect body output until table is finished.
        self.pushbody(self.table.body)

    def depart_tbody(self, node: Element) -> None:
        self.popbody()

    def visit_row(self, node: Element) -> None:
        self.table.col = 0

        # fill columns if the row starts with the bottom of multirow cell
        while True:
            cell = self.table.cell(self.table.row, self.table.col)
            if cell is None:  # not a bottom of multirow cell
                break
            else:  # a bottom of multirow cell
                self.table.col += cell.width
                if cell.col:
                    self.body.append('&')
                if cell.width == 1:
                    # insert suitable strut for equalizing row heights in given multirow
                    self.body.append('\\sphinxtablestrut{%d}' % cell.cell_id)
                else:  # use \multicolumn for wide multirow cell
                    self.body.append('\\multicolumn{%d}{|l|}'
                                     '{\\sphinxtablestrut{%d}}' %
                                     (cell.width, cell.cell_id))

    def depart_row(self, node: Element) -> None:
        self.body.append('\\\\\n')
        cells = [self.table.cell(self.table.row, i) for i in range(self.table.colcount)]
        underlined = [cell.row + cell.height == self.table.row + 1 for cell in cells]
        if all(underlined):
            self.body.append('\\hline')
        else:
            i = 0
            underlined.extend([False])  # sentinel
            while i < len(underlined):
                if underlined[i] is True:
                    j = underlined[i:].index(False)
                    self.body.append('\\cline{%d-%d}' % (i + 1, i + j))
                    i += j
                i += 1
        self.table.row += 1

    def visit_entry(self, node: Element) -> None:
        if self.table.col > 0:
            self.body.append('&')
        self.table.add_cell(node.get('morerows', 0) + 1, node.get('morecols', 0) + 1)
        cell = self.table.cell()
        context = ''
        if cell.width > 1:
            if self.builder.config.latex_use_latex_multicolumn:
                if self.table.col == 0:
                    self.body.append('\\multicolumn{%d}{|l|}{%%\n' % cell.width)
                else:
                    self.body.append('\\multicolumn{%d}{l|}{%%\n' % cell.width)
                context = '}%\n'
            else:
                self.body.append('\\sphinxstartmulticolumn{%d}%%\n' % cell.width)
                context = '\\sphinxstopmulticolumn\n'
        if cell.height > 1:
            # \sphinxmultirow 2nd arg "cell_id" will serve as id for LaTeX macros as well
            self.body.append('\\sphinxmultirow{%d}{%d}{%%\n' % (cell.height, cell.cell_id))
            context = '}%\n' + context
        if cell.width > 1 or cell.height > 1:
            self.body.append('\\begin{varwidth}[t]{\\sphinxcolwidth{%d}{%d}}\n'
                             % (cell.width, self.table.colcount))
            context = ('\\par\n\\vskip-\\baselineskip'
                       '\\vbox{\\hbox{\\strut}}\\end{varwidth}%\n') + context
            self.needs_linetrimming = 1
        if len(node.traverse(nodes.paragraph)) >= 2:
            self.table.has_oldproblematic = True
        if isinstance(node.parent.parent, nodes.thead) or (cell.col in self.table.stubs):
            if len(node) == 1 and isinstance(node[0], nodes.paragraph) and node.astext() == '':
                pass
            else:
                self.body.append('\\sphinxstyletheadfamily ')
        if self.needs_linetrimming:
            self.pushbody([])
        self.context.append(context)

    def depart_entry(self, node: Element) -> None:
        if self.needs_linetrimming:
            self.needs_linetrimming = 0
            body = self.popbody()

            # Remove empty lines from top of merged cell
            while body and body[0] == "\n":
                body.pop(0)
            self.body.extend(body)

        self.body.append(self.context.pop())

        cell = self.table.cell()
        self.table.col += cell.width

        # fill columns if next ones are a bottom of wide-multirow cell
        while True:
            nextcell = self.table.cell()
            if nextcell is None:  # not a bottom of multirow cell
                break
            else:  # a bottom part of multirow cell
                self.table.col += nextcell.width
                self.body.append('&')
                if nextcell.width == 1:
                    # insert suitable strut for equalizing row heights in multirow
                    # they also serve to clear colour panels which would hide the text
                    self.body.append('\\sphinxtablestrut{%d}' % nextcell.cell_id)
                else:
                    # use \multicolumn for wide multirow cell
                    self.body.append('\\multicolumn{%d}{l|}'
                                     '{\\sphinxtablestrut{%d}}' %
                                     (nextcell.width, nextcell.cell_id))

    def visit_acks(self, node: Element) -> None:
        # this is a list in the source, but should be rendered as a
        # comma-separated list here
        bullet_list = cast(nodes.bullet_list, node[0])
        list_items = cast(Iterable[nodes.list_item], bullet_list)
        self.body.append('\n\n')
        self.body.append(', '.join(n.astext() for n in list_items) + '.')
        self.body.append('\n\n')
        raise nodes.SkipNode

    def visit_bullet_list(self, node: Element) -> None:
        if not self.compact_list:
            self.body.append('\\begin{itemize}\n')
        if self.table:
            self.table.has_problematic = True

    def depart_bullet_list(self, node: Element) -> None:
        if not self.compact_list:
            self.body.append('\\end{itemize}\n')

    def visit_enumerated_list(self, node: Element) -> None:
        def get_enumtype(node: Element) -> str:
            enumtype = node.get('enumtype', 'arabic')
            if 'alpha' in enumtype and 26 < node.get('start', 0) + len(node):
                # fallback to arabic if alphabet counter overflows
                enumtype = 'arabic'

            return enumtype

        def get_nested_level(node: Element) -> int:
            if node is None:
                return 0
            elif isinstance(node, nodes.enumerated_list):
                return get_nested_level(node.parent) + 1
            else:
                return get_nested_level(node.parent)

        enum = "enum%s" % toRoman(get_nested_level(node)).lower()
        enumnext = "enum%s" % toRoman(get_nested_level(node) + 1).lower()
        style = ENUMERATE_LIST_STYLE.get(get_enumtype(node))
        prefix = node.get('prefix', '')
        suffix = node.get('suffix', '.')

        self.body.append('\\begin{enumerate}\n')
        self.body.append('\\sphinxsetlistlabels{%s}{%s}{%s}{%s}{%s}%%\n' %
                         (style, enum, enumnext, prefix, suffix))
        if 'start' in node:
            self.body.append('\\setcounter{%s}{%d}\n' % (enum, node['start'] - 1))
        if self.table:
            self.table.has_problematic = True

    def depart_enumerated_list(self, node: Element) -> None:
        self.body.append('\\end{enumerate}\n')

    def visit_list_item(self, node: Element) -> None:
        # Append "{}" in case the next character is "[", which would break
        # LaTeX's list environment (no numbering and the "[" is not printed).
        self.body.append(r'\item {} ')

    def depart_list_item(self, node: Element) -> None:
        self.body.append('\n')

    def visit_definition_list(self, node: Element) -> None:
        self.body.append('\\begin{description}\n')
        if self.table:
            self.table.has_problematic = True

    def depart_definition_list(self, node: Element) -> None:
        self.body.append('\\end{description}\n')

    def visit_definition_list_item(self, node: Element) -> None:
        pass

    def depart_definition_list_item(self, node: Element) -> None:
        pass

    def visit_term(self, node: Element) -> None:
        self.in_term += 1
        ctx = ''
        if node.get('ids'):
            ctx = '\\phantomsection'
            for node_id in node['ids']:
                ctx += self.hypertarget(node_id, anchor=False)
        ctx += '}] \\leavevmode'
        self.body.append('\\item[{')
        self.context.append(ctx)

    def depart_term(self, node: Element) -> None:
        self.body.append(self.context.pop())
        self.in_term -= 1

    def visit_classifier(self, node: Element) -> None:
        self.body.append('{[}')

    def depart_classifier(self, node: Element) -> None:
        self.body.append('{]}')

    def visit_definition(self, node: Element) -> None:
        pass

    def depart_definition(self, node: Element) -> None:
        self.body.append('\n')

    def visit_field_list(self, node: Element) -> None:
        self.body.append('\\begin{quote}\\begin{description}\n')
        if self.table:
            self.table.has_problematic = True

    def depart_field_list(self, node: Element) -> None:
        self.body.append('\\end{description}\\end{quote}\n')

    def visit_field(self, node: Element) -> None:
        pass

    def depart_field(self, node: Element) -> None:
        pass

    visit_field_name = visit_term
    depart_field_name = depart_term

    visit_field_body = visit_definition
    depart_field_body = depart_definition

    def visit_paragraph(self, node: Element) -> None:
        index = node.parent.index(node)
        if (index > 0 and isinstance(node.parent, nodes.compound) and
                not isinstance(node.parent[index - 1], nodes.paragraph) and
                not isinstance(node.parent[index - 1], nodes.compound)):
            # insert blank line, if the paragraph follows a non-paragraph node in a compound
            self.body.append('\\noindent\n')
        elif index == 1 and isinstance(node.parent, (nodes.footnote, footnotetext)):
            # don't insert blank line, if the paragraph is second child of a footnote
            # (first one is label node)
            pass
        else:
            self.body.append('\n')

    def depart_paragraph(self, node: Element) -> None:
        self.body.append('\n')

    def visit_centered(self, node: Element) -> None:
        self.body.append('\n\\begin{center}')
        if self.table:
            self.table.has_problematic = True

    def depart_centered(self, node: Element) -> None:
        self.body.append('\n\\end{center}')

    def visit_hlist(self, node: Element) -> None:
        # for now, we don't support a more compact list format
        # don't add individual itemize environments, but one for all columns
        self.compact_list += 1
        self.body.append('\\begin{itemize}\\setlength{\\itemsep}{0pt}'
                         '\\setlength{\\parskip}{0pt}\n')
        if self.table:
            self.table.has_problematic = True

    def depart_hlist(self, node: Element) -> None:
        self.compact_list -= 1
        self.body.append('\\end{itemize}\n')

    def visit_hlistcol(self, node: Element) -> None:
        pass

    def depart_hlistcol(self, node: Element) -> None:
        pass

    def latex_image_length(self, width_str: str, scale: int = 100) -> str:
        try:
            return rstdim_to_latexdim(width_str, scale)
        except ValueError:
            logger.warning(__('dimension unit %s is invalid. Ignored.'), width_str)
            return None

    def is_inline(self, node: Element) -> bool:
        """Check whether a node represents an inline element."""
        return isinstance(node.parent, nodes.TextElement)

    def visit_image(self, node: Element) -> None:
        attrs = node.attributes
        pre = []    # type: List[str]
                    # in reverse order
        post = []   # type: List[str]
        include_graphics_options = []
        has_hyperlink = isinstance(node.parent, nodes.reference)
        if has_hyperlink:
            is_inline = self.is_inline(node.parent)
        else:
            is_inline = self.is_inline(node)
        if 'width' in attrs:
            if 'scale' in attrs:
                w = self.latex_image_length(attrs['width'], attrs['scale'])
            else:
                w = self.latex_image_length(attrs['width'])
            if w:
                include_graphics_options.append('width=%s' % w)
        if 'height' in attrs:
            if 'scale' in attrs:
                h = self.latex_image_length(attrs['height'], attrs['scale'])
            else:
                h = self.latex_image_length(attrs['height'])
            if h:
                include_graphics_options.append('height=%s' % h)
        if 'scale' in attrs:
            if not include_graphics_options:
                # if no "width" nor "height", \sphinxincludegraphics will fit
                # to the available text width if oversized after rescaling.
                include_graphics_options.append('scale=%s'
                                                % (float(attrs['scale']) / 100.0))
        if 'align' in attrs:
            align_prepost = {
                # By default latex aligns the top of an image.
                (1, 'top'): ('', ''),
                (1, 'middle'): ('\\raisebox{-0.5\\height}{', '}'),
                (1, 'bottom'): ('\\raisebox{-\\height}{', '}'),
                (0, 'center'): ('{\\hspace*{\\fill}', '\\hspace*{\\fill}}'),
                (0, 'default'): ('{\\hspace*{\\fill}', '\\hspace*{\\fill}}'),
                # These 2 don't exactly do the right thing.  The image should
                # be floated alongside the paragraph.  See
                # https://www.w3.org/TR/html4/struct/objects.html#adef-align-IMG
                (0, 'left'): ('{', '\\hspace*{\\fill}}'),
                (0, 'right'): ('{\\hspace*{\\fill}', '}'),
            }
            try:
                pre.append(align_prepost[is_inline, attrs['align']][0])
                post.append(align_prepost[is_inline, attrs['align']][1])
            except KeyError:
                pass
        if self.in_parsed_literal:
            pre.append('{\\sphinxunactivateextrasandspace ')
            post.append('}')
        if not is_inline and not has_hyperlink:
            pre.append('\n\\noindent')
            post.append('\n')
        pre.reverse()
        if node['uri'] in self.builder.images:
            uri = self.builder.images[node['uri']]
        else:
            # missing image!
            if self.ignore_missing_images:
                return
            uri = node['uri']
        if uri.find('://') != -1:
            # ignore remote images
            return
        self.body.extend(pre)
        options = ''
        if include_graphics_options:
            options = '[%s]' % ','.join(include_graphics_options)
        base, ext = path.splitext(uri)
        if self.in_title and base:
            # Lowercase tokens forcely because some fncychap themes capitalize
            # the options of \sphinxincludegraphics unexpectly (ex. WIDTH=...).
            self.body.append('\\lowercase{\\sphinxincludegraphics%s}{{%s}%s}' %
                             (options, base, ext))
        else:
            self.body.append('\\sphinxincludegraphics%s{{%s}%s}' %
                             (options, base, ext))
        self.body.extend(post)

    def depart_image(self, node: Element) -> None:
        pass

    def visit_figure(self, node: Element) -> None:
        align = self.elements['figure_align']
        if self.no_latex_floats:
            align = "H"
        if self.table:
            # TODO: support align option
            if 'width' in node:
                length = self.latex_image_length(node['width'])
                if length:
                    self.body.append('\\begin{sphinxfigure-in-table}[%s]\n'
                                     '\\centering\n' % length)
            else:
                self.body.append('\\begin{sphinxfigure-in-table}\n\\centering\n')
            if any(isinstance(child, nodes.caption) for child in node):
                self.body.append('\\capstart')
            self.context.append('\\end{sphinxfigure-in-table}\\relax\n')
        elif node.get('align', '') in ('left', 'right'):
            length = None
            if 'width' in node:
                length = self.latex_image_length(node['width'])
            elif isinstance(node[0], nodes.image) and 'width' in node[0]:
                length = self.latex_image_length(node[0]['width'])
            self.body.append('\n\n')    # Insert a blank line to prevent infinite loop
                                        # https://github.com/sphinx-doc/sphinx/issues/7059
            self.body.append('\\begin{wrapfigure}{%s}{%s}\n\\centering' %
                             ('r' if node['align'] == 'right' else 'l', length or '0pt'))
            self.context.append('\\end{wrapfigure}\n')
        elif self.in_minipage:
            self.body.append('\n\\begin{center}')
            self.context.append('\\end{center}\n')
        else:
            self.body.append('\n\\begin{figure}[%s]\n\\centering\n' % align)
            if any(isinstance(child, nodes.caption) for child in node):
                self.body.append('\\capstart\n')
            self.context.append('\\end{figure}\n')

    def depart_figure(self, node: Element) -> None:
        self.body.append(self.context.pop())

    def visit_caption(self, node: Element) -> None:
        self.in_caption += 1
        if isinstance(node.parent, captioned_literal_block):
            self.body.append('\\sphinxSetupCaptionForVerbatim{')
        elif self.in_minipage and isinstance(node.parent, nodes.figure):
            self.body.append('\\captionof{figure}{')
        elif self.table and node.parent.tagname == 'figure':
            self.body.append('\\sphinxfigcaption{')
        else:
            self.body.append('\\caption{')

    def depart_caption(self, node: Element) -> None:
        self.body.append('}')
        if isinstance(node.parent, nodes.figure):
            labels = self.hypertarget_to(node.parent)
            self.body.append(labels)
        self.in_caption -= 1

    def visit_legend(self, node: Element) -> None:
        self.body.append('\n\\begin{sphinxlegend}')

    def depart_legend(self, node: Element) -> None:
        self.body.append('\\end{sphinxlegend}\n')

    def visit_admonition(self, node: Element) -> None:
        self.body.append('\n\\begin{sphinxadmonition}{note}')
        self.no_latex_floats += 1

    def depart_admonition(self, node: Element) -> None:
        self.body.append('\\end{sphinxadmonition}\n')
        self.no_latex_floats -= 1

    def _visit_named_admonition(self, node: Element) -> None:
        label = admonitionlabels[node.tagname]
        self.body.append('\n\\begin{sphinxadmonition}{%s}{%s:}' %
                         (node.tagname, label))
        self.no_latex_floats += 1

    def _depart_named_admonition(self, node: Element) -> None:
        self.body.append('\\end{sphinxadmonition}\n')
        self.no_latex_floats -= 1

    visit_attention = _visit_named_admonition
    depart_attention = _depart_named_admonition
    visit_caution = _visit_named_admonition
    depart_caution = _depart_named_admonition
    visit_danger = _visit_named_admonition
    depart_danger = _depart_named_admonition
    visit_error = _visit_named_admonition
    depart_error = _depart_named_admonition
    visit_hint = _visit_named_admonition
    depart_hint = _depart_named_admonition
    visit_important = _visit_named_admonition
    depart_important = _depart_named_admonition
    visit_note = _visit_named_admonition
    depart_note = _depart_named_admonition
    visit_tip = _visit_named_admonition
    depart_tip = _depart_named_admonition
    visit_warning = _visit_named_admonition
    depart_warning = _depart_named_admonition

    def visit_versionmodified(self, node: Element) -> None:
        pass

    def depart_versionmodified(self, node: Element) -> None:
        pass

    def visit_target(self, node: Element) -> None:
        def add_target(id: str) -> None:
            # indexing uses standard LaTeX index markup, so the targets
            # will be generated differently
            if id.startswith('index-'):
                return

            # equations also need no extra blank line nor hypertarget
            # TODO: fix this dependency on mathbase extension internals
            if id.startswith('equation-'):
                return

            # insert blank line, if the target follows a paragraph node
            index = node.parent.index(node)
            if index > 0 and isinstance(node.parent[index - 1], nodes.paragraph):
                self.body.append('\n')

            # do not generate \phantomsection in \section{}
            anchor = not self.in_title
            self.body.append(self.hypertarget(id, anchor=anchor))

        # skip if visitor for next node supports hyperlink
        next_node = node  # type: nodes.Node
        while isinstance(next_node, nodes.target):
            next_node = next_node.next_node(ascend=True)

        domain = cast(StandardDomain, self.builder.env.get_domain('std'))
        if isinstance(next_node, HYPERLINK_SUPPORT_NODES):
            return
        elif domain.get_enumerable_node_type(next_node) and domain.get_numfig_title(next_node):
            return

        if 'refuri' in node:
            return
        if 'anonymous' in node:
            return
        if node.get('refid'):
            prev_node = get_prev_node(node)
            if isinstance(prev_node, nodes.reference) and node['refid'] == prev_node['refid']:
                # a target for a hyperlink reference having alias
                pass
            else:
                add_target(node['refid'])
        for id in node['ids']:
            add_target(id)

    def depart_target(self, node: Element) -> None:
        pass

    def visit_attribution(self, node: Element) -> None:
        self.body.append('\n\\begin{flushright}\n')
        self.body.append('---')

    def depart_attribution(self, node: Element) -> None:
        self.body.append('\n\\end{flushright}\n')

    def visit_index(self, node: Element) -> None:
        def escape(value: str) -> str:
            value = self.encode(value)
            value = value.replace(r'\{', r'\sphinxleftcurlybrace{}')
            value = value.replace(r'\}', r'\sphinxrightcurlybrace{}')
            value = value.replace('"', '""')
            value = value.replace('@', '"@')
            value = value.replace('!', '"!')
            value = value.replace('|', r'\textbar{}')
            return value

        def style(string: str) -> str:
            match = EXTRA_RE.match(string)
            if match:
                return match.expand(r'\\spxentry{\1}\\spxextra{\2}')
            else:
                return '\\spxentry{%s}' % string

        if not node.get('inline', True):
            self.body.append('\n')
        entries = node['entries']
        for type, string, tid, ismain, key_ in entries:
            m = ''
            if ismain:
                m = '|spxpagem'
            try:
                if type == 'single':
                    try:
                        p1, p2 = [escape(x) for x in split_into(2, 'single', string)]
                        P1, P2 = style(p1), style(p2)
                        self.body.append(r'\index{%s@%s!%s@%s%s}' % (p1, P1, p2, P2, m))
                    except ValueError:
                        p = escape(split_into(1, 'single', string)[0])
                        P = style(p)
                        self.body.append(r'\index{%s@%s%s}' % (p, P, m))
                elif type == 'pair':
                    p1, p2 = [escape(x) for x in split_into(2, 'pair', string)]
                    P1, P2 = style(p1), style(p2)
                    self.body.append(r'\index{%s@%s!%s@%s%s}\index{%s@%s!%s@%s%s}' %
                                     (p1, P1, p2, P2, m, p2, P2, p1, P1, m))
                elif type == 'triple':
                    p1, p2, p3 = [escape(x) for x in split_into(3, 'triple', string)]
                    P1, P2, P3 = style(p1), style(p2), style(p3)
                    self.body.append(
                        r'\index{%s@%s!%s %s@%s %s%s}'
                        r'\index{%s@%s!%s, %s@%s, %s%s}'
                        r'\index{%s@%s!%s %s@%s %s%s}' %
                        (p1, P1, p2, p3, P2, P3, m,
                         p2, P2, p3, p1, P3, P1, m,
                         p3, P3, p1, p2, P1, P2, m))
                elif type == 'see':
                    p1, p2 = [escape(x) for x in split_into(2, 'see', string)]
                    P1 = style(p1)
                    self.body.append(r'\index{%s@%s|see{%s}}' % (p1, P1, p2))
                elif type == 'seealso':
                    p1, p2 = [escape(x) for x in split_into(2, 'seealso', string)]
                    P1 = style(p1)
                    self.body.append(r'\index{%s@%s|see{%s}}' % (p1, P1, p2))
                else:
                    logger.warning(__('unknown index entry type %s found'), type)
            except ValueError as err:
                logger.warning(str(err))
        if not node.get('inline', True):
            self.body.append('\\ignorespaces ')
        raise nodes.SkipNode

    def visit_raw(self, node: Element) -> None:
        if not self.is_inline(node):
            self.body.append('\n')
        if 'latex' in node.get('format', '').split():
            self.body.append(node.astext())
        if not self.is_inline(node):
            self.body.append('\n')
        raise nodes.SkipNode

    def visit_reference(self, node: Element) -> None:
        if not self.in_title:
            for id in node.get('ids'):
                anchor = not self.in_caption
                self.body += self.hypertarget(id, anchor=anchor)
        if not self.is_inline(node):
            self.body.append('\n')
        uri = node.get('refuri', '')
        if not uri and node.get('refid'):
            uri = '%' + self.curfilestack[-1] + '#' + node['refid']
        if self.in_title or not uri:
            self.context.append('')
        elif uri.startswith('#'):
            # references to labels in the same document
            id = self.curfilestack[-1] + ':' + uri[1:]
            self.body.append(self.hyperlink(id))
            self.body.append(r'\emph{')
            if self.builder.config.latex_show_pagerefs and not \
                    self.in_production_list:
                self.context.append('}}} (%s)' % self.hyperpageref(id))
            else:
                self.context.append('}}}')
        elif uri.startswith('%'):
            # references to documents or labels inside documents
            hashindex = uri.find('#')
            if hashindex == -1:
                # reference to the document
                id = uri[1:] + '::doc'
            else:
                # reference to a label
                id = uri[1:].replace('#', ':')
            self.body.append(self.hyperlink(id))
            if (len(node) and
                    isinstance(node[0], nodes.Element) and
                    'std-term' in node[0].get('classes', [])):
                # don't add a pageref for glossary terms
                self.context.append('}}}')
                # mark up as termreference
                self.body.append(r'\sphinxtermref{')
            else:
                self.body.append(r'\sphinxcrossref{')
                if self.builder.config.latex_show_pagerefs and not \
                   self.in_production_list:
                    self.context.append('}}} (%s)' % self.hyperpageref(id))
                else:
                    self.context.append('}}}')
        else:
            if len(node) == 1 and uri == node[0]:
                if node.get('nolinkurl'):
                    self.body.append('\\sphinxnolinkurl{%s}' % self.encode_uri(uri))
                else:
                    self.body.append('\\sphinxurl{%s}' % self.encode_uri(uri))
                raise nodes.SkipNode
            else:
                self.body.append('\\sphinxhref{%s}{' % self.encode_uri(uri))
                self.context.append('}')

    def depart_reference(self, node: Element) -> None:
        self.body.append(self.context.pop())
        if not self.is_inline(node):
            self.body.append('\n')

    def visit_number_reference(self, node: Element) -> None:
        if node.get('refid'):
            id = self.curfilestack[-1] + ':' + node['refid']
        else:
            id = node.get('refuri', '')[1:].replace('#', ':')

        title = self.escape(node.get('title', '%s')).replace('\\%s', '%s')
        if '\\{name\\}' in title or '\\{number\\}' in title:
            # new style format (cf. "Fig.%{number}")
            title = title.replace('\\{name\\}', '{name}').replace('\\{number\\}', '{number}')
            text = escape_abbr(title).format(name='\\nameref{%s}' % self.idescape(id),
                                             number='\\ref{%s}' % self.idescape(id))
        else:
            # old style format (cf. "Fig.%{number}")
            text = escape_abbr(title) % ('\\ref{%s}' % self.idescape(id))
        hyperref = '\\hyperref[%s]{%s}' % (self.idescape(id), text)
        self.body.append(hyperref)

        raise nodes.SkipNode

    def visit_download_reference(self, node: Element) -> None:
        pass

    def depart_download_reference(self, node: Element) -> None:
        pass

    def visit_pending_xref(self, node: Element) -> None:
        pass

    def depart_pending_xref(self, node: Element) -> None:
        pass

    def visit_emphasis(self, node: Element) -> None:
        self.body.append(r'\sphinxstyleemphasis{')

    def depart_emphasis(self, node: Element) -> None:
        self.body.append('}')

    def visit_literal_emphasis(self, node: Element) -> None:
        self.body.append(r'\sphinxstyleliteralemphasis{\sphinxupquote{')

    def depart_literal_emphasis(self, node: Element) -> None:
        self.body.append('}}')

    def visit_strong(self, node: Element) -> None:
        self.body.append(r'\sphinxstylestrong{')

    def depart_strong(self, node: Element) -> None:
        self.body.append('}')

    def visit_literal_strong(self, node: Element) -> None:
        self.body.append(r'\sphinxstyleliteralstrong{\sphinxupquote{')

    def depart_literal_strong(self, node: Element) -> None:
        self.body.append('}}')

    def visit_abbreviation(self, node: Element) -> None:
        abbr = node.astext()
        self.body.append(r'\sphinxstyleabbreviation{')
        # spell out the explanation once
        if node.hasattr('explanation') and abbr not in self.handled_abbrs:
            self.context.append('} (%s)' % self.encode(node['explanation']))
            self.handled_abbrs.add(abbr)
        else:
            self.context.append('}')

    def depart_abbreviation(self, node: Element) -> None:
        self.body.append(self.context.pop())

    def visit_manpage(self, node: Element) -> None:
        return self.visit_literal_emphasis(node)

    def depart_manpage(self, node: Element) -> None:
        return self.depart_literal_emphasis(node)

    def visit_title_reference(self, node: Element) -> None:
        self.body.append(r'\sphinxtitleref{')

    def depart_title_reference(self, node: Element) -> None:
        self.body.append('}')

    def visit_thebibliography(self, node: Element) -> None:
        citations = cast(Iterable[nodes.citation], node)
        labels = (cast(nodes.label, citation[0]) for citation in citations)
        longest_label = max((label.astext() for label in labels), key=len)
        if len(longest_label) > MAX_CITATION_LABEL_LENGTH:
            # adjust max width of citation labels not to break the layout
            longest_label = longest_label[:MAX_CITATION_LABEL_LENGTH]

        self.body.append('\n\\begin{sphinxthebibliography}{%s}\n' %
                         self.encode(longest_label))

    def depart_thebibliography(self, node: Element) -> None:
        self.body.append('\\end{sphinxthebibliography}\n')

    def visit_citation(self, node: Element) -> None:
        label = cast(nodes.label, node[0])
        self.body.append('\\bibitem[%s]{%s:%s}' % (self.encode(label.astext()),
                                                   node['docname'], node['ids'][0]))

    def depart_citation(self, node: Element) -> None:
        pass

    def visit_citation_reference(self, node: Element) -> None:
        if self.in_title:
            pass
        else:
            self.body.append('\\sphinxcite{%s:%s}' % (node['docname'], node['refname']))
            raise nodes.SkipNode

    def depart_citation_reference(self, node: Element) -> None:
        pass

    def visit_literal(self, node: Element) -> None:
        if self.in_title:
            self.body.append(r'\sphinxstyleliteralintitle{\sphinxupquote{')
        elif 'kbd' in node['classes']:
            self.body.append(r'\sphinxkeyboard{\sphinxupquote{')
        else:
            self.body.append(r'\sphinxcode{\sphinxupquote{')

    def depart_literal(self, node: Element) -> None:
        self.body.append('}}')

    def visit_footnote_reference(self, node: Element) -> None:
        raise nodes.SkipNode

    def visit_footnotemark(self, node: Element) -> None:
        self.body.append('\\sphinxfootnotemark[')

    def depart_footnotemark(self, node: Element) -> None:
        self.body.append(']')

    def visit_footnotetext(self, node: Element) -> None:
        label = cast(nodes.label, node[0])
        self.body.append('%%\n\\begin{footnotetext}[%s]'
                         '\\sphinxAtStartFootnote\n' % label.astext())

    def depart_footnotetext(self, node: Element) -> None:
        # the \ignorespaces in particular for after table header use
        self.body.append('%\n\\end{footnotetext}\\ignorespaces ')

    def visit_captioned_literal_block(self, node: Element) -> None:
        pass

    def depart_captioned_literal_block(self, node: Element) -> None:
        pass

    def visit_literal_block(self, node: Element) -> None:
        if node.rawsource != node.astext():
            # most probably a parsed-literal block -- don't highlight
            self.in_parsed_literal += 1
            self.body.append('\\begin{sphinxalltt}\n')
        else:
            labels = self.hypertarget_to(node)
            if isinstance(node.parent, captioned_literal_block):
                labels += self.hypertarget_to(node.parent)
            if labels and not self.in_footnote:
                self.body.append('\n\\def\\sphinxLiteralBlockLabel{' + labels + '}')

            lang = node.get('language', 'default')
            linenos = node.get('linenos', False)
            highlight_args = node.get('highlight_args', {})
            highlight_args['force'] = node.get('force', False)
            if lang is self.builder.config.highlight_language:
                # only pass highlighter options for original language
                opts = self.builder.config.highlight_options
            else:
                opts = {}

            hlcode = self.highlighter.highlight_block(
                node.rawsource, lang, opts=opts, linenos=linenos,
                location=node, **highlight_args
            )
            if self.in_footnote:
                self.body.append('\n\\sphinxSetupCodeBlockInFootnote')
                hlcode = hlcode.replace('\\begin{Verbatim}',
                                        '\\begin{sphinxVerbatim}')
            # if in table raise verbatim flag to avoid "tabulary" environment
            # and opt for sphinxVerbatimintable to handle caption & long lines
            elif self.table:
                self.table.has_problematic = True
                self.table.has_verbatim = True
                hlcode = hlcode.replace('\\begin{Verbatim}',
                                        '\\begin{sphinxVerbatimintable}')
            else:
                hlcode = hlcode.replace('\\begin{Verbatim}',
                                        '\\begin{sphinxVerbatim}')
            # get consistent trailer
            hlcode = hlcode.rstrip()[:-14]  # strip \end{Verbatim}
            if self.table and not self.in_footnote:
                hlcode += '\\end{sphinxVerbatimintable}'
            else:
                hlcode += '\\end{sphinxVerbatim}'

            hllines = str(highlight_args.get('hl_lines', []))[1:-1]
            if hllines:
                self.body.append('\n\\fvset{hllines={, %s,}}%%' % hllines)
            self.body.append('\n' + hlcode + '\n')
            if hllines:
                self.body.append('\\sphinxresetverbatimhllines\n')
            raise nodes.SkipNode

    def depart_literal_block(self, node: Element) -> None:
        self.body.append('\n\\end{sphinxalltt}\n')
        self.in_parsed_literal -= 1
    visit_doctest_block = visit_literal_block
    depart_doctest_block = depart_literal_block

    def visit_line(self, node: Element) -> None:
        self.body.append('\\item[] ')

    def depart_line(self, node: Element) -> None:
        self.body.append('\n')

    def visit_line_block(self, node: Element) -> None:
        if isinstance(node.parent, nodes.line_block):
            self.body.append('\\item[]\n'
                             '\\begin{DUlineblock}{\\DUlineblockindent}\n')
        else:
            self.body.append('\n\\begin{DUlineblock}{0em}\n')
        if self.table:
            self.table.has_problematic = True

    def depart_line_block(self, node: Element) -> None:
        self.body.append('\\end{DUlineblock}\n')

    def visit_block_quote(self, node: Element) -> None:
        # If the block quote contains a single object and that object
        # is a list, then generate a list not a block quote.
        # This lets us indent lists.
        done = 0
        if len(node.children) == 1:
            child = node.children[0]
            if isinstance(child, nodes.bullet_list) or \
                    isinstance(child, nodes.enumerated_list):
                done = 1
        if not done:
            self.body.append('\\begin{quote}\n')
            if self.table:
                self.table.has_problematic = True

    def depart_block_quote(self, node: Element) -> None:
        done = 0
        if len(node.children) == 1:
            child = node.children[0]
            if isinstance(child, nodes.bullet_list) or \
                    isinstance(child, nodes.enumerated_list):
                done = 1
        if not done:
            self.body.append('\\end{quote}\n')

    # option node handling copied from docutils' latex writer

    def visit_option(self, node: Element) -> None:
        if self.context[-1]:
            # this is not the first option
            self.body.append(', ')

    def depart_option(self, node: Element) -> None:
        # flag that the first option is done.
        self.context[-1] += 1

    def visit_option_argument(self, node: Element) -> None:
        """The delimiter betweeen an option and its argument."""
        self.body.append(node.get('delimiter', ' '))

    def depart_option_argument(self, node: Element) -> None:
        pass

    def visit_option_group(self, node: Element) -> None:
        self.body.append('\\item [')
        # flag for first option
        self.context.append(0)

    def depart_option_group(self, node: Element) -> None:
        self.context.pop()  # the flag
        self.body.append('] ')

    def visit_option_list(self, node: Element) -> None:
        self.body.append('\\begin{optionlist}{3cm}\n')
        if self.table:
            self.table.has_problematic = True

    def depart_option_list(self, node: Element) -> None:
        self.body.append('\\end{optionlist}\n')

    def visit_option_list_item(self, node: Element) -> None:
        pass

    def depart_option_list_item(self, node: Element) -> None:
        pass

    def visit_option_string(self, node: Element) -> None:
        ostring = node.astext()
        self.body.append(self.encode(ostring))
        raise nodes.SkipNode

    def visit_description(self, node: Element) -> None:
        self.body.append(' ')

    def depart_description(self, node: Element) -> None:
        pass

    def visit_superscript(self, node: Element) -> None:
        self.body.append('$^{\\text{')

    def depart_superscript(self, node: Element) -> None:
        self.body.append('}}$')

    def visit_subscript(self, node: Element) -> None:
        self.body.append('$_{\\text{')

    def depart_subscript(self, node: Element) -> None:
        self.body.append('}}$')

    def visit_inline(self, node: Element) -> None:
        classes = node.get('classes', [])
        if classes in [['menuselection']]:
            self.body.append(r'\sphinxmenuselection{')
            self.context.append('}')
        elif classes in [['guilabel']]:
            self.body.append(r'\sphinxguilabel{')
            self.context.append('}')
        elif classes in [['accelerator']]:
            self.body.append(r'\sphinxaccelerator{')
            self.context.append('}')
        elif classes and not self.in_title:
            self.body.append(r'\DUrole{%s}{' % ','.join(classes))
            self.context.append('}')
        else:
            self.context.append('')

    def depart_inline(self, node: Element) -> None:
        self.body.append(self.context.pop())

    def visit_generated(self, node: Element) -> None:
        pass

    def depart_generated(self, node: Element) -> None:
        pass

    def visit_compound(self, node: Element) -> None:
        pass

    def depart_compound(self, node: Element) -> None:
        pass

    def visit_container(self, node: Element) -> None:
        pass

    def depart_container(self, node: Element) -> None:
        pass

    def visit_decoration(self, node: Element) -> None:
        pass

    def depart_decoration(self, node: Element) -> None:
        pass

    # docutils-generated elements that we don't support

    def visit_header(self, node: Element) -> None:
        raise nodes.SkipNode

    def visit_footer(self, node: Element) -> None:
        raise nodes.SkipNode

    def visit_docinfo(self, node: Element) -> None:
        raise nodes.SkipNode

    # text handling

    def encode(self, text: str) -> str:
        text = self.escape(text)
        if self.literal_whitespace:
            # Insert a blank before the newline, to avoid
            # ! LaTeX Error: There's no line here to end.
            text = text.replace('\n', '~\\\\\n').replace(' ', '~')
        return text

    def encode_uri(self, text: str) -> str:
        # TODO: it is probably wrong that this uses texescape.escape()
        #       this must be checked against hyperref package exact dealings
        #       mainly, %, #, {, } and \ need escaping via a \ escape
        # in \href, the tilde is allowed and must be represented literally
        return self.encode(text).replace('\\textasciitilde{}', '~').\
            replace('\\sphinxhyphen{}', '-').\
            replace('\\textquotesingle{}', "'")

    def visit_Text(self, node: Text) -> None:
        text = self.encode(node.astext())
        self.body.append(text)

    def depart_Text(self, node: Text) -> None:
        pass

    def visit_comment(self, node: Element) -> None:
        raise nodes.SkipNode

    def visit_meta(self, node: Element) -> None:
        # only valid for HTML
        raise nodes.SkipNode

    def visit_system_message(self, node: Element) -> None:
        pass

    def depart_system_message(self, node: Element) -> None:
        self.body.append('\n')

    def visit_math(self, node: Element) -> None:
        if self.in_title:
            self.body.append(r'\protect\(%s\protect\)' % node.astext())
        else:
            self.body.append(r'\(%s\)' % node.astext())
        raise nodes.SkipNode

    def visit_math_block(self, node: Element) -> None:
        if node.get('label'):
            label = "equation:%s:%s" % (node['docname'], node['label'])
        else:
            label = None

        if node.get('nowrap'):
            if label:
                self.body.append(r'\label{%s}' % label)
            self.body.append(node.astext())
        else:
            from sphinx.util.math import wrap_displaymath
            self.body.append(wrap_displaymath(node.astext(), label,
                                              self.builder.config.math_number_all))
        raise nodes.SkipNode

    def visit_math_reference(self, node: Element) -> None:
        label = "equation:%s:%s" % (node['docname'], node['target'])
        eqref_format = self.builder.config.math_eqref_format
        if eqref_format:
            try:
                ref = r'\ref{%s}' % label
                self.body.append(eqref_format.format(number=ref))
            except KeyError as exc:
                logger.warning(__('Invalid math_eqref_format: %r'), exc,
                               location=node)
                self.body.append(r'\eqref{%s}' % label)
        else:
            self.body.append(r'\eqref{%s}' % label)

    def depart_math_reference(self, node: Element) -> None:
        pass

    def unknown_visit(self, node: Node) -> None:
        raise NotImplementedError('Unknown node: ' + node.__class__.__name__)

    # --------- METHODS FOR COMPATIBILITY --------------------------------------

    def collect_footnotes(self, node: Element) -> Dict[str, List[Union["collected_footnote", bool]]]:  # NOQA
        def footnotes_under(n: Element) -> Iterator[nodes.footnote]:
            if isinstance(n, nodes.footnote):
                yield n
            else:
                for c in n.children:
                    if isinstance(c, addnodes.start_of_file):
                        continue
                    elif isinstance(c, nodes.Element):
                        yield from footnotes_under(c)

        warnings.warn('LaTeXWriter.collected_footnote() is deprecated.',
                      RemovedInSphinx40Warning, stacklevel=2)

        fnotes = {}  # type: Dict[str, List[Union[collected_footnote, bool]]]
        for fn in footnotes_under(node):
            label = cast(nodes.label, fn[0])
            num = label.astext().strip()
            newnode = collected_footnote('', *fn.children, number=num)
            fnotes[num] = [newnode, False]
        return fnotes

    @property
    def no_contractions(self) -> int:
        warnings.warn('LaTeXTranslator.no_contractions is deprecated.',
                      RemovedInSphinx40Warning, stacklevel=2)
        return 0

    def babel_defmacro(self, name: str, definition: str) -> str:
        warnings.warn('babel_defmacro() is deprecated.',
                      RemovedInSphinx40Warning, stacklevel=2)

        if self.elements['babel']:
            prefix = '\\addto\\extras%s{' % self.babel.get_language()
            suffix = '}'
        else:  # babel is disabled (mainly for Japanese environment)
            prefix = ''
            suffix = ''

        return ('%s\\def%s{%s}%s\n' % (prefix, name, definition, suffix))

    def generate_numfig_format(self, builder: "LaTeXBuilder") -> str:
        warnings.warn('generate_numfig_format() is deprecated.',
                      RemovedInSphinx40Warning, stacklevel=2)
        ret = []  # type: List[str]
        figure = self.builder.config.numfig_format['figure'].split('%s', 1)
        if len(figure) == 1:
            ret.append('\\def\\fnum@figure{%s}\n' % self.escape(figure[0]).strip())
        else:
            definition = escape_abbr(self.escape(figure[0]))
            ret.append(self.babel_renewcommand('\\figurename', definition))
            ret.append('\\makeatletter\n')
            ret.append('\\def\\fnum@figure{\\figurename\\thefigure{}%s}\n' %
                       self.escape(figure[1]))
            ret.append('\\makeatother\n')

        table = self.builder.config.numfig_format['table'].split('%s', 1)
        if len(table) == 1:
            ret.append('\\def\\fnum@table{%s}\n' % self.escape(table[0]).strip())
        else:
            definition = escape_abbr(self.escape(table[0]))
            ret.append(self.babel_renewcommand('\\tablename', definition))
            ret.append('\\makeatletter\n')
            ret.append('\\def\\fnum@table{\\tablename\\thetable{}%s}\n' %
                       self.escape(table[1]))
            ret.append('\\makeatother\n')

        codeblock = self.builder.config.numfig_format['code-block'].split('%s', 1)
        if len(codeblock) == 1:
            pass  # FIXME
        else:
            definition = self.escape(codeblock[0]).strip()
            ret.append(self.babel_renewcommand('\\literalblockname', definition))
            if codeblock[1]:
                pass  # FIXME

        return ''.join(ret)


# Import old modules here for compatibility
from sphinx.builders.latex import constants  # NOQA
from sphinx.builders.latex.util import ExtBabel  # NOQA


deprecated_alias('sphinx.writers.latex',
                 {
                     'ADDITIONAL_SETTINGS': constants.ADDITIONAL_SETTINGS,
                     'DEFAULT_SETTINGS': constants.DEFAULT_SETTINGS,
                     'LUALATEX_DEFAULT_FONTPKG': constants.LUALATEX_DEFAULT_FONTPKG,
                     'PDFLATEX_DEFAULT_FONTPKG': constants.PDFLATEX_DEFAULT_FONTPKG,
                     'SHORTHANDOFF': constants.SHORTHANDOFF,
                     'XELATEX_DEFAULT_FONTPKG': constants.XELATEX_DEFAULT_FONTPKG,
                     'XELATEX_GREEK_DEFAULT_FONTPKG': constants.XELATEX_GREEK_DEFAULT_FONTPKG,
                     'ExtBabel': ExtBabel,
                 },
                 RemovedInSphinx40Warning,
                 {
                     'ADDITIONAL_SETTINGS':
                     'sphinx.builders.latex.constants.ADDITIONAL_SETTINGS',
                     'DEFAULT_SETTINGS':
                     'sphinx.builders.latex.constants.DEFAULT_SETTINGS',
                     'LUALATEX_DEFAULT_FONTPKG':
                     'sphinx.builders.latex.constants.LUALATEX_DEFAULT_FONTPKG',
                     'PDFLATEX_DEFAULT_FONTPKG':
                     'sphinx.builders.latex.constants.PDFLATEX_DEFAULT_FONTPKG',
                     'SHORTHANDOFF':
                     'sphinx.builders.latex.constants.SHORTHANDOFF',
                     'XELATEX_DEFAULT_FONTPKG':
                     'sphinx.builders.latex.constants.XELATEX_DEFAULT_FONTPKG',
                     'XELATEX_GREEK_DEFAULT_FONTPKG':
                     'sphinx.builders.latex.constants.XELATEX_GREEK_DEFAULT_FONTPKG',
                     'ExtBabel': 'sphinx.builders.latex.util.ExtBabel',
                 })

# FIXME: Workaround to avoid circular import
# refs: https://github.com/sphinx-doc/sphinx/issues/5433
from sphinx.builders.latex.nodes import HYPERLINK_SUPPORT_NODES, captioned_literal_block, footnotetext  # NOQA
