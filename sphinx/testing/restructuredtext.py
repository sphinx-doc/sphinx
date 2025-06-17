from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes

from sphinx.io import SphinxBaseReader
from sphinx.parsers import RSTParser
from sphinx.transforms import SphinxTransformer
from sphinx.util.docutils import LoggingReporter, _get_settings, sphinx_domains

if TYPE_CHECKING:
    from sphinx.application import Sphinx


def parse(app: Sphinx, text: str, docname: str = 'index') -> nodes.document:
    """Parse a string as reStructuredText with Sphinx."""
    config = app.config
    env = app.env
    registry = app.registry
    srcdir = app.srcdir

    source_path = str(srcdir / f'{docname}.rst')

    # Get settings
    settings_overrides = {
        'gettext_compact': True,
        'input_encoding': 'utf-8',
        'output_encoding': 'unicode',
        'traceback': True,
    }
    settings = _get_settings(SphinxBaseReader, RSTParser, defaults=settings_overrides)
    settings._source = source_path
    settings.env = env

    # Create parser
    parser = RSTParser()
    parser._config = config
    parser._env = env

    # Create root document node
    reporter = LoggingReporter(
        source_path,
        settings.report_level,
        settings.halt_level,
        settings.debug,
        settings.error_encoding_error_handler,
    )
    document = nodes.document(settings, reporter, source=source_path)
    document.note_source(source_path, -1)

    # substitute transformer
    document.transformer = transformer = SphinxTransformer(document)
    transformer.add_transforms(SphinxBaseReader().get_transforms())
    transformer.add_transforms(registry.get_transforms())
    transformer.add_transforms(parser.get_transforms())

    env.current_document.docname = docname
    try:
        with sphinx_domains(env):
            parser.parse(text, document)
            document.current_source = document.current_line = None

            transformer.apply_transforms()
    finally:
        env.current_document.docname = ''

    return document
