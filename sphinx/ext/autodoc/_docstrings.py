from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from sphinx.errors import PycodeError
from sphinx.ext.autodoc._property_types import _ClassDefProperties
from sphinx.ext.autodoc._sentinels import (
    RUNTIME_INSTANCE_ATTRIBUTE,
    SLOTS_ATTR,
    UNINITIALIZED_ATTR,
)
from sphinx.locale import __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.inspect import getdoc

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, Literal

    from sphinx.ext.autodoc._property_types import _ItemProperties
    from sphinx.ext.autodoc.importer import _AttrGetter

logger = logging.getLogger('sphinx.ext.autodoc')

_OBJECT_INIT_DOCSTRING = (tuple(prepare_docstring(object.__init__.__doc__ or '')),)
_OBJECT_NEW_DOCSTRING = (tuple(prepare_docstring(object.__new__.__doc__ or '')),)


def _class_variable_comment(props: _ItemProperties) -> bool:
    try:
        analyzer = ModuleAnalyzer.for_module(props.module_name)
        analyzer.analyze()
        key = ('', props.dotted_parts)
        return bool(analyzer.attr_docs.get(key, False))
    except PycodeError:
        return False


def _get_docstring_lines(
    props: _ItemProperties,
    *,
    class_doc_from: Literal['both', 'class', 'init'],
    get_attr: _AttrGetter,
    inherit_docstrings: bool,
    parent: Any,
    tab_width: int,
    _new_docstrings: Sequence[Sequence[str]] | None = None,
) -> Sequence[Sequence[str]] | None:
    obj = props._obj

    if props.obj_type in {'class', 'exception'}:
        assert isinstance(props, _ClassDefProperties)

        if isinstance(obj, TypeVar):
            if obj.__doc__ == TypeVar.__doc__:
                return ()
        if props.doc_as_attr:
            # Don't show the docstring of the class when it is an alias.
            if _class_variable_comment(props):
                return ()
            return None

        if _new_docstrings is not None:
            return tuple(tuple(doc) for doc in _new_docstrings)

        docstrings = []
        attrdocstring = getdoc(obj)
        if attrdocstring:
            docstrings.append(attrdocstring)

        # for classes, what the "docstring" is can be controlled via a
        # config value; the default is only the class docstring
        if class_doc_from in {'both', 'init'}:
            __init__ = get_attr(obj, '__init__', None)
            init_docstring = getdoc(
                __init__,
                allow_inherited=inherit_docstrings,
                cls=obj,  # TODO: object or obj?
                name='__init__',
            )
            # no __init__ means default __init__
            if init_docstring == object.__init__.__doc__:
                init_docstring = None
            if not init_docstring:
                # try __new__
                __new__ = get_attr(obj, '__new__', None)
                init_docstring = getdoc(
                    __new__,
                    allow_inherited=inherit_docstrings,
                    cls=object,  # TODO: object or obj?
                    name='__new__',
                )
                # no __new__ means default __new__
                if init_docstring == object.__new__.__doc__:
                    init_docstring = None
            if init_docstring:
                if class_doc_from == 'init':
                    docstrings = [init_docstring]
                else:
                    docstrings.append(init_docstring)

        return tuple(
            tuple(prepare_docstring(docstring, tab_width)) for docstring in docstrings
        )

    if props.obj_type == 'method':
        docstring = _get_doc(
            obj,
            props=props,
            inherit_docstrings=inherit_docstrings,
            _new_docstrings=_new_docstrings,
            parent=parent,
            tab_width=tab_width,
        )
        if props.name == '__init__':
            if docstring == _OBJECT_INIT_DOCSTRING:
                return ()
        if props.name == '__new__':
            if docstring == _OBJECT_NEW_DOCSTRING:
                return ()
        return docstring

    if props.obj_type == 'data':
        # Check the variable has a docstring-comment

        # get_module_comment()
        comment = None
        try:
            analyzer = ModuleAnalyzer.for_module(props.module_name)
            analyzer.analyze()
            key = ('', props.name)
            if key in analyzer.attr_docs:
                comment = tuple(analyzer.attr_docs[key])
        except PycodeError:
            pass

        if comment:
            return (comment,)
        return _get_doc(
            obj,
            props=props,
            inherit_docstrings=inherit_docstrings,
            _new_docstrings=_new_docstrings,
            parent=parent,
            tab_width=tab_width,
        )

    if props.obj_type == 'attribute':
        from sphinx.ext.autodoc.importer import (
            _get_attribute_comment,
            _is_runtime_instance_attribute_not_commented,
        )

        # Check the attribute has a docstring-comment
        comment = _get_attribute_comment(
            parent=parent, obj_path=props.parts, attrname=props.parts[-1]
        )
        if comment:
            return (comment,)

        # Disable `autodoc_inherit_docstring` to avoid to obtain
        # a docstring from the value which descriptor returns unexpectedly.
        # See: https://github.com/sphinx-doc/sphinx/issues/7805
        inherit_docstrings = False

        if obj is SLOTS_ATTR:
            # support for __slots__
            try:
                parent___slots__ = inspect.getslots(parent)
                if parent___slots__ and (docstring := parent___slots__.get(props.name)):
                    docstring = tuple(prepare_docstring(docstring))
                    return (docstring,)
                return ()
            except ValueError as exc:
                logger.warning(
                    __('Invalid __slots__ found on %s. Ignored.'),
                    (parent.__qualname__, exc),
                    type='autodoc',
                )
                return ()

        if (
            obj is RUNTIME_INSTANCE_ATTRIBUTE
            and _is_runtime_instance_attribute_not_commented(
                parent=parent, obj_path=props.parts
            )
        ):
            return None

        if obj is UNINITIALIZED_ATTR:
            return None

        if not inspect.isattributedescriptor(obj):
            # the docstring of non-data descriptor is very probably
            # the wrong thing to display
            return None

        return _get_doc(
            obj,
            props=props,
            inherit_docstrings=inherit_docstrings,
            _new_docstrings=_new_docstrings,
            parent=parent,
            tab_width=tab_width,
        )

    docstring = _get_doc(
        obj,
        props=props,
        inherit_docstrings=inherit_docstrings,
        _new_docstrings=_new_docstrings,
        parent=parent,
        tab_width=tab_width,
    )
    return docstring


def _get_doc(
    obj: Any,
    *,
    props: _ItemProperties,
    inherit_docstrings: bool,
    _new_docstrings: Sequence[Sequence[str]] | None,
    parent: Any,
    tab_width: int,
) -> Sequence[Sequence[str]] | None:
    """Decode and return lines of the docstring(s) for the object.

    When it returns None, autodoc-process-docstring will not be called for this
    object.
    """
    if obj is UNINITIALIZED_ATTR:
        return ()

    if props.obj_type not in {'module', 'data'} and _new_docstrings is not None:
        # docstring already returned previously, then modified due to
        # ``Documenter._find_signature()``. Just return the
        # previously-computed result, so that we don't lose the processing.
        return _new_docstrings

    docstring = getdoc(
        obj,
        allow_inherited=inherit_docstrings,
        cls=parent,
        name=props.object_name,
    )
    if docstring:
        return (tuple(prepare_docstring(docstring, tab_width)),)
    return ()
