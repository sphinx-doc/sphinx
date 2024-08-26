from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, NamedTuple

from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence


class todo(nodes.Admonition, nodes.Element):
    pass


class todolist(nodes.General, nodes.Element):
    pass


class TodoInfo(NamedTuple):
    docname: str
    lineno: int
    todo: todo
    target: nodes.target


def visit_todo_node(self: nodes.GenericNodeVisitor, node: nodes.Node) -> None:
    self.visit_admonition(node)


def depart_todo_node(self: nodes.GenericNodeVisitor, node: nodes.Node) -> None:
    self.depart_admonition(node)


class TodolistDirective(Directive):
    def run(self) -> Sequence[nodes.Node]:
        return [todolist('')]


@contextmanager
def get_all_todos(env: BuildEnvironment) -> Iterator[list[TodoInfo]]:
    """A context manager for accessing plugin state stored in the build environment.

    This state should never be accessed directly, only using this helper method.

    Changes to the 'all_todos' list are saved back to the build environment once the context
    manager exits.
    """
    all_todos: list[TodoInfo] = getattr(env, '_todo_all_todos', [])
    yield all_todos
    env._todo_all_todos = all_todos  # type: ignore[attr-defined]


class TodoDirective(SphinxDirective):
    # this enables content in the directive
    has_content = True

    def run(self) -> Sequence[nodes.Node]:
        targetid = 'todo-%d' % self.env.new_serialno('todo')
        targetnode = nodes.target('', '', ids=[targetid])

        todo_node = todo('\n'.join(self.content))
        todo_node += nodes.title(_('Todo'), _('Todo'))
        todo_node += self.parse_content_to_nodes()

        with get_all_todos(self.env) as all_todos:
            all_todos.append(
                TodoInfo(
                    docname=self.env.docname,
                    lineno=self.lineno,
                    todo=todo_node.deepcopy(),
                    target=targetnode,
                )
            )

        return [targetnode, todo_node]


def purge_todos(_app: Sphinx, env: BuildEnvironment, docname: str) -> None:
    with get_all_todos(env) as all_todos:
        all_todos[:] = [todo for todo in all_todos if todo.docname != docname]


def merge_todos(
    _app: Sphinx, env: BuildEnvironment, _docnames: list[str], other: BuildEnvironment
) -> None:
    with get_all_todos(env) as all_todos, get_all_todos(other) as other_todos:
        all_todos.extend(other_todos)


def process_todo_nodes(app: Sphinx, doctree: nodes.document, fromdocname: str) -> None:
    if not app.config.todo_include_todos:
        for todo_node in doctree.findall(todo):
            todo_node.parent.remove(todo_node)

    # Replace all todolist nodes with a list of the collected todos.
    # Augment each todo with a backlink to the original location.
    env = app.builder.env

    with get_all_todos(env) as all_todos:
        for todolist_node in doctree.findall(todolist):
            if not app.config.todo_include_todos:
                todolist_node.replace_self([])
                continue

            content: list[nodes.Node] = []

            for todo_info in all_todos:
                para = nodes.paragraph()
                filename = env.doc2path(todo_info.docname, base=False)
                description = _(
                    '(The original entry is located in %s, line %d and can be found '
                ) % (filename, todo_info.lineno)
                para += nodes.Text(description)

                # Create a reference
                newnode = nodes.reference('', '')
                innernode = nodes.emphasis(_('here'), _('here'))
                newnode['refdocname'] = todo_info.docname
                newnode['refuri'] = app.builder.get_relative_uri(
                    fromdocname, todo_info.docname
                )
                newnode['refuri'] += '#' + todo_info.target['refid']
                newnode.append(innernode)
                para += newnode
                para += nodes.Text('.)')

                # Insert into the todolist
                content.extend((
                    todo_info.todo,
                    para,
                ))

            todolist_node.replace_self(content)


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_config_value('todo_include_todos', False, 'html')

    app.add_node(todolist)
    app.add_node(
        todo,
        html=(visit_todo_node, depart_todo_node),
        latex=(visit_todo_node, depart_todo_node),
        text=(visit_todo_node, depart_todo_node),
    )

    app.add_directive('todo', TodoDirective)
    app.add_directive('todolist', TodolistDirective)
    app.connect('doctree-resolved', process_todo_nodes)
    app.connect('env-purge-doc', purge_todos)
    app.connect('env-merge-info', merge_todos)

    return {
        'version': '0.1',
        'env_version': 1,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
