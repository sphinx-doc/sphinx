from __future__ import annotations

import operator
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
from sphinx.ext.autodoc._renderer import _add_content, _directive_header_lines
from sphinx.ext.autodoc._sentinels import ALL
from sphinx.ext.autodoc.importer import _load_object_by_name, _resolve_name
from sphinx.ext.autodoc.mock import ismock
from sphinx.locale import _, __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.inspect import safe_getattr
from sphinx.util.typing import AnyTypeAliasType, restify, stringify_annotation

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import ModuleType
    from typing import Any, ClassVar, Final, Literal

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
        _TypeStatementProperties,
    )
    from sphinx.ext.autodoc.directive import DocumenterBridge
    from sphinx.registry import SphinxComponentRegistry
    from sphinx.util.typing import OptionSpec, _RestifyMode

logger = logging.getLogger('sphinx.ext.autodoc')


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
    #: order if autodoc_member_order is set to 'groupwise'
    member_order: ClassVar = 0
    #: true if the generated content may contain titles
    titles_allowed: ClassVar = True

    __uninitialized_global_variable__: ClassVar[bool] = False
    """If True, support uninitialized (type annotation only) global variables"""

    option_spec: ClassVar[OptionSpec] = {
        'no-index': bool_option,
        'no-index-entry': bool_option,
        'noindex': bool_option,
    }

    def get_attr(self, obj: Any, name: str, *defargs: Any) -> Any:
        """getattr() override for types such as Zope interfaces."""
        return autodoc_attrgetter(obj, name, *defargs, registry=self.env._registry)

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
        self.indent: Final = indent
        # the module and object path within the module, and the fully
        # qualified name (all set after resolve_name succeeds)
        self.modname: str = ''
        self.module: ModuleType | None = None
        self.objpath: list[str] = []
        self.fullname = ''
        # the object to document (set after import_object succeeds)
        self.object: Any = None
        self.object_name = ''
        # the parent/owner of the object to document
        self.parent: Any = None
        # the module analyzer to get at attribute docs, or None
        self.analyzer: ModuleAnalyzer | None = None

        self._load_object_has_been_called = False

        if isinstance(self, ModuleDocumenter):
            self.options = self.options.merge_member_options()
        elif isinstance(self, ClassDocumenter):
            if self.config.autodoc_class_signature == 'separated':
                # show __init__() method
                if self.options.special_members is None:
                    self.options.special_members = []
                self.options.special_members += ['__new__', '__init__']
            self.options = self.options.merge_member_options()

    @property
    def documenters(self) -> dict[str, type[Documenter]]:
        """Returns registered Documenter classes"""
        return self.env._registry.documenters

    def add_line(self, line: str, source: str, *lineno: int, indent: str) -> None:
        """Append one line of generated reST to the output."""
        if line.strip():  # not a blank line
            self.directive.result.append(indent + line, source, *lineno)
        else:
            self.directive.result.append('', source, *lineno)

    def _load_object_by_name(self) -> Literal[True] | None:
        if self._load_object_has_been_called:
            return True

        ret = _load_object_by_name(
            name=self.name,
            objtype=self.objtype,  # type: ignore[arg-type]
            mock_imports=self.config.autodoc_mock_imports,
            type_aliases=self.config.autodoc_type_aliases,
            current_document=self._current_document,
            config=self.config,
            env=self.env,
            events=self._events,
            get_attr=self.get_attr,
            options=self.options,
        )
        if ret is None:
            return None
        props, module, parent = ret

        self.props = props
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

    def add_directive_header(self, *, indent: str) -> None:
        """Add the directive header and options to the generated content."""
        domain_name = getattr(self, 'domain', 'py')
        if self.objtype in {'class', 'exception'} and self.props.doc_as_attr:  # type: ignore[attr-defined]
            directive_name = 'attribute'
        else:
            directive_name = getattr(self, 'directivetype', self.objtype)
        directive_name = f'{domain_name}:{directive_name}'

        if self.analyzer:
            is_final = self.props.dotted_parts in self.analyzer.finals
        else:
            is_final = False

        result = self.directive.result
        sourcename = self.get_sourcename()
        for line in _directive_header_lines(
            autodoc_typehints=self.config.autodoc_typehints,
            directive_name=directive_name,
            is_final=is_final,
            options=self.options,
            props=self.props,
        ):
            if line.strip():  # not a blank line
                result.append(indent + line, sourcename)
            else:
                result.append('', sourcename)

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

    def add_content(self, more_content: StringList | None, *, indent: str) -> None:
        """Add content from docstrings, attribute documentation and user."""
        # add content from docstrings
        processed_doc = StringList(
            list(
                self._process_docstrings(
                    self._get_docstrings(),
                    events=self._events,
                    props=self.props,
                    obj=self.props._obj,
                    options=self.options,
                )
            ),
            source=self.get_sourcename(),
        )
        _add_content(
            processed_doc,
            result=self.directive.result,
            indent=indent + '   ',
        )

        # add additional content (e.g. from document), if present
        more_content = self._assemble_more_content(
            more_content=StringList() if more_content is None else more_content,
            typehints_format=self.config.autodoc_typehints_format,
            python_display_short_literal_types=self.config.python_display_short_literal_types,
            props=self.props,
        )
        _add_content(
            more_content,
            result=self.directive.result,
            indent=indent + '   ' * (self.props.obj_type != 'module'),
        )

    def _get_docstrings(self) -> list[list[str]] | None:
        """Add content from docstrings, attribute documentation and user."""
        if self.props._docstrings is not None:
            docstrings = [list(doc) for doc in self.props._docstrings]
        else:
            docstrings = None
        props = self.props

        if docstrings is not None and len(docstrings) == 0:
            # append at least a dummy docstring, so that the event
            # autodoc-process-docstring is fired and can add some
            # content if desired
            docstrings.append([])

        if props.obj_type in {'data', 'attribute'}:
            return docstrings

        attr_docs = None if self.analyzer is None else self.analyzer.find_attr_docs()
        if props.obj_type in {'class', 'exception'}:
            real_module = props._obj___module__ or props.module_name
            if props.module_name != real_module:
                try:
                    # override analyzer to obtain doc-comment around its definition.
                    ma = ModuleAnalyzer.for_module(props.module_name)
                    ma.analyze()
                    attr_docs = ma.attr_docs
                except PycodeError:
                    pass

        # add content from attribute documentation
        if attr_docs is not None and props.parts:
            key = ('.'.join(props.parent_names), props.name)
            if key in attr_docs:
                # make a copy of docstring for attributes to avoid cache
                # the change of autodoc-process-docstring event.
                return [list(attr_docs[key])]

        return docstrings

    @staticmethod
    def _process_docstrings(
        docstrings: list[list[str]] | None,
        *,
        events: EventManager,
        props: _ItemProperties,
        obj: Any,
        options: _AutoDocumenterOptions,
    ) -> Iterator[str]:
        """Let the user process the docstrings before adding them."""
        if docstrings is None:
            return
        for docstring_lines in docstrings:
            # let extensions preprocess docstrings
            events.emit(
                'autodoc-process-docstring',
                props.obj_type,
                props.full_name,
                obj,
                options,
                docstring_lines,
            )

            if docstring_lines and docstring_lines[-1]:
                # append a blank line to the end of the docstring
                docstring_lines.append('')

            yield from docstring_lines

    @staticmethod
    def _assemble_more_content(
        more_content: StringList,
        *,
        props: _ItemProperties,
        typehints_format: Literal['fully-qualified', 'short'],
        python_display_short_literal_types: bool,
    ) -> StringList:
        """Add content from docstrings, attribute documentation and user."""
        obj = props._obj

        if props.obj_type in {'data', 'attribute'}:
            mode = _get_render_mode(typehints_format)

            # Support for documenting GenericAliases
            if inspect.isgenericalias(obj):
                alias = restify(obj, mode=mode)
                more_content.append(_('alias of %s') % alias, '')
                more_content.append('', '')
            return more_content

        if props.obj_type in {'class', 'exception'}:
            from sphinx.ext.autodoc._property_types import _ClassDefProperties

            assert isinstance(props, _ClassDefProperties)

            mode = _get_render_mode(typehints_format)

            if isinstance(obj, NewType):
                supertype = restify(obj.__supertype__, mode=mode)
                return StringList([_('alias of %s') % supertype, ''], source='')

            if isinstance(obj, TypeVar):
                short_literals = python_display_short_literal_types
                attrs = [
                    repr(obj.__name__),
                    *(
                        stringify_annotation(
                            constraint, mode, short_literals=short_literals
                        )
                        for constraint in obj.__constraints__
                    ),
                ]
                if obj.__bound__:
                    attrs.append(rf'bound=\ {restify(obj.__bound__, mode=mode)}')
                if obj.__covariant__:
                    attrs.append('covariant=True')
                if obj.__contravariant__:
                    attrs.append('contravariant=True')

                alias = f'TypeVar({", ".join(attrs)})'
                return StringList([_('alias of %s') % alias, ''], source='')

            if props.doc_as_attr:
                try:
                    analyzer = ModuleAnalyzer.for_module(props.module_name)
                    analyzer.analyze()
                    key = ('', props.dotted_parts)
                    no_classvar_doc_comment = key not in analyzer.attr_docs
                except PycodeError:
                    no_classvar_doc_comment = True

                if no_classvar_doc_comment:
                    alias = restify(obj, mode=mode)
                    return StringList([_('alias of %s') % alias], source='')

            return more_content

        return more_content

    def sort_members(
        self, documenters: list[tuple[Documenter, bool]], order: str
    ) -> list[tuple[Documenter, bool]]:
        """Sort the given member list."""
        if order == 'groupwise':
            # sort by group; alphabetically within groups
            documenters.sort(key=lambda e: (e[0].member_order, e[0].name))
        elif order == 'bysource':
            if (
                isinstance(self, ModuleDocumenter)
                and not self.options.ignore_module_all
                and (module_all := self.props.all)
            ):
                # Sort by __all__
                module_all_idx = {name: idx for idx, name in enumerate(module_all)}
                module_all_len = len(module_all)

                def key_func(entry: tuple[Documenter, bool]) -> int:
                    fullname = entry[0].name.split('::')[1]
                    return module_all_idx.get(fullname, module_all_len)

                documenters.sort(key=key_func)

            # By default, member discovery order matches source order,
            # as dicts are insertion-ordered from Python 3.7.
            elif self.analyzer is not None:
                # sort by source order, by virtue of the module analyzer
                tagorder = self.analyzer.tagorder
                tagorder_len = len(tagorder)

                def key_func(entry: tuple[Documenter, bool]) -> int:
                    fullname = entry[0].name.split('::')[1]
                    return tagorder.get(fullname, tagorder_len)

                documenters.sort(key=key_func)
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
        if isinstance(self, ClassDocumenter):
            # Do not pass real_modname and use the name from the __module__
            # attribute of the class.
            # If a class gets imported into the module real_modname
            # the analyzer won't find the source of the class, if
            # it looks in real_modname.
            real_modname = None

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

        if self.real_modname != guess_modname:
            # Add module to dependency list if target object is defined in other module.
            try:
                analyzer = ModuleAnalyzer.for_module(guess_modname)
                self.directive.record_dependencies.add(analyzer.srcname)
            except PycodeError:
                pass

        has_docstring = any(self.props._docstrings or ())
        if ismock(self.props._obj) and not has_docstring:
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

        indent = self.indent
        sourcename = self.get_sourcename()

        # make sure that the result starts with an empty line.  This is
        # necessary for some situations where another directive preprocesses
        # reST and no starting newline is present
        self.directive.result.append('', sourcename)

        # generate the directive header and options, if applicable
        self.add_directive_header(indent=indent)
        self.directive.result.append('', sourcename)

        # add all content (from docstrings, attribute docs etc.)
        self.add_content(more_content, indent=indent)

        # document members, if possible
        has_members = isinstance(self, ModuleDocumenter) or (
            isinstance(self, ClassDocumenter) and not self.props.doc_as_attr
        )
        if has_members:
            want_all = bool(
                all_members
                or self.options.inherited_members
                or self.options.members is ALL
            )
            member_documenters = self._gather_members(want_all=want_all, indent=indent)
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
        indent += '   ' * (props.obj_type != 'module')

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
            obj_type = _best_object_type_for_member(
                member=member,
                member_name=member_name,
                is_attr=is_attr,
                parent_documenter=self,
            )
            if not obj_type:
                # don't know how to document this member
                continue
            doccls = registry.documenters[obj_type]
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


