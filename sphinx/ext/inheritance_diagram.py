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

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import builtins
import inspect
from importlib import import_module
from typing import Any, Dict, Iterable, List, Set, Optional
from typing import cast

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import directives

import sphinx
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.ext.graphviz import (
    graphviz, figure_wrapper,
    render_dot_html, render_dot_latex, render_dot_texinfo
)
from sphinx.util import md5
from sphinx.util.docutils import SphinxDirective
from sphinx.writers.html import HTMLTranslator
from sphinx.writers.latex import LaTeXTranslator
from sphinx.writers.texinfo import TexinfoTranslator


def try_import(objname: str) -> Any:
    """Import a module or an object using its fully-qualified *objname*.

    It supports nested objects
    """
    try:
        return import_module(objname)
    except TypeError:
        # Relative import
        return None
    except ImportError:
        elements = objname.split(".")
        if len(elements) < 2:
            return None

        for i in reversed(range(1, len(elements))):
            modname = ".".join(elements[0:i])
            try:
                module = import_module(modname)
                current = module
                for attrname in elements[i:]:
                    if hasattr(current, attrname):
                        current = getattr(current, attrname)
                else:
                    return current
            except ImportError:
                pass
        return None


def import_classes(name: str, module_name: str) -> List[Any]:
    """Import classes from it's *name* and it's *module_name*.

    *name* should be a relative name from *module_name* or
    a fully-qualified name.

    If the input identify a class, a list of this single class is returned.
    If the input identify a module, the list of the whole classes contained is
    returned. Else raises *InheritanceException*.
    """
    target = None

    # import class or module using module_name
    if module_name:
        target = try_import(module_name + '.' + name)

    # import class or module without module_name
    if target is None:
        target = try_import(name)

    if target is None:
        raise InheritanceException(
            'Could not import class or module %r specified for '
            'inheritance diagram' % name)

    if inspect.isclass(target):
        # If imported object is a class, just return it
        return [target]
    elif inspect.ismodule(target):
        # If imported object is a module, return classes defined on it
        classes = []
        for cls in target.__dict__.values():
            if inspect.isclass(cls) and cls.__module__ == target.__name__:
                classes.append(cls)
        return classes
    raise InheritanceException('%r specified for inheritance diagram is '
                               'not a class or module' % name)


class InheritanceException(Exception):
    """Exception raised if the extension as configured can't be used."""
    pass


