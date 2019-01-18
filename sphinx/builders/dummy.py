"""
    sphinx.builders.dummy
    ~~~~~~~~~~~~~~~~~~~~~

    Do syntax checks, but no writing.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""


from sphinx.builders import Builder
from sphinx.locale import __

if False:
    # For type annotation
    from typing import Any, Dict, Set  # NOQA
    from docutils import nodes  # NOQA
    from sphinx.application import Sphinx  # NOQA


class DummyBuilder(Builder):
    name = 'dummy'
    epilog = __('The dummy builder generates no files.')

    allow_parallel = True

    def init(self):
        # type: () -> None
        pass

    def get_outdated_docs(self):
        # type: () -> Set[str]
        return self.env.found_docs

    def get_target_uri(self, docname, typ=None):
        # type: (str, str) -> str
        return ''

    def prepare_writing(self, docnames):
        # type: (Set[str]) -> None
        pass

    def write_doc(self, docname, doctree):
        # type: (str, nodes.Node) -> None
        pass

    def finish(self):
        # type: () -> None
        pass


def setup(app):
    # type: (Sphinx) -> Dict[str, Any]
    app.add_builder(DummyBuilder)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