class FunctionDocumenter(Documenter):
    """Specialized Documenter subclass for functions."""

    props: _FunctionDefProperties

    objtype = 'function'
    member_order = 30


class DecoratorDocumenter(FunctionDocumenter):
    """Specialized Documenter subclass for decorator functions."""

    props: _FunctionDefProperties

    objtype = 'decorator'


class ClassDocumenter(Documenter):
    """Specialized Documenter subclass for classes."""

    props: _ClassDefProperties

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


class ExceptionDocumenter(ClassDocumenter):
    """Specialized ClassDocumenter subclass for exceptions."""

    props: _ClassDefProperties

    objtype = 'exception'
    member_order = 10


class DataDocumenter(Documenter):
    """Specialized Documenter subclass for data items."""

    props: _AssignStatementProperties

    __uninitialized_global_variable__ = True

    objtype = 'data'
    member_order = 40
    option_spec: ClassVar[OptionSpec] = dict(Documenter.option_spec)
    option_spec['annotation'] = annotation_option
    option_spec['no-value'] = bool_option


class MethodDocumenter(Documenter):
    """Specialized Documenter subclass for methods (normal, static and class)."""

    props: _FunctionDefProperties

    objtype = 'method'
    directivetype = 'method'
    member_order = 50


class AttributeDocumenter(Documenter):
    """Specialized Documenter subclass for attributes."""

    props: _AssignStatementProperties

    objtype = 'attribute'
    member_order = 60
    option_spec: ClassVar[OptionSpec] = dict(Documenter.option_spec)
    option_spec['annotation'] = annotation_option
    option_spec['no-value'] = bool_option

    @staticmethod
    def is_function_or_method(obj: Any) -> bool:
        return (
            inspect.isfunction(obj) or inspect.isbuiltin(obj) or inspect.ismethod(obj)
        )


