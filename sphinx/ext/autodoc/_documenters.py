from __future__ import annotations

import functools
import operator
import re
import sys
from inspect import Parameter, Signature
from typing import TYPE_CHECKING, NewType, TypeVar

from docutils.statemachine import StringList

from sphinx.errors import PycodeError
from sphinx.ext.autodoc._directive_options import (
    annotation_option,
    bool_option,
    class_doc_from_option,
    exclude_members_option,
    identity,
    inherited_members_option,
    member_order_option,
    members_option,
)
from sphinx.ext.autodoc._member_finder import _filter_members, _get_members_to_document
from sphinx.ext.autodoc._sentinels import (
    ALL,
    RUNTIME_INSTANCE_ATTRIBUTE,
    SLOTS_ATTR,
    SUPPRESS,
    UNINITIALIZED_ATTR,
)
from sphinx.ext.autodoc.importer import (
    _get_attribute_comment,
    _is_runtime_instance_attribute_not_commented,
    _load_object_by_name,
    _resolve_name,
)
from sphinx.ext.autodoc.mock import ismock
from sphinx.locale import _, __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.docstrings import prepare_docstring, separate_metadata
from sphinx.util.inspect import (
    evaluate_signature,
    getdoc,
    object_description,
    safe_getattr,
    stringify_signature,
)
from sphinx.util.typing import get_type_hints, restify, stringify_annotation

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from types import ModuleType
    from typing import Any, ClassVar, Literal

    from sphinx.config import Config
    from sphinx.environment import BuildEnvironment, _CurrentDocument
    from sphinx.events import EventManager
    from sphinx.ext.autodoc._directive_options import _AutoDocumenterOptions
    from sphinx.ext.autodoc._property_types import (
        _AssignStatementProperties,
        _ClassDefProperties,
        _FunctionDefProperties,
        _ItemProperties,
        _ModuleProperties,
    )
    from sphinx.ext.autodoc.directive import DocumenterBridge
    from sphinx.registry import SphinxComponentRegistry
    from sphinx.util.typing import OptionSpec, _RestifyMode

logger = logging.getLogger('sphinx.ext.autodoc')

#: extended signature RE: with explicit module name separated by ::
py_ext_sig_re = re.compile(
    r"""^ ([\w.]+::)?            # explicit module name
          ([\w.]+\.)?            # module and/or class name(s)
          (\w+)  \s*             # thing name
          (?: \[\s*(.*?)\s*])?   # optional: type parameters list
          (?: \((.*)\)           # optional: arguments
           (?:\s* -> \s* (.*))?  #           return annotation
          )? $                   # and nothing more
    """,
    re.VERBOSE,
)


def _get_render_mode(
    typehints_format: Literal['fully-qualified', 'short'],
) -> _RestifyMode:
    if typehints_format == 'short':
        return 'smart'
    return 'fully-qualified-except-typing'


