from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective


class todo(nodes.Admonition, nodes.Element):
    pass


class todolist(nodes.General, nodes.Element):
    pass


def visit_todo_node(self, node):
    self.visit_admonition(node)


def depart_todo_node(self, node):
    self.depart_admonition(node)


class TodolistDirective(Directive):

    def run(self):
        return [todolist('')]


class TodoDirective(SphinxDirective):

    # this enables content in the directive
    has_content = True

    def run(self):
        targetid = 'todo-%d' % self.env.new_serialno('todo')
        targetnode = nodes.target('', '', ids=[targetid])

        todo_node = todo('\n'.join(self.content))
        todo_node += nodes.title(_('Todo'), _('Todo'))
        self.state.nested_parse(self.content, self.content_offset, todo_node)

        if not hasattr(self.env, 'todo_all_todos'):
            self.env.todo_all_todos = []

        self.env.todo_all_todos.append({
            'docname': self.env.docname,
            'lineno': self.lineno,
            'todo': todo_node.deepcopy(),
            'target': targetnode,
        })

        return [targetnode, todo_node]


def purge_todos(app, env, docname):
    if not hasattr(env, 'todo_all_todos'):
        return

    env.todo_all_todos = [todo for todo in env.todo_all_todos
                          if todo['docname'] != docname]


def merge_todos(app, env, docnames, other):
    if not hasattr(env, 'todo_all_todos'):
        env.todo_all_todos = []
    if hasattr(other, 'todo_all_todos'):
        env.todo_all_todos.extend(other.todo_all_todos)


def process_todo_nodes(app, doctree, fromdocname):
    if not app.config.todo_include_todos:
        for node in doctree.traverse(todo):
            node.parent.remove(node)

    # Replace all todolist nodes with a list of the collected todos.
    # Augment each todo with a backlink to the original location.
    env = app.builder.env

    if not hasattr(env, 'todo_all_todos'):
        env.todo_all_todos = []

    for node in doctree.traverse(todolist):
        if not app.config.todo_include_todos:
            node.replace_self([])
            continue

        content = []

        for todo_info in env.todo_all_todos:
            para = nodes.paragraph()
            filename = env.doc2path(todo_info['docname'], base=None)
            description = (
                _('(The original entry is located in %s, line %d and can be found ') %
                (filename, todo_info['lineno']))
            para += nodes.Text(description, description)

            # Create a reference
            newnode = nodes.reference('', '')
            innernode = nodes.emphasis(_('here'), _('here'))
            newnode['refdocname'] = todo_info['docname']
            newnode['refuri'] = app.builder.get_relative_uri(
                fromdocname, todo_info['docname'])
            newnode['refuri'] += '#' + todo_info['target']['refid']
            newnode.append(innernode)
            para += newnode
            para += nodes.Text('.)', '.)')

            # Insert into the todolist
            content.append(todo_info['todo'])
            content.append(para)

        node.replace_self(content)


def setup(app):
    app.add_config_value('todo_include_todos', False, 'html')

    app.add_node(todolist)
    app.add_node(todo,
                 html=(visit_todo_node, depart_todo_node),
                 latex=(visit_todo_node, depart_todo_node),
                 text=(visit_todo_node, depart_todo_node))

    app.add_directive('todo', TodoDirective)
    app.add_directive('todolist', TodolistDirective)
    app.connect('doctree-resolved', process_todo_nodes)
    app.connect('env-purge-doc', purge_todos)
    app.connect('env-merge-info', merge_todos)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
