# -*- coding: utf-8 -*-
"""
    sphinx.ext.mathbase
    ~~~~~~~~~~~~~~~~~~~

    Set up math support in source files and LaTeX/text output.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes, utils
from docutils.parsers.rst import directives

from sphinx.util.nodes import set_source_info
from sphinx.util.compat import Directive


class math(nodes.Inline, nodes.TextElement):
    pass


class displaymath(nodes.Part, nodes.Element):
    pass


class eqref(nodes.Inline, nodes.TextElement):
    pass


def wrap_displaymath(math, label):
    parts = math.split('\n\n')
    ret = []
    for i, part in enumerate(parts):
        if not part.strip():
            continue
        if label is not None and i == 0:
            ret.append('\\begin{split}%s\\end{split}' % part +
                       (label and '\\label{'+label+'}' or ''))
        else:
            ret.append('\\begin{split}%s\\end{split}\\notag' % part)
    if not ret:
        return ''
    return '\\begin{gather}\n' + '\\\\'.join(ret) + '\n\\end{gather}'


def math_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    latex = utils.unescape(text, restore_backslashes=True)
    return [math(latex=latex)], []


def eq_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    text = utils.unescape(text)
    node = eqref('(?)', '(?)', target=text)
    node['docname'] = inliner.document.settings.env.docname
    return [node], []


def is_in_section_title(node):
    """Determine whether the node is in a section title"""
    from sphinx.util.nodes import traverse_parent

    for ancestor in traverse_parent(node):
        if isinstance(ancestor, nodes.title) and \
           isinstance(ancestor.parent, nodes.section):
            return True
    return False


class MathDirective(Directive):

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        'label': directives.unchanged,
        'name': directives.unchanged,
        'nowrap': directives.flag,
    }

    def run(self):
        latex = '\n'.join(self.content)
        if self.arguments and self.arguments[0]:
            latex = self.arguments[0] + '\n\n' + latex
        node = displaymath()
        node['latex'] = latex
        node['label'] = self.options.get('name', None)
        if node['label'] is None:
            node['label'] = self.options.get('label', None)
        node['nowrap'] = 'nowrap' in self.options
        node['docname'] = self.state.document.settings.env.docname
        ret = [node]
        set_source_info(self, node)
        if hasattr(self, 'src'):
            node.source = self.src
        if node['label']:
            tnode = nodes.target('', '', ids=['equation-' + node['label']])
            self.state.document.note_explicit_target(tnode)
            ret.insert(0, tnode)
        return ret


def latex_visit_math(self, node):
    if is_in_section_title(node):
        protect = r'\protect'
    else:
        protect = ''
    equation = protect + r'\(' + node['latex'] + protect + r'\)'
    self.body.append(equation)
    raise nodes.SkipNode


def latex_visit_displaymath(self, node):
    if node['nowrap']:
        self.body.append(node['latex'])
    else:
        label = node['label'] and node['docname'] + '-' + node['label'] or None
        self.body.append(wrap_displaymath(node['latex'], label))
    raise nodes.SkipNode


def latex_visit_eqref(self, node):
    self.body.append('\\eqref{%s-%s}' % (node['docname'], node['target']))
    raise nodes.SkipNode


def text_visit_math(self, node):
    self.add_text(node['latex'])
    raise nodes.SkipNode


def text_visit_displaymath(self, node):
    self.new_state()
    self.add_text(node['latex'])
    self.end_state()
    raise nodes.SkipNode


def text_visit_eqref(self, node):
    self.add_text(node['target'])
    raise nodes.SkipNode


def man_visit_math(self, node):
    self.body.append(node['latex'])
    raise nodes.SkipNode


def man_visit_displaymath(self, node):
    self.visit_centered(node)


def man_depart_displaymath(self, node):
    self.depart_centered(node)


def man_visit_eqref(self, node):
    self.body.append(node['target'])
    raise nodes.SkipNode


def texinfo_visit_math(self, node):
    self.body.append('@math{' + self.escape_arg(node['latex']) + '}')
    raise nodes.SkipNode


def texinfo_visit_displaymath(self, node):
    if node.get('label'):
        self.add_anchor(node['label'], node)
    self.body.append('\n\n@example\n%s\n@end example\n\n' %
                     self.escape_arg(node['latex']))


def texinfo_depart_displaymath(self, node):
    pass


def texinfo_visit_eqref(self, node):
    self.add_xref(node['docname'] + ':' + node['target'],
                  node['target'], node)
    raise nodes.SkipNode


def html_visit_eqref(self, node):
    self.body.append('<a href="#equation-%s">' % node['target'])


def html_depart_eqref(self, node):
    self.body.append('</a>')


def number_equations(app, doctree, docname):
    num = 0
    numbers = {}
    for node in doctree.traverse(displaymath):
        if node['label'] is not None:
            num += 1
            node['number'] = num
            numbers[node['label']] = num
        else:
            node['number'] = None
    for node in doctree.traverse(eqref):
        if node['target'] not in numbers:
            continue
        num = '(%d)' % numbers[node['target']]
        node[0] = nodes.Text(num, num)


def setup_math(app, htmlinlinevisitors, htmldisplayvisitors):
    app.add_node(math,
                 latex=(latex_visit_math, None),
                 text=(text_visit_math, None),
                 man=(man_visit_math, None),
                 texinfo=(texinfo_visit_math, None),
                 html=htmlinlinevisitors)
    app.add_node(displaymath,
                 latex=(latex_visit_displaymath, None),
                 text=(text_visit_displaymath, None),
                 man=(man_visit_displaymath, man_depart_displaymath),
                 texinfo=(texinfo_visit_displaymath, texinfo_depart_displaymath),
                 html=htmldisplayvisitors)
    app.add_node(eqref,
                 latex=(latex_visit_eqref, None),
                 text=(text_visit_eqref, None),
                 man=(man_visit_eqref, None),
                 texinfo=(texinfo_visit_eqref, None),
                 html=(html_visit_eqref, html_depart_eqref))
    app.add_role('math', math_role)
    app.add_role('eq', eq_role)
    app.add_directive('math', MathDirective)
    app.connect('doctree-resolved', number_equations)
    app.add_latex_package('amsfonts')
