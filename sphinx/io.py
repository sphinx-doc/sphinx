"""
    sphinx.io
    ~~~~~~~~~

    Input/Output files

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import codecs
import warnings
from typing import Any, List, Tuple
from typing import Type  # for python3.5.1

from docutils import nodes
from docutils.core import Publisher
from docutils.frontend import Values
from docutils.io import FileInput, Input, NullOutput
from docutils.parsers import Parser
from docutils.parsers.rst import Parser as RSTParser
from docutils.readers import standalone
from docutils.statemachine import StringList, string2lines
from docutils.transforms import Transform
from docutils.transforms.references import DanglingReferences
from docutils.writers import UnfilteredWriter

from sphinx.deprecation import (
    RemovedInSphinx30Warning, RemovedInSphinx40Warning, deprecated_alias
)
from sphinx.environment import BuildEnvironment
from sphinx.errors import FiletypeNotFoundError
from sphinx.transforms import (
    AutoIndexUpgrader, DoctreeReadEvent, FigureAligner, SphinxTransformer
)
from sphinx.transforms.i18n import (
    PreserveTranslatableMessages, Locale, RemoveTranslatableInline,
)
from sphinx.transforms.references import SphinxDomains
from sphinx.util import logging, get_filetype
from sphinx.util import UnicodeDecodeErrorHandler
from sphinx.util.docutils import LoggingReporter
from sphinx.util.rst import append_epilog, docinfo_re, prepend_prolog
from sphinx.versioning import UIDTransform

if False:
    # For type annotation
    from sphinx.application import Sphinx


logger = logging.getLogger(__name__)


class SphinxBaseReader(standalone.Reader):
    """
    A base class of readers for Sphinx.

    This replaces reporter by Sphinx's on generating document.
    """

    transforms = []  # type: List[Type[Transform]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        from sphinx.application import Sphinx
        if len(args) > 0 and isinstance(args[0], Sphinx):
            self._app = args[0]
            self._env = self._app.env
            args = args[1:]

        super().__init__(*args, **kwargs)

    @property
    def app(self) -> "Sphinx":
        warnings.warn('SphinxBaseReader.app is deprecated.',
                      RemovedInSphinx40Warning, stacklevel=2)
        return self._app

    @property
    def env(self) -> BuildEnvironment:
        warnings.warn('SphinxBaseReader.env is deprecated.',
                      RemovedInSphinx40Warning, stacklevel=2)
        return self._env

    def setup(self, app: "Sphinx") -> None:
        self._app = app      # hold application object only for compatibility
        self._env = app.env

    def get_transforms(self) -> List[Type[Transform]]:
        transforms = super().get_transforms() + self.transforms

        # remove transforms which is not needed for Sphinx
        unused = [DanglingReferences]
        for transform in unused:
            if transform in transforms:
                transforms.remove(transform)

        return transforms

    def new_document(self) -> nodes.document:
        """Creates a new document object which having a special reporter object good
        for logging.
        """
        document = super().new_document()

        # substitute transformer
        document.transformer = SphinxTransformer(document)
        document.transformer.set_environment(self.settings.env)

        # substitute reporter
        reporter = document.reporter
        document.reporter = LoggingReporter.from_reporter(reporter)

        return document


class SphinxStandaloneReader(SphinxBaseReader):
    """
    A basic document reader for Sphinx.
    """

    def setup(self, app: "Sphinx") -> None:
        self.transforms = self.transforms + app.registry.get_transforms()
        super().setup(app)

    def read(self, source: Input, parser: Parser, settings: Values) -> nodes.document:
        self.source = source
        if not self.parser:
            self.parser = parser
        self.settings = settings
        self.input = self.read_source(settings.env)
        self.parse()
        return self.document

    def read_source(self, env: BuildEnvironment) -> str:
        """Read content from source and do post-process."""
        content = self.source.read()

        # emit "source-read" event
        arg = [content]
        env.events.emit('source-read', env.docname, arg)
        return arg[0]


class SphinxI18nReader(SphinxBaseReader):
    """
    A document reader for i18n.

    This returns the source line number of original text as current source line number
    to let users know where the error happened.
    Because the translated texts are partial and they don't have correct line numbers.
    """

    def setup(self, app: "Sphinx") -> None:
        super().setup(app)

        self.transforms = self.transforms + app.registry.get_transforms()
        unused = [PreserveTranslatableMessages, Locale, RemoveTranslatableInline,
                  AutoIndexUpgrader, FigureAligner, SphinxDomains, DoctreeReadEvent,
                  UIDTransform]
        for transform in unused:
            if transform in self.transforms:
                self.transforms.remove(transform)

    def set_lineno_for_reporter(self, lineno: int) -> None:
        """Stores the source line number of original text."""
        warnings.warn('SphinxI18nReader.set_lineno_for_reporter() is deprecated.',
                      RemovedInSphinx30Warning, stacklevel=2)

    @property
    def line(self) -> int:
        warnings.warn('SphinxI18nReader.line is deprecated.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return 0


class SphinxDummyWriter(UnfilteredWriter):
    """Dummy writer module used for generating doctree."""

    supported = ('html',)  # needed to keep "meta" nodes

    def translate(self) -> None:
        pass


def SphinxDummySourceClass(source: Any, *args: Any, **kwargs: Any) -> Any:
    """Bypass source object as is to cheat Publisher."""
    return source


class SphinxBaseFileInput(FileInput):
    """A base class of SphinxFileInput.

    It supports to replace unknown Unicode characters to '?'.
    """

    def __init__(self, app: "Sphinx", env: BuildEnvironment,
                 *args: Any, **kwargs: Any) -> None:
        self.app = app
        self.env = env

        warnings.warn('%s is deprecated.' % self.__class__.__name__,
                      RemovedInSphinx30Warning, stacklevel=2)

        kwargs['error_handler'] = 'sphinx'  # py3: handle error on open.
        super().__init__(*args, **kwargs)

    def warn_and_replace(self, error: Any) -> Tuple:
        return UnicodeDecodeErrorHandler(self.env.docname)(error)


class SphinxFileInput(FileInput):
    """A basic FileInput for Sphinx."""
    supported = ('*',)  # RemovedInSphinx30Warning

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs['error_handler'] = 'sphinx'
        super().__init__(*args, **kwargs)


class SphinxRSTFileInput(SphinxBaseFileInput):
    """A reST FileInput for Sphinx.

    This FileInput automatically prepends and appends text by :confval:`rst_prolog` and
    :confval:`rst_epilog`.

    .. important::

       This FileInput uses an instance of ``StringList`` as a return value of ``read()``
       method to indicate original source filename and line numbers after prepending and
       appending.
       For that reason, ``sphinx.parsers.RSTParser`` should be used with this to parse
       a content correctly.
    """
    supported = ('restructuredtext',)

    def prepend_prolog(self, text: StringList, prolog: str) -> None:
        docinfo = self.count_docinfo_lines(text)
        if docinfo:
            # insert a blank line after docinfo
            text.insert(docinfo, '', '<generated>', 0)
            docinfo += 1

        # insert prolog (after docinfo if exists)
        for lineno, line in enumerate(prolog.splitlines()):
            text.insert(docinfo + lineno, line, '<rst_prolog>', lineno)

        text.insert(docinfo + lineno + 1, '', '<generated>', 0)

    def append_epilog(self, text: StringList, epilog: str) -> None:
        # append a blank line and rst_epilog
        text.append('', '<generated>', 0)
        for lineno, line in enumerate(epilog.splitlines()):
            text.append(line, '<rst_epilog>', lineno)

    def read(self) -> StringList:  # type: ignore
        inputstring = super().read()
        lines = string2lines(inputstring, convert_whitespace=True)
        content = StringList()
        for lineno, line in enumerate(lines):
            content.append(line, self.source_path, lineno)

        prepend_prolog(content, self.env.config.rst_prolog)
        append_epilog(content, self.env.config.rst_epilog)

        return content

    def count_docinfo_lines(self, content: StringList) -> int:
        if len(content) == 0:
            return 0
        else:
            for lineno, line in enumerate(content.data):
                if not docinfo_re.match(line):
                    break
            return lineno


def read_doc(app: "Sphinx", env: BuildEnvironment, filename: str) -> nodes.document:
    """Parse a document and convert to doctree."""
    # set up error_handler for the target document
    error_handler = UnicodeDecodeErrorHandler(env.docname)
    codecs.register_error('sphinx', error_handler)  # type: ignore

    reader = SphinxStandaloneReader()
    reader.setup(app)
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
        pub = Publisher(reader=reader,
                        parser=parser,
                        writer=SphinxDummyWriter(),
                        source_class=SphinxDummySourceClass,  # type: ignore
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


deprecated_alias('sphinx.io',
                 {
                     'FiletypeNotFoundError': FiletypeNotFoundError,
                     'get_filetype': get_filetype,
                 },
                 RemovedInSphinx40Warning)
