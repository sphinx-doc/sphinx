"""
    sphinx.parsers
    ~~~~~~~~~~~~~~

    A Base class for additional parsers.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import docutils.parsers
import docutils.parsers.rst
from docutils.parsers.rst import states
from docutils.statemachine import StringList
from docutils.transforms.universal import SmartQuotes

from sphinx.util.rst import append_epilog, prepend_prolog

if False:
    # For type annotation
    from typing import Any, Dict, List, Union  # NOQA
    from typing import Type  # for python3.5.1
    from docutils import nodes  # NOQA
    from docutils.transforms import Transform  # NOQA
    from sphinx.application import Sphinx  # NOQA


class Parser(docutils.parsers.Parser):
    """
    A base class of source parsers.  The additional parsers should inherit this class instead
    of ``docutils.parsers.Parser``.  Compared with ``docutils.parsers.Parser``, this class
    improves accessibility to Sphinx APIs.

    The subclasses can access following objects and functions:

    self.app
        The application object (:class:`sphinx.application.Sphinx`)
    self.config
        The config object (:class:`sphinx.config.Config`)
    self.env
        The environment object (:class:`sphinx.environment.BuildEnvironment`)
    self.warn()
        Emit a warning. (Same as :meth:`sphinx.application.Sphinx.warn()`)
    self.info()
        Emit a informational message. (Same as :meth:`sphinx.application.Sphinx.info()`)

    .. deprecated:: 1.6
       ``warn()`` and ``info()`` is deprecated.  Use :mod:`sphinx.util.logging` instead.
    """

    def set_application(self, app):
        # type: (Sphinx) -> None
        """set_application will be called from Sphinx to set app and other instance variables

        :param sphinx.application.Sphinx app: Sphinx application object
        """
        self.app = app
        self.config = app.config
        self.env = app.env


class RSTParser(docutils.parsers.rst.Parser, Parser):
    """A reST parser for Sphinx."""

    def get_transforms(self):
        # type: () -> List[Type[Transform]]
        """Sphinx's reST parser replaces a transform class for smart-quotes by own's

        refs: sphinx.io.SphinxStandaloneReader
        """
        transforms = super().get_transforms()
        transforms.remove(SmartQuotes)
        return transforms

    def parse(self, inputstring, document):
        # type: (Union[str, StringList], nodes.document) -> None
        """Parse text and generate a document tree."""
        self.setup_parse(inputstring, document)  # type: ignore
        self.statemachine = states.RSTStateMachine(
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

    def decorate(self, content):
        # type: (StringList) -> None
        """Preprocess reST content before parsing."""
        prepend_prolog(content, self.config.rst_prolog)
        append_epilog(content, self.config.rst_epilog)


def setup(app):
    # type: (Sphinx) -> Dict[str, Any]
    app.add_source_parser(RSTParser)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
