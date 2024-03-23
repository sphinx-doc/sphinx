"""Sphinx deprecation classes and utilities."""

from __future__ import annotations

import warnings


class RemovedInSphinx80Warning(DeprecationWarning):
    pass


class RemovedInSphinx90Warning(PendingDeprecationWarning):
    pass


RemovedInNextVersionWarning = RemovedInSphinx80Warning


def _deprecation_warning(
    module: str,
    attribute: str,
    canonical_name: str,
    *,
    remove: tuple[int, int],
    strict: bool = False
) -> None:
    """Helper function for module-level deprecations using __getattr__

    Exemplar usage:

    .. code:: python

       # deprecated name -> (object to return, canonical path or empty string)
       _DEPRECATED_OBJECTS = {
           'deprecated_name': (object_to_return, 'fully_qualified_replacement_name', (8, 0)),
       }


       def __getattr__(name: str) -> Any:
           if name not in _DEPRECATED_OBJECTS:
               msg = f'module {__name__!r} has no attribute {name!r}'
               raise AttributeError(msg)

           from sphinx.deprecation import _deprecation_warning

           deprecated_object, canonical_name, remove = _DEPRECATED_OBJECTS[name]
           _deprecation_warning(__name__, name, canonical_name, remove=remove)
           return deprecated_object

    When *strict* is ``True``, an :exc:`AttributeError` is raised instead
    so that it is easy to locate deprecated objects in tests which could
    suppress deprecation warnings.
    """
    if remove == (8, 0):
        warning_class: type[Warning] = RemovedInSphinx80Warning
    elif remove == (9, 0):
        warning_class = RemovedInSphinx90Warning
    else:
        msg = f'removal version {remove!r} is invalid!'
        raise RuntimeError(msg)

    qualified_name = f'{module}.{attribute}'
    if canonical_name:
        message = (
            f'The alias {qualified_name!r} is deprecated, use {canonical_name!r} instead.'
        )
    else:
        message = f'{qualified_name!r} is deprecated.'

    if strict:
        raise AttributeError(message)

    message = f'{message} Check CHANGES for Sphinx API modifications.'
    warnings.warn(message, warning_class, stacklevel=3)