class Documenter:
    """A Documenter knows how to autodocument a single object type.  When
    registered with the AutoDirective, it will be used to document objects
    of that type when needed by autodoc.

    Its *objtype* attribute selects what auto directive it is assigned to
    (the directive name is 'auto' + objtype), and what directive it generates
    by default, though that can be overridden by an attribute called
    *directivetype*.

    A Documenter has an *option_spec* that works like a docutils directive's;
    in fact, it will be used to parse an auto directive's options that matches
    the Documenter.
    """

    props: _ItemProperties

    #: name by which the directive is called (auto...) and the default
    #: generated directive name
    objtype: ClassVar = 'object'
    #: indentation by which to indent the directive content
    content_indent: ClassVar = '   '
    #: priority if multiple documenters return True from can_document_member
    priority: ClassVar = 0
    #: order if autodoc_member_order is set to 'groupwise'
    member_order: ClassVar = 0
    #: true if the generated content may contain titles
    titles_allowed: ClassVar = True

    __docstring_signature__: ClassVar[bool] = False
    """If True, attempt to read the signature from the docstring."""

    __docstring_strip_signature__: ClassVar[bool] = False
    """If True, strip any function signature from the docstring."""

    __uninitialized_global_variable__: ClassVar[bool] = False
    """If True, support uninitialized (type annotation only) global variables"""

    _new_docstrings: list[list[str]] | None = None
    _signatures: list[str] = []

    option_spec: ClassVar[OptionSpec] = {
        'no-index': bool_option,
        'no-index-entry': bool_option,
        'noindex': bool_option,
    }

    def get_attr(self, obj: Any, name: str, *defargs: Any) -> Any:
        """getattr() override for types such as Zope interfaces."""
        return autodoc_attrgetter(obj, name, *defargs, registry=self.env._registry)

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        """Called to see if a member can be documented by this Documenter."""
        msg = 'must be implemented in subclasses'
        raise NotImplementedError(msg)

    def __init__(
        self, directive: DocumenterBridge, name: str, indent: str = ''
    ) -> None:
        self.directive = directive
        self.config: Config = directive.env.config
        self.env: BuildEnvironment = directive.env
        self._current_document: _CurrentDocument = directive.env.current_document
        self._events: EventManager = directive.env.events
        self.options: _AutoDocumenterOptions = directive.genopt
        self.name = name
        self.indent = indent
        # the module and object path within the module, and the fully
        # qualified name (all set after resolve_name succeeds)
        self.modname: str = ''
        self.module: ModuleType | None = None
        self.objpath: list[str] = []
        self.fullname = ''
        # extra signature items (arguments and return annotation,
        # also set after resolve_name succeeds)
        self.args: str | None = None
        self.retann: str | None = ''
        # the object to document (set after import_object succeeds)
        self.object: Any = None
        self.object_name = ''
        # the parent/owner of the object to document
        self.parent: Any = None
        # the module analyzer to get at attribute docs, or None
        self.analyzer: ModuleAnalyzer | None = None

        self._load_object_has_been_called = False

    @property
    def documenters(self) -> dict[str, type[Documenter]]:
        """Returns registered Documenter classes"""
        return self.env._registry.documenters

    def add_line(self, line: str, source: str, *lineno: int) -> None:
        """Append one line of generated reST to the output."""
        if line.strip():  # not a blank line
            self.directive.result.append(self.indent + line, source, *lineno)
        else:
            self.directive.result.append('', source, *lineno)

    def _load_object_by_name(self) -> Literal[True] | None:
        if self._load_object_has_been_called:
            return True

        ret = _load_object_by_name(
            name=self.name,
            objtype=self.objtype,
            mock_imports=self.config.autodoc_mock_imports,
            type_aliases=self.config.autodoc_type_aliases,
            current_document=self._current_document,
            env=self.env,
            get_attr=self.get_attr,
        )
        if ret is None:
            return None
        props, args, retann, module, parent = ret

        self.props = props
        self.args = args
        self.retann = retann
        self.modname = props.module_name
        self.objpath = list(props.parts)
        self.fullname = props.full_name
        self.module = module
        self.parent = parent
        self.object_name = props.object_name
        self.object = props._obj
        if self.objtype == 'method':
            if 'staticmethod' in props.properties:  # type: ignore[attr-defined]
                # document static members before regular methods
                self.member_order -= 1  # type: ignore[misc]
            elif 'classmethod' in props.properties:  # type: ignore[attr-defined]
                # document class methods before static methods as
                # they usually behave as alternative constructors
                self.member_order -= 2  # type: ignore[misc]
        self._load_object_has_been_called = True
        return True

    def resolve_name(
        self, modname: str | None, parents: Any, path: str, base: str
    ) -> tuple[str | None, list[str]]:
        """Resolve the module and name of the object to document given by the
        arguments and the current module/class.

        Must return a pair of the module name and a chain of attributes; for
        example, it would return ``('zipfile', ['ZipFile', 'open'])`` for the
        ``zipfile.ZipFile.open`` method.
        """
        ret = _resolve_name(
            objtype=self.objtype,
            module_name=modname,
            path=path,
            base=base,
            parents=parents,
            current_document=self._current_document,
            ref_context_py_module=self.env.ref_context.get('py:module'),
            ref_context_py_class=self.env.ref_context.get('py:class', ''),
        )
        if ret is not None:
            module_name, parts = ret
            return module_name, list(parts)

        msg = 'must be implemented in subclasses'
        raise NotImplementedError(msg)

    def parse_name(self) -> bool:
        """Determine what module to import and what attribute to document.

        Returns True and sets *self.modname*, *self.objpath*, *self.fullname*,
        *self.args* and *self.retann* if parsing and resolving was successful.
        """
        return self._load_object_by_name() is not None

    def import_object(self, raiseerror: bool = False) -> bool:
        """Import the object given by *self.modname* and *self.objpath* and set
        it as *self.object*.

        Returns True if successful, False if an error occurred.
        """
        return self._load_object_by_name() is not None

    def get_real_modname(self) -> str:
        """Get the real module name of an object to document.

        It can differ from the name of the module through which the object was
        imported.
        """
        return self.props._obj___module__ or self.props.module_name

    def check_module(self) -> bool:
        """Check if *self.object* is really defined in the module given by
        *self.modname*.
        """
        if self.options.imported_members:
            return True

        subject = inspect.unpartial(self.props._obj)
        modname = self.get_attr(subject, '__module__', None)
        return not modname or modname == self.props.module_name

    def format_args(self, **kwargs: Any) -> str:
        """Format the argument signature of *self.object*.

        Should return None if the object does not have a signature.
        """
        return ''

    def format_name(self) -> str:
        """Format the name of *self.object*.

        This normally should be something that can be parsed by the generated
        directive, but doesn't need to be (Sphinx will display it unparsed
        then).
        """
        # normally the name doesn't contain the module (except for module
        # directives of course)
        return self.props.dotted_parts or self.props.module_name

    def _call_format_args(self, **kwargs: Any) -> str:
        if kwargs:
            try:
                return self.format_args(**kwargs)
            except TypeError:
                # avoid chaining exceptions, by putting nothing here
                pass

        # retry without arguments for old documenters
        return self.format_args()

    def _find_signature(self) -> tuple[str | None, str | None] | None:
        # candidates of the object name
        valid_names = [self.props.parts[-1]]
        if isinstance(self, ClassDocumenter):
            valid_names.append('__init__')
            if hasattr(self.props._obj, '__mro__'):
                valid_names.extend(cls.__name__ for cls in self.props._obj.__mro__)

        docstrings = self.get_doc()
        if docstrings is None:
            return None, None
        self._new_docstrings = docstrings[:]
        self._signatures = []
        result = None
        for i, doclines in enumerate(docstrings):
            for j, line in enumerate(doclines):
                if not line:
                    # no lines in docstring, no match
                    break

                if line.endswith('\\'):
                    line = line.rstrip('\\').rstrip()

                # match first line of docstring against signature RE
                match = py_ext_sig_re.match(line)
                if not match:
                    break
                _exmod, _path, base, _tp_list, args, retann = match.groups()

                # the base name must match ours
                if base not in valid_names:
                    break

                # re-prepare docstring to ignore more leading indentation
                directive = self.directive
                tab_width = directive.state.document.settings.tab_width
                self._new_docstrings[i] = prepare_docstring(
                    '\n'.join(doclines[j + 1 :]), tab_width
                )

                if result is None:
                    # first signature
                    result = args, retann
                else:
                    # subsequent signatures
                    self._signatures.append(f'({args}) -> {retann}')

            if result is not None:
                # finish the loop when signature found
                break

        return result

    def format_signature(self, **kwargs: Any) -> str:
        """Format the signature (arguments and return annotation) of the object.

        Let the user process it via the ``autodoc-process-signature`` event.
        """
        if (
            self.__docstring_signature__
            and self.args is None
            and self.config.autodoc_docstring_signature
        ):
            # only act if a signature is not explicitly given already, and if
            # the feature is enabled
            result = self._find_signature()
            if result is not None:
                if self.__docstring_strip_signature__:
                    # Discarding _args is the only difference.
                    # Documenter.format_signature use self.args value to format.
                    _args, self.retann = result
                else:
                    self.args, self.retann = result

        if self.args is not None:
            # signature given explicitly
            args = f'({self.args})'
            retann = self.retann
        else:
            # try to introspect the signature
            try:
                retann = None
                args = self._call_format_args(**kwargs)
                if args:
                    matched = re.match(r'^(\(.*\))\s+->\s+(.*)$', args)
                    if matched:
                        args = matched.group(1)
                        retann = matched.group(2)
            except Exception as exc:
                msg = __('error while formatting arguments for %s: %s')
                logger.warning(msg, self.props.full_name, exc, type='autodoc')
                args = None

        result = self._events.emit_firstresult(
            'autodoc-process-signature',
            self.objtype,
            self.props.full_name,
            self.props._obj,
            self.options,
            args,
            retann,
        )
        if result:
            args, retann = result

        if args is not None:
            if retann:
                sig = f'{args} -> {retann}'
            else:
                sig = args
        else:
            sig = ''

        if self.__docstring_signature__ and self._signatures:
            return '\n'.join((sig, *self._signatures))
        return sig

    def add_directive_header(self, sig: str) -> None:
        """Add the directive header and options to the generated content."""
        domain = getattr(self, 'domain', 'py')
        directive = getattr(self, 'directivetype', self.objtype)
        name = self.format_name()
        sourcename = self.get_sourcename()

        # one signature per line, indented by column
        prefix = f'.. {domain}:{directive}:: '
        for i, sig_line in enumerate(sig.split('\n')):
            self.add_line(f'{prefix}{name}{sig_line}', sourcename)
            if i == 0:
                prefix = ' ' * len(prefix)

        if self.options.no_index or self.options.noindex:
            self.add_line('   :no-index:', sourcename)
        if self.options.no_index_entry:
            self.add_line('   :no-index-entry:', sourcename)
        if self.props.parts:
            # Be explicit about the module, this is necessary since .. class::
            # etc. don't support a prepended module name
            self.add_line('   :module: %s' % self.props.module_name, sourcename)

    def get_doc(self) -> list[list[str]] | None:
        """Decode and return lines of the docstring(s) for the object.

        When it returns None, autodoc-process-docstring will not be called for this
        object.
        """
        if self.props._obj is UNINITIALIZED_ATTR:
            return []

        if self.__docstring_signature__ and self._new_docstrings is not None:
            return self._new_docstrings

        docstring = getdoc(
            self.props._obj,
            self.get_attr,
            self.config.autodoc_inherit_docstrings,
            self.parent,
            self.props.object_name,
        )
        if docstring:
            tab_width = self.directive.state.document.settings.tab_width
            return [prepare_docstring(docstring, tab_width)]
        return []

    def process_doc(self, docstrings: list[list[str]]) -> Iterator[str]:
        """Let the user process the docstrings before adding them."""
        for docstringlines in docstrings:
            if self._events is not None:
                # let extensions preprocess docstrings
                self._events.emit(
                    'autodoc-process-docstring',
                    self.objtype,
                    self.props.full_name,
                    self.props._obj,
                    self.options,
                    docstringlines,
                )

                if docstringlines and docstringlines[-1]:
                    # append a blank line to the end of the docstring
                    docstringlines.append('')

            yield from docstringlines

    def get_sourcename(self) -> str:
        obj_module = inspect.safe_getattr(self.props._obj, '__module__', None)
        obj_qualname = inspect.safe_getattr(self.props._obj, '__qualname__', None)
        if obj_module and obj_qualname:
            # Get the correct location of docstring from self.object
            # to support inherited methods
            fullname = f'{self.props._obj.__module__}.{self.props._obj.__qualname__}'
        else:
            fullname = self.props.full_name

        if self.analyzer:
            return f'{self.analyzer.srcname}:docstring of {fullname}'
        else:
            return 'docstring of %s' % fullname

    def add_content(self, more_content: StringList | None) -> None:
        """Add content from docstrings, attribute documentation and user."""
        docstring = True

        # set sourcename and add content from attribute documentation
        sourcename = self.get_sourcename()
        if self.analyzer:
            attr_docs = self.analyzer.find_attr_docs()
            if self.props.parts:
                key = ('.'.join(self.props.parts[:-1]), self.props.parts[-1])
                if key in attr_docs:
                    docstring = False
                    # make a copy of docstring for attributes to avoid cache
                    # the change of autodoc-process-docstring event.
                    attribute_docstrings = [list(attr_docs[key])]

                    for i, line in enumerate(self.process_doc(attribute_docstrings)):
                        self.add_line(line, sourcename, i)

        # add content from docstrings
        if docstring:
            docstrings = self.get_doc()
            if docstrings is None:
                # Do not call autodoc-process-docstring on get_doc() returns None.
                pass
            else:
                if not docstrings:
                    # append at least a dummy docstring, so that the event
                    # autodoc-process-docstring is fired and can add some
                    # content if desired
                    docstrings.append([])
                for i, line in enumerate(self.process_doc(docstrings)):
                    self.add_line(line, sourcename, i)

        # add additional content (e.g. from document), if present
        if more_content:
            for line, src in zip(more_content.data, more_content.items, strict=True):
                self.add_line(line, src[0], src[1])

    def sort_members(
        self, documenters: list[tuple[Documenter, bool]], order: str
    ) -> list[tuple[Documenter, bool]]:
        """Sort the given member list."""
        if order == 'groupwise':
            # sort by group; alphabetically within groups
            documenters.sort(key=lambda e: (e[0].member_order, e[0].name))
        elif order == 'bysource':
            # By default, member discovery order matches source order,
            # as dicts are insertion-ordered from Python 3.7.
            if self.analyzer:
                # sort by source order, by virtue of the module analyzer
                tagorder = self.analyzer.tagorder

                def keyfunc(entry: tuple[Documenter, bool]) -> int:
                    fullname = entry[0].name.split('::')[1]
                    return tagorder.get(fullname, len(tagorder))

                documenters.sort(key=keyfunc)
        else:  # alphabetical
            documenters.sort(key=lambda e: e[0].name)

        return documenters

    def generate(
        self,
        more_content: StringList | None = None,
        real_modname: str | None = None,
        check_module: bool = False,
        all_members: bool = False,
    ) -> None:
        """Generate reST for the object given by *self.name*, and possibly for
        its members.

        If *more_content* is given, include that content. If *real_modname* is
        given, use that module name to find attribute docs. If *check_module* is
        True, only generate if the object is defined in the module name it is
        imported from. If *all_members* is True, document all members.
        """
        if self._load_object_by_name() is None:
            return

        self._generate(more_content, real_modname, check_module, all_members)

    def _generate(
        self,
        more_content: StringList | None = None,
        real_modname: str | None = None,
        check_module: bool = False,
        all_members: bool = False,
    ) -> None:
        has_members = isinstance(self, ModuleDocumenter) or (
            isinstance(self, ClassDocumenter) and not self.props.doc_as_attr
        )

        # If there is no real module defined, figure out which to use.
        # The real module is used in the module analyzer to look up the module
        # where the attribute documentation would actually be found in.
        # This is used for situations where you have a module that collects the
        # functions and classes of internal submodules.
        guess_modname = self.props._obj___module__ or self.props.module_name
        self.real_modname: str = real_modname or guess_modname

        # try to also get a source code analyzer for attribute docs
        try:
            self.analyzer = ModuleAnalyzer.for_module(self.real_modname)
            # parse right now, to get PycodeErrors on parsing (results will
            # be cached anyway)
            self.analyzer.find_attr_docs()
        except PycodeError as exc:
            logger.debug('[autodoc] module analyzer failed: %s', exc)
            # no source file -- e.g. for builtin and C modules
            self.analyzer = None
            # at least add the module.__file__ as a dependency
            if module___file__ := getattr(self.module, '__file__', ''):
                self.directive.record_dependencies.add(module___file__)
        else:
            self.directive.record_dependencies.add(self.analyzer.srcname)

        want_all = bool(
            all_members or self.options.inherited_members or self.options.members is ALL
        )
        if has_members:
            member_documenters = self._gather_members(
                want_all=want_all, indent=self.indent + self.content_indent
            )

        if self.real_modname != guess_modname:
            # Add module to dependency list if target object is defined in other module.
            try:
                analyzer = ModuleAnalyzer.for_module(guess_modname)
                self.directive.record_dependencies.add(analyzer.srcname)
            except PycodeError:
                pass

        docstrings: list[str] = functools.reduce(
            operator.iadd, self.get_doc() or [], []
        )
        if ismock(self.props._obj) and not docstrings:
            logger.warning(
                __('A mocked object is detected: %r'),
                self.name,
                type='autodoc',
                subtype='mocked_object',
            )

        # check __module__ of object (for members not given explicitly)
        if check_module and not self.options.imported_members:
            subject = inspect.unpartial(self.props._obj)
            modname = self.get_attr(subject, '__module__', None)
            if modname and modname != self.props.module_name:
                return

        sourcename = self.get_sourcename()

        # make sure that the result starts with an empty line.  This is
        # necessary for some situations where another directive preprocesses
        # reST and no starting newline is present
        self.add_line('', sourcename)

        # format the object's signature, if any
        try:
            sig = self.format_signature()
        except Exception as exc:
            msg = __('error while formatting signature for %s: %s')
            logger.warning(msg, self.props.full_name, exc, type='autodoc')
            return

        # generate the directive header and options, if applicable
        self.add_directive_header(sig)
        self.add_line('', sourcename)

        # e.g. the module directive doesn't have content
        self.indent += self.content_indent

        # add all content (from docstrings, attribute docs etc.)
        self.add_content(more_content)

        # document members, if possible
        if has_members:
            # for implicit module members, check __module__ to avoid
            # documenting imported objects
            members_check_module = bool(
                isinstance(self, ModuleDocumenter)
                and want_all
                and (self.options.ignore_module_all or self.props.all is None)
            )
            _document_members(
                member_documenters=member_documenters,
                real_modname=self.real_modname,
                members_check_module=members_check_module,
            )

    def _gather_members(
        self, *, want_all: bool, indent: str
    ) -> list[tuple[Documenter, bool]]:
        """Generate reST for member documentation.

        If *want_all* is True, document all members, else those given by
        *self.options.members*.
        """
        if not isinstance(self, (ModuleDocumenter, ClassDocumenter)):
            msg = 'must be implemented in subclasses'
            raise NotImplementedError(msg)

        current_document = self._current_document
        events = self._events
        registry = self.env._registry
        props = self.props

        # set current namespace for finding members
        current_document.autodoc_module = props.module_name
        if props.parts:
            current_document.autodoc_class = props.parts[0]

        inherited_members = frozenset(self.options.inherited_members or ())
        if self.analyzer:
            self.analyzer.analyze()
            attr_docs = self.analyzer.attr_docs
        else:
            attr_docs = {}
        found_members = _get_members_to_document(
            want_all=want_all,
            get_attr=self.get_attr,
            inherit_docstrings=self.config.autodoc_inherit_docstrings,
            props=props,
            opt_members=self.options.members or (),
            inherited_members=inherited_members,
            ignore_module_all=bool(self.options.ignore_module_all),
            attr_docs=attr_docs,
        )
        filtered_members = _filter_members(
            found_members,
            want_all=want_all,
            events=events,
            get_attr=self.get_attr,
            inherit_docstrings=self.config.autodoc_inherit_docstrings,
            options=self.options,
            orig_name=self.name,
            props=props,
            inherited_members=inherited_members,
            exclude_members=self.options.exclude_members,
            special_members=self.options.special_members,
            private_members=self.options.private_members,
            undoc_members=self.options.undoc_members,
            attr_docs=attr_docs,
        )
        # document non-skipped members
        member_documenters: list[tuple[Documenter, bool]] = []
        for member_name, member, is_attr in filtered_members:
            # prefer the documenter with the highest priority
            doccls = max(
                (
                    cls
                    for cls in registry.documenters.values()
                    if cls.can_document_member(member, member_name, is_attr, self)
                ),
                key=lambda cls: cls.priority,
                default=None,
            )
            if doccls is None:
                # don't know how to document this member
                continue
            # give explicitly separated module name, so that members
            # of inner classes can be documented
            module_prefix = f'{props.module_name}::'
            full_mname = module_prefix + '.'.join((*props.parts, member_name))
            documenter = doccls(self.directive, full_mname, indent)

            # We now try to import all objects before ordering them. This is to
            # avoid possible circular imports if we were to import objects after
            # their associated documenters have been sorted.
            if documenter._load_object_by_name() is None:
                continue

            member_documenters.append((documenter, is_attr))

        member_order = self.options.member_order or self.config.autodoc_member_order
        member_documenters = self.sort_members(member_documenters, member_order)

        # reset current objects
        current_document.autodoc_module = ''
        current_document.autodoc_class = ''

        return member_documenters


