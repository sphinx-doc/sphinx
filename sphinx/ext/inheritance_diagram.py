# -*- coding: utf-8 -*-
"""
    sphinx.ext.inheritance_diagram
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Defines a docutils directive for inserting inheritance diagrams.

    Provide the directive with one or more classes or modules (separated
    by whitespace).  For modules, all of the classes in that module will
    be used.

    Example::

       Given the following classes:

       class A: pass
       class B(A): pass
       class C(A): pass
       class D(B, C): pass
       class E(B): pass

       .. inheritance-diagram: D E

       Produces a graph like the following:

                   A
                  / \
                 B   C
                / \ /
               E   D

    The graph is inserted as a PNG+image map into HTML and a PDF in
    LaTeX.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
import inspect
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx.roles import xfileref_role
from sphinx.ext.graphviz import render_dot_html, render_dot_latex
from sphinx.util.compat import Directive


class_sig_re = re.compile(r'''^([\w.]*\.)?    # module names
                          (\w+)  \s* $        # class/final module name
                          ''', re.VERBOSE)


class InheritanceException(Exception):
    pass


class InheritanceGraph(object):
    """
    Given a list of classes, determines the set of classes that they inherit
    from all the way to the root "object", and then is able to generate a
    graphviz dot graph from them.
    """
    def __init__(self, class_names, currmodule, show_builtins=False):
        """
        *class_names* is a list of child classes to show bases from.

        If *show_builtins* is True, then Python builtins will be shown
        in the graph.
        """
        self.class_names = class_names
        self.classes = self._import_classes(class_names, currmodule)
        self.all_classes = self._all_classes(self.classes)
        if len(self.all_classes) == 0:
            raise InheritanceException('No classes found for '
                                       'inheritance diagram')
        self.show_builtins = show_builtins

    def _import_class_or_module(self, name, currmodule):
        """
        Import a class using its fully-qualified *name*.
        """
        try:
            path, base = class_sig_re.match(name).groups()
        except ValueError:
            raise InheritanceException('Invalid class or module %r specified '
                                       'for inheritance diagram' % name)

        fullname = (path or '') + base
        path = (path and path.rstrip('.') or '')

        # two possibilities: either it is a module, then import it
        try:
            module = __import__(fullname)
            todoc = sys.modules[fullname]
        except ImportError:
            # else it is a class, then import the module
            if not path:
                if currmodule:
                    # try the current module
                    path = currmodule
                else:
                    raise InheritanceException(
                        'Could not import class %r specified for '
                        'inheritance diagram' % base)
            try:
                module = __import__(path)
                todoc = getattr(sys.modules[path], base)
            except (ImportError, AttributeError):
                raise InheritanceException(
                    'Could not import class or module %r specified for '
                    'inheritance diagram' % (path + '.' + base))

        # If a class, just return it
        if inspect.isclass(todoc):
            return [todoc]
        elif inspect.ismodule(todoc):
            classes = []
            for cls in todoc.__dict__.values():
                if inspect.isclass(cls) and cls.__module__ == todoc.__name__:
                    classes.append(cls)
            return classes
        raise InheritanceException('%r specified for inheritance diagram is '
                                   'not a class or module' % name)

    def _import_classes(self, class_names, currmodule):
        """
        Import a list of classes.
        """
        classes = []
        for name in class_names:
            classes.extend(self._import_class_or_module(name, currmodule))
        return classes

    def _all_classes(self, classes):
        """
        Return a list of all classes that are ancestors of *classes*.
        """
        all_classes = {}

        def recurse(cls):
            all_classes[cls] = None
            for c in cls.__bases__:
                if c not in all_classes:
                    recurse(c)

        for cls in classes:
            recurse(cls)

        return all_classes.keys()

    def class_name(self, cls, parts=0):
        """
        Given a class object, return a fully-qualified name.  This
        works for things I've tested in matplotlib so far, but may not
        be completely general.
        """
        module = cls.__module__
        if module == '__builtin__':
            fullname = cls.__name__
        else:
            fullname = '%s.%s' % (module, cls.__name__)
        if parts == 0:
            return fullname
        name_parts = fullname.split('.')
        return '.'.join(name_parts[-parts:])

    def get_all_class_names(self):
        """
        Get all of the class names involved in the graph.
        """
        return [self.class_name(x) for x in self.all_classes]

    # These are the default attrs for graphviz
    default_graph_attrs = {
        'rankdir': 'LR',
        'size': '"8.0, 12.0"',
    }
    default_node_attrs = {
        'shape': 'box',
        'fontsize': 10,
        'height': 0.25,
        'fontname': 'Vera Sans, DejaVu Sans, Liberation Sans, '
                    'Arial, Helvetica, sans',
        'style': '"setlinewidth(0.5)"',
    }
    default_edge_attrs = {
        'arrowsize': 0.5,
        'style': '"setlinewidth(0.5)"',
    }

    def _format_node_attrs(self, attrs):
        return ','.join(['%s=%s' % x for x in attrs.items()])

    def _format_graph_attrs(self, attrs):
        return ''.join(['%s=%s;\n' % x for x in attrs.items()])

    def generate_dot(self, name, parts=0, urls={}, env=None,
                     graph_attrs={}, node_attrs={}, edge_attrs={}):
        """
        Generate a graphviz dot graph from the classes that
        were passed in to __init__.

        *name* is the name of the graph.

        *urls* is a dictionary mapping class names to HTTP URLs.

        *graph_attrs*, *node_attrs*, *edge_attrs* are dictionaries containing
        key/value pairs to pass on as graphviz properties.
        """
        g_attrs = self.default_graph_attrs.copy()
        n_attrs = self.default_node_attrs.copy()
        e_attrs = self.default_edge_attrs.copy()
        g_attrs.update(graph_attrs)
        n_attrs.update(node_attrs)
        e_attrs.update(edge_attrs)
        if env:
            g_attrs.update(env.config.inheritance_graph_attrs)
            n_attrs.update(env.config.inheritance_node_attrs)
            e_attrs.update(env.config.inheritance_edge_attrs)

        res = []
        res.append('digraph %s {\n' % name)
        res.append(self._format_graph_attrs(g_attrs))

        for cls in self.all_classes:
            if not self.show_builtins and cls in __builtins__.values():
                continue

            name = self.class_name(cls, parts)

            # Write the node
            this_node_attrs = n_attrs.copy()
            url = urls.get(self.class_name(cls))
            if url is not None:
                this_node_attrs['URL'] = '"%s"' % url
            res.append('  "%s" [%s];\n' %
                       (name, self._format_node_attrs(this_node_attrs)))

            # Write the edges
            for base in cls.__bases__:
                if not self.show_builtins and base in __builtins__.values():
                    continue

                base_name = self.class_name(base, parts)
                res.append('  "%s" -> "%s" [%s];\n' %
                           (base_name, name,
                            self._format_node_attrs(e_attrs)))
        res.append('}\n')
        return ''.join(res)


class inheritance_diagram(nodes.General, nodes.Element):
    """
    A docutils node to use as a placeholder for the inheritance diagram.
    """
    pass


class InheritanceDiagram(Directive):
    """
    Run when the inheritance_diagram directive is first encountered.
    """
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'parts': directives.nonnegative_int,
    }

    def run(self):
        node = inheritance_diagram()
        node.document = self.state.document
        env = self.state.document.settings.env
        class_names = self.arguments[0].split()

        # Create a graph starting with the list of classes
        try:
            graph = InheritanceGraph(class_names, env.currmodule)
        except InheritanceException, err:
            return [node.document.reporter.warning(err.args[0],
                                                   line=self.lineno)]

        # Create xref nodes for each target of the graph's image map and
        # add them to the doc tree so that Sphinx can resolve the
        # references to real URLs later.  These nodes will eventually be
        # removed from the doctree after we're done with them.
        for name in graph.get_all_class_names():
            refnodes, x = xfileref_role(
                'class', ':class:`%s`' % name, name, 0, self.state)
            node.extend(refnodes)
        # Store the graph object so we can use it to generate the
        # dot file later
        node['graph'] = graph
        # Store the original content for use as a hash
        node['parts'] = self.options.get('parts', 0)
        node['content'] = ', '.join(class_names)
        return [node]


def get_graph_hash(node):
    return md5(node['content'] + str(node['parts'])).hexdigest()[-10:]


def html_visit_inheritance_diagram(self, node):
    """
    Output the graph for HTML.  This will insert a PNG with clickable
    image map.
    """
    graph = node['graph']
    parts = node['parts']

    graph_hash = get_graph_hash(node)
    name = 'inheritance%s' % graph_hash

    # Create a mapping from fully-qualified class names to URLs.
    urls = {}
    for child in node:
        if child.get('refuri') is not None:
            urls[child['reftitle']] = child.get('refuri')
        elif child.get('refid') is not None:
            urls[child['reftitle']] = '#' + child.get('refid')

    dotcode = graph.generate_dot(name, parts, urls, env=self.builder.env)
    render_dot_html(self, node, dotcode, [], 'inheritance', 'inheritance',
                    alt='Inheritance diagram of ' + node['content'])
    raise nodes.SkipNode


def latex_visit_inheritance_diagram(self, node):
    """
    Output the graph for LaTeX.  This will insert a PDF.
    """
    graph = node['graph']
    parts = node['parts']

    graph_hash = get_graph_hash(node)
    name = 'inheritance%s' % graph_hash

    dotcode = graph.generate_dot(name, parts, env=self.builder.env,
                                 graph_attrs={'size': '"6.0,6.0"'})
    render_dot_latex(self, node, dotcode, [], 'inheritance')
    raise nodes.SkipNode


def skip(self, node):
    raise nodes.SkipNode


def setup(app):
    app.setup_extension('sphinx.ext.graphviz')
    app.add_node(
        inheritance_diagram,
        latex=(latex_visit_inheritance_diagram, None),
        html=(html_visit_inheritance_diagram, None),
        text=(skip, None))
    app.add_directive('inheritance-diagram', InheritanceDiagram)
    app.add_config_value('inheritance_graph_attrs', {}, False),
    app.add_config_value('inheritance_node_attrs', {}, False),
    app.add_config_value('inheritance_edge_attrs', {}, False),
