"""
    sphinx.util.docutils
    ~~~~~~~~~~~~~~~~~~~~

    Utility functions for docutils.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import types
import warnings
from contextlib import contextmanager
from copy import copy
from distutils.version import LooseVersion
from os import path
from typing import IO, cast

import docutils
from docutils import nodes
from docutils.io import FileOutput
from docutils.parsers.rst import Directive, directives, roles, convert_directive_function
from docutils.statemachine import StateMachine
from docutils.utils import Reporter, unescape

from sphinx.deprecation import RemovedInSphinx30Warning
from sphinx.errors import ExtensionError, SphinxError
from sphinx.locale import __
from sphinx.util import logging

logger = logging.getLogger(__name__)
report_re = re.compile('^(.+?:(?:\\d+)?): \\((DEBUG|INFO|WARNING|ERROR|SEVERE)/(\\d+)?\\) ')

if False:
    # For type annotation
    from types import ModuleType  # NOQA
    from typing import Any, Callable, Dict, Generator, List, Set, Tuple, Type  # NOQA
    from docutils.parsers.rst.states import Inliner  # NOQA
    from docutils.statemachine import State, StringList  # NOQA
    from sphinx.builders import Builder  # NOQA
    from sphinx.config import Config  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA
    from sphinx.util.typing import RoleFunction  # NOQA


__version_info__ = tuple(LooseVersion(docutils.__version__).version)
additional_nodes = set()  # type: Set[Type[nodes.Element]]


@contextmanager
def docutils_namespace():
    # type: () -> Generator[None, None, None]
    """Create namespace for reST parsers."""
    try:
        _directives = copy(directives._directives)  # type: ignore
        _roles = copy(roles._roles)  # type: ignore

        yield
    finally:
        directives._directives = _directives  # type: ignore
        roles._roles = _roles  # type: ignore

        for node in list(additional_nodes):
            unregister_node(node)
            additional_nodes.discard(node)


def is_directive_registered(name):
    # type: (str) -> bool
    """Check the *name* directive is already registered."""
    return name in directives._directives  # type: ignore


def register_directive(name, directive):
    # type: (str, Type[Directive]) -> None
    """Register a directive to docutils.

    This modifies global state of docutils.  So it is better to use this
    inside ``docutils_namespace()`` to prevent side-effects.
    """
    directives.register_directive(name, directive)


def is_role_registered(name):
    # type: (str) -> bool
    """Check the *name* role is already registered."""
    return name in roles._roles  # type: ignore


def register_role(name, role):
    # type: (str, RoleFunction) -> None
    """Register a role to docutils.

    This modifies global state of docutils.  So it is better to use this
    inside ``docutils_namespace()`` to prevent side-effects.
    """
    roles.register_local_role(name, role)


def unregister_role(name):
    # type: (str) -> None
    """Unregister a role from docutils."""
    roles._roles.pop(name, None)  # type: ignore


def is_node_registered(node):
    # type: (Type[nodes.Element]) -> bool
    """Check the *node* is already registered."""
    return hasattr(nodes.GenericNodeVisitor, 'visit_' + node.__name__)


def register_node(node):
    # type: (Type[nodes.Element]) -> None
    """Register a node to docutils.

    This modifies global state of some visitors.  So it is better to use this
    inside ``docutils_namespace()`` to prevent side-effects.
    """
    if not hasattr(nodes.GenericNodeVisitor, 'visit_' + node.__name__):
        nodes._add_node_class_names([node.__name__])  # type: ignore
        additional_nodes.add(node)


def unregister_node(node):
    # type: (Type[nodes.Element]) -> None
    """Unregister a node from docutils.

    This is inverse of ``nodes._add_nodes_class_names()``.
    """
    if hasattr(nodes.GenericNodeVisitor, 'visit_' + node.__name__):
        delattr(nodes.GenericNodeVisitor, "visit_" + node.__name__)
        delattr(nodes.GenericNodeVisitor, "depart_" + node.__name__)
        delattr(nodes.SparseNodeVisitor, 'visit_' + node.__name__)
        delattr(nodes.SparseNodeVisitor, 'depart_' + node.__name__)


@contextmanager
def patched_get_language():
    # type: () -> Generator[None, None, None]
    """Patch docutils.languages.get_language() temporarily.

    This ignores the second argument ``reporter`` to suppress warnings.
    refs: https://github.com/sphinx-doc/sphinx/issues/3788
    """
    from docutils.languages import get_language

    def patched_get_language(language_code, reporter=None):
        # type: (str, Reporter) -> Any
        return get_language(language_code)

    try:
        docutils.languages.get_language = patched_get_language
        yield
    finally:
        # restore original implementations
        docutils.languages.get_language = get_language


@contextmanager
def using_user_docutils_conf(confdir):
    # type: (str) -> Generator[None, None, None]
    """Let docutils know the location of ``docutils.conf`` for Sphinx."""
    try:
        docutilsconfig = os.environ.get('DOCUTILSCONFIG', None)
        if confdir:
            os.environ['DOCUTILSCONFIG'] = path.join(path.abspath(confdir), 'docutils.conf')

        yield
    finally:
        if docutilsconfig is None:
            os.environ.pop('DOCUTILSCONFIG', None)
        else:
            os.environ['DOCUTILSCONFIG'] = docutilsconfig


@contextmanager
def patch_docutils(confdir=None):
    # type: (str) -> Generator[None, None, None]
    """Patch to docutils temporarily."""
    with patched_get_language(), using_user_docutils_conf(confdir):
        yield


class ElementLookupError(Exception):
    pass


class sphinx_domains:
    """Monkey-patch directive and role dispatch, so that domain-specific
    markup takes precedence.
    """
    def __init__(self, env):
        # type: (BuildEnvironment) -> None
        self.env = env
        self.directive_func = None  # type: Callable
        self.roles_func = None  # type: Callable

    def __enter__(self):
        # type: () -> None
        self.enable()

    def __exit__(self, type, value, traceback):
        # type: (str, str, str) -> None
        self.disable()

    def enable(self):
        # type: () -> None
        self.directive_func = directives.directive
        self.role_func = roles.role

        directives.directive = self.lookup_directive  # type: ignore
        roles.role = self.lookup_role  # type: ignore

    def disable(self):
        # type: () -> None
        directives.directive = self.directive_func
        roles.role = self.role_func

    def lookup_domain_element(self, type, name):
        # type: (str, str) -> Any
        """Lookup a markup element (directive or role), given its name which can
        be a full name (with domain).
        """
        name = name.lower()
        # explicit domain given?
        if ':' in name:
            domain_name, name = name.split(':', 1)
            if domain_name in self.env.domains:
                domain = self.env.get_domain(domain_name)
                element = getattr(domain, type)(name)
                if element is not None:
                    return element, []
        # else look in the default domain
        else:
            def_domain = self.env.temp_data.get('default_domain')
            if def_domain is not None:
                element = getattr(def_domain, type)(name)
                if element is not None:
                    return element, []

        # always look in the std domain
        element = getattr(self.env.get_domain('std'), type)(name)
        if element is not None:
            return element, []

        raise ElementLookupError

    def lookup_directive(self, name, lang_module, document):
        # type: (str, ModuleType, nodes.document) -> Tuple[Type[Directive], List[nodes.system_message]]  # NOQA
        try:
            return self.lookup_domain_element('directive', name)
        except ElementLookupError:
            return self.directive_func(name, lang_module, document)

    def lookup_role(self, name, lang_module, lineno, reporter):
        # type: (str, ModuleType, int, Reporter) -> Tuple[RoleFunction, List[nodes.system_message]]  # NOQA
        try:
            return self.lookup_domain_element('role', name)
        except ElementLookupError:
            return self.role_func(name, lang_module, lineno, reporter)


class WarningStream:
    def write(self, text):
        # type: (str) -> None
        matched = report_re.search(text)
        if not matched:
            logger.warning(text.rstrip("\r\n"))
        else:
            location, type, level = matched.groups()
            message = report_re.sub('', text).rstrip()
            logger.log(type, message, location=location)


class LoggingReporter(Reporter):
    @classmethod
    def from_reporter(cls, reporter):
        # type: (Reporter) -> LoggingReporter
        """Create an instance of LoggingReporter from other reporter object."""
        return cls(reporter.source, reporter.report_level, reporter.halt_level,
                   reporter.debug_flag, reporter.error_handler)

    def __init__(self, source, report_level=Reporter.WARNING_LEVEL,
                 halt_level=Reporter.SEVERE_LEVEL, debug=False,
                 error_handler='backslashreplace'):
        # type: (str, int, int, bool, str) -> None
        stream = cast(IO, WarningStream())
        super().__init__(source, report_level, halt_level,
                         stream, debug, error_handler=error_handler)


class NullReporter(Reporter):
    """A dummy reporter; write nothing."""

    def __init__(self):
        # type: () -> None
        super().__init__('', 999, 4)


def is_html5_writer_available():
    # type: () -> bool
    return __version_info__ > (0, 13, 0)


def directive_helper(obj, has_content=None, argument_spec=None, **option_spec):
    # type: (Any, bool, Tuple[int, int, bool], Any) -> Any
    warnings.warn('function based directive support is now deprecated. '
                  'Use class based directive instead.',
                  RemovedInSphinx30Warning)

    if isinstance(obj, (types.FunctionType, types.MethodType)):
        obj.content = has_content                       # type: ignore
        obj.arguments = argument_spec or (0, 0, False)  # type: ignore
        obj.options = option_spec                       # type: ignore
        return convert_directive_function(obj)
    else:
        if has_content or argument_spec or option_spec:
            raise ExtensionError(__('when adding directive classes, no '
                                    'additional arguments may be given'))
        return obj


@contextmanager
def switch_source_input(state, content):
    # type: (State, StringList) -> Generator[None, None, None]
    """Switch current source input of state temporarily."""
    try:
        # remember the original ``get_source_and_line()`` method
        get_source_and_line = state.memo.reporter.get_source_and_line  # type: ignore

        # replace it by new one
        state_machine = StateMachine([], None)
        state_machine.input_lines = content
        state.memo.reporter.get_source_and_line = state_machine.get_source_and_line  # type: ignore  # NOQA

        yield
    finally:
        # restore the method
        state.memo.reporter.get_source_and_line = get_source_and_line  # type: ignore


class SphinxFileOutput(FileOutput):
    """Better FileOutput class for Sphinx."""

    def __init__(self, **kwargs):
        # type: (Any) -> None
        self.overwrite_if_changed = kwargs.pop('overwrite_if_changed', False)
        super().__init__(**kwargs)

    def write(self, data):
        # type: (str) -> str
        if (self.destination_path and self.autoclose and 'b' not in self.mode and
                self.overwrite_if_changed and os.path.exists(self.destination_path)):
            with open(self.destination_path, encoding=self.encoding) as f:
                # skip writing: content not changed
                if f.read() == data:
                    return data

        return super().write(data)


class SphinxDirective(Directive):
    """A base class for Sphinx directives.

    This class provides helper methods for Sphinx directives.

    .. note:: The subclasses of this class might not work with docutils.
              This class is strongly coupled with Sphinx.
    """

    @property
    def env(self):
        # type: () -> BuildEnvironment
        """Reference to the :class:`.BuildEnvironment` object."""
        return self.state.document.settings.env

    @property
    def config(self):
        # type: () -> Config
        """Reference to the :class:`.Config` object."""
        return self.env.config

    def set_source_info(self, node):
        # type: (nodes.Node) -> None
        """Set source and line number to the node."""
        node.source, node.line = self.state_machine.get_source_and_line(self.lineno)


class SphinxRole:
    """A base class for Sphinx roles.

    This class provides helper methods for Sphinx roles.

    .. note:: The subclasses of this class might not work with docutils.
              This class is strongly coupled with Sphinx.
    """
    name = None     #: The role name actually used in the document.
    rawtext = None  #: A string containing the entire interpreted text input.
    text = None     #: The interpreted text content.
    lineno = None   #: The line number where the interpreted text begins.
    inliner = None  #: The ``docutils.parsers.rst.states.Inliner`` object.
    options = None  #: A dictionary of directive options for customization
                    #: (from the "role" directive).
    content = None  #: A list of strings, the directive content for customization
                    #: (from the "role" directive).

    def __call__(self, name, rawtext, text, lineno, inliner, options={}, content=[]):
        # type: (str, str, str, int, Inliner, Dict, List[str]) -> Tuple[List[nodes.Node], List[nodes.system_message]]  # NOQA
        self.rawtext = rawtext
        self.text = unescape(text)
        self.lineno = lineno
        self.inliner = inliner
        self.options = options
        self.content = content

        # guess role type
        if name:
            self.name = name.lower()
        else:
            self.name = self.env.temp_data.get('default_role')
            if not self.name:
                self.name = self.env.config.default_role
            if not self.name:
                raise SphinxError('cannot determine default role!')

        return self.run()

    def run(self):
        # type: () -> Tuple[List[nodes.Node], List[nodes.system_message]]
        raise NotImplementedError

    @property
    def env(self):
        # type: () -> BuildEnvironment
        """Reference to the :class:`.BuildEnvironment` object."""
        return self.inliner.document.settings.env

    @property
    def config(self):
        # type: () -> Config
        """Reference to the :class:`.Config` object."""
        return self.env.config

    def set_source_info(self, node, lineno=None):
        # type: (nodes.Node, int) -> None
        if lineno is None:
            lineno = self.lineno

        source_info = self.inliner.reporter.get_source_and_line(lineno)  # type: ignore
        node.source, node.line = source_info


class ReferenceRole(SphinxRole):
    """A base class for reference roles.

    The reference roles can accpet ``link title <target>`` style as a text for
    the role.  The parsed result; link title and target will be stored to
    ``self.title`` and ``self.target``.
    """
    has_explicit_title = None   #: A boolean indicates the role has explicit title or not.
    title = None                #: The link title for the interpreted text.
    target = None               #: The link target for the interpreted text.

    # \x00 means the "<" was backslash-escaped
    explicit_title_re = re.compile(r'^(.+?)\s*(?<!\x00)<(.*?)>$', re.DOTALL)

    def __call__(self, name, rawtext, text, lineno, inliner, options={}, content=[]):
        # type: (str, str, str, int, Inliner, Dict, List[str]) -> Tuple[List[nodes.Node], List[nodes.system_message]]  # NOQA
        matched = self.explicit_title_re.match(text)
        if matched:
            self.has_explicit_title = True
            self.title = unescape(matched.group(1))
            self.target = unescape(matched.group(2))
        else:
            self.has_explicit_title = False
            self.title = unescape(text)
            self.target = unescape(text)

        return super().__call__(name, rawtext, text, lineno, inliner, options, content)


class SphinxTranslator(nodes.NodeVisitor):
    """A base class for Sphinx translators.

    This class provides helper methods for Sphinx translators.

    .. note:: The subclasses of this class might not work with docutils.
              This class is strongly coupled with Sphinx.
    """

    def __init__(self, document, builder):
        # type: (nodes.document, Builder) -> None
        super().__init__(document)
        self.builder = builder
        self.config = builder.config
        self.settings = document.settings


# cache a vanilla instance of nodes.document
# Used in new_document() function
__document_cache__ = None  # type: nodes.document


def new_document(source_path, settings=None):
    # type: (str, Any) -> nodes.document
    """Return a new empty document object.  This is an alternative of docutils'.

    This is a simple wrapper for ``docutils.utils.new_document()``.  It
    caches the result of docutils' and use it on second call for instanciation.
    This makes an instantiation of document nodes much faster.
    """
    global __document_cache__
    if __document_cache__ is None:
        __document_cache__ = docutils.utils.new_document(source_path)

    if settings is None:
        # Make a copy of ``settings`` from cache to accelerate instansiation
        settings = copy(__document_cache__.settings)

    # Create a new instance of nodes.document using cached reporter
    document = nodes.document(settings, __document_cache__.reporter, source=source_path)
    document.note_source(source_path, -1)
    return document
