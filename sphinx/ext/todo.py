# -*- coding: utf-8 -*-
"""
    sphinx.ext.todo
    ~~~~~~~~~~~~~~~

    Allow todos to be inserted into your documentation.  Inclusion of todos can
    be switched of by a configuration variable.  The todolist directive collects
    all todos of your project and lists them along with a backlink to the
    original location.

    :copyright: 2008 Daniel Bültmann.
    :license: BSD.
"""

from docutils import nodes

from sphinx.util.compat import make_admonition

class todo_node(nodes.Admonition, nodes.Element): pass
class todolist(nodes.General, nodes.Element): pass


def todo_directive(name, arguments, options, content, lineno,
                   content_offset, block_text, state, state_machine):
    env = state.document.settings.env

    targetid = "todo-%s" % env.index_num
    env.index_num += 1
    targetnode = nodes.target('', '', ids=[targetid])

    ad = make_admonition(todo_node, name, [_('Todo')], options, content, lineno,
                         content_offset, block_text, state, state_machine)

    # Attach a list of all todos to the environment,
    # the todolist works with the collected todo nodes
    if not hasattr(env, 'todo_all_todos'):
        env.todo_all_todos = []
    env.todo_all_todos.append({
        'docname': env.docname,
        'lineno': lineno,
        'todo': ad[0].deepcopy(),
        'target': targetnode,
    })

    return [targetnode] + ad


def todolist_directive(name, arguments, options, content, lineno,
                       content_offset, block_text, state, state_machine):
    # Simply insert an empty todolist node which will be replaced later
    # when process_todo_nodes is called
    return [todolist('')]


def process_todo_nodes(app, doctree, fromdocname):
    if not app.config['todo_include_todos']:
        for node in doctree.traverse(todo_node):
            node.parent.remove(node)

    # Replace all todolist nodes with a list of the collected todos.
    # Augment each todo with a backlink to the original location.
    env = app.builder.env

    for node in doctree.traverse(todolist):
        if not app.config['todo_include_todos']:
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


def purge_todos(app, env, docname):
    if not hasattr(env, 'todo_all_todos'):
        return
    env.todo_all_todos = [todo for todo in env.todo_all_todos
                          if todo['docname'] != docname]


def visit_todo_node(self, node):
    self.visit_admonition(node)

def depart_todo_node(self, node):
    self.depart_admonition(node)

def setup(app):
    app.add_config_value('todo_include_todos', False, False)

    app.add_node(todolist)
    app.add_node(todo_node,
                 html=(visit_todo_node, depart_todo_node),
                 latex=(visit_todo_node, depart_todo_node),
                 text=(visit_todo_node, depart_todo_node))

    app.add_directive('todo', todo_directive, 1, (0, 0, 1))
    app.add_directive('todolist', todolist_directive, 0, (0, 0, 0))
    app.connect('doctree-resolved', process_todo_nodes)
    app.connect('env-purge-doc', purge_todos)

