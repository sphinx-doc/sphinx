# -*- coding: utf-8 -*-
"""
    sphinx.addnodes
    ~~~~~~~~~~~~~~~

    Additional docutils nodes.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

# index markup
class index(nodes.Invisible, nodes.Inline, nodes.TextElement): pass

# description units (classdesc, funcdesc etc.)

# parent node for signature and content
class desc(nodes.Admonition, nodes.Element): pass

# additional name parts (module name, class name)
class desc_addname(nodes.Part, nodes.Inline, nodes.TextElement): pass
# compatibility alias
desc_classname = desc_addname
# return type (C); object type
class desc_type(nodes.Part, nodes.Inline, nodes.TextElement): pass
# -> annotation (Python)
class desc_returns(desc_type):
    def astext(self):
        return ' -> ' + nodes.TextElement.astext(self)
# main name of object
class desc_name(nodes.Part, nodes.Inline, nodes.TextElement): pass
# argument list
class desc_signature(nodes.Part, nodes.Inline, nodes.TextElement): pass
class desc_parameterlist(nodes.Part, nodes.Inline, nodes.TextElement):
    child_text_separator = ', '
class desc_parameter(nodes.Part, nodes.Inline, nodes.TextElement): pass
class desc_optional(nodes.Part, nodes.Inline, nodes.TextElement):
    child_text_separator = ', '
    def astext(self):
        return '[' + nodes.TextElement.astext(self) + ']'
# annotation (not Python 3-style annotations)
class desc_annotation(nodes.Part, nodes.Inline, nodes.TextElement): pass

# node for content
class desc_content(nodes.General, nodes.Element): pass

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
class pending_xref(nodes.Inline, nodes.Element): pass

# compact paragraph -- never makes a <p>
class compact_paragraph(nodes.paragraph): pass

# reference to a file to download
class download_reference(nodes.reference): pass

# for the ACKS list
class acks(nodes.Element): pass

# for horizontal lists
class hlist(nodes.Element): pass
class hlistcol(nodes.Element): pass

# sets the highlighting language for literal blocks
class highlightlang(nodes.Element): pass

# like emphasis, but doesn't apply further text processors, e.g. smartypants
class literal_emphasis(nodes.emphasis): pass

# for abbreviations (with explanations)
class abbreviation(nodes.Inline, nodes.TextElement): pass

# glossary
class glossary(nodes.Element): pass

# module declaration
class module(nodes.Element): pass

# start of a file, used in the LaTeX builder only
class start_of_file(nodes.Element): pass

# tabular column specification, used for the LaTeX writer
class tabular_col_spec(nodes.Element): pass

# only (in/exclusion based on tags)
class only(nodes.Element): pass

# meta directive -- same as docutils' standard meta node, but pickleable
class meta(nodes.Special, nodes.PreBibliographic, nodes.Element): pass

# make them known to docutils. this is needed, because the HTML writer
# will choke at some point if these are not added
nodes._add_node_class_names("""index desc desc_content desc_signature
      desc_type desc_returns desc_addname desc_name desc_parameterlist
      desc_parameter desc_optional download_reference hlist hlistcol
      centered versionmodified seealso productionlist production toctree
      pending_xref compact_paragraph highlightlang literal_emphasis
      abbreviation glossary acks module start_of_file tabular_col_spec
      meta""".split())