class PropertyDocumenter(Documenter):
    """Specialized Documenter subclass for properties."""

    props: _FunctionDefProperties

    objtype = 'property'
    member_order = 60


class TypeAliasDocumenter(Documenter):
    """Specialized Documenter subclass for type aliases."""

    props: _TypeStatementProperties

    objtype = 'type'
    member_order = 70
    option_spec: ClassVar[OptionSpec] = {
        'no-index': bool_option,
        'no-index-entry': bool_option,
        'annotation': annotation_option,
        'no-value': bool_option,
    }


class DocstringSignatureMixin:
    """Retained for compatibility."""


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


def _best_object_type_for_member(
    member: Any,
    member_name: str,
    is_attr: bool,
    parent_documenter: Documenter,
) -> str | None:
    """Return the best object type that supports documenting *member*."""
    filtered = []

    # Don't document submodules automatically: 'module' is never returned.

    try:
        if isinstance(member, type) and issubclass(member, BaseException):
            # priority must be higher than 'class'
            filtered.append((20, 'exception'))
    except TypeError as exc:
        # It's possible for a member to be considered a type, but fail
        # issubclass checks due to not being a class. For example:
        # https://github.com/sphinx-doc/sphinx/issues/11654#issuecomment-1696790436
        msg = f'Failed to discern if member {member} is a BaseException subclass.'
        raise ValueError(msg) from exc

    if isinstance(member, type) or (is_attr and isinstance(member, (NewType, TypeVar))):
        # priority must be higher than 'function', 'class', and 'attribute'
        # as NewType can be an attribute and is a class after Python 3.10.
        filtered.append((15, 'class'))

    if isinstance(parent_documenter, ClassDocumenter):
        if inspect.isproperty(member):
            # priority must be higher than 'attribute'
            filtered.append((11, 'property'))

        # Support for class properties. Note: these only work on Python 3.9.
        elif hasattr(parent_documenter, 'props'):
            # See FakeDirective &c in autosummary, parent might not be a
            # 'proper' Documenter.
            __dict__ = safe_getattr(parent_documenter.props._obj, '__dict__', {})
            obj = __dict__.get(member_name)
            if isinstance(obj, classmethod) and inspect.isproperty(obj.__func__):
                # priority must be higher than 'attribute'
                filtered.append((11, 'property'))

    if not isinstance(parent_documenter, ModuleDocumenter):
        if inspect.isattributedescriptor(member) or not (
            inspect.isroutine(member) or isinstance(member, type)
        ):
            # priority must be higher than 'method', else it will recognise
            # some non-data descriptors as methods
            filtered.append((10, 'attribute'))

    if inspect.isroutine(member) and not isinstance(
        parent_documenter, ModuleDocumenter
    ):
        # priority must be higher than 'function'
        filtered.append((1, 'method'))

    if (
        inspect.isfunction(member)
        or inspect.isbuiltin(member)
        or (
            inspect.isroutine(member)
            and isinstance(parent_documenter, ModuleDocumenter)
        )
    ):
        # supports functions, builtins and bound methods exported
        # at the module level
        filtered.extend(((0, 'function'), (-1, 'decorator')))

    if isinstance(member, AnyTypeAliasType):
        filtered.append((0, 'type'))

    if isinstance(parent_documenter, ModuleDocumenter) and is_attr:
        filtered.append((-10, 'data'))

    if filtered:
        # return the highest priority object type
        return max(filtered, key=operator.itemgetter(0))[1]
    return None
