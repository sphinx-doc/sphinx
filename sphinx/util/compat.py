# -*- coding: utf-8 -*-
"""
    sphinx.util.compat
    ~~~~~~~~~~~~~~~~~~

    Stuff for docutils compatibility.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

# function missing in 0.5 SVN
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


# support the class-style Directive interface even when using docutils 0.4

try:
    from docutils.parsers.rst import Directive

except ImportError:
    class Directive(object):
        """
        Fake Directive class to allow Sphinx directives to be written in
        class style.
        """
        required_arguments = 0
        optional_arguments = 0
        final_argument_whitespace = False
        option_spec = None
        has_content = False

        def __init__(self, name, arguments, options, content, lineno,
                     content_offset, block_text, state, state_machine):
            self.name = name
            self.arguments = arguments
            self.options = options
            self.content = content
            self.lineno = lineno
            self.content_offset = content_offset
            self.block_text = block_text
            self.state = state
            self.state_machine = state_machine

        def run(self):
            raise NotImplementedError('Must override run() is subclass.')

    def directive_dwim(obj):
        """
        Return something usable with register_directive(), regardless if
        class or function.  For that, we need to convert classes to a
        function for docutils 0.4.
        """
        if isinstance(obj, type) and issubclass(obj, Directive):
            def _class_directive(name, arguments, options, content,
                                 lineno, content_offset, block_text,
                                 state, state_machine):
                return obj(name, arguments, options, content,
                           lineno, content_offset, block_text,
                           state, state_machine).run()
            _class_directive.options = obj.option_spec
            _class_directive.content = obj.has_content
            _class_directive.arguments = (obj.required_arguments,
                                          obj.optional_arguments,
                                          obj.final_argument_whitespace)
            return _class_directive
        return obj

else:
    def directive_dwim(obj):
        """
        Return something usable with register_directive(), regardless if
        class or function.  Nothing to do here, because docutils 0.5 takes
        care of converting functions itself.
        """
        return obj