class InheritanceGraph:
    """
    Given a list of classes, determines the set of classes that they inherit
    from all the way to the root "object", and then is able to generate a
    graphviz dot graph from them.
    """

    class Node:
        """Hold a class and it's relations with the other classes"""
        def __init__(self, cls):
            self.cls = cls
            self.based = set()  # type: Set[Any]
            self.derived = set()  # type: Set[Any]
            self.used = False

    def __init__(self, class_names: List[str], currmodule: str, show_builtins: bool = False,
                 private_bases: bool = False, parts: int = 0, aliases: Dict[str, str] = None,
                 top_classes: List[Any] = [], style: str = "default",
                 direction: Optional[str] = None) -> None:
        """*class_names* is a list of child classes to show bases from.

        *parts* gives the number of dotted name parts to include in the
        displayed node names, from right to left. If given as a negative, the
        number of parts to drop from the left. A value of 0 displays the full
        dotted name. E.g. ``sphinx.ext.inheritance_diagram.InheritanceGraph``
        with ``parts=2`` or ``parts=-2`` gets displayed as
        ``inheritance_diagram.InheritanceGraph``, and as
        ``ext.inheritance_diagram.InheritanceGraph`` with ``parts=3`` or
        ``parts=-1``.

        *top_classes* gives the name(s) of the top most ancestor class to
        traverse to. Multiple names can be specified.

        If *show_builtins* is True, then Python builtins will be shown
        in the graph.
        """
        self.parts = parts
        self.aliases = aliases
        self.class_names = class_names
        self.diagram_style = style
        self.diagram_direction = direction
        self.show_builtins = show_builtins
        self.private_bases = private_bases
        self.classes = self._import_classes(class_names, currmodule)
        self.top_classes = self._import_classes(top_classes, currmodule)

        # Create the whole relationships
        self.class_dag = {}  # type: Dict[Any, InheritanceGraph.Node]
        for c in self.classes:
            self._add_class(c)

        # Flag the classes to finally use
        if not self.top_classes:
            for _cls, node in self.class_dag.items():
                node.used = True
        else:
            for top_class in self.top_classes:
                self._use_all_derived_classes(top_class)

        if not self.class_dag:
            raise InheritanceException('No classes found for '
                                       'inheritance diagram')

    def _import_classes(self, class_names: List[str], currmodule: str) -> List[Any]:
        """Import a list of classes."""
        classes = []  # type: List[Any]
        for name in class_names:
            classes.extend(import_classes(name, currmodule))
        return classes

    def _add_class(self, cls, force=False):
        """
        Add a new class to the DAG structure.

        If *force* is True, the node is added anyway there is filter. This is
        the case for an explicit user request.
        """
        if cls in self.class_dag:
            # Already known
            return

        # Is filtered by something
        if not force:
            if not self.show_builtins:
                py_builtins = vars(builtins).values()
                if cls in py_builtins:
                    return
            if not self.private_bases and cls.__name__.startswith('_'):
                return

        node = self.Node(cls)
        self.class_dag[cls] = node
        for base in cls.__bases__:
            if base not in self.class_dag:
                self._add_class(base)
            basenode = self.class_dag.get(base, None)
            if basenode is not None:
                node.based.add(base)
                basenode.derived.add(cls)

    def _use_all_derived_classes(self, cls):
        """Flag all the known derived classes from the **cls** class."""
        if cls not in self.class_dag:
            # A top class without classes interest specified
            # Skip it
            return
        visiting = [cls]
        while visiting:
            cls = visiting.pop()
            node = self.class_dag[cls]
            if node.used:
                continue
            node.used = True
            visiting.extend(node.derived)

    def full_class_name(self, cls):
        """Returns the full class name from a class."""
        module = cls.__module__
        if module in (None, '__builtin__', 'builtins'):
            return cls.__name__
        else:
            return '%s.%s' % (module, cls.__qualname__)

    def class_name(self, cls: Any, parts: int = 0, aliases: Dict[str, str] = None) -> str:
        """Given a class object, return a fully-qualified name.

        This works for things I've tested in matplotlib so far, but may not be
        completely general.
        """
        fullname = self.full_class_name(cls)
        if parts == 0:
            result = fullname
        else:
            name_parts = fullname.split('.')
            result = '.'.join(name_parts[-parts:])
        if aliases is not None and result in aliases:
            return aliases[result]
        return result

    def get_all_class_names(self) -> List[str]:
        """Get all of the class names involved in the graph."""
        nodes = self.class_dag.values()
        return [self.class_name(n.cls, 0, self.aliases) for n in nodes if n.used]

    # These are the default attrs for graphviz
    default_graph_attrs = {
        'rankdir': 'LR',
        'size': '"8.0, 12.0"',
        'bgcolor': 'transparent',
    }
    default_node_attrs = {
        'shape': 'box',
        'fontsize': 10,
        'height': 0.25,
        'fontname': '"Vera Sans, DejaVu Sans, Liberation Sans, '
                    'Arial, Helvetica, sans"',
        'style': '"setlinewidth(0.5),filled"',
        'fillcolor': 'white',
    }
    default_edge_attrs = {
        'arrowsize': 0.5,
        'style': '"setlinewidth(0.5)"',
    }
    uml_edge_attrs = {
        'arrowsize': 0.8,
        'style': '"setlinewidth(0.5)"',
        'arrowtail': '"empty"',
        'arrowhead': '"none"',
        'dir': '"both"',
    }

    def _format_node_attrs(self, attrs: Dict) -> str:
        return ','.join(['%s=%s' % x for x in sorted(attrs.items())])

    def _format_graph_attrs(self, attrs: Dict) -> str:
        return ''.join(['%s=%s;\n' % x for x in sorted(attrs.items())])

    def _iter_used_classes(self):
        """Iter through all the used classes"""
        for node in self.class_dag.values():
            if node.used:
                yield node.cls

    def _iter_used_edges(self):
        """Iter through all the used edges"""
        for base in self.class_dag.values():
            if not base.used:
                continue
            for cls in base.derived:
                node = self.class_dag[cls]
                if not node.used:
                    continue
                yield base.cls, cls

    def generate_dot(self, name: str, urls: Dict = {},
                     env: BuildEnvironment = None, graph_attrs: Dict = {},
                     node_attrs: Dict = {}, edge_attrs: Dict = {}) -> str:
        """Generate a graphviz dot graph from the classes that were passed in
        to __init__.

        *name* is the name of the graph.

        *urls* is a dictionary mapping class names to HTTP URLs.

        *graph_attrs*, *node_attrs*, *edge_attrs* are dictionaries containing
        key/value pairs to pass on as graphviz properties.
        """
        g_attrs = self.default_graph_attrs.copy()
        n_attrs = self.default_node_attrs.copy()
        if self.diagram_style == "uml":
            e_attrs = self.uml_edge_attrs.copy()
        else:
            e_attrs = self.default_edge_attrs.copy()
        g_attrs.update(graph_attrs)
        n_attrs.update(node_attrs)
        e_attrs.update(edge_attrs)
        if env:
            g_attrs.update(env.config.inheritance_graph_attrs)
            n_attrs.update(env.config.inheritance_node_attrs)
            e_attrs.update(env.config.inheritance_edge_attrs)

        if self.diagram_direction is not None:
            rankdirs = {"left-right": "LR", "top-bottom": "TB"}
            rankdir = rankdirs[self.diagram_direction]
            g_attrs["rankdir"] = rankdir

        res = []  # type: List[str]
        res.append('digraph %s {' % name)
        res.append(self._format_graph_attrs(g_attrs))

        # Write the nodes
        for cls in self._iter_used_classes():
            nodename = self.class_name(cls, self.parts, self.aliases)
            fullname = self.class_name(cls, 0, self.aliases)
            # Use first line of docstring as tooltip, if available
            tooltip = None
            try:
                if cls.__doc__:
                    doc = cls.__doc__.strip().split("\n")[0]
                    if doc:
                        tooltip = '"%s"' % doc.replace('"', '\\"')
            except Exception:  # might raise AttributeError for strange classes
                pass

            # Write the node
            this_node_attrs = n_attrs.copy()
            if fullname in urls:
                this_node_attrs['URL'] = '"%s"' % urls[fullname]
                this_node_attrs['target'] = '"_top"'
            if tooltip:
                this_node_attrs['tooltip'] = tooltip
            this_node_attrs['label'] = '"%s"' % nodename

            full_class_name = self.full_class_name(cls)
            node_style = self._format_node_attrs(this_node_attrs)
            line = '  "%s" [%s];' % (full_class_name, node_style)
            res.append(line)

        # Write the edges
        edges_style = self._format_node_attrs(e_attrs)
        for basecls, cls in self._iter_used_edges():
            base_id = self.full_class_name(basecls)
            cls_id = self.full_class_name(cls)
            line = '  "%s" -> "%s" [%s];' % (base_id, cls_id, edges_style)
            res.append(line)

        res.append('}')
        dot = '\n'.join(res)
        return dot


