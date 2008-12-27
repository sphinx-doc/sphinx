# -*- coding: utf-8 -*-
"""
    sphinx.ext.ifconfig
    ~~~~~~~~~~~~~~~~~~~

    Provides the ``ifconfig`` directive that allows to write documentation
    that is included depending on configuration variables.

    Usage::

        .. ifconfig:: releaselevel in ('alpha', 'beta', 'rc')

           This stuff is only included in the built docs for unstable versions.

    The argument for ``ifconfig`` is a plain Python expression, evaluated in the
    namespace of the project configuration (that is, all variables from ``conf.py``
    are available.)

    :copyright: 2008 by Georg Brandl.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes


class ifconfig(nodes.Element): pass


def ifconfig_directive(name, arguments, options, content, lineno,
                       content_offset, block_text, state, state_machine):
    node = ifconfig()
    node.line = lineno
    node['expr'] = arguments[0]
    state.nested_parse(content, content_offset, node)
    return [node]


def process_ifconfig_nodes(app, doctree, docname):
    ns = app.config.__dict__.copy()
    ns['builder'] = app.builder.name
    for node in doctree.traverse(ifconfig):
        try:
            res = eval(node['expr'], ns)
        except Exception, err:
            # handle exceptions in a clean fashion
            from traceback import format_exception_only
            msg = ''.join(format_exception_only(err.__class__, err))
            newnode = doctree.reporter.error('Exception occured in '
                                             'ifconfig expression: \n%s' %
                                             msg, base_node=node)
            node.replace_self(newnode)
        else:
            if not res:
                node.replace_self([])
            else:
                node.replace_self(node.children)


def setup(app):
    app.add_node(ifconfig)
    app.add_directive('ifconfig', ifconfig_directive, 1, (1, 0, 1))
    app.connect('doctree-resolved', process_ifconfig_nodes)
