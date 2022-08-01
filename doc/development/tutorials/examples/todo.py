from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, List, TypedDict
from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment


class todo(nodes.Admonition, nodes.Element):  # type: ignore[misc]
    pass


class todolist(nodes.General, nodes.Element):  # type: ignore[misc]
    pass


@dataclass
class TodoInfo:
    """ToDo node information"""

    docname: str
    lineno: int
    todo: todo
    target: nodes.target


def visit_todo_node(self: nodes.GenericNodeVisitor, node: todo) -> None:
    self.visit_admonition(node)


def depart_todo_node(self: nodes.GenericNodeVisitor, node: todo) -> None:
    self.depart_admonition(node)


@contextmanager
def get_all_nodes(env: BuildEnvironment) -> Iterator[List[TodoInfo]]:
    all_nodes = getattr(env, "todo_all_todos", [])
    yield all_nodes
    env.todo_all_nodes = all_nodes  # type: ignore[attr-defined]


class TodolistDirective(Directive):
    def run(self) -> List[todolist]:
        return [todolist("")]


class TodoDirective(SphinxDirective):

    # this enables content in the directive
    has_content = True

    def run(self) -> List[nodes.Node]:
        targetid = "todo-%d" % self.env.new_serialno("todo")
        targetnode = nodes.target("", "", ids=[targetid])

        todo_node = todo("\n".join(self.content))
        todo_node += nodes.title(_("Todo"), _("Todo"))
        self.state.nested_parse(self.content, self.content_offset, todo_node)

        with get_all_nodes(self.env) as all_todos:
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
    with get_all_nodes(env) as all_todos:
        all_todos = [todo for todo in all_todos if todo.docname != docname]


def merge_todos(
    _app: Sphinx, env: BuildEnvironment, _docnames: List[str], other: BuildEnvironment
) -> None:
    with get_all_nodes(env) as all_todos, get_all_nodes(other) as other_todos:
        all_todos.extend(other_todos)


def process_todo_nodes(app: Sphinx, doctree: nodes.document, fromdocname: str) -> None:
    if not app.config.todo_include_todos:
        for node in doctree.findall(todo):
            node.parent.remove(node)  # type: ignore[union-attr]

    # Replace all todolist nodes with a list of the collected todos.
    # Augment each todo with a backlink to the original location.
    env = app.builder.env

    for node in doctree.findall(todolist):
        if not app.config.todo_include_todos:
            node.replace_self([])
            continue

        content = []

        with get_all_nodes(env) as all_todos:
            for todo_info in all_todos:
                para = nodes.paragraph()
                filename = env.doc2path(todo_info.docname, base=False)
                description = _(
                    "(The original entry is located in %s, line %d and can be found "
                ) % (filename, todo_info.lineno)
                para += nodes.Text(description)

                # Create a reference
                newnode = nodes.reference("", "")
                innernode = nodes.emphasis(_("here"), _("here"))
                newnode["refdocname"] = todo_info.docname
                newnode["refuri"] = app.builder.get_relative_uri(
                    fromdocname, todo_info.docname
                )
                newnode["refuri"] += "#" + todo_info.target["refid"]
                newnode.append(innernode)
                para += newnode
                para += nodes.Text(".)")

                # Insert into the todolist
                content.append(todo_info.todo)
                content.append(para)

        node.replace_self(content)


class ExtensionMetadata(TypedDict):
    """The metadata returned by this extension."""

    version: str
    env_version: int
    parallel_read_safe: bool
    parallel_write_safe: bool


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_config_value("todo_include_todos", False, "html")

    app.add_node(todolist)
    app.add_node(
        todo,
        html=(visit_todo_node, depart_todo_node),
        latex=(visit_todo_node, depart_todo_node),
        text=(visit_todo_node, depart_todo_node),
    )

    app.add_directive("todo", TodoDirective)
    app.add_directive("todolist", TodolistDirective)
    app.connect("doctree-resolved", process_todo_nodes)
    app.connect("env-purge-doc", purge_todos)
    app.connect("env-merge-info", merge_todos)

    return {
        "version": "0.1",
        "env_version": 0,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
