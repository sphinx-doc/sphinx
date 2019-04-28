"""
    sphinx.deprecation
    ~~~~~~~~~~~~~~~~~~

    Sphinx deprecation classes and utilities.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import warnings
from importlib import import_module

if False:
    # For type annotation
    from typing import Any, Dict, Type  # NOQA


class RemovedInSphinx30Warning(DeprecationWarning):
    pass


class RemovedInSphinx40Warning(PendingDeprecationWarning):
    pass


RemovedInNextVersionWarning = RemovedInSphinx30Warning


def deprecated_alias(modname, objects, warning):
    # type: (str, Dict, Type[Warning]) -> None
    module = sys.modules.get(modname)
    if module is None:
        module = import_module(modname)

    sys.modules[modname] = _ModuleWrapper(module, modname, objects, warning)  # type: ignore


class _ModuleWrapper:
    def __init__(self, module, modname, objects, warning):
        # type: (Any, str, Dict, Type[Warning]) -> None
        self._module = module
        self._modname = modname
        self._objects = objects
        self._warning = warning

    def __getattr__(self, name):
        # type: (str) -> Any
        if name in self._objects:
            warnings.warn("%s.%s is deprecated. Check CHANGES for Sphinx "
                          "API modifications." % (self._modname, name),
                          self._warning, stacklevel=3)
            return self._objects[name]

        return getattr(self._module, name)


class DeprecatedDict(dict):
    """A deprecated dict which warns on each access."""

    def __init__(self, data, message, warning):
        # type: (Dict, str, Type[Warning]) -> None
        self.message = message
        self.warning = warning
        super().__init__(data)

    def __setitem__(self, key, value):
        # type: (str, Any) -> None
        warnings.warn(self.message, self.warning, stacklevel=2)
        super().__setitem__(key, value)

    def setdefault(self, key, default=None):
        # type: (str, Any) -> None
        warnings.warn(self.message, self.warning, stacklevel=2)
        return super().setdefault(key, default)

    def __getitem__(self, key):
        # type: (str) -> None
        warnings.warn(self.message, self.warning, stacklevel=2)
        return super().__getitem__(key)

    def get(self, key, default=None):
        # type: (str, Any) -> None
        warnings.warn(self.message, self.warning, stacklevel=2)
        return super().get(key, default)

    def update(self, other=None):  # type: ignore
        # type: (Dict) -> None
        warnings.warn(self.message, self.warning, stacklevel=2)
        super().update(other)
