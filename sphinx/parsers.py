"""A Base class for additional parsers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import docutils.parsers
import docutils.parsers.rst
from docutils import nodes
from docutils.parsers.rst import languages, states
from docutils.statemachine import StringList
from docutils.transforms.universal import SmartQuotes

from sphinx.util.rst import append_epilog, prepend_prolog

if TYPE_CHECKING:
    from docutils.transforms import Transform

    from sphinx.application import Sphinx
    from sphinx.config import Config
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import ExtensionMetadata


class Parser(docutils.parsers.Parser):
    """
    A base class of source parsers.  The additional parsers should inherit this class instead
    of ``docutils.parsers.Parser``.  Compared with ``docutils.parsers.Parser``, this class
    improves accessibility to Sphinx APIs.

    The subclasses can access sphinx core runtime objects (app, config and env).
    """

    #: The config object
    config: Config

    #: The environment object
    env: BuildEnvironment

    def set_application(self, app: Sphinx) -> None:
        """set_application will be called from Sphinx to set app and other instance variables

        :param sphinx.application.Sphinx app: Sphinx application object
        """
        self._app = app
        self.config = app.config
        self.env = app.env

    def parse_inline(self, inputstring: str, document: nodes.document, lineno: int) -> None:
        """Parse the inline elements of a text block and generate a document tree."""
        msg = 'Parser subclasses must implement parse_inline'
        raise NotImplementedError(msg)


class RSTParser(docutils.parsers.rst.Parser, Parser):
    """A reST parser for Sphinx."""

    def get_transforms(self) -> list[type[Transform]]:
        """
        Sphinx's reST parser replaces a transform class for smart-quotes by its own

        refs: sphinx.io.SphinxStandaloneReader
        """
        transforms = super().get_transforms()
        transforms.remove(SmartQuotes)
        return transforms

    def parse_inline(self, inputstring: str, document: nodes.document, lineno: int) -> None:
        """Parse inline syntax from text and generate a document tree."""
        # Avoid "Literal block expected; none found." warnings.
        if inputstring.endswith('::'):
            inputstring = inputstring[:-1]

        reporter = document.reporter
        reporter.get_source_and_line = lambda x: (document['source'], x)  # type: ignore[attr-defined]
        language = languages.get_language(document.settings.language_code, reporter)
        if self.inliner is None:
            inliner = states.Inliner()
        else:
            inliner = self.inliner
        inliner.init_customizations(document.settings)
        memo = states.Struct(
            document=document,
            reporter=reporter,
            language=language,
        )
        textnodes, messages = inliner.parse(inputstring, lineno, memo, document)
        p = nodes.paragraph(inputstring, '', *textnodes)
        p.source, p.line = document['source'], lineno
        document += [p, *messages]

    def parse(self, inputstring: str | StringList, document: nodes.document) -> None:
        """Parse text and generate a document tree."""
        self.setup_parse(inputstring, document)  # type: ignore[arg-type]
        self.statemachine = states.RSTStateMachine(
            state_classes=self.state_classes,
            initial_state=self.initial_state,
            debug=document.reporter.debug_flag,
        )

        # preprocess inputstring
        if isinstance(inputstring, str):
            lines = docutils.statemachine.string2lines(
                inputstring, tab_width=document.settings.tab_width, convert_whitespace=True
            )

            inputlines = StringList(lines, document.current_source)
        else:
            inputlines = inputstring

        self.decorate(inputlines)
        self.statemachine.run(inputlines, document, inliner=self.inliner)
        self.finish_parse()

    def decorate(self, content: StringList) -> None:
        """Preprocess reST content before parsing."""
        prepend_prolog(content, self.config.rst_prolog)
        append_epilog(content, self.config.rst_epilog)


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_source_parser(RSTParser)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
