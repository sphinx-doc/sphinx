"""
    sphinx.testing.restructuredtext
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path

from docutils.core import publish_doctree

from sphinx.io import SphinxStandaloneReader
from sphinx.parsers import RSTParser
from sphinx.util.docutils import sphinx_domains


if False:
    # For type annotation
    from docutils import nodes  # NOQA
    from sphinx.application import Sphinx  # NOQA


def parse(app, text, docname='index'):
    # type: (Sphinx, str, str) -> nodes.document
    """Parse a string as reStructuredText with Sphinx application."""
    try:
        app.env.temp_data['docname'] = docname
        parser = RSTParser()
        parser.set_application(app)
        with sphinx_domains(app.env):
            return publish_doctree(text, path.join(app.srcdir, docname + '.rst'),
                                   reader=SphinxStandaloneReader(app),
                                   parser=parser,
                                   settings_overrides={'env': app.env,
                                                       'gettext_compact': True})
    finally:
        app.env.temp_data.pop('docname', None)
