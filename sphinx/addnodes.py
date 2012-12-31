# -*- coding: utf-8 -*-
"""
    sphinx.addnodes
    ~~~~~~~~~~~~~~~

    Additional docutils nodes.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes


class toctree(nodes.General, nodes.Element):
    """Node for inserting a "TOC tree"."""


# domain-specific object descriptions (class, function etc.)

class desc(nodes.Admonition, nodes.Element):
    """Node for object descriptions.

    This node is similar to a "definition list" with one definition.  It
    contains one or more ``desc_signature`` and a ``desc_content``.
    """

class desc_signature(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for object signatures.

    The "term" part of the custom Sphinx definition list.
    """


# nodes to use within a desc_signature

class desc_addname(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for additional name parts (module name, class name)."""
# compatibility alias
desc_classname = desc_addname

class desc_type(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for return types or object type names."""

class desc_returns(desc_type):
    """Node for a "returns" annotation (a la -> in Python)."""
    def astext(self):
        return ' -> ' + nodes.TextElement.astext(self)

class desc_name(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for the main object name."""

class desc_parameterlist(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for a general parameter list."""
    child_text_separator = ', '

class desc_parameter(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for a single parameter."""

class desc_optional(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for marking optional parts of the parameter list."""
    child_text_separator = ', '
    def astext(self):
        return '[' + nodes.TextElement.astext(self) + ']'

class desc_annotation(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for signature annotations (not Python 3-style annotations)."""

class desc_content(nodes.General, nodes.Element):
    """Node for object description content.

    This is the "definition" part of the custom Sphinx definition list.
    """


# new admonition-like constructs

class versionmodified(nodes.Admonition, nodes.TextElement):
    """Node for version change entries.

    Currently used for "versionadded", "versionchanged" and "deprecated"
    directives.
    """

class seealso(nodes.Admonition, nodes.Element):
    """Custom "see also" admonition."""

class productionlist(nodes.Admonition, nodes.Element):
    """Node for grammar production lists.

    Contains ``production`` nodes.
    """

class production(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for a single grammar production rule."""


# other directive-level nodes

class index(nodes.Invisible, nodes.Inline, nodes.TextElement):
    """Node for index entries.

    This node is created by the ``index`` directive and has one attribute,
    ``entries``.  Its value is a list of 4-tuples of ``(entrytype, entryname,
    target, ignored)``.

    *entrytype* is one of "single", "pair", "double", "triple".
    """

class centered(nodes.Part, nodes.Element):
    """Deprecated."""

class acks(nodes.Element):
    """Special node for "acks" lists."""

class hlist(nodes.Element):
    """Node for "horizontal lists", i.e. lists that should be compressed to
    take up less vertical space.
    """

class hlistcol(nodes.Element):
    """Node for one column in a horizontal list."""

class compact_paragraph(nodes.paragraph):
    """Node for a compact paragraph (which never makes a <p> node)."""

class glossary(nodes.Element):
    """Node to insert a glossary."""

class only(nodes.Element):
    """Node for "only" directives (conditional inclusion based on tags)."""


# meta-information nodes

class start_of_file(nodes.Element):
    """Node to mark start of a new file, used in the LaTeX builder only."""

class highlightlang(nodes.Element):
    """Inserted to set the highlight language and line number options for
    subsequent code blocks.
    """

class tabular_col_spec(nodes.Element):
    """Node for specifying tabular columns, used for LaTeX output."""

class meta(nodes.Special, nodes.PreBibliographic, nodes.Element):
    """Node for meta directive -- same as docutils' standard meta node,
    but pickleable.
    """


# inline nodes

class pending_xref(nodes.Inline, nodes.Element):
    """Node for cross-references that cannot be resolved without complete
    information about all documents.

    These nodes are resolved before writing output, in
    BuildEnvironment.resolve_references.
    """

class download_reference(nodes.reference):
    """Node for download references, similar to pending_xref."""

class literal_emphasis(nodes.emphasis):
    """Node that behaves like `emphasis`, but further text processors are not
    applied (e.g. smartypants for HTML output).
    """

class abbreviation(nodes.Inline, nodes.TextElement):
    """Node for abbreviations with explanations."""

class termsep(nodes.Structural, nodes.Element):
    """Separates two terms within a <term> node."""


# make the new nodes known to docutils; needed because the HTML writer will
# choke at some point if these are not added
nodes._add_node_class_names(k for k in globals().keys()
                            if k != 'nodes' and k[0] != '_')