class ModuleDocumenter(Documenter):
    """Specialized Documenter subclass for modules."""

    props: _ModuleProperties

    objtype = 'module'
    content_indent = ''
    _extra_indent = '   '

    option_spec: ClassVar[OptionSpec] = {
        'members': members_option,
        'undoc-members': bool_option,
        'no-index': bool_option,
        'no-index-entry': bool_option,
        'inherited-members': inherited_members_option,
        'show-inheritance': bool_option,
        'synopsis': identity,
        'platform': identity,
        'deprecated': bool_option,
        'member-order': member_order_option,
        'exclude-members': exclude_members_option,
        'private-members': members_option,
        'special-members': members_option,
        'imported-members': bool_option,
        'ignore-module-all': bool_option,
        'no-value': bool_option,
        'noindex': bool_option,
    }

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.options = self.options.merge_member_options()
        self.__all__: Sequence[str] | None = None

    def add_content(self, more_content: StringList | None) -> None:
        old_indent = self.indent
        self.indent += self._extra_indent
        super().add_content(None)
        self.indent = old_indent
        if more_content:
            for line, src in zip(more_content.data, more_content.items, strict=True):
                self.add_line(line, src[0], src[1])

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        # don't document submodules automatically
        return False

    def _module_all(self) -> Sequence[str] | None:
        if self.__all__ is None and not self.options.ignore_module_all:
            self.__all__ = self.props.all
        return self.__all__

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()

        # add some module-specific options
        if self.options.synopsis:
            self.add_line('   :synopsis: ' + self.options.synopsis, sourcename)
        if self.options.platform:
            self.add_line('   :platform: ' + self.options.platform, sourcename)
        if self.options.deprecated:
            self.add_line('   :deprecated:', sourcename)

    def sort_members(
        self, documenters: list[tuple[Documenter, bool]], order: str
    ) -> list[tuple[Documenter, bool]]:
        module_all = self.props.all
        if (
            order == 'bysource'
            and not self.options.ignore_module_all
            and module_all is not None
        ):
            assert module_all is not None
            module_all_set = frozenset(module_all)
            module_all_len = len(module_all)

            # Sort alphabetically first (for members not listed on the __all__)
            documenters.sort(key=lambda e: e[0].name)

            # Sort by __all__
            def keyfunc(entry: tuple[Documenter, bool]) -> int:
                name = entry[0].name.split('::')[1]
                if name in module_all_set:
                    return module_all.index(name)
                else:
                    return module_all_len

            documenters.sort(key=keyfunc)

            return documenters
        else:
            return super().sort_members(documenters, order)


