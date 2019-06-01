"""
    sphinx.directives.patches
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import cast

from docutils import nodes
from docutils.nodes import make_id
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import images, html, tables

from sphinx import addnodes
from sphinx.directives import optional_int
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import set_source_info

if False:
    # For type annotation
    from typing import Dict, List, Tuple  # NOQA
    from sphinx.application import Sphinx  # NOQA


class Figure(images.Figure):
    """The figure directive which applies `:name:` option to the figure node
    instead of the image node.
    """

    def run(self):
        # type: () -> List[nodes.Node]
        name = self.options.pop('name', None)
        result = super().run()
        if len(result) == 2 or isinstance(result[0], nodes.system_message):
            return result

        assert len(result) == 1
        figure_node = cast(nodes.figure, result[0])
        if name:
            # set ``name`` to figure_node if given
            self.options['name'] = name
            self.add_name(figure_node)

        # copy lineno from image node
        if figure_node.line is None and len(figure_node) == 2:
            caption = cast(nodes.caption, figure_node[1])
            figure_node.line = caption.line

        return [figure_node]


class Meta(html.Meta, SphinxDirective):
    def run(self):
        # type: () -> List[nodes.Node]
        result = super().run()
        for node in result:
            if (isinstance(node, nodes.pending) and
               isinstance(node.details['nodes'][0], html.MetaBody.meta)):
                meta = node.details['nodes'][0]
                meta.source = self.env.doc2path(self.env.docname)
                meta.line = self.lineno
                meta.rawcontent = meta['content']  # type: ignore

                # docutils' meta nodes aren't picklable because the class is nested
                meta.__class__ = addnodes.meta  # type: ignore

        return result


class RSTTable(tables.RSTTable):
    """The table directive which sets source and line information to its caption.

    Only for docutils-0.13 or older version."""

    def make_title(self):
        # type: () -> Tuple[nodes.title, List[nodes.system_message]]
        title, message = super().make_title()
        if title:
            set_source_info(self, title)

        return title, message


class CSVTable(tables.CSVTable):
    """The csv-table directive which sets source and line information to its caption.

    Only for docutils-0.13 or older version."""

    def make_title(self):
        # type: () -> Tuple[nodes.title, List[nodes.system_message]]
        title, message = super().make_title()
        if title:
            set_source_info(self, title)

        return title, message


class ListTable(tables.ListTable):
    """The list-table directive which sets source and line information to its caption.

    Only for docutils-0.13 or older version."""

    def make_title(self):
        # type: () -> Tuple[nodes.title, List[nodes.system_message]]
        title, message = super().make_title()
        if title:
            set_source_info(self, title)

        return title, message


class Code(SphinxDirective):
    """Parse and mark up content of a code block.

    This is compatible with docutils' :rst:dir:`code` directive.
    """
    optional_arguments = 1
    option_spec = {
        'class': directives.class_option,
        'force': directives.flag,
        'name': directives.unchanged,
        'number-lines': optional_int,
    }
    has_content = True

    def run(self):
        # type: () -> List[nodes.Node]
        self.assert_has_content()

        code = '\n'.join(self.content)
        node = nodes.literal_block(code, code,
                                   classes=self.options.get('classes', []),
                                   force='force' in self.options,
                                   highlight_args={})
        self.add_name(node)
        set_source_info(self, node)

        if self.arguments:
            # highlight language specified
            node['language'] = self.arguments[0]
        else:
            # no highlight language specified.  Then this directive refers the current
            # highlight setting via ``highlight`` directive or ``highlight_language``
            # configuration.
            node['language'] = self.env.temp_data.get('highlight_language',
                                                      self.config.highlight_language)

        if 'number-lines' in self.options:
            node['linenos'] = True

            # if number given, treat as lineno-start.
            if self.options['number-lines']:
                node['highlight_args']['linenostart'] = self.options['number-lines']

        return [node]


class MathDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        'label': directives.unchanged,
        'name': directives.unchanged,
        'class': directives.class_option,
        'nowrap': directives.flag,
    }

    def run(self):
        # type: () -> List[nodes.Node]
        latex = '\n'.join(self.content)
        if self.arguments and self.arguments[0]:
            latex = self.arguments[0] + '\n\n' + latex
        label = self.options.get('label', self.options.get('name'))
        node = nodes.math_block(latex, latex,
                                classes=self.options.get('class', []),
                                docname=self.env.docname,
                                number=None,
                                label=label,
                                nowrap='nowrap' in self.options)
        self.add_name(node)
        self.set_source_info(node)

        ret = [node]  # type: List[nodes.Node]
        self.add_target(ret)
        return ret

    def add_target(self, ret):
        # type: (List[nodes.Node]) -> None
        node = cast(nodes.math_block, ret[0])

        # assign label automatically if math_number_all enabled
        if node['label'] == '' or (self.config.math_number_all and not node['label']):
            seq = self.env.new_serialno('sphinx.ext.math#equations')
            node['label'] = "%s:%d" % (self.env.docname, seq)

        # no targets and numbers are needed
        if not node['label']:
            return

        # register label to domain
        domain = self.env.get_domain('math')
        try:
            eqno = domain.add_equation(self.env, self.env.docname, node['label'])  # type: ignore  # NOQA
            node['number'] = eqno

            # add target node
            node_id = make_id('equation-%s' % node['label'])
            target = nodes.target('', '', ids=[node_id])
            self.state.document.note_explicit_target(target)
            ret.insert(0, target)
        except UserWarning as exc:
            self.state_machine.reporter.warning(exc, line=self.lineno)


def setup(app):
    # type: (Sphinx) -> Dict
    directives.register_directive('figure', Figure)
    directives.register_directive('meta', Meta)
    directives.register_directive('table', RSTTable)
    directives.register_directive('csv-table', CSVTable)
    directives.register_directive('list-table', ListTable)
    directives.register_directive('code', Code)
    directives.register_directive('math', MathDirective)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
