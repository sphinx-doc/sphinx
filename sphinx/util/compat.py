# -*- coding: utf-8 -*-
"""
    sphinx.util.compat
    ~~~~~~~~~~~~~~~~~~

    Stuff for docutils compatibility.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

def make_admonition(node_class, name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    #if not content:
    #    error = state_machine.reporter.error(
    #        'The "%s" admonition is empty; content required.' % (name),
    #        nodes.literal_block(block_text, block_text), line=lineno)
    #    return [error]
    text = '\n'.join(content)
    admonition_node = node_class(text)
    if arguments:
        title_text = arguments[0]
        textnodes, messages = state.inline_text(title_text, lineno)
        admonition_node += nodes.title(title_text, '', *textnodes)
        admonition_node += messages
        if 'class' in options:
            classes = options['class']
        else:
            classes = ['admonition-' + nodes.make_id(title_text)]
        admonition_node['classes'] += classes
    state.nested_parse(content, content_offset, admonition_node)
    return [admonition_node]


# backwards-compatibility aliases for helpers in older Sphinx versions that
# supported the docutils 0.4 directive function interface

from docutils.parsers.rst import Directive

def directive_dwim(obj):
    import warnings
    warnings.warn('directive_dwim is deprecated and no longer needed',
                  DeprecationWarning, stacklevel=2)
    return obj
