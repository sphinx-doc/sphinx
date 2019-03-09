"""
    sphinx.ext.todo
    ~~~~~~~~~~~~~~~

    Allow todos to be inserted into your documentation.  Inclusion of todos can
    be switched of by a configuration variable.  The todolist directive collects
    all todos of your project and lists them along with a backlink to the
    original location.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import cast

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.admonitions import BaseAdmonition

import sphinx
from sphinx.errors import NoUri
from sphinx.locale import _, __
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_refnode
from sphinx.util.texescape import tex_escape_map

if False:
    # For type annotation
    from typing import Any, Dict, Iterable, List, Tuple  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA
    from sphinx.writers.html import HTMLTranslator  # NOQA
    from sphinx.writers.latex import LaTeXTranslator  # NOQA

logger = logging.getLogger(__name__)


class todo_node(nodes.Admonition, nodes.Element):
    pass


class todolist(nodes.General, nodes.Element):
    pass


class Todo(BaseAdmonition, SphinxDirective):
    """
    A todo entry, displayed (if configured) in the form of an admonition.
    """

    node_class = todo_node
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'class': directives.class_option,
        'name': directives.unchanged,
    }

    def run(self):
        # type: () -> List[nodes.Node]
        if not self.options.get('class'):
            self.options['class'] = ['admonition-todo']

        (todo,) = super().run()  # type: Tuple[nodes.Node]
        if isinstance(todo, nodes.system_message):
            return [todo]
        elif isinstance(todo, todo_node):
            todo.insert(0, nodes.title(text=_('Todo')))
            self.add_name(todo)
            self.set_source_info(todo)
            self.state.document.note_explicit_target(todo)
            return [todo]
        else:
            raise RuntimeError  # never reached here


def process_todos(app, doctree):
    # type: (Sphinx, nodes.document) -> None
    # collect all todos in the environment
    # this is not done in the directive itself because it some transformations
    # must have already been run, e.g. substitutions
    env = app.builder.env
    if not hasattr(env, 'todo_all_todos'):
        env.todo_all_todos = []  # type: ignore
    for node in doctree.traverse(todo_node):
        app.events.emit('todo-defined', node)

        newnode = node.deepcopy()
        newnode['ids'] = []
        env.todo_all_todos.append({  # type: ignore
            'docname': env.docname,
            'source': node.source or env.doc2path(env.docname),
            'lineno': node.line,
            'todo': newnode,
            'target': node['ids'][0],
        })

        if env.config.todo_emit_warnings:
            label = cast(nodes.Element, node[1])
            logger.warning(__("TODO entry found: %s"), label.astext(),
                           location=node)


class TodoList(SphinxDirective):
    """
    A list of all todo entries.
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}  # type: Dict

    def run(self):
        # type: () -> List[nodes.Node]
        # Simply insert an empty todolist node which will be replaced later
        # when process_todo_nodes is called
        return [todolist('')]


def process_todo_nodes(app, doctree, fromdocname):
    # type: (Sphinx, nodes.document, str) -> None
    node = None  # type: nodes.Element
    if not app.config['todo_include_todos']:
        for node in doctree.traverse(todo_node):
            node.parent.remove(node)

    # Replace all todolist nodes with a list of the collected todos.
    # Augment each todo with a backlink to the original location.
    env = app.builder.env

    if not hasattr(env, 'todo_all_todos'):
        env.todo_all_todos = []  # type: ignore

    for node in doctree.traverse(todolist):
        if node.get('ids'):
            content = [nodes.target()]  # type: List[nodes.Element]
        else:
            content = []

        if not app.config['todo_include_todos']:
            node.replace_self(content)
            continue

        for todo_info in env.todo_all_todos:  # type: ignore
            para = nodes.paragraph(classes=['todo-source'])
            if app.config['todo_link_only']:
                description = _('<<original entry>>')
            else:
                description = (
                    _('(The <<original entry>> is located in %s, line %d.)') %
                    (todo_info['source'], todo_info['lineno'])
                )
            desc1 = description[:description.find('<<')]
            desc2 = description[description.find('>>') + 2:]
            para += nodes.Text(desc1, desc1)

            # Create a reference
            innernode = nodes.emphasis(_('original entry'), _('original entry'))
            try:
                para += make_refnode(app.builder, fromdocname, todo_info['docname'],
                                     todo_info['target'], innernode)
            except NoUri:
                # ignore if no URI can be determined, e.g. for LaTeX output
                pass
            para += nodes.Text(desc2, desc2)

            todo_entry = todo_info['todo']

            # (Recursively) resolve references in the todo content
            env.resolve_references(todo_entry, todo_info['docname'],
                                   app.builder)

            # Insert into the todolist
            content.append(todo_entry)
            content.append(para)

        node.replace_self(content)


def purge_todos(app, env, docname):
    # type: (Sphinx, BuildEnvironment, str) -> None
    if not hasattr(env, 'todo_all_todos'):
        return
    env.todo_all_todos = [todo for todo in env.todo_all_todos  # type: ignore
                          if todo['docname'] != docname]


def merge_info(app, env, docnames, other):
    # type: (Sphinx, BuildEnvironment, Iterable[str], BuildEnvironment) -> None
    if not hasattr(other, 'todo_all_todos'):
        return
    if not hasattr(env, 'todo_all_todos'):
        env.todo_all_todos = []  # type: ignore
    env.todo_all_todos.extend(other.todo_all_todos)  # type: ignore


def visit_todo_node(self, node):
    # type: (HTMLTranslator, todo_node) -> None
    self.visit_admonition(node)


def depart_todo_node(self, node):
    # type: (HTMLTranslator, todo_node) -> None
    self.depart_admonition(node)


def latex_visit_todo_node(self, node):
    # type: (LaTeXTranslator, todo_node) -> None
    self.body.append('\n\\begin{sphinxadmonition}{note}{')
    self.body.append(self.hypertarget_to(node))
    title_node = cast(nodes.title, node[0])
    self.body.append('%s:}' % title_node.astext().translate(tex_escape_map))
    node.pop(0)


def latex_depart_todo_node(self, node):
    # type: (LaTeXTranslator, todo_node) -> None
    self.body.append('\\end{sphinxadmonition}\n')


def setup(app):
    # type: (Sphinx) -> Dict[str, Any]
    app.add_event('todo-defined')
    app.add_config_value('todo_include_todos', False, 'html')
    app.add_config_value('todo_link_only', False, 'html')
    app.add_config_value('todo_emit_warnings', False, 'html')

    app.add_node(todolist)
    app.add_node(todo_node,
                 html=(visit_todo_node, depart_todo_node),
                 latex=(latex_visit_todo_node, latex_depart_todo_node),
                 text=(visit_todo_node, depart_todo_node),
                 man=(visit_todo_node, depart_todo_node),
                 texinfo=(visit_todo_node, depart_todo_node))

    app.add_directive('todo', Todo)
    app.add_directive('todolist', TodoList)
    app.connect('doctree-read', process_todos)
    app.connect('doctree-resolved', process_todo_nodes)
    app.connect('env-purge-doc', purge_todos)
    app.connect('env-merge-info', merge_info)
    return {
        'version': sphinx.__display_version__,
        'env_version': 1,
        'parallel_read_safe': True
    }
