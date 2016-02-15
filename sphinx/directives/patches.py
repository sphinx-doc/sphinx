# -*- coding: utf-8 -*-
"""
    sphinx.directives.patches
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import images, tables


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


def halign(argument):
    return directives.choice(argument, ('left', 'center', 'right'))


class RSTTable(tables.RSTTable):
    """The table directive which supports ``align`` option.

    An ``align`` option can adjust the alignment of the table. The value should
    be one of ``left``, ``center`` of ``right``.
    """

    option_spec = tables.RSTTable.option_spec.copy()
    option_spec['align'] = halign

    def run(self):
        result = tables.RSTTable.run(self)
        if isinstance(result[0], nodes.system_message):
            return result

        if 'align' in self.options:
            result[0]['align'] = self.options['align']

        return result


class CSVTable(tables.CSVTable):
    """The csv-table directive which supports ``align`` option.

    An ``align`` option can adjust the alignment of the table. The value should
    be one of ``left``, ``center`` of ``right``.
    """

    option_spec = tables.CSVTable.option_spec.copy()
    option_spec['align'] = halign

    def run(self):
        result = tables.CSVTable.run(self)
        if isinstance(result[0], nodes.system_message):
            return result

        if 'align' in self.options:
            result[0]['align'] = self.options['align']

        return result


class ListTable(tables.ListTable):
    """The list-table directive which supports ``align`` option.

    An ``align`` option can adjust the alignment of the table. The value should
    be one of ``left``, ``center`` of ``right``.
    """

    option_spec = tables.ListTable.option_spec.copy()
    option_spec['align'] = halign

    def run(self):
        result = tables.ListTable.run(self)
        if isinstance(result[0], nodes.system_message):
            return result

        if 'align' in self.options:
            result[0]['align'] = self.options['align']

        return result

directives.register_directive('figure', Figure)
directives.register_directive('table', RSTTable)
directives.register_directive('csv-table', CSVTable)
directives.register_directive('list-table', ListTable)
