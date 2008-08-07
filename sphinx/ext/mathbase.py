# -*- coding: utf-8 -*-
"""
    sphinx.ext.mathbase
    ~~~~~~~~~~~~~~~~~~~

    Set up math support in source files and LaTeX/text output.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

from docutils import nodes, utils
from docutils.parsers.rst import directives


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
        if label is not None and i == 0:
            ret.append('\\begin{split}%s\\end{split}' % part +
                       (label and '\\label{'+label+'}' or ''))
        else:
            ret.append('\\begin{split}%s\\end{split}\\notag' % part)
    return '\\begin{gather}\n' + '\\\\'.join(ret) + '\n\\end{gather}'


def math_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    latex = utils.unescape(text, restore_backslashes=True)
    return [math(latex=latex)], []

def eq_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    text = utils.unescape(text)
    node = eqref('(?)', '(?)', target=text)
    node['docname'] = inliner.document.settings.env.docname
    return [node], []

def math_directive(name, arguments, options, content, lineno,
                   content_offset, block_text, state, state_machine):
    latex = '\n'.join(content)
    if arguments and arguments[0]:
        latex = arguments[0] + '\n\n' + latex
    node = displaymath()
    node['latex'] = latex
    node['label'] = options.get('label', None)
    node['nowrap'] = 'nowrap' in options
    node['docname'] = state.document.settings.env.docname
    ret = [node]
    if node['label']:
        tnode = nodes.target('', '', ids=['equation-' + node['label']])
        state.document.note_explicit_target(tnode)
        ret.insert(0, tnode)
    return ret


def latex_visit_math(self, node):
    self.body.append('$' + node['latex'] + '$')
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


def setup(app, htmlinlinevisitors, htmldisplayvisitors):
    app.add_node(math,
                 latex=(latex_visit_math, None),
                 text=(text_visit_math, None),
                 html=htmlinlinevisitors)
    app.add_node(displaymath,
                 latex=(latex_visit_displaymath, None),
                 text=(text_visit_displaymath, None),
                 html=htmldisplayvisitors)
    app.add_node(eqref,
                 latex=(latex_visit_eqref, None),
                 text=(text_visit_eqref, None),
                 html=(html_visit_eqref, html_depart_eqref))
    app.add_role('math', math_role)
    app.add_role('eq', eq_role)
    app.add_directive('math', math_directive, 1, (0, 1, 1),
                      label=directives.unchanged, nowrap=directives.flag)
    app.connect('doctree-resolved', number_equations)
