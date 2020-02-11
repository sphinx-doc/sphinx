"""
    sphinx.ext.todo
    ~~~~~~~~~~~~~~~

    Allow todos to be inserted into your documentation.  Inclusion of todos can
    be switched of by a configuration variable.  The todolist directive collects
    all todos of your project and lists them along with a backlink to the
    original location.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings
from typing import Any, Dict, Iterable, List, Tuple
from typing import cast

from docutils import nodes
from docutils.nodes import Element, Node
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.admonitions import BaseAdmonition

import sphinx
from sphinx.application import Sphinx
from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.domains import Domain
from sphinx.environment import BuildEnvironment
from sphinx.errors import NoUri
from sphinx.locale import _, __
from sphinx.util import logging, texescape
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_refnode
from sphinx.writers.html import HTMLTranslator
from sphinx.writers.latex import LaTeXTranslator

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

    def run(self) -> List[Node]:
        if not self.options.get('class'):
            self.options['class'] = ['admonition-todo']

        (todo,) = super().run()  # type: Tuple[Node]
        if isinstance(todo, nodes.system_message):
            return [todo]
        elif isinstance(todo, todo_node):
            todo.insert(0, nodes.title(text=_('Todo')))
            todo['docname'] = self.env.docname
            self.add_name(todo)
            self.set_source_info(todo)
            self.state.document.note_explicit_target(todo)
            return [todo]
        else:
            raise RuntimeError  # never reached here


class TodoDomain(Domain):
    name = 'todo'
    label = 'todo'

    @property
    def todos(self) -> Dict[str, List[todo_node]]:
        return self.data.setdefault('todos', {})

    def clear_doc(self, docname: str) -> None:
        self.todos.pop(docname, None)

    def merge_domaindata(self, docnames: List[str], otherdata: Dict) -> None:
        for docname in docnames:
            self.todos[docname] = otherdata['todos'][docname]

    def process_doc(self, env: BuildEnvironment, docname: str,
                    document: nodes.document) -> None:
        todos = self.todos.setdefault(docname, [])
        for todo in document.traverse(todo_node):
            env.app.emit('todo-defined', todo)
            todos.append(todo)

            if env.config.todo_emit_warnings:
                logger.warning(__("TODO entry found: %s"), todo[1].astext(),
                               location=todo)


def process_todos(app: Sphinx, doctree: nodes.document) -> None:
    warnings.warn('process_todos() is deprecated.', RemovedInSphinx40Warning)
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

    def run(self) -> List[Node]:
        # Simply insert an empty todolist node which will be replaced later
        # when process_todo_nodes is called
        return [todolist('')]


class TodoListProcessor:
    def __init__(self, app: Sphinx, doctree: nodes.document, docname: str) -> None:
        self.builder = app.builder
        self.config = app.config
        self.env = app.env
        self.domain = cast(TodoDomain, app.env.get_domain('todo'))

        self.process(doctree, docname)

    def process(self, doctree: nodes.document, docname: str) -> None:
        todos = sum(self.domain.todos.values(), [])  # type: List[todo_node]
        for node in doctree.traverse(todolist):
            if not self.config.todo_include_todos:
                node.parent.remove(node)
                continue

            if node.get('ids'):
                content = [nodes.target()]  # type: List[Element]
            else:
                content = []

            for todo in todos:
                # Create a copy of the todo node
                new_todo = todo.deepcopy()
                new_todo['ids'].clear()

                # (Recursively) resolve references in the todo content
                self.env.resolve_references(new_todo, todo['docname'], self.builder)  # type: ignore  # NOQA
                content.append(new_todo)

                todo_ref = self.create_todo_reference(todo, docname)
                content.append(todo_ref)

            node.replace_self(content)

    def create_todo_reference(self, todo: todo_node, docname: str) -> nodes.paragraph:
        if self.config.todo_link_only:
            description = _('<<original entry>>')
        else:
            description = (_('(The <<original entry>> is located in %s, line %d.)') %
                           (todo.source, todo.line))

        prefix = description[:description.find('<<')]
        suffix = description[description.find('>>') + 2:]

        para = nodes.paragraph(classes=['todo-source'])
        para += nodes.Text(prefix, prefix)

        # Create a reference
        linktext = nodes.emphasis(_('original entry'), _('original entry'))
        reference = nodes.reference('', '', linktext, internal=True)
        try:
            reference['refuri'] = self.builder.get_relative_uri(docname, todo['docname'])
            reference['refuri'] += '#' + todo['ids'][0]
        except NoUri:
            # ignore if no URI can be determined, e.g. for LaTeX output
            pass

        para += reference
        para += nodes.Text(suffix, suffix)

        return para


def process_todo_nodes(app: Sphinx, doctree: nodes.document, fromdocname: str) -> None:
    """Replace all todolist nodes with a list of the collected todos.
    Augment each todo with a backlink to the original location.
    """
    warnings.warn('process_todo_nodes() is deprecated.', RemovedInSphinx40Warning)

    domain = cast(TodoDomain, app.env.get_domain('todo'))
    todos = sum(domain.todos.values(), [])  # type: List[todo_node]

    for node in doctree.traverse(todolist):
        if node.get('ids'):
            content = [nodes.target()]  # type: List[Element]
        else:
            content = []

        if not app.config['todo_include_todos']:
            node.replace_self(content)
            continue

        for todo_info in todos:
            para = nodes.paragraph(classes=['todo-source'])
            if app.config['todo_link_only']:
                description = _('<<original entry>>')
            else:
                description = (
                    _('(The <<original entry>> is located in %s, line %d.)') %
                    (todo_info.source, todo_info.line)
                )
            desc1 = description[:description.find('<<')]
            desc2 = description[description.find('>>') + 2:]
            para += nodes.Text(desc1, desc1)

            # Create a reference
            innernode = nodes.emphasis(_('original entry'), _('original entry'))
            try:
                para += make_refnode(app.builder, fromdocname, todo_info['docname'],
                                     todo_info['ids'][0], innernode)
            except NoUri:
                # ignore if no URI can be determined, e.g. for LaTeX output
                pass
            para += nodes.Text(desc2, desc2)

            todo_entry = todo_info.deepcopy()
            todo_entry['ids'].clear()

            # (Recursively) resolve references in the todo content
            app.env.resolve_references(todo_entry, todo_info['docname'], app.builder)  # type: ignore  # NOQA

            # Insert into the todolist
            content.append(todo_entry)
            content.append(para)

        node.replace_self(content)


def purge_todos(app: Sphinx, env: BuildEnvironment, docname: str) -> None:
    warnings.warn('purge_todos() is deprecated.', RemovedInSphinx40Warning)
    if not hasattr(env, 'todo_all_todos'):
        return
    env.todo_all_todos = [todo for todo in env.todo_all_todos  # type: ignore
                          if todo['docname'] != docname]


def merge_info(app: Sphinx, env: BuildEnvironment, docnames: Iterable[str],
               other: BuildEnvironment) -> None:
    warnings.warn('merge_info() is deprecated.', RemovedInSphinx40Warning)
    if not hasattr(other, 'todo_all_todos'):
        return
    if not hasattr(env, 'todo_all_todos'):
        env.todo_all_todos = []  # type: ignore
    env.todo_all_todos.extend(other.todo_all_todos)  # type: ignore


def visit_todo_node(self: HTMLTranslator, node: todo_node) -> None:
    if self.config.todo_include_todos:
        self.visit_admonition(node)
    else:
        raise nodes.SkipNode


def depart_todo_node(self: HTMLTranslator, node: todo_node) -> None:
    self.depart_admonition(node)


def latex_visit_todo_node(self: LaTeXTranslator, node: todo_node) -> None:
    if self.config.todo_include_todos:
        self.body.append('\n\\begin{sphinxadmonition}{note}{')
        self.body.append(self.hypertarget_to(node))

        title_node = cast(nodes.title, node[0])
        title = texescape.escape(title_node.astext(), self.config.latex_engine)
        self.body.append('%s:}' % title)
        node.pop(0)
    else:
        raise nodes.SkipNode


def latex_depart_todo_node(self: LaTeXTranslator, node: todo_node) -> None:
    self.body.append('\\end{sphinxadmonition}\n')


def setup(app: Sphinx) -> Dict[str, Any]:
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
    app.add_domain(TodoDomain)
    app.connect('doctree-resolved', TodoListProcessor)
    return {
        'version': sphinx.__display_version__,
        'env_version': 2,
        'parallel_read_safe': True
    }