class FunctionDocumenter(Documenter):
    """Specialized Documenter subclass for functions."""

    props: _FunctionDefProperties

    __docstring_signature__ = True

    objtype = 'function'
    member_order = 30

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        # supports functions, builtins and bound methods exported at the module level
        return (
            inspect.isfunction(member)
            or inspect.isbuiltin(member)
            or (inspect.isroutine(member) and isinstance(parent, ModuleDocumenter))
        )

    def format_args(self, **kwargs: Any) -> str:
        if self.config.autodoc_typehints in {'none', 'description'}:
            kwargs.setdefault('show_annotation', False)
        if self.config.autodoc_typehints_format == 'short':
            kwargs.setdefault('unqualified_typehints', True)
        if self.config.python_display_short_literal_types:
            kwargs.setdefault('short_literals', True)

        try:
            self._events.emit(
                'autodoc-before-process-signature', self.props._obj, False
            )
            sig = inspect.signature(
                self.props._obj, type_aliases=self.config.autodoc_type_aliases
            )
            args = stringify_signature(sig, **kwargs)
        except TypeError as exc:
            msg = __('Failed to get a function signature for %s: %s')
            logger.warning(msg, self.props.full_name, exc)
            return ''
        except ValueError:
            args = ''

        if self.config.strip_signature_backslash:
            # escape backslashes for reST
            args = args.replace('\\', '\\\\')

        if self.objtype == 'decorator' and ',' not in args:
            # Special case for single-argument decorators
            return ''
        return args

    def add_directive_header(self, sig: str) -> None:
        sourcename = self.get_sourcename()
        super().add_directive_header(sig)

        is_coro = inspect.iscoroutinefunction(self.props._obj)
        is_acoro = inspect.isasyncgenfunction(self.props._obj)
        if is_coro or is_acoro:
            self.add_line('   :async:', sourcename)

    def format_signature(self, **kwargs: Any) -> str:
        if self.config.autodoc_typehints_format == 'short':
            kwargs.setdefault('unqualified_typehints', True)
        if self.config.python_display_short_literal_types:
            kwargs.setdefault('short_literals', True)

        sigs = []
        if (
            self.analyzer
            and self.props.dotted_parts in self.analyzer.overloads
            and self.config.autodoc_typehints != 'none'
        ):
            # Use signatures for overloaded functions instead of the implementation function.
            overloaded = True
        else:
            overloaded = False
            sig = super().format_signature(**kwargs)
            sigs.append(sig)

        if inspect.is_singledispatch_function(self.props._obj):
            from sphinx.ext.autodoc._property_types import _FunctionDefProperties

            # append signature of singledispatch'ed functions
            for typ, func in self.props._obj.registry.items():
                if typ is object:
                    pass  # default implementation. skipped.
                else:
                    dispatchfunc = self.annotate_to_first_argument(func, typ)
                    if dispatchfunc:
                        documenter = FunctionDocumenter(self.directive, '')
                        documenter.props = _FunctionDefProperties(
                            obj_type='function',
                            module_name='',
                            parts=('',),
                            docstring_lines=(),
                            _obj=dispatchfunc,
                            _obj___module__=None,
                            properties=frozenset(),
                        )
                        sigs.append(documenter.format_signature())
        if overloaded and self.analyzer is not None:
            actual = inspect.signature(
                self.props._obj, type_aliases=self.config.autodoc_type_aliases
            )
            __globals__ = safe_getattr(self.props._obj, '__globals__', {})
            for overload in self.analyzer.overloads[self.props.dotted_parts]:
                overload = self.merge_default_value(actual, overload)
                overload = evaluate_signature(
                    overload, __globals__, self.config.autodoc_type_aliases
                )

                sig = stringify_signature(overload, **kwargs)
                sigs.append(sig)

        return '\n'.join(sigs)

    def merge_default_value(self, actual: Signature, overload: Signature) -> Signature:
        """Merge default values of actual implementation to the overload variants."""
        parameters = list(overload.parameters.values())
        for i, param in enumerate(parameters):
            actual_param = actual.parameters.get(param.name)
            if actual_param and param.default == '...':
                parameters[i] = param.replace(default=actual_param.default)

        return overload.replace(parameters=parameters)

    def annotate_to_first_argument(
        self, func: Callable[..., Any], typ: type
    ) -> Callable[..., Any] | None:
        """Annotate type hint to the first argument of function if needed."""
        try:
            sig = inspect.signature(func, type_aliases=self.config.autodoc_type_aliases)
        except TypeError as exc:
            msg = __('Failed to get a function signature for %s: %s')
            logger.warning(msg, self.props.full_name, exc)
            return None
        except ValueError:
            return None

        if len(sig.parameters) == 0:
            return None

        def dummy():  # type: ignore[no-untyped-def]  # NoQA: ANN202
            pass

        params = list(sig.parameters.values())
        if params[0].annotation is Parameter.empty:
            params[0] = params[0].replace(annotation=typ)
            try:
                dummy.__signature__ = sig.replace(parameters=params)  # type: ignore[attr-defined]
                return dummy
            except (AttributeError, TypeError):
                # failed to update signature (ex. built-in or extension types)
                return None

        return func


class DecoratorDocumenter(FunctionDocumenter):
    """Specialized Documenter subclass for decorator functions."""

    props: _FunctionDefProperties

    objtype = 'decorator'

    # must be lower than FunctionDocumenter
    priority = FunctionDocumenter.priority - 1


# Types which have confusing metaclass signatures it would be best not to show.
# These are listed by name, rather than storing the objects themselves, to avoid
# needing to import the modules.
_METACLASS_CALL_BLACKLIST = frozenset({
    'enum.EnumType.__call__',
})


# Types whose __new__ signature is a pass-through.
_CLASS_NEW_BLACKLIST = frozenset({
    'typing.Generic.__new__',
})


