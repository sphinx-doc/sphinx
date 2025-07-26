from __future__ import annotations

from typing import TYPE_CHECKING

from docutils.utils import assemble_option_dict

from sphinx.ext.autodoc._sentinels import ALL, EMPTY, SUPPRESS
from sphinx.locale import __

if TYPE_CHECKING:
    from typing import Any

    from sphinx.ext.autodoc._documenters import Documenter


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


def identity(x: Any) -> Any:
    return x


def members_option(arg: Any) -> object | list[str]:
    """Used to convert the :members: option to auto directives."""
    if arg in {None, True}:
        return ALL
    elif arg is False:
        return None
    else:
        return [x.strip() for x in arg.split(',') if x.strip()]


def exclude_members_option(arg: Any) -> object | set[str]:
    """Used to convert the :exclude-members: option."""
    if arg in {None, True}:
        return EMPTY
    return {x.strip() for x in arg.split(',') if x.strip()}


def inherited_members_option(arg: Any) -> set[str]:
    """Used to convert the :inherited-members: option to auto directives."""
    if arg in {None, True}:
        return {'object'}
    elif arg:
        return {x.strip() for x in arg.split(',')}
    else:
        return set()


def member_order_option(arg: Any) -> str | None:
    """Used to convert the :member-order: option to auto directives."""
    if arg in {None, True}:
        return None
    elif arg in {'alphabetical', 'bysource', 'groupwise'}:
        return arg
    else:
        raise ValueError(__('invalid value for member-order option: %s') % arg)


def class_doc_from_option(arg: Any) -> str | None:
    """Used to convert the :class-doc-from: option to autoclass directives."""
    if arg in {'both', 'class', 'init'}:
        return arg
    else:
        raise ValueError(__('invalid value for class-doc-from option: %s') % arg)


def annotation_option(arg: Any) -> Any:
    if arg in {None, True}:
        # suppress showing the representation of the object
        return SUPPRESS
    else:
        return arg


def bool_option(arg: Any) -> bool:
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
    documenter: type[Documenter],
    *,
    default_options: dict[str, str | bool],
    options: dict[str, str],
) -> Options:
    """Recognize options of Documenter from user input."""
    for name in AUTODOC_DEFAULT_OPTIONS:
        if name not in documenter.option_spec:
            continue

        negated = options.pop(f'no-{name}', True) is None
        if name in default_options and not negated:
            if name in options and isinstance(default_options[name], str):
                # take value from options if present or extend it
                # with autodoc_default_options if necessary
                if name in AUTODOC_EXTENDABLE_OPTIONS:
                    if options[name] is not None and options[name].startswith('+'):
                        options[name] = f'{default_options[name]},{options[name][1:]}'
            else:
                options[name] = default_options[name]  # type: ignore[assignment]
        elif options.get(name) is not None:
            # remove '+' from option argument if there's nothing to merge it with
            options[name] = options[name].removeprefix('+')

    opts = assemble_option_dict(options.items(), documenter.option_spec)
    return Options(opts)
