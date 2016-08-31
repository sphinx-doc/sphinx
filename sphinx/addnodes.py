# -*- coding: utf-8 -*-
"""
    sphinx.addnodes
    ~~~~~~~~~~~~~~~

    Additional docutils nodes.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

if False:
    # For type annotation
    from typing import Sequence, Tuple  # NOQA


class translatable(object):
    """Node which supports translation.

    The translation goes forward with following steps:

    1. Preserve original translatable messages
    2. Apply translated messages from message catalog
    3. Extract preserved messages (for gettext builder)

    The translatable nodes MUST preserve original messages.
    And these messages should not be overridden at applying step.
    Because they are used at final step; extraction.
    """

    def preserve_original_messages(self):
        # type: () -> None
        """Preserve original translatable messages."""
        raise NotImplementedError

    def apply_translated_message(self, original_message, translated_message):
        # type: (unicode, unicode) -> None
        """Apply translated message."""
        raise NotImplementedError

    def extract_original_messages(self):
        # type: () -> Sequence[unicode]
        """Extract translation messages.

        :returns: list of extracted messages or messages generator
        """
        raise NotImplementedError


class toctree(nodes.General, nodes.Element, translatable):
    """Node for inserting a "TOC tree"."""

    def preserve_original_messages(self):
        # type: () -> None
        if self.get('caption'):
            self['rawcaption'] = self['caption']

    def apply_translated_message(self, original_message, translated_message):
        # type: (unicode, unicode) -> None
        if self.get('rawcaption') == original_message:
            self['caption'] = translated_message

    def extract_original_messages(self):
        # type: () -> List[unicode]
        if 'rawcaption' in self:
            return [self['rawcaption']]
        else:
            return []


# domain-specific object descriptions (class, function etc.)

class desc(nodes.Admonition, nodes.Element):
    """Node for object descriptions.

    This node is similar to a "definition list" with one definition.  It
    contains one or more ``desc_signature`` and a ``desc_content``.
    """


class desc_signature(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for object signatures.

    The "term" part of the custom Sphinx definition list.

    As default the signature is a single line signature,
    but set ``is_multiline = True`` to describe a multi-line signature.
    In that case all child nodes must be ``desc_signature_line`` nodes.
    """


class desc_signature_line(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for a line in a multi-line object signatures.

    It should only be used in a ``desc_signature`` with ``is_multiline`` set.
    Set ``add_permalink = True`` for the line that should get the permalink.
    """


# nodes to use within a desc_signature or desc_signature_line

class desc_addname(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for additional name parts (module name, class name)."""


# compatibility alias
desc_classname = desc_addname


class desc_type(nodes.Part, nodes.Inline, nodes.TextElement):
    """Node for return types or object type names."""


class desc_returns(desc_type):
    """Node for a "returns" annotation (a la -> in Python)."""
    def astext(self):
        # type: () -> unicode
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
        # type: () -> unicode
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
    ``entries``.  Its value is a list of 5-tuples of ``(entrytype, entryname,
    target, ignored, key)``.

    *entrytype* is one of "single", "pair", "double", "triple".

    *key* is categolziation characters (usually it is single character) for
    general index page. For the detail of this, please see also:
    :rst:dir:`glossary` and issue #2320.
    """


class centered(nodes.Part, nodes.TextElement):
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


class number_reference(nodes.reference):
    """Node for number references, similar to pending_xref."""


class download_reference(nodes.reference):
    """Node for download references, similar to pending_xref."""


class literal_emphasis(nodes.emphasis):
    """Node that behaves like `emphasis`, but further text processors are not
    applied (e.g. smartypants for HTML output).
    """


class literal_strong(nodes.strong):
    """Node that behaves like `strong`, but further text processors are not
    applied (e.g. smartypants for HTML output).
    """


class abbreviation(nodes.Inline, nodes.TextElement):
    """Node for abbreviations with explanations."""


class manpage(nodes.Inline, nodes.TextElement):
    """Node for references to manpages."""


class ruby(nodes.General, nodes.Element):
    """Node for ruby annotation"""

    BASE = 0
    RUBY = 1

    def preserve_original_messages(self):
        rubies = self.get('ruby', [])
        raw_texts = {}  # type: Dict[str, Tuple[int, int, str]]

        def search_unique_key(original_key):
            suffix = 1
            key = original_key
            while key in raw_texts:
                key = "%s_%d" % (original_key, suffix)
            return key

        for i, (base, ruby, have_space) in enumerate(rubies):
            if base is not None:
                key = search_unique_key(base)
                raw_texts[key] = (i, self.BASE, base)
            if ruby is not None:
                key = search_unique_key(ruby)
                raw_texts[key] = (i, self.RUBY, ruby)
        self['raw_texts'] = raw_texts

    def apply_translated_message(self, original_message, translated_message):
        raw_texts = self.get('raw_texts')
        if original_message in raw_texts:
            i, typeid, _ = raw_texts[original_message]
            ruby = self.get('ruby')[i]
            if typeid == self.BASE:
                self.get('ruby')[i] = (translated_message, ruby[1], ruby[2])
            else:
                self.get('ruby')[i] = (ruby[0], translated_message, ruby[2])

    def extract_original_messages(self):
        if 'raw_texts' in self:
            for _, _, word in self.get('raw_texts').values():
                yield word

    def to_plaintext(self):
        rubies = self.get('ruby')
        result = []
        for base, ruby, have_space in rubies:
            if have_space:
                result.append(' ')
            if ruby is None:
                ruby = '-'
            if base is None:
                base = '-'
            result.append(r'%s(%s)' % (base, ruby))
        return ''.join(result)


class delete(nodes.General, nodes.Element):
    """Node for del role"""

    def preserve_original_messages(self):
        self['raw_text'] = self['text']

    def apply_translated_message(self, original_message, translated_message):
        if self['text'] == original_message:
            self['text'] = translated_message
        elif 'DELETE' == original_message:
            self['label'] = translated_message

    def extract_original_messages(self):
        return ['DELETE', self['raw_text']]

    def to_plaintext(self):
        return '[%s:%s]' % (self['label'], self['text'])


# make the new nodes known to docutils; needed because the HTML writer will
# choke at some point if these are not added
nodes._add_node_class_names(k for k in globals().keys()
                            if k != 'nodes' and k[0] != '_')