class ClassDocumenter(Documenter):
    """Specialized Documenter subclass for classes."""

    props: _ClassDefProperties

    __docstring_signature__ = True

    objtype = 'class'
    member_order = 20
    option_spec: ClassVar[OptionSpec] = {
        'members': members_option,
        'undoc-members': bool_option,
        'no-index': bool_option,
        'no-index-entry': bool_option,
        'inherited-members': inherited_members_option,
        'show-inheritance': bool_option,
        'member-order': member_order_option,
        'exclude-members': exclude_members_option,
        'private-members': members_option,
        'special-members': members_option,
        'class-doc-from': class_doc_from_option,
        'noindex': bool_option,
    }

    # Must be higher than FunctionDocumenter, ClassDocumenter, and
    # AttributeDocumenter as NewType can be an attribute and is a class
    # after Python 3.10.
    priority = 15

    _signature_class: Any = None
    _signature_method_name: str = ''

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)

        if self.config.autodoc_class_signature == 'separated':
            self.options = self.options.copy()

            # show __init__() method
            if self.options.special_members is None:
                self.options.special_members = ['__new__', '__init__']
            else:
                self.options.special_members.append('__new__')
                self.options.special_members.append('__init__')

        self.options = self.options.merge_member_options()

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        return isinstance(member, type) or (
            isattr and isinstance(member, NewType | TypeVar)
        )

    def _get_signature(self) -> tuple[Any | None, str | None, Signature | None]:
        if isinstance(self.props._obj, NewType | TypeVar):
            # Suppress signature
            return None, None, None

        def get_user_defined_function_or_method(obj: Any, attr: str) -> Any:
            """Get the `attr` function or method from `obj`, if it is user-defined."""
            if inspect.is_builtin_class_method(obj, attr):
                return None
            attr = self.get_attr(obj, attr, None)
            if not (inspect.ismethod(attr) or inspect.isfunction(attr)):
                return None
            return attr

        # This sequence is copied from inspect._signature_from_callable.
        # ValueError means that no signature could be found, so we keep going.

        # First, we check if obj has a __signature__ attribute
        if hasattr(self.props._obj, '__signature__'):
            object_sig = self.props._obj.__signature__
            if isinstance(object_sig, Signature):
                return None, None, object_sig
            if sys.version_info[:2] in {(3, 12), (3, 13)} and callable(object_sig):
                # Support for enum.Enum.__signature__ in Python 3.12
                if isinstance(object_sig_str := object_sig(), str):
                    return None, None, inspect.signature_from_str(object_sig_str)

        # Next, let's see if it has an overloaded __call__ defined
        # in its metaclass
        call = get_user_defined_function_or_method(type(self.props._obj), '__call__')

        if call is not None:
            if f'{call.__module__}.{call.__qualname__}' in _METACLASS_CALL_BLACKLIST:
                call = None

        if call is not None:
            self._events.emit('autodoc-before-process-signature', call, True)
            try:
                sig = inspect.signature(
                    call,
                    bound_method=True,
                    type_aliases=self.config.autodoc_type_aliases,
                )
                return type(self.props._obj), '__call__', sig
            except ValueError:
                pass

        # Now we check if the 'obj' class has a '__new__' method
        new = get_user_defined_function_or_method(self.props._obj, '__new__')

        if new is not None:
            if f'{new.__module__}.{new.__qualname__}' in _CLASS_NEW_BLACKLIST:
                new = None

        if new is not None:
            self._events.emit('autodoc-before-process-signature', new, True)
            try:
                sig = inspect.signature(
                    new,
                    bound_method=True,
                    type_aliases=self.config.autodoc_type_aliases,
                )
                return self.props._obj, '__new__', sig
            except ValueError:
                pass

        # Finally, we should have at least __init__ implemented
        init = get_user_defined_function_or_method(self.props._obj, '__init__')
        if init is not None:
            self._events.emit('autodoc-before-process-signature', init, True)
            try:
                sig = inspect.signature(
                    init,
                    bound_method=True,
                    type_aliases=self.config.autodoc_type_aliases,
                )
                return self.props._obj, '__init__', sig
            except ValueError:
                pass

        # None of the attributes are user-defined, so fall back to let inspect
        # handle it.
        # We don't know the exact method that inspect.signature will read
        # the signature from, so just pass the object itself to our hook.
        self._events.emit('autodoc-before-process-signature', self.props._obj, False)
        try:
            sig = inspect.signature(
                self.props._obj,
                bound_method=False,
                type_aliases=self.config.autodoc_type_aliases,
            )
            return None, None, sig
        except ValueError:
            pass

        # Still no signature: happens e.g. for old-style classes
        # with __init__ in C and no `__text_signature__`.
        return None, None, None

    def format_args(self, **kwargs: Any) -> str:
        if self.config.autodoc_typehints in {'none', 'description'}:
            kwargs.setdefault('show_annotation', False)
        if self.config.autodoc_typehints_format == 'short':
            kwargs.setdefault('unqualified_typehints', True)
        if self.config.python_display_short_literal_types:
            kwargs.setdefault('short_literals', True)

        try:
            self._signature_class, _signature_method_name, sig = self._get_signature()
        except TypeError as exc:
            # __signature__ attribute contained junk
            msg = __('Failed to get a constructor signature for %s: %s')
            logger.warning(msg, self.props.full_name, exc)
            return ''
        self._signature_method_name = _signature_method_name or ''

        if sig is None:
            return ''

        return stringify_signature(sig, show_return_annotation=False, **kwargs)

    def _find_signature(self) -> tuple[str | None, str | None] | None:
        result = super()._find_signature()
        if result is not None:
            # Strip a return value from signature of constructor in docstring (first entry)
            result = (result[0], None)

        for i, sig in enumerate(self._signatures):
            if sig.endswith(' -> None'):
                # Strip a return value from signatures of constructor in docstring (subsequent
                # entries)
                self._signatures[i] = sig[:-8]

        return result

    def format_signature(self, **kwargs: Any) -> str:
        if self.props.doc_as_attr:
            return ''
        if self.config.autodoc_class_signature == 'separated':
            # do not show signatures
            return ''

        if self.config.autodoc_typehints_format == 'short':
            kwargs.setdefault('unqualified_typehints', True)
        if self.config.python_display_short_literal_types:
            kwargs.setdefault('short_literals', True)

        sig = super().format_signature()
        sigs = []

        overloads = self.get_overloaded_signatures()
        if overloads and self.config.autodoc_typehints != 'none':
            # Use signatures for overloaded methods instead of the implementation method.
            method = safe_getattr(
                self._signature_class, self._signature_method_name, None
            )
            __globals__ = safe_getattr(method, '__globals__', {})
            for overload in overloads:
                overload = evaluate_signature(
                    overload, __globals__, self.config.autodoc_type_aliases
                )

                parameters = list(overload.parameters.values())
                overload = overload.replace(
                    parameters=parameters[1:], return_annotation=Parameter.empty
                )
                sig = stringify_signature(overload, **kwargs)
                sigs.append(sig)
        else:
            sigs.append(sig)

        return '\n'.join(sigs)

    def get_overloaded_signatures(self) -> list[Signature]:
        if self._signature_class and self._signature_method_name:
            for cls in self._signature_class.__mro__:
                try:
                    analyzer = ModuleAnalyzer.for_module(cls.__module__)
                    analyzer.analyze()
                    qualname = f'{cls.__qualname__}.{self._signature_method_name}'
                    if qualname in analyzer.overloads:
                        return analyzer.overloads.get(qualname, [])
                    elif qualname in analyzer.tagorder:
                        # the constructor is defined in the class, but not overridden.
                        return []
                except PycodeError:
                    pass

        return []

    def get_canonical_fullname(self) -> str | None:
        __modname__ = safe_getattr(
            self.props._obj, '__module__', self.props.module_name
        )
        __qualname__ = safe_getattr(self.props._obj, '__qualname__', None)
        if __qualname__ is None:
            __qualname__ = safe_getattr(self.props._obj, '__name__', None)
        if __qualname__ and '<locals>' in __qualname__:
            # No valid qualname found if the object is defined as locals
            __qualname__ = None

        if __modname__ and __qualname__:
            return f'{__modname__}.{__qualname__}'
        else:
            return None

    def add_directive_header(self, sig: str) -> None:
        sourcename = self.get_sourcename()

        if self.props.doc_as_attr:
            self.directivetype = 'attribute'
        super().add_directive_header(sig)

        if isinstance(self.props._obj, NewType | TypeVar):
            return

        if self.analyzer and self.props.dotted_parts in self.analyzer.finals:
            self.add_line('   :final:', sourcename)

        canonical_fullname = self.get_canonical_fullname()
        if (
            not self.props.doc_as_attr
            and not isinstance(self.props._obj, NewType)
            and canonical_fullname
            and self.props.full_name != canonical_fullname
        ):
            self.add_line('   :canonical: %s' % canonical_fullname, sourcename)

        # add inheritance info, if wanted
        if not self.props.doc_as_attr and self.options.show_inheritance:
            if inspect.getorigbases(self.props._obj):
                # A subclass of generic types
                # refs: PEP-560 <https://peps.python.org/pep-0560/>
                bases = list(self.props._obj.__orig_bases__)
            elif hasattr(self.props._obj, '__bases__') and len(
                self.props._obj.__bases__
            ):
                # A normal class
                bases = list(self.props._obj.__bases__)
            else:
                bases = []

            self._events.emit(
                'autodoc-process-bases',
                self.props.full_name,
                self.props._obj,
                self.options,
                bases,
            )

            mode = _get_render_mode(self.config.autodoc_typehints_format)
            base_classes = [restify(cls, mode=mode) for cls in bases]

            sourcename = self.get_sourcename()
            self.add_line('', sourcename)
            self.add_line('   ' + _('Bases: %s') % ', '.join(base_classes), sourcename)

    def get_doc(self) -> list[list[str]] | None:
        if isinstance(self.props._obj, TypeVar):
            if self.props._obj.__doc__ == TypeVar.__doc__:
                return []
        if self.props.doc_as_attr:
            # Don't show the docstring of the class when it is an alias.
            if self.get_variable_comment():
                return []
            else:
                return None

        lines = getattr(self, '_new_docstrings', None)
        if lines is not None:
            return lines

        if self.options.class_doc_from is not None:
            classdoc_from = self.options.class_doc_from
        else:
            classdoc_from = self.config.autoclass_content

        docstrings = []
        attrdocstring = getdoc(self.props._obj, self.get_attr)
        if attrdocstring:
            docstrings.append(attrdocstring)

        # for classes, what the "docstring" is can be controlled via a
        # config value; the default is only the class docstring
        if classdoc_from in {'both', 'init'}:
            __init__ = self.get_attr(self.props._obj, '__init__', None)
            initdocstring = getdoc(
                __init__,
                self.get_attr,
                self.config.autodoc_inherit_docstrings,
                self.props._obj,
                '__init__',
            )
            # for new-style classes, no __init__ means default __init__
            if initdocstring is not None and (
                initdocstring == object.__init__.__doc__  # for pypy
                or initdocstring.strip() == object.__init__.__doc__  # for !pypy
            ):
                initdocstring = None
            if not initdocstring:
                # try __new__
                __new__ = self.get_attr(self.props._obj, '__new__', None)
                initdocstring = getdoc(
                    __new__,
                    self.get_attr,
                    self.config.autodoc_inherit_docstrings,
                    self.props._obj,
                    '__new__',
                )
                # for new-style classes, no __new__ means default __new__
                if initdocstring is not None and (
                    initdocstring == object.__new__.__doc__  # for pypy
                    or initdocstring.strip() == object.__new__.__doc__  # for !pypy
                ):
                    initdocstring = None
            if initdocstring:
                if classdoc_from == 'init':
                    docstrings = [initdocstring]
                else:
                    docstrings.append(initdocstring)

        tab_width = self.directive.state.document.settings.tab_width
        return [prepare_docstring(docstring, tab_width) for docstring in docstrings]

    def get_variable_comment(self) -> list[str] | None:
        try:
            key = ('', self.props.dotted_parts)
            if self.props.doc_as_attr:
                analyzer = ModuleAnalyzer.for_module(self.props.module_name)
            else:
                analyzer = ModuleAnalyzer.for_module(
                    self.props._obj___module__ or self.props.module_name
                )
            analyzer.analyze()
            return list(analyzer.attr_docs.get(key, []))
        except PycodeError:
            return None

    def add_content(self, more_content: StringList | None) -> None:
        mode = _get_render_mode(self.config.autodoc_typehints_format)
        short_literals = self.config.python_display_short_literal_types

        if isinstance(self.props._obj, NewType):
            supertype = restify(self.props._obj.__supertype__, mode=mode)

            more_content = StringList([_('alias of %s') % supertype, ''], source='')
        if isinstance(self.props._obj, TypeVar):
            attrs = [repr(self.props._obj.__name__)]
            attrs.extend(
                stringify_annotation(constraint, mode, short_literals=short_literals)
                for constraint in self.props._obj.__constraints__
            )
            if self.props._obj.__bound__:
                bound = restify(self.props._obj.__bound__, mode=mode)
                attrs.append(r'bound=\ ' + bound)
            if self.props._obj.__covariant__:
                attrs.append('covariant=True')
            if self.props._obj.__contravariant__:
                attrs.append('contravariant=True')

            more_content = StringList(
                [_('alias of TypeVar(%s)') % ', '.join(attrs), ''], source=''
            )
        if self.props.doc_as_attr and self.props.module_name != (
            self.props._obj___module__ or self.props.module_name
        ):
            try:
                # override analyzer to obtain doccomment around its definition.
                self.analyzer = ModuleAnalyzer.for_module(self.props.module_name)
                self.analyzer.analyze()
            except PycodeError:
                pass

        if self.props.doc_as_attr and not self.get_variable_comment():
            try:
                alias = restify(self.props._obj, mode=mode)
                more_content = StringList([_('alias of %s') % alias], source='')
            except AttributeError:
                pass  # Invalid class object is passed.

        super().add_content(more_content)

    def generate(
        self,
        more_content: StringList | None = None,
        real_modname: str | None = None,
        check_module: bool = False,
        all_members: bool = False,
    ) -> None:
        # Do not pass real_modname and use the name from the __module__
        # attribute of the class.
        # If a class gets imported into the module real_modname
        # the analyzer won't find the source of the class, if
        # it looks in real_modname.
        return super().generate(
            more_content=more_content,
            check_module=check_module,
            all_members=all_members,
        )


