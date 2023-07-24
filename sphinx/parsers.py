"""A Base class for additional parsers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

import docutils.parsers
import docutils.parsers.rst
from docutils import nodes
from docutils.statemachine import State, StringList
from docutils.transforms import Transform
from docutils.transforms.universal import SmartQuotes

from sphinx.config import Config
from sphinx.environment import BuildEnvironment
from sphinx.util.rst import append_epilog, prepend_prolog

if TYPE_CHECKING:
    from sphinx.application import Sphinx


class RSTStateMachine(docutils.parsers.rst.states.RSTStateMachine):
    def __init__(self, app: Sphinx, state_classes: Sequence[type[State]], initial_state: str,
                 debug: bool = False):
        self.app = app
        super().__init__(state_classes=state_classes, initial_state=initial_state,
                         debug=debug)

    def insert_input(self, include_lines, path):
        # First we need to combine the lines back into text so we can send it with the 
        # source-read event. In newer releases of docutils there are two lines at the end, 
        # that act as markers. We must preserve them and leave them out of the source-read 
        # event:
        text = "\n".join(include_lines[:-2])
        # turn the path back to doc reference for source-read event
        doc = self.app.env.path2doc(path)
        # emit "source-read" event
        arg = [text]
        self.app.env.events.emit("source-read", doc, arg)
        text = arg[0]
        # split back into lines and reattach the two marker lines
        processed_lines = text.splitlines()
        processed_lines += include_lines[-2:]
        # call the parent implementation
        return super().insert_input(include_lines, path)


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

    def parse(self, inputstring: str | StringList, document: nodes.document) -> None:
        """Parse text and generate a document tree."""
        self.setup_parse(inputstring, document)  # type: ignore
        self.statemachine = RSTStateMachine(
            self.env.app,
            state_classes=self.state_classes,
            initial_state=self.initial_state,
            debug=document.reporter.debug_flag)

        # preprocess inputstring
        if isinstance(inputstring, str):
            lines = docutils.statemachine.string2lines(
                inputstring, tab_width=document.settings.tab_width,
                convert_whitespace=True)

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


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_source_parser(RSTParser)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
