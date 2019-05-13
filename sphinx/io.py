"""
    sphinx.io
    ~~~~~~~~~

    Input/Output files

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import codecs
from typing import Any

from docutils.core import Publisher
from docutils.io import FileInput, NullOutput
from docutils.parsers.rst import Parser as RSTParser
from docutils.readers import standalone
from docutils.transforms.references import DanglingReferences
from docutils.writers import UnfilteredWriter

from sphinx.transforms import (
    AutoIndexUpgrader, DoctreeReadEvent, FigureAligner, SphinxTransformer
)
from sphinx.transforms.i18n import (
    PreserveTranslatableMessages, Locale, RemoveTranslatableInline,
)
from sphinx.transforms.references import SphinxDomains
from sphinx.util import logging
from sphinx.util import UnicodeDecodeErrorHandler
from sphinx.util.docutils import LoggingReporter
from sphinx.versioning import UIDTransform

if False:
    # For type annotation
    from typing import Dict, List, Tuple, Type  # NOQA
    from docutils import nodes  # NOQA
    from docutils.frontend import Values  # NOQA
    from docutils.io import Input  # NOQA
    from docutils.parsers import Parser  # NOQA
    from docutils.transforms import Transform  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA


logger = logging.getLogger(__name__)


class SphinxBaseReader(standalone.Reader):
    """
    A base class of readers for Sphinx.

    This replaces reporter by Sphinx's on generating document.
    """

    transforms = []  # type: List[Type[Transform]]

    def __init__(self, app, *args, **kwargs):
        # type: (Sphinx, Any, Any) -> None
        self.app = app
        self.env = app.env
        super().__init__(*args, **kwargs)

    def get_transforms(self):
        # type: () -> List[Type[Transform]]
        transforms = super().get_transforms() + self.transforms

        # remove transforms which is not needed for Sphinx
        unused = [DanglingReferences]
        for transform in unused:
            if transform in transforms:
                transforms.remove(transform)

        return transforms

    def new_document(self):
        # type: () -> nodes.document
        """Creates a new document object which having a special reporter object good
        for logging.
        """
        document = super().new_document()

        # substitute transformer
        document.transformer = SphinxTransformer(document)
        document.transformer.set_environment(self.env)

        # substitute reporter
        reporter = document.reporter
        document.reporter = LoggingReporter.from_reporter(reporter)

        return document


class SphinxStandaloneReader(SphinxBaseReader):
    """
    A basic document reader for Sphinx.
    """

    def __init__(self, app, *args, **kwargs):
        # type: (Sphinx, Any, Any) -> None
        self.transforms = self.transforms + app.registry.get_transforms()
        super().__init__(app, *args, **kwargs)

    def read(self, source, parser, settings):
        # type: (Input, Parser, Values) -> nodes.document
        self.source = source
        if not self.parser:
            self.parser = parser
        self.settings = settings
        self.input = self.read_source()
        self.parse()
        return self.document

    def read_source(self):
        # type: () -> str
        """Read content from source and do post-process."""
        content = self.source.read()

        # emit "source-read" event
        arg = [content]
        self.app.emit('source-read', self.env.docname, arg)
        return arg[0]


class SphinxI18nReader(SphinxBaseReader):
    """
    A document reader for i18n.

    This returns the source line number of original text as current source line number
    to let users know where the error happened.
    Because the translated texts are partial and they don't have correct line numbers.
    """

    def __init__(self, app, *args, **kwargs):
        # type: (Sphinx, Any, Any) -> None
        self.transforms = self.transforms + app.registry.get_transforms()
        unused = [PreserveTranslatableMessages, Locale, RemoveTranslatableInline,
                  AutoIndexUpgrader, FigureAligner, SphinxDomains, DoctreeReadEvent,
                  UIDTransform]
        for transform in unused:
            if transform in self.transforms:
                self.transforms.remove(transform)

        super().__init__(app, *args, **kwargs)


class SphinxDummyWriter(UnfilteredWriter):
    """Dummy writer module used for generating doctree."""

    supported = ('html',)  # needed to keep "meta" nodes

    def translate(self):
        # type: () -> None
        pass


def SphinxDummySourceClass(source, *args, **kwargs):
    # type: (Any, Any, Any) -> Any
    """Bypass source object as is to cheat Publisher."""
    return source


class SphinxFileInput(FileInput):
    """A basic FileInput for Sphinx."""
    def __init__(self, *args, **kwargs):
        # type: (Any, Any) -> None
        kwargs['error_handler'] = 'sphinx'
        super().__init__(*args, **kwargs)


class FiletypeNotFoundError(Exception):
    pass


def get_filetype(source_suffix, filename):
    # type: (Dict[str, str], str) -> str
    for suffix, filetype in source_suffix.items():
        if filename.endswith(suffix):
            # If default filetype (None), considered as restructuredtext.
            return filetype or 'restructuredtext'
    else:
        raise FiletypeNotFoundError


def read_doc(app, env, filename):
    # type: (Sphinx, BuildEnvironment, str) -> nodes.document
    """Parse a document and convert to doctree."""
    # set up error_handler for the target document
    error_handler = UnicodeDecodeErrorHandler(env.docname)
    codecs.register_error('sphinx', error_handler)  # type: ignore

    reader = SphinxStandaloneReader(app)
    filetype = get_filetype(app.config.source_suffix, filename)
    parser = app.registry.create_source_parser(app, filetype)
    if parser.__class__.__name__ == 'CommonMarkParser' and parser.settings_spec == ():
        # a workaround for recommonmark
        #   If recommonmark.AutoStrictify is enabled, the parser invokes reST parser
        #   internally.  But recommonmark-0.4.0 does not provide settings_spec for reST
        #   parser.  As a workaround, this copies settings_spec for RSTParser to the
        #   CommonMarkParser.
        parser.settings_spec = RSTParser.settings_spec

    input_class = app.registry.get_source_input(filetype)
    if input_class:
        # Sphinx-1.8 style
        source = input_class(app, env, source=None, source_path=filename,  # type: ignore
                             encoding=env.config.source_encoding)
        pub = Publisher(reader=reader,  # type: ignore
                        parser=parser,
                        writer=SphinxDummyWriter(),
                        source_class=SphinxDummySourceClass,
                        destination=NullOutput())
        pub.process_programmatic_settings(None, env.settings, None)
        pub.set_source(source, filename)
    else:
        # Sphinx-2.0 style
        pub = Publisher(reader=reader,
                        parser=parser,
                        writer=SphinxDummyWriter(),
                        source_class=SphinxFileInput,
                        destination=NullOutput())
        pub.process_programmatic_settings(None, env.settings, None)
        pub.set_source(source_path=filename)

    pub.publish()
    return pub.document