class ExceptionDocumenter(ClassDocumenter):
    """Specialized ClassDocumenter subclass for exceptions."""

    props: _ClassDefProperties

    objtype = 'exception'
    member_order = 10

    # needs a higher priority than ClassDocumenter
    priority = ClassDocumenter.priority + 5

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        try:
            return isinstance(member, type) and issubclass(member, BaseException)
        except TypeError as exc:
            # It's possible for a member to be considered a type, but fail
            # issubclass checks due to not being a class. For example:
            # https://github.com/sphinx-doc/sphinx/issues/11654#issuecomment-1696790436
            msg = (
                f'{cls.__name__} failed to discern if member {member} with'
                f' membername {membername} is a BaseException subclass.'
            )
            raise ValueError(msg) from exc


class DataDocumenter(Documenter):
    """Specialized Documenter subclass for data items."""

    props: _AssignStatementProperties

    __uninitialized_global_variable__ = True

    objtype = 'data'
    member_order = 40
    priority = -10
    option_spec: ClassVar[OptionSpec] = dict(Documenter.option_spec)
    option_spec['annotation'] = annotation_option
    option_spec['no-value'] = bool_option

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        return isinstance(parent, ModuleDocumenter) and isattr

    def update_annotations(self, parent: Any) -> None:
        """Update __annotations__ to support type_comment and so on."""
        annotations = dict(inspect.getannotations(parent))
        parent.__annotations__ = annotations

        try:
            analyzer = ModuleAnalyzer.for_module(self.props.module_name)
            analyzer.analyze()
            for (classname, attrname), annotation in analyzer.annotations.items():
                if not classname and attrname not in annotations:
                    annotations[attrname] = annotation
        except PycodeError:
            pass

    def should_suppress_value_header(self) -> bool:
        if self.props._obj is UNINITIALIZED_ATTR:
            return True
        else:
            doc = self.get_doc() or []
            _docstring, metadata = separate_metadata(
                '\n'.join(functools.reduce(operator.iadd, doc, []))
            )
            if 'hide-value' in metadata:
                return True

        return False

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)
        sourcename = self.get_sourcename()
        if self.options.annotation is SUPPRESS or inspect.isgenericalias(
            self.props._obj
        ):
            pass
        elif self.options.annotation:
            self.add_line('   :annotation: %s' % self.options.annotation, sourcename)
        else:
            if self.config.autodoc_typehints != 'none':
                # obtain annotation for this data
                annotations = get_type_hints(
                    self.parent,
                    None,
                    self.config.autodoc_type_aliases,
                    include_extras=True,
                )
                if self.props.name in annotations:
                    mode = _get_render_mode(self.config.autodoc_typehints_format)
                    short_literals = self.config.python_display_short_literal_types
                    objrepr = stringify_annotation(
                        annotations.get(self.props.name),
                        mode,
                        short_literals=short_literals,
                    )
                    self.add_line('   :type: ' + objrepr, sourcename)

            try:
                if (
                    self.options.no_value
                    or self.should_suppress_value_header()
                    or ismock(self.props._obj)
                ):
                    pass
                else:
                    objrepr = object_description(self.props._obj)
                    self.add_line('   :value: ' + objrepr, sourcename)
            except ValueError:
                pass

    def get_module_comment(self, attrname: str) -> list[str] | None:
        try:
            analyzer = ModuleAnalyzer.for_module(self.props.module_name)
            analyzer.analyze()
            key = ('', attrname)
            if key in analyzer.attr_docs:
                return list(analyzer.attr_docs[key])
        except PycodeError:
            pass

        return None

    def get_doc(self) -> list[list[str]] | None:
        # Check the variable has a docstring-comment
        comment = self.get_module_comment(self.props.name)
        if comment:
            return [comment]
        else:
            return super().get_doc()

    def add_content(self, more_content: StringList | None) -> None:
        # Disable analyzing variable comment on Documenter.add_content() to control it on
        # DataDocumenter.add_content()
        self.analyzer = None

        if not more_content:
            more_content = StringList()

        _add_content_generic_alias_(
            more_content,
            self.props._obj,
            autodoc_typehints_format=self.config.autodoc_typehints_format,
        )
        super().add_content(more_content)