class inheritance_diagram(graphviz):
    """
    A docutils node to use as a placeholder for the inheritance diagram.
    """
    pass


def style_spec(argument: Any) -> str:
    return directives.choice(argument, ('default', 'uml', None))


def direction_spec(argument: Any) -> str:
    return directives.choice(argument, ('left-right', 'top-bottom', None))


class InheritanceDiagram(SphinxDirective):
    """
    Run when the inheritance_diagram directive is first encountered.
    """
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'parts': int,
        'style': style_spec,
        'direction': direction_spec,
        'private-bases': directives.flag,
        'caption': directives.unchanged,
        'top-classes': directives.unchanged_required,
    }

    def run(self) -> List[Node]:
        node = inheritance_diagram()
        node.document = self.state.document
        class_names = self.arguments[0].split()
        class_role = self.env.get_domain('py').role('class')
        top_classes = self.options.get('top-classes', '').replace(',', ' ').split()

        # Store the original content for use as a hash
        node['parts'] = self.options.get('parts', 0)
        node['style'] = self.options.get('style', 'default')
        node['direction'] = self.options.get('direction', None)
        node['class_names'] = class_names
        node['top-classes'] = top_classes

        # Check style property validity
        available_styles = ['default', 'uml']
        if node['style'] not in available_styles:
            available_str = ", ".join(['"%s"' % s for s in available_styles])
            msg = ':style: property but be one of %s' % available_str
            return [node.document.reporter.warning(msg, line=self.lineno)]

        # Check direction property validity
        available_directions = ['left-right', 'top-bottom']
        if node['direction'] is not None and node['direction'] not in available_directions:
            available_str = ", ".join(['"%s"' % s for s in available_directions])
            msg = ':direction: property but be one of %s' % available_str
            return [node.document.reporter.warning(msg, line=self.lineno)]

        # Create a graph starting with the list of classes
        try:
            graph = InheritanceGraph(
                class_names, self.env.ref_context.get('py:module'),
                parts=node['parts'],
                style=node['style'],
                direction=node['direction'],
                private_bases='private-bases' in self.options,
                aliases=self.config.inheritance_alias,
                top_classes=node['top-classes'])
        except InheritanceException as err:
            return [node.document.reporter.warning(err, line=self.lineno)]

        # Create xref nodes for each target of the graph's image map and
        # add them to the doc tree so that Sphinx can resolve the
        # references to real URLs later.  These nodes will eventually be
        # removed from the doctree after we're done with them.
        for name in graph.get_all_class_names():
            refnodes, _x = class_role(  # type: ignore
                'class', ':class:`%s`' % name, name, 0, self.state)  # type: ignore
            node.extend(refnodes)
        # Store the graph object so we can use it to generate the
        # dot file later
        node['graph'] = graph

        if 'caption' not in self.options:
            self.add_name(node)
            return [node]
        else:
            figure = figure_wrapper(self, node, self.options['caption'])
            self.add_name(figure)
            return [figure]


