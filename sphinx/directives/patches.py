# -*- coding: utf-8 -*-
"""
    sphinx.directives.patches
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import images


class Figure(images.Figure):
    """The figure directive which applies `:name:` option to the figure node
    instead of the image node.
    """

    def run(self):
        name = self.options.pop('name', None)
        (figure_node,) = images.Figure.run(self)
        if isinstance(figure_node, nodes.system_message):
            return [figure_node]

        if name:
            self.options['name'] = name
            self.add_name(figure_node)

        return [figure_node]


directives.register_directive('figure', Figure)