class MethodDocumenter(Documenter):
    """Specialized Documenter subclass for methods (normal, static and class)."""

    props: _FunctionDefProperties

    __docstring_signature__ = True

    objtype = 'method'
    directivetype = 'method'
    member_order = 50
    priority = 1  # must be more than FunctionDocumenter

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        return inspect.isroutine(member) and not isinstance(parent, ModuleDocumenter)

    def format_args(self, **kwargs: Any) -> str:
        if self.config.autodoc_typehints in {'none', 'description'}:
            kwargs.setdefault('show_annotation', False)
        if self.config.autodoc_typehints_format == 'short':
            kwargs.setdefault('unqualified_typehints', True)
        if self.config.python_display_short_literal_types:
            kwargs.setdefault('short_literals', True)

        try:
            if self.props._obj == object.__init__ and self.parent != object:  # NoQA: E721
                # Classes not having own __init__() method are shown as no arguments.
                #
                # Note: The signature of object.__init__() is (self, /, *args, **kwargs).
                #       But it makes users confused.
                args = '()'
            else:
                if inspect.isstaticmethod(
                    self.props._obj, cls=self.parent, name=self.props.object_name
                ):
                    self._events.emit(
                        'autodoc-before-process-signature', self.props._obj, False
                    )
                    sig = inspect.signature(
                        self.props._obj,
                        bound_method=False,
                        type_aliases=self.config.autodoc_type_aliases,
                    )
                else:
                    self._events.emit(
                        'autodoc-before-process-signature', self.props._obj, True
                    )
                    sig = inspect.signature(
                        self.props._obj,
                        bound_method=True,
                        type_aliases=self.config.autodoc_type_aliases,
                    )
                args = stringify_signature(sig, **kwargs)
        except TypeError as exc:
            msg = __('Failed to get a method signature for %s: %s')
            logger.warning(msg, self.props.full_name, exc)
            return ''
        except ValueError:
            args = ''

        if self.config.strip_signature_backslash:
            # escape backslashes for reST
            args = args.replace('\\', '\\\\')
        return args

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()
        obj = self.parent.__dict__.get(self.props.object_name, self.props._obj)
        if inspect.isabstractmethod(obj):
            self.add_line('   :abstractmethod:', sourcename)
        if inspect.iscoroutinefunction(obj) or inspect.isasyncgenfunction(obj):
            self.add_line('   :async:', sourcename)
        if (
            inspect.is_classmethod_like(obj)
            or inspect.is_singledispatch_method(obj)
            and inspect.is_classmethod_like(obj.func)
        ):
            self.add_line('   :classmethod:', sourcename)
        if inspect.isstaticmethod(obj, cls=self.parent, name=self.props.object_name):
            self.add_line('   :staticmethod:', sourcename)
        if self.analyzer and self.props.dotted_parts in self.analyzer.finals:
            self.add_line('   :final:', sourcename)

    def format_signature(self, **kwargs: Any) -> str:
        if self.config.autodoc_typehints_format == 'short':
            kwargs.setdefault('unqualified_typehints', True)
        if self.config.python_display_short_literal_types:
            kwargs.setdefault('short_literals', True)

        sigs = []
        if (
            self.analyzer
            and self.props.dotted_parts in self.analyzer.overloads
            and self.config.autodoc_typehints != 'none'
        ):
            # Use signatures for overloaded methods instead of the implementation method.
            overloaded = True
        else:
            overloaded = False
            sig = super().format_signature(**kwargs)
            sigs.append(sig)

        meth = self.parent.__dict__.get(self.props.name)
        if inspect.is_singledispatch_method(meth):
            from sphinx.ext.autodoc._property_types import _FunctionDefProperties

            # append signature of singledispatch'ed functions
            for typ, func in meth.dispatcher.registry.items():
                if typ is object:
                    pass  # default implementation. skipped.
                else:
                    if inspect.isclassmethod(func):
                        func = func.__func__
                    dispatchmeth = self.annotate_to_first_argument(func, typ)
                    if dispatchmeth:
                        documenter = MethodDocumenter(self.directive, '')
                        documenter.props = _FunctionDefProperties(
                            obj_type='method',
                            module_name='',
                            parts=('',),
                            docstring_lines=(),
                            _obj=dispatchmeth,
                            _obj___module__=None,
                            properties=frozenset(),
                        )
                        documenter.parent = self.parent
                        sigs.append(documenter.format_signature())
        if overloaded and self.analyzer is not None:
            if inspect.isstaticmethod(
                self.props._obj, cls=self.parent, name=self.props.object_name
            ):
                actual = inspect.signature(
                    self.props._obj,
                    bound_method=False,
                    type_aliases=self.config.autodoc_type_aliases,
                )
            else:
                actual = inspect.signature(
                    self.props._obj,
                    bound_method=True,
                    type_aliases=self.config.autodoc_type_aliases,
                )

            __globals__ = safe_getattr(self.props._obj, '__globals__', {})
            for overload in self.analyzer.overloads[self.props.dotted_parts]:
                overload = self.merge_default_value(actual, overload)
                overload = evaluate_signature(
                    overload, __globals__, self.config.autodoc_type_aliases
                )

                if not inspect.isstaticmethod(
                    self.props._obj, cls=self.parent, name=self.props.object_name
                ):
                    parameters = list(overload.parameters.values())
                    overload = overload.replace(parameters=parameters[1:])
                sig = stringify_signature(overload, **kwargs)
                sigs.append(sig)

        return '\n'.join(sigs)

    def merge_default_value(self, actual: Signature, overload: Signature) -> Signature:
        """Merge default values of actual implementation to the overload variants."""
        parameters = list(overload.parameters.values())
        for i, param in enumerate(parameters):
            actual_param = actual.parameters.get(param.name)
            if actual_param and param.default == '...':
                parameters[i] = param.replace(default=actual_param.default)

        return overload.replace(parameters=parameters)

    def annotate_to_first_argument(
        self, func: Callable[..., Any], typ: type
    ) -> Callable[..., Any] | None:
        """Annotate type hint to the first argument of function if needed."""
        try:
            sig = inspect.signature(func, type_aliases=self.config.autodoc_type_aliases)
        except TypeError as exc:
            msg = __('Failed to get a method signature for %s: %s')
            logger.warning(msg, self.props.full_name, exc)
            return None
        except ValueError:
            return None

        if len(sig.parameters) == 1:
            return None

        def dummy():  # type: ignore[no-untyped-def]  # NoQA: ANN202
            pass

        params = list(sig.parameters.values())
        if params[1].annotation is Parameter.empty:
            params[1] = params[1].replace(annotation=typ)
            try:
                dummy.__signature__ = sig.replace(  # type: ignore[attr-defined]
                    parameters=params
                )
                return dummy
            except (AttributeError, TypeError):
                # failed to update signature (ex. built-in or extension types)
                return None

        return func

    def get_doc(self) -> list[list[str]] | None:
        if self._new_docstrings is not None:
            # docstring already returned previously, then modified due to
            # ``__docstring_signature__ = True``. Just return the
            # previously-computed result, so that we don't loose the processing.
            return self._new_docstrings
        if self.props.name == '__init__':
            docstring = getdoc(
                self.props._obj,
                self.get_attr,
                self.config.autodoc_inherit_docstrings,
                self.parent,
                self.props.object_name,
            )
            if docstring is not None and (
                docstring == object.__init__.__doc__  # for pypy
                or docstring.strip() == object.__init__.__doc__  # for !pypy
            ):
                docstring = None
            if docstring:
                tab_width = self.directive.state.document.settings.tab_width
                return [prepare_docstring(docstring, tabsize=tab_width)]
            else:
                return []
        elif self.props.name == '__new__':
            docstring = getdoc(
                self.props._obj,
                self.get_attr,
                self.config.autodoc_inherit_docstrings,
                self.parent,
                self.props.object_name,
            )
            if docstring is not None and (
                docstring == object.__new__.__doc__  # for pypy
                or docstring.strip() == object.__new__.__doc__  # for !pypy
            ):
                docstring = None
            if docstring:
                tab_width = self.directive.state.document.settings.tab_width
                return [prepare_docstring(docstring, tabsize=tab_width)]
            else:
                return []
        else:
            return super().get_doc()


