from __future__ import annotations

from typing import TYPE_CHECKING

from docutils.utils import assemble_option_dict

from sphinx.ext.autodoc._sentinels import ALL, EMPTY, SUPPRESS
from sphinx.locale import __

if TYPE_CHECKING:
    from collections.abc import Mapping, Set
    from typing import Any, Literal, Self

    from sphinx.ext.autodoc._sentinels import ALL_T, EMPTY_T, SUPPRESS_T
    from sphinx.util.typing import OptionSpec


# common option names for autodoc directives
AUTODOC_DEFAULT_OPTIONS = (
    'members',
    'undoc-members',
    'no-index',
    'no-index-entry',
    'inherited-members',
    'show-inheritance',
    'private-members',
    'special-members',
    'ignore-module-all',
    'exclude-members',
    'member-order',
    'imported-members',
    'class-doc-from',
    'no-value',
)

AUTODOC_EXTENDABLE_OPTIONS = frozenset({
    'members',
    'private-members',
    'special-members',
    'exclude-members',
})


class _AutoDocumenterOptions:
    # TODO: make immutable.

    no_index: Literal[True] | None = None
    no_index_entry: Literal[True] | None = None

    # module-like options
    members: ALL_T | list[str] | None = None
    undoc_members: Literal[True] | None = None
    inherited_members: Set[str] | None = None
    show_inheritance: Literal[True] | None = None
    synopsis: str | None = None
    platform: str | None = None
    deprecated: Literal[True] | None = None
    member_order: Literal['alphabetical', 'bysource', 'groupwise'] | None = None
    exclude_members: EMPTY_T | set[str] | None = None
    private_members: ALL_T | list[str] | None = None
    special_members: ALL_T | list[str] | None = None
    imported_members: Literal[True] | None = None
    ignore_module_all: Literal[True] | None = None
    no_value: Literal[True] | None = None

    # class-like options (class, exception)
    class_doc_from: Literal['both', 'class', 'init'] | None = None

    # assignment-like (data, attribute)
    annotation: SUPPRESS_T | str | None = None

    noindex: Literal[True] | None = None

    def __init__(self, **kwargs: Any) -> None:
        vars(self).update(kwargs)

    def __repr__(self) -> str:
        args = ', '.join(f'{k}={v!r}' for k, v in vars(self).items())
        return f'_AutoDocumenterOptions({args})'

    def __getattr__(self, name: str) -> object:
        return None  # return None for missing attributes

    def copy(self) -> Self:
        return self.__class__(**vars(self))

    @classmethod
    def from_directive_options(cls, opts: Mapping[str, Any], /) -> Self:
        return cls(**{k.replace('-', '_'): v for k, v in opts.items() if v is not None})

    def merge_member_options(self) -> Self:
        """Merge :private-members: and :special-members: into :members:"""
        if self.members is ALL:
            # merging is not needed when members: ALL
            return self

        members = self.members or []
        for others in self.private_members, self.special_members:
            if others is not None and others is not ALL:
                members.extend(others)
        new = self.copy()
        new.members = list(dict.fromkeys(members))  # deduplicate; preserve order
        return new


def identity(x: Any) -> Any:
    return x


def members_option(arg: str | None) -> ALL_T | list[str] | None:
    """Used to convert the :members: option to auto directives."""
    if arg is None or arg is True:
        return ALL
    if arg is False:
        return None
    return [stripped for x in arg.split(',') if (stripped := x.strip())]


def exclude_members_option(arg: str | None) -> EMPTY_T | set[str]:
    """Used to convert the :exclude-members: option."""
    if arg is None or arg is True:
        return EMPTY
    return {stripped for x in arg.split(',') if (stripped := x.strip())}


def inherited_members_option(arg: str | None) -> set[str]:
    """Used to convert the :inherited-members: option to auto directives."""
    if arg is None or arg is True:
        return {'object'}
    if arg:
        return {x.strip() for x in arg.split(',')}
    return set()


def member_order_option(
    arg: str | None,
) -> Literal['alphabetical', 'bysource', 'groupwise'] | None:
    """Used to convert the :member-order: option to auto directives."""
    if arg is None or arg is True:
        return None
    if arg in {'alphabetical', 'bysource', 'groupwise'}:
        return arg  # type: ignore[return-value]
    raise ValueError(__('invalid value for member-order option: %s') % arg)


def class_doc_from_option(arg: str | None) -> Literal['both', 'class', 'init']:
    """Used to convert the :class-doc-from: option to autoclass directives."""
    if arg in {'both', 'class', 'init'}:
        return arg  # type: ignore[return-value]
    raise ValueError(__('invalid value for class-doc-from option: %s') % arg)


def annotation_option(arg: str | None) -> SUPPRESS_T | str | Literal[False]:
    if arg is None or arg is True:
        # suppress showing the representation of the object
        return SUPPRESS
    return arg


def bool_option(arg: str | None) -> bool:
    """Used to convert flag options to auto directives.  (Instead of
    directives.flag(), which returns None).
    """
    return True


def merge_members_option(options: dict[str, Any]) -> None:
    """Merge :private-members: and :special-members: options to the
    :members: option.
    """
    if options.get('members') is ALL:
        # merging is not needed when members: ALL
        return

    members = options.setdefault('members', [])
    for key in ('private-members', 'special-members'):
        other_members = options.get(key)
        if other_members is not None and other_members is not ALL:
            for member in other_members:
                if member not in members:
                    members.append(member)


class Options(dict[str, object]):  # NoQA: FURB189
    """A dict/attribute hybrid that returns None on nonexisting keys."""

    def __repr__(self) -> str:
        return f'Options({super().__repr__()})'

    def copy(self) -> Options:
        return Options(super().copy())

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name.replace('_', '-')]
        except KeyError:
            return None


def _process_documenter_options(
    *,
    option_spec: OptionSpec,
    default_options: dict[str, str | bool],
    options: dict[str, str | None],
) -> dict[str, object]:
    """Recognize options of Documenter from user input."""
    for name in AUTODOC_DEFAULT_OPTIONS:
        if name not in option_spec:
            continue

        negated = options.pop(f'no-{name}', True) is None
        if name in default_options and not negated:
            if name in options and isinstance(default_options[name], str):
                # take value from options if present or extend it
                # with autodoc_default_options if necessary
                if name in AUTODOC_EXTENDABLE_OPTIONS:
                    opt_value = options[name]
                    if opt_value is not None and opt_value.startswith('+'):
                        options[name] = f'{default_options[name]},{opt_value[1:]}'
            else:
                options[name] = default_options[name]  # type: ignore[assignment]
        elif (opt_value := options.get(name)) is not None:
            # remove '+' from option argument if there's nothing to merge it with
            options[name] = opt_value.removeprefix('+')

    return assemble_option_dict(options.items(), option_spec)  # type: ignore[arg-type]