def get_graph_hash(node: inheritance_diagram) -> str:
    encoded = (node['class_names'],
               node['top-classes'],
               node['style'],
               node['direction'],
               node['parts'])
    bencoded = str(encoded).encode()
    return md5(bencoded).hexdigest()[-10:]


def html_visit_inheritance_diagram(self: HTMLTranslator, node: inheritance_diagram) -> None:
    """
    Output the graph for HTML. This will insert a PNG with clickable
    image map.
    """
    graph = node['graph']

    graph_hash = get_graph_hash(node)
    name = 'inheritance%s' % graph_hash

    # Create a mapping from fully-qualified class names to URLs.
    graphviz_output_format = self.builder.env.config.graphviz_output_format.upper()
    current_filename = self.builder.current_docname + self.builder.out_suffix
    urls = {}
    pending_xrefs = cast(Iterable[addnodes.pending_xref], node)
    for child in pending_xrefs:
        if child.get('refuri') is not None:
            if graphviz_output_format == 'SVG':
                urls[child['reftitle']] = "../" + child.get('refuri')
            else:
                urls[child['reftitle']] = child.get('refuri')
        elif child.get('refid') is not None:
            if graphviz_output_format == 'SVG':
                urls[child['reftitle']] = '../' + current_filename + '#' + child.get('refid')
            else:
                urls[child['reftitle']] = '#' + child.get('refid')

    dotcode = graph.generate_dot(name, urls, env=self.builder.env)
    alt = 'Inheritance diagram of ' + ', '.join(node['class_names'])
    render_dot_html(self, node, dotcode, {}, 'inheritance', 'inheritance', alt=alt)
    raise nodes.SkipNode


def latex_visit_inheritance_diagram(self: LaTeXTranslator, node: inheritance_diagram) -> None:
    """
    Output the graph for LaTeX.  This will insert a PDF.
    """
    graph = node['graph']

    graph_hash = get_graph_hash(node)
    name = 'inheritance%s' % graph_hash

    dotcode = graph.generate_dot(name, env=self.builder.env,
                                 graph_attrs={'size': '"6.0,6.0"'})
    render_dot_latex(self, node, dotcode, {}, 'inheritance')
    raise nodes.SkipNode


def texinfo_visit_inheritance_diagram(self: TexinfoTranslator, node: inheritance_diagram
                                      ) -> None:
    """
    Output the graph for Texinfo.  This will insert a PNG.
    """
    graph = node['graph']

    graph_hash = get_graph_hash(node)
    name = 'inheritance%s' % graph_hash

    dotcode = graph.generate_dot(name, env=self.builder.env,
                                 graph_attrs={'size': '"6.0,6.0"'})
    render_dot_texinfo(self, node, dotcode, {}, 'inheritance')
    raise nodes.SkipNode


def skip(self: nodes.NodeVisitor, node: inheritance_diagram) -> None:
    raise nodes.SkipNode


def setup(app: Sphinx) -> Dict[str, Any]:
    app.setup_extension('sphinx.ext.graphviz')
    app.add_node(
        inheritance_diagram,
        latex=(latex_visit_inheritance_diagram, None),
        html=(html_visit_inheritance_diagram, None),
        text=(skip, None),
        man=(skip, None),
        texinfo=(texinfo_visit_inheritance_diagram, None))
    app.add_directive('inheritance-diagram', InheritanceDiagram)
    app.add_config_value('inheritance_graph_attrs', {}, False)
    app.add_config_value('inheritance_node_attrs', {}, False)
    app.add_config_value('inheritance_edge_attrs', {}, False)
    app.add_config_value('inheritance_alias', {}, False)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