class AttributeDocumenter(Documenter):
    """Specialized Documenter subclass for attributes."""

    props: _AssignStatementProperties

    __docstring_signature__ = True
    __docstring_strip_signature__ = True

    objtype = 'attribute'
    member_order = 60
    option_spec: ClassVar[OptionSpec] = dict(Documenter.option_spec)
    option_spec['annotation'] = annotation_option
    option_spec['no-value'] = bool_option

    # must be higher than the MethodDocumenter, else it will recognize
    # some non-data descriptors as methods
    priority = 10

    @staticmethod
    def is_function_or_method(obj: Any) -> bool:
        return (
            inspect.isfunction(obj) or inspect.isbuiltin(obj) or inspect.ismethod(obj)
        )

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        if isinstance(parent, ModuleDocumenter):
            return False
        if inspect.isattributedescriptor(member):
            return True
        return not inspect.isroutine(member) and not isinstance(member, type)

    def update_annotations(self, parent: Any) -> None:
        """Update __annotations__ to support type_comment and so on."""
        try:
            annotations = dict(inspect.getannotations(parent))
            parent.__annotations__ = annotations

            for cls in inspect.getmro(parent):
                try:
                    module = safe_getattr(cls, '__module__')
                    qualname = safe_getattr(cls, '__qualname__')

                    analyzer = ModuleAnalyzer.for_module(module)
                    analyzer.analyze()
                    anns = analyzer.annotations
                    for (classname, attrname), annotation in anns.items():
                        if classname == qualname and attrname not in annotations:
                            annotations[attrname] = annotation
                except (AttributeError, PycodeError):
                    pass
        except (AttributeError, TypeError):
            # Failed to set __annotations__ (built-in, extensions, etc.)
            pass

    @property
    def _is_non_data_descriptor(self) -> bool:
        return not inspect.isattributedescriptor(self.props._obj)

    def should_suppress_value_header(self) -> bool:
        if self.props._obj is SLOTS_ATTR:
            return True
        if self.props._obj is RUNTIME_INSTANCE_ATTRIBUTE:
            return True
        if self.props._obj is UNINITIALIZED_ATTR:
            return True
        if not self._is_non_data_descriptor or inspect.isgenericalias(self.props._obj):
            return True
        else:
            doc = self.get_doc()
            if doc:
                _docstring, metadata = separate_metadata(
                    '\n'.join(functools.reduce(operator.iadd, doc, []))
                )
                if 'hide-value' in metadata:
                    return True

        return False

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)
        sourcename = self.get_sourcename()
        if self.options.annotation is SUPPRESS or inspect.isgenericalias(
            self.props._obj
        ):
            pass
        elif self.options.annotation:
            self.add_line('   :annotation: %s' % self.options.annotation, sourcename)
        else:
            if self.config.autodoc_typehints != 'none':
                # obtain type annotation for this attribute
                annotations = get_type_hints(
                    self.parent,
                    None,
                    self.config.autodoc_type_aliases,
                    include_extras=True,
                )
                if self.props.name in annotations:
                    mode = _get_render_mode(self.config.autodoc_typehints_format)
                    short_literals = self.config.python_display_short_literal_types
                    objrepr = stringify_annotation(
                        annotations.get(self.props.name),
                        mode,
                        short_literals=short_literals,
                    )
                    self.add_line('   :type: ' + objrepr, sourcename)

            try:
                if (
                    self.options.no_value
                    or self.should_suppress_value_header()
                    or ismock(self.props._obj)
                ):
                    pass
                else:
                    objrepr = object_description(self.props._obj)
                    self.add_line('   :value: ' + objrepr, sourcename)
            except ValueError:
                pass

    def get_attribute_comment(self, parent: Any, attrname: str) -> list[str] | None:
        return _get_attribute_comment(
            parent=parent, obj_path=self.props.parts, attrname=attrname
        )

    def get_doc(self) -> list[list[str]] | None:
        # Check the attribute has a docstring-comment
        comment = _get_attribute_comment(
            parent=self.parent, obj_path=self.props.parts, attrname=self.props.parts[-1]
        )
        if comment:
            return [comment]

        try:
            # Disable `autodoc_inherit_docstring` temporarily to avoid to obtain
            # a docstring from the value which descriptor returns unexpectedly.
            # See: https://github.com/sphinx-doc/sphinx/issues/7805
            orig = self.config.autodoc_inherit_docstrings
            self.config.autodoc_inherit_docstrings = False

            if self.props._obj is SLOTS_ATTR:
                # support for __slots__
                try:
                    parent___slots__ = inspect.getslots(self.parent)
                    if parent___slots__ and (
                        docstring := parent___slots__.get(self.props.name)
                    ):
                        docstring = prepare_docstring(docstring)
                        return [docstring]
                    else:
                        return []
                except ValueError as exc:
                    logger.warning(
                        __('Invalid __slots__ found on %s. Ignored.'),
                        (self.parent.__qualname__, exc),
                        type='autodoc',
                    )
                    return []

            if (
                self.props._obj is RUNTIME_INSTANCE_ATTRIBUTE
                and _is_runtime_instance_attribute_not_commented(
                    parent=self.parent, obj_path=self.props.parts
                )
            ):
                return None

            if self.props._obj is UNINITIALIZED_ATTR:
                return None

            if self._is_non_data_descriptor:
                # the docstring of non-data descriptor is very probably
                # the wrong thing to display
                return None

            return super().get_doc()
        finally:
            self.config.autodoc_inherit_docstrings = orig

    def add_content(self, more_content: StringList | None) -> None:
        # Disable analyzing attribute comment on Documenter.add_content() to control it on
        # AttributeDocumenter.add_content()
        self.analyzer = None

        if more_content is None:
            more_content = StringList()
        _add_content_generic_alias_(
            more_content,
            self.props._obj,
            autodoc_typehints_format=self.config.autodoc_typehints_format,
        )
        super().add_content(more_content)


class PropertyDocumenter(Documenter):
    """Specialized Documenter subclass for properties."""

    props: _FunctionDefProperties

    __docstring_signature__ = True
    __docstring_strip_signature__ = True

    objtype = 'property'
    member_order = 60

    # before AttributeDocumenter
    priority = AttributeDocumenter.priority + 1

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        if isinstance(parent, ClassDocumenter):
            if inspect.isproperty(member):
                return True
            else:
                # See FakeDirective &c in autosummary, parent might not be a
                # 'proper' Documenter.
                obj = parent.props._obj if hasattr(parent, 'props') else None
                __dict__ = safe_getattr(obj, '__dict__', {})
                obj = __dict__.get(membername)
                return isinstance(obj, classmethod) and inspect.isproperty(obj.__func__)
        else:
            return False

    def format_args(self, **kwargs: Any) -> str:
        func = self._get_property_getter()
        if func is None:
            return ''

        # update the annotations of the property getter
        self._events.emit('autodoc-before-process-signature', func, False)
        # correctly format the arguments for a property
        return super().format_args(**kwargs)

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)
        sourcename = self.get_sourcename()
        if inspect.isabstractmethod(self.props._obj):
            self.add_line('   :abstractmethod:', sourcename)
        # Support for class properties. Note: these only work on Python 3.9.
        if self.props.is_classmethod:
            self.add_line('   :classmethod:', sourcename)

        func = self._get_property_getter()
        if func is None or self.config.autodoc_typehints == 'none':
            return

        try:
            signature = inspect.signature(
                func, type_aliases=self.config.autodoc_type_aliases
            )
            if signature.return_annotation is not Parameter.empty:
                mode = _get_render_mode(self.config.autodoc_typehints_format)
                short_literals = self.config.python_display_short_literal_types
                objrepr = stringify_annotation(
                    signature.return_annotation, mode, short_literals=short_literals
                )
                self.add_line('   :type: ' + objrepr, sourcename)
        except TypeError as exc:
            msg = __('Failed to get a function signature for %s: %s')
            logger.warning(msg, self.props.full_name, exc)
            pass
        except ValueError:
            pass

    def _get_property_getter(self) -> Callable[..., Any] | None:
        if safe_getattr(self.props._obj, 'fget', None):  # property
            return self.props._obj.fget
        if safe_getattr(self.props._obj, 'func', None):  # cached_property
            return self.props._obj.func
        return None


class DocstringSignatureMixin:
    """Retained for compatibility."""

    __docstring_signature__ = True


class ModuleLevelDocumenter(Documenter):
    """Retained for compatibility."""


class ClassLevelDocumenter(Documenter):
    """Retained for compatibility."""


def autodoc_attrgetter(
    obj: Any, name: str, *defargs: Any, registry: SphinxComponentRegistry
) -> Any:
    """Alternative getattr() for types"""
    for typ, func in registry.autodoc_attrgetters.items():
        if isinstance(obj, typ):
            return func(obj, name, *defargs)

    return safe_getattr(obj, name, *defargs)


def _add_content_generic_alias_(
    more_content: StringList,
    /,
    obj: object,
    autodoc_typehints_format: Literal['fully-qualified', 'short'],
) -> None:
    """Support for documenting GenericAliases."""
    if inspect.isgenericalias(obj):
        alias = restify(obj, mode=_get_render_mode(autodoc_typehints_format))
        more_content.append(_('alias of %s') % alias, '')
        more_content.append('', '')


def _document_members(
    *,
    member_documenters: list[tuple[Documenter, bool]],
    real_modname: str,
    members_check_module: bool,
) -> None:
    """Generate reST for member documentation.

    If *all_members* is True, document all members, else those given by
    *self.options.members*.
    """
    for documenter, is_attr in member_documenters:
        assert documenter.props.module_name
        # We can directly call ._generate() since the documenters
        # already called parse_name() and import_object() before.
        #
        # Note that those two methods above do not emit events, so
        # whatever objects we deduced should not have changed.
        documenter._generate(
            all_members=True,
            real_modname=real_modname,
            check_module=members_check_module and not is_attr,
        )
