# -*- coding: utf-8 -*-
"""
    sphinx.writers.wikisyntax
    ~~~~~~~~~~~~~~~~~~~

    Custom docutils writer for wikisyntax

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from docutils import writers, nodes
from sphinx.writers.text import TextTranslator


class WikisyntaxWriter(writers.Writer):
    supported = ('text',)
    settings_spec = ('No options here.', '', ())
    settings_defaults = {}

    output = None

    def __init__(self, builder):
        writers.Writer.__init__(self)
        self.builder = builder
        self.translator_class = self.builder.translator_class or WikisyntaxTranslator

    def translate(self):
        visitor = self.translator_class(self.document, self.builder)
        self.document.walkabout(visitor)
        self.output = visitor.body


class WikisyntaxTranslator(TextTranslator):

    MAXWIDTH = 200
    STDINDENT = 1

    def depart_document(self, node):
        self.end_state()
        self.body = self.nl.join(line and (':'*indent + line)
                                 for indent, lines in self.states[0]
                                 for line in lines)

    def depart_title(self, node):
        text = ''.join(x[1] for x in self.states.pop() if x[0] == -1)
        delimiter = '=' * self.sectionlevel

        self.stateindent.pop()
        self.states[-1].append((0, ['%s %s %s' % (delimiter, text, delimiter)]))

    def visit_desc_signature(self, node):
        self.new_state(0)
        self.add_text('<br />')
        self.add_text("'''")

    def visit_desc_parameterlist(self, node):
        self.add_text("'''")
        self.add_text('(')
        self.first_param = 1

    def depart_table(self, node):
        text = []
        text.append('<table border="1">')

        text.append('<tr>')
        for field in self.table[1]:
            text.append('<th>%s</th>' % field.rstrip('\n'))
        text.append('</tr>')

        for row in self.table[3:]:
            text.append('<tr>')
            for field in row:
                text.append('<td>%s</td>' % field.rstrip('\n'))
            text.append('</tr>')
        text.append('</table>')

        self.add_text(''.join(text))
        self.table = None
        self.end_state(wrap=False)

    def visit_transition(self, node):
        self.new_state(0)
        self.add_text('----')
        self.end_state()
        raise nodes.SkipNode

    def depart_list_item(self, node):
        if self.list_counter[-1] == -1:
            self.end_state(first='* ')
        elif self.list_counter[-1] == -2:
            pass
        else:
            self.end_state(first='# ')

    def visit_centered(self, node):
        self.add_text('{center|')

    def depart_centered(self, node):
        self.add_text('}')

    def visit_block_quote(self, node):
        self.new_state()
        self.add_text('<blockquote>')

    def depart_block_quote(self, node):
        self.add_text('</blockquote>')
        self.end_state()

    def visit_emphasis(self, node):
        self.add_text("''")

    def depart_emphasis(self, node):
        self.add_text("''")

    def visit_literal_emphasis(self, node):
        self.add_text("''")

    def depart_literal_emphasis(self, node):
        self.add_text("''")

    def visit_strong(self, node):
        self.add_text("'''")

    def depart_strong(self, node):
        self.add_text("'''")

    def visit_literal_strong(self, node):
        self.add_text("'''")

    def depart_literal_strong(self, node):
        self.add_text("'''")

    def visit_subscript(self, node):
        self.add_text('<sub>')

    def depart_subscript(self, node):
        self.add_text('</sub>')

    def visit_superscript(self, node):
        self.add_text('<sup>')

    def depart_superscript(self, node):
        self.add_text('</sup>')

    def visit_doctest_block(self, node):
        self.new_state(0)

    def depart_doctest_block(self, node):
        _, doctest = self.states.pop()[0]
        self.states.append([(0, [
            '<syntaxhighlight lang="python">' + self.nl +
            doctest + self.nl +
            '</syntaxhighlight>'
        ])])
        self.end_state(wrap=False)
