# -*- coding: utf-8 -*-
r"""
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

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
import inspect
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from six import text_type
from six.moves import builtins

from docutils import nodes
from docutils.parsers.rst import directives

import sphinx
from sphinx.ext.graphviz import render_dot_html, render_dot_latex, \
    render_dot_texinfo
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import force_decode
from sphinx.util.compat import Directive

import collections
import collections.abc


class GraphNode(object):
    def __init__(self, data=None, names_in=None, names_out=None):
        self.data = data
        self.names_in = set(names_in or [])
        self.names_out = set(names_out or [])

    def empty(self):
        return\
            (   self.data is None
            and not node.names_in
            and not node.names_out
            )

    def __str__(self):
        return "<{}|..|{}>".format(self.names_in, self.names_out)


class Graph(object):
    """
    Simple structure representing arbitrary connections
    """

    def __init__(self):
        self.names = dict()
        self.roots = set()

    def node_add(self, data, name, names_in=None, names_out=None):
        if name in self.names:
            node = self.names[name]
            node.names_in |= set(names_in or [])
            node.names_out |= set(names_out or [])
            node.data = data
        else:
            node = GraphNode(data, names_in, names_out)
            self.names[name] = node
        if not node.names_in:
            self.roots.add(name)
        for name_in in node.names_in:
            node_in = self.names.setdefault(name_in, GraphNode())
            node_in.names_out.add(name)
            if not node_in.names_in:
                self.roots.add(name_in)
        for name_out in node.names_out:
            node_out = self.names.setdefault(name_out, GraphNode())
            node_out.names_in.add(name)
            self.roots.discard(name_out)

    def node_iterate(self, name, selector):
        cache = set()
        def node_iterate(name, selector):
            node = self.names[name]
            if node not in cache:
                cache.add(node)
                yield (name, node)
                for name in selector(node):
                    yield from node_iterate(name, selector)
        yield from node_iterate(name, selector)

    @staticmethod
    def node_filter(node_iter, matcher):
        for name, node in node_iter:
            if matcher(name, node):
                yield(name, node)

    def node_delete(self, name, preserve_links=False):
        node = self.names.pop(name)
        self.roots.discard(name)
        # unlink
        for name_in in node.names_in:
            self.names[name_in].names_out.remove(name)
        for name_out in node.names_out:
            self.names[name_out].names_in.remove(name)
        # relink
        if preserve_links:
            for name_in in node.names_in:
                for name_out in node.names_out:
                    self.names[name_out].names_in.add(name_in)
                    self.names[name_in].names_out.add(name_out)
        # delete empty placeholders
        for name in node.names_in | node.names_out:
            if self.names[name].empty():
                self.node_delete(name)
        # recreate roots
        for name_out in node.names_out:
            if not self.names[name_out].names_in:
                self.roots.add(name_out)

    def children(self, *names):
        if not names:
            names = self.roots
        cache = set()
        selector = lambda v: v.names_out
        for name_root in names:
            for name, node in self.node_iterate(name, selector):
                if node not in cache:
                    cache.add(node)
                    yield (name, node)

    @property
    def names_data(self):
        return\
            { name:node
              for name, node
              in self.names.items()
              if node.data is not None
            }

    def __len__(self):
        return len(self.names_data)


class_sig_re = re.compile(r'''^([\w.]*\.)?    # module names
                          (\w+)  \s* $        # class/final module name
                          ''', re.VERBOSE)


ClassInfo = collections.namedtuple\
    ( "ClassInfo"
    , ["cls", "fullname", "baselist", "tooltip"]
    )


class InheritanceException(Exception):
    pass


class InheritanceGraph(object):
    """
    Given a list of classes, determines the set of classes that they inherit
    from all the way to the root "object", and then is able to generate a
    graphviz dot graph from them.
    """
    def __init__(self, class_names, currmodule, show_builtins=False,
                 private_bases=False, parts=0):
        """*class_names* is a list of child classes to show bases from.

        If *show_builtins* is True, then Python builtins will be shown
        in the graph.
        """
        self.class_names = class_names
        classes = self._import_classes(class_names, currmodule)
        self.class_info = self._class_info(classes, show_builtins,
                                           private_bases, parts)
        if not self.class_info:
            raise InheritanceException('No classes found for '
                                       'inheritance diagram')

    def _import_class_or_module(self, name, currmodule):
        """Import a class using its fully-qualified *name*."""
        try:
            path, base = class_sig_re.match(name).groups()
        except (AttributeError, ValueError):
            raise InheritanceException('Invalid class or module %r specified '
                                       'for inheritance diagram' % name)

        fullname = (path or '') + base
        path = (path and path.rstrip('.') or '')

        # two possibilities: either it is a module, then import it
        try:
            __import__(fullname)
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
                __import__(path)
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
        """Import a list of classes."""
        classes = []
        for name in class_names:
            classes.extend(self._import_class_or_module(name, currmodule))
        return classes

    def _class_info(self, classes, show_builtins, private_bases, parts):
        """Return name and bases for all classes that are ancestors of
        *classes*.

        *parts* gives the number of dotted name parts that is removed from the
        displayed node names.
        """
        py_builtins = vars(builtins).values()
        graph = Graph()
        cache = set()
        marks = list()

        def recurse(cls):
            cache.add(cls)

            nodename = self.class_name(cls, parts)
            fullname = self.class_name(cls, 0)

            # Use first line of docstring as tooltip, if available
            tooltip = None
            try:
                if cls.__doc__:
                    enc = ModuleAnalyzer.for_module(cls.__module__).encoding
                    doc = cls.__doc__.strip().split("\n")[0]
                    if not isinstance(doc, text_type):
                        doc = force_decode(doc, enc)
                    if doc:
                        tooltip = '"%s"' % doc.replace('"', '\\"')
            except Exception:  # might raise AttributeError for strange classes
                pass

            baselist = [self.class_name(base, parts) for base in cls.__bases__]

            graph.node_add\
                ( ClassInfo(cls, fullname, baselist, tooltip)
                , nodename, baselist
                )

            for base in cls.__bases__:
                if base not in cache:
                    recurse(base)

        for cls in classes:
            recurse(cls)

        for name, node in graph.names.items():
            if not node.data:
                marks.append(name)
                continue
            if  (   (   node.data.cls in py_builtins
                    and node.data.cls not in classes
                    and not show_builtins
                    )
                or  (   node.data.cls.__name__.startswith("_")
                    and node.data.cls not in classes
                    and not private_bases
                    )
                ):
                marks.append(name)

        for name in marks:
            if name in graph.names:
                graph.node_delete(name, preserve_links=True)

        return graph

    def class_name(self, cls, parts=0):
        """Given a class object, return a fully-qualified name.

        This works for things I've tested in matplotlib so far, but may not be
        completely general.
        """
        module = cls.__module__
        if module in ('__builtin__', 'builtins'):
            fullname = cls.__name__
        else:
            fullname = '%s.%s' % (module, cls.__name__)
        if parts == 0:
            return fullname
        name_parts = fullname.split('.')
        return '.'.join(name_parts[-parts:])

    def get_all_class_names(self):
        """Get all of the class names involved in the graph."""
        return\
            [ node.data.fullname
              for node
              in self.class_info.names.values()
              if node.data is not None
            ]

    # These are the default attrs for graphviz
    default_graph_attrs = {
        'rankdir': 'LR',
        'size': '"8.0, 12.0"',
    }
    default_node_attrs = {
        'shape': 'box',
        'fontsize': 10,
        'height': 0.25,
        'fontname': '"Vera Sans, DejaVu Sans, Liberation Sans, '
                    'Arial, Helvetica, sans"',
        'style': [ 'setlinewidth(0.5)' ],
    }
    default_edge_attrs = {
        'arrowsize': 0.5,
        'style': [ 'setlinewidth(0.5)' ],
    }
    builtin_node_attrs = {
        'style': [ 'dashed' ],
    }
    express_edge_attrs = {
        'style': [ 'dotted' ],
    }

    def _attr_merge(self, *args):
        merged = {}
        for attribute in args:
            for k,v in attribute.items():
                if  (   k in merged
                    and all(    (   isinstance(i, collections.abc.Iterable)
                                and not isinstance(i, str)
                                )
                                for i
                                in (v, merged[k])
                            )
                    ):
                    v = list(merged[k]) + list(v)
                merged[k] = v
        return merged

    def _attr_format(self, attrs, sep=","):
        formatted = []
        for k,v in attrs.items():
            if isinstance(v, collections.abc.Iterable) and not isinstance(v, str):
                v = "\"" + ",".join(v) + "\""
            formatted.append("{}={}".format(k,v))
        return sep.join(formatted)

    def generate_dot(self, name, urls={}, env=None,
                     graph_attrs_default={},
                     node_attrs_default={}, node_attrs_builtin={},
                     edge_attrs_default={}, edge_attrs_express={}):
        """Generate a graphviz dot graph from the classes that were passed in
        to __init__.

        *name* is the name of the graph.

        *urls* is a dictionary mapping class names to HTTP URLs.

        *graph_attrs*, *node_attrs*, *edge_attrs* are dictionaries containing
        key/value pairs to pass on as graphviz properties.
        """
        py_builtins = vars(builtins).values()

        attrs_graph_default = self._attr_merge\
                ( self.default_graph_attrs
                , graph_attrs_default
                , env.config.inheritance_graph_attrs if env else {}
                )
        attrs_node_default = self._attr_merge\
                ( self.default_node_attrs
                , node_attrs_default
                , env.config.inheritance_node_attrs if env else {}
                )
        attrs_edge_default = self._attr_merge\
                ( self.default_edge_attrs
                , edge_attrs_default
                , env.config.inheritance_edge_attrs if env else {}
                )
        attrs_node_builtin = self._attr_merge\
                ( attrs_node_default
                , self.builtin_node_attrs
                , node_attrs_builtin
                , env.config.inheritance_node_attrs_builtin if env else {}
                )
        attrs_edge_express = self._attr_merge\
                ( attrs_edge_default
                , self.express_edge_attrs
                , edge_attrs_express
                , env.config.inheritance_edge_attrs_express if env else {}
                )

        res = []
        res.append('digraph %s {\n' % name)
        res.append(self._attr_format(attrs_graph_default, ";\n"))

        for name, node in self.class_info.names.items():
            bases_linked = node.names_in
            bases_actual = node.data.baselist
            cls = node.data.cls
            fullname = node.data.fullname
            tooltip = node.data.tooltip

            # Write the node
            if cls in py_builtins:
                attrs_node_current = attrs_node_builtin.copy()
            else:
                attrs_node_current = attrs_node_default.copy()
            if fullname in urls:
                attrs_node_current['URL'] = '"%s"' % urls[fullname]
            if tooltip:
                attrs_node_current['tooltip'] = tooltip
            res.append('  "{}" [{}];\n'.format\
                ( name
                , self._attr_format(attrs_node_current)
                ))

            # Write the edges
            for basename in bases_linked:
                if basename in bases_actual:
                    attrs_edge_current = attrs_edge_default
                else:
                    attrs_edge_current = attrs_edge_express
                res.append('  "{}" -> "{}" [{}];\n'.format\
                    ( basename
                    , name
                    , self._attr_format(attrs_edge_current)
                    ))

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
        'private-bases': directives.flag,
    }

    def run(self):
        node = inheritance_diagram()
        node.document = self.state.document
        env = self.state.document.settings.env
        class_names = self.arguments[0].split()
        class_role = env.get_domain('py').role('class')
        # Store the original content for use as a hash
        node['parts'] = self.options.get('parts', 0)
        node['content'] = ', '.join(class_names)

        # Create a graph starting with the list of classes
        try:
            graph = InheritanceGraph(
                class_names, env.ref_context.get('py:module'),
                parts=node['parts'],
                private_bases='private-bases' in self.options)
        except InheritanceException as err:
            return [node.document.reporter.warning(err.args[0],
                                                   line=self.lineno)]

        # Create xref nodes for each target of the graph's image map and
        # add them to the doc tree so that Sphinx can resolve the
        # references to real URLs later.  These nodes will eventually be
        # removed from the doctree after we're done with them.
        for name in graph.get_all_class_names():
            refnodes, x = class_role(
                'class', ':class:`%s`' % name, name, 0, self.state)
            node.extend(refnodes)
        # Store the graph object so we can use it to generate the
        # dot file later
        node['graph'] = graph
        return [node]


def get_graph_hash(node):
    encoded = (node['content'] + str(node['parts'])).encode('utf-8')
    return md5(encoded).hexdigest()[-10:]


def html_visit_inheritance_diagram(self, node):
    """
    Output the graph for HTML.  This will insert a PNG with clickable
    image map.
    """
    graph = node['graph']

    graph_hash = get_graph_hash(node)
    name = 'inheritance%s' % graph_hash

    # Create a mapping from fully-qualified class names to URLs.
    urls = {}
    for child in node:
        if child.get('refuri') is not None:
            urls[child['reftitle']] = child.get('refuri')
        elif child.get('refid') is not None:
            urls[child['reftitle']] = '#' + child.get('refid')

    dotcode = graph.generate_dot(name, urls, env=self.builder.env)
    render_dot_html(self, node, dotcode, [], 'inheritance', 'inheritance',
                    alt='Inheritance diagram of ' + node['content'])
    raise nodes.SkipNode


def latex_visit_inheritance_diagram(self, node):
    """
    Output the graph for LaTeX.  This will insert a PDF.
    """
    graph = node['graph']

    graph_hash = get_graph_hash(node)
    name = 'inheritance%s' % graph_hash

    dotcode = graph.generate_dot(name, env=self.builder.env,
                                 graph_attrs_default={'size': '"6.0,6.0"'})
    render_dot_latex(self, node, dotcode, [], 'inheritance')
    raise nodes.SkipNode


def texinfo_visit_inheritance_diagram(self, node):
    """
    Output the graph for Texinfo.  This will insert a PNG.
    """
    graph = node['graph']

    graph_hash = get_graph_hash(node)
    name = 'inheritance%s' % graph_hash

    dotcode = graph.generate_dot(name, env=self.builder.env,
                                 graph_attrs_default={'size': '"6.0,6.0"'})
    render_dot_texinfo(self, node, dotcode, [], 'inheritance')
    raise nodes.SkipNode


def skip(self, node):
    raise nodes.SkipNode


def setup(app):
    app.setup_extension('sphinx.ext.graphviz')
    app.add_node(
        inheritance_diagram,
        latex=(latex_visit_inheritance_diagram, None),
        html=(html_visit_inheritance_diagram, None),
        text=(skip, None),
        man=(skip, None),
        texinfo=(texinfo_visit_inheritance_diagram, None))
    app.add_directive('inheritance-diagram', InheritanceDiagram)
    app.add_config_value('inheritance_graph_attrs', {}, False),
    app.add_config_value('inheritance_node_attrs', {}, False),
    app.add_config_value('inheritance_edge_attrs', {}, False),
    app.add_config_value('inheritance_node_attrs_builtin', {}, False),
    app.add_config_value('inheritance_edge_attrs_express', {}, False),
    return {'version': sphinx.__version__, 'parallel_read_safe': True}
