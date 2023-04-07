"""Sphinx deprecation classes and utilities."""

from __future__ import annotations

import warnings


class RemovedInSphinx70Warning(DeprecationWarning):
    pass


class RemovedInSphinx80Warning(PendingDeprecationWarning):
    pass


RemovedInNextVersionWarning = RemovedInSphinx70Warning


def _deprecation_warning(
    module: str,
    attribute: str,
    canonical_name: str,
    *,
    remove: tuple[int, int],
) -> None:
    """Helper function for module-level deprecations using __getattr__

    Exemplar usage:

    .. code:: python

       # deprecated name -> (object to return, canonical path or empty string)
       _DEPRECATED_OBJECTS = {
           'deprecated_name': (object_to_return, 'fully_qualified_replacement_name'),
       }


       def __getattr__(name):
           if name not in _DEPRECATED_OBJECTS:
               raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

           from sphinx.deprecation import _deprecation_warning

           deprecated_object, canonical_name = _DEPRECATED_OBJECTS[name]
           _deprecation_warning(__name__, name, canonical_name, remove=(7, 0))
           return deprecated_object
    """

    if remove == (7, 0):
        warning_class: type[Warning] = RemovedInSphinx70Warning
    elif remove == (8, 0):
        warning_class = RemovedInSphinx80Warning
    else:
        raise RuntimeError(f'removal version {remove!r} is invalid!')

    qualified_name = f'{module}.{attribute}'
    if canonical_name:
        message = (f'The alias {qualified_name!r} is deprecated, '
                   f'use {canonical_name!r} instead.')
    else:
        message = f'{qualified_name!r} is deprecated.'

    warnings.warn(message + " Check CHANGES for Sphinx API modifications.",
                  warning_class, stacklevel=3)


class OldJinjaSuffixWarning(PendingDeprecationWarning):
    """Warning class for ``_old_jinja_template_suffix_warning``.

    This class exists only so that extensions and themes can silence the legacy
    filename warning via Python's `warning control`_ mechanisms. See
    :ref:`theming-static-templates` for an example.

    This warning class will be removed, and the warning class changed to the
    appropriate RemovedInSphinx_0Warning no earlier than 31 December 2024, at
    which point the standard deprecation process for ``_t`` template suffixes
    will start.

    .. _warning control: https://docs.python.org/3/library/warnings.html#the-warnings-filter
    """


def _old_jinja_template_suffix_warning(filename: str) -> None:
    if filename.endswith('_t'):
        warnings.warn(
            f"{filename!r}: the '_t' suffix for Jinja templates is deprecated. "
            "If the file is a template, use the suffix '.jinja' instead. "
            'For more information, see '
            'https://www.sphinx-doc.org/en/master/development/theming.html#static-templates',
            OldJinjaSuffixWarning,
            stacklevel=3,
        )
