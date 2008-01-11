# -*- coding: utf-8 -*-
"""
    sphinx.addnodes
    ~~~~~~~~~~~~~~~

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

from docutils import nodes

# index markup
class index(nodes.Invisible, nodes.Inline, nodes.TextElement): pass

# description units (classdesc, funcdesc etc.)
class desc(nodes.Admonition, nodes.Element): pass
class desc_content(nodes.General, nodes.Element): pass
class desc_signature(nodes.Part, nodes.Inline, nodes.TextElement): pass
class desc_classname(nodes.Part, nodes.Inline, nodes.TextElement): pass
class desc_type(nodes.Part, nodes.Inline, nodes.TextElement): pass
class desc_name(nodes.Part, nodes.Inline, nodes.TextElement): pass
class desc_parameterlist(nodes.Part, nodes.Inline, nodes.TextElement):
    child_text_separator = ', '
class desc_parameter(nodes.Part, nodes.Inline, nodes.TextElement): pass
class desc_optional(nodes.Part, nodes.Inline, nodes.TextElement):
    child_text_separator = ', '
    def astext(self):
        return '[' + nodes.TextElement.astext(self) + ']'

# refcount annotation
class refcount(nodes.emphasis): pass

# \versionadded, \versionchanged, \deprecated
class versionmodified(nodes.Admonition, nodes.TextElement): pass

# seealso
class seealso(nodes.Admonition, nodes.Element): pass

# productionlist
class productionlist(nodes.Admonition, nodes.Element): pass
class production(nodes.Part, nodes.Inline, nodes.TextElement): pass

# toc tree
class toctree(nodes.General, nodes.Element): pass

# centered
class centered(nodes.Part, nodes.Element): pass

# pending xref
class pending_xref(nodes.Element): pass

# compact paragraph -- never makes a <p>
class compact_paragraph(nodes.paragraph): pass

# for the ACKS list
class acks(nodes.Element): pass

# sets the highlighting language for literal blocks
class highlightlang(nodes.Element): pass

# like emphasis, but doesn't apply further text processors, e.g. smartypants
class literal_emphasis(nodes.emphasis): pass

# glossary
class glossary(nodes.Element): pass

# module declaration
class module(nodes.Element): pass

# make them known to docutils. this is needed, because the HTMl writer
# will choke at some point if these are not added
nodes._add_node_class_names("""index desc desc_content desc_signature desc_type
      desc_classname desc_name desc_parameterlist desc_parameter desc_optional
      centered versionmodified seealso productionlist production toctree
      pending_xref compact_paragraph highlightlang literal_emphasis
      glossary acks module""".split())
