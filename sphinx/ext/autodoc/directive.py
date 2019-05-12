"""
    sphinx.ext.autodoc.directive
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings

from docutils import nodes
from docutils.parsers.rst.states import Struct
from docutils.statemachine import StringList
from docutils.utils import assemble_option_dict

from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.ext.autodoc import Options, get_documenters
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective, switch_source_input
from sphinx.util.nodes import nested_parse_with_titles

if False:
    # For type annotation
    from typing import Any, Callable, Dict, List, Set, Type  # NOQA
    from docutils.parsers.rst.state import RSTState  # NOQA
    from docutils.utils import Reporter  # NOQA
    from sphinx.config import Config  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA
    from sphinx.ext.autodoc import Documenter  # NOQA

logger = logging.getLogger(__name__)


# common option names for autodoc directives
AUTODOC_DEFAULT_OPTIONS = ['members', 'undoc-members', 'inherited-members',
                           'show-inheritance', 'private-members', 'special-members',
                           'ignore-module-all', 'exclude-members', 'member-order',
                           'imported-members']


class DummyOptionSpec(dict):
    """An option_spec allows any options."""

    def __bool__(self):
        # type: () -> bool
        """Behaves like some options are defined."""
        return True

    def __getitem__(self, key):
        # type: (str) -> Callable[[str], str]
        return lambda x: x


class DocumenterBridge:
    """A parameters container for Documenters."""

    def __init__(self, env, reporter, options, lineno, state=None):
        # type: (BuildEnvironment, Reporter, Options, int, Any) -> None
        self.env = env
        self.reporter = reporter
        self.genopt = options
        self.lineno = lineno
        self.filename_set = set()  # type: Set[str]
        self.result = StringList()

        if state:
            self.state = state
        else:
            # create fake object for self.state.document.settings.tab_width
            warnings.warn('DocumenterBridge requires a state object on instantiation.',
                          RemovedInSphinx40Warning)
            settings = Struct(tab_width=8)
            document = Struct(settings=settings)
            self.state = Struct(document=document)

    def warn(self, msg):
        # type: (str) -> None
        logger.warning(msg, location=(self.env.docname, self.lineno))


def process_documenter_options(documenter, config, options):
    # type: (Type[Documenter], Config, Dict) -> Options
    """Recognize options of Documenter from user input."""
    for name in AUTODOC_DEFAULT_OPTIONS:
        if name not in documenter.option_spec:
            continue
        else:
            negated = options.pop('no-' + name, True) is None
            if name in config.autodoc_default_options and not negated:
                options[name] = config.autodoc_default_options[name]

    return Options(assemble_option_dict(options.items(), documenter.option_spec))


def parse_generated_content(state, content, documenter):
    # type: (RSTState, StringList, Documenter) -> List[nodes.Node]
    """Parse a generated content by Documenter."""
    with switch_source_input(state, content):
        if documenter.titles_allowed:
            node = nodes.section()  # type: nodes.Element
            # necessary so that the child nodes get the right source/line set
            node.document = state.document
            nested_parse_with_titles(state, content, node)
        else:
            node = nodes.paragraph()
            node.document = state.document
            state.nested_parse(content, 0, node)

        return node.children


class AutodocDirective(SphinxDirective):
    """A directive class for all autodoc directives. It works as a dispatcher of Documenters.

    It invokes a Documenter on running. After the processing, it parses and returns
    the generated content by Documenter.
    """
    option_spec = DummyOptionSpec()
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        # type: () -> List[nodes.Node]
        reporter = self.state.document.reporter

        try:
            source, lineno = reporter.get_source_and_line(self.lineno)  # type: ignore
        except AttributeError:
            source, lineno = (None, None)
        logger.debug('[autodoc] %s:%s: input:\n%s', source, lineno, self.block_text)

        # look up target Documenter
        objtype = self.name[4:]  # strip prefix (auto-).
        doccls = get_documenters(self.env.app)[objtype]

        # process the options with the selected documenter's option_spec
        try:
            documenter_options = process_documenter_options(doccls, self.config, self.options)
        except (KeyError, ValueError, TypeError) as exc:
            # an option is either unknown or has a wrong type
            logger.error('An option to %s is either unknown or has an invalid value: %s' %
                         (self.name, exc), location=(source, lineno))
            return []

        # generate the output
        params = DocumenterBridge(self.env, reporter, documenter_options, lineno, self.state)
        documenter = doccls(params, self.arguments[0])
        documenter.generate(more_content=self.content)
        if not params.result:
            return []

        logger.debug('[autodoc] output:\n%s', '\n'.join(params.result))

        # record all filenames as dependencies -- this will at least
        # partially make automatic invalidation possible
        for fn in params.filename_set:
            self.state.document.settings.record_dependencies.add(fn)

        result = parse_generated_content(self.state, params.result, documenter)
        return result
