"""Sphinx deprecation classes and utilities."""

from __future__ import annotations

import sys
import warnings
from importlib import import_module
from typing import Any, Dict


class RemovedInSphinx70Warning(DeprecationWarning):
    pass


class RemovedInSphinx80Warning(PendingDeprecationWarning):
    pass


RemovedInNextVersionWarning = RemovedInSphinx70Warning


def deprecated_alias(modname: str, objects: dict[str, object],
                     warning: type[Warning], names: dict[str, str] = {}) -> None:
    module = import_module(modname)
    sys.modules[modname] = _ModuleWrapper(  # type: ignore
        module, modname, objects, warning, names)


class _ModuleWrapper:
    def __init__(self, module: Any, modname: str,
                 objects: dict[str, object],
                 warning: type[Warning],
                 names: dict[str, str]) -> None:
        self._module = module
        self._modname = modname
        self._objects = objects
        self._warning = warning
        self._names = names

    def __getattr__(self, name: str) -> Any:
        if name not in self._objects:
            return getattr(self._module, name)

        canonical_name = self._names.get(name, None)
        if canonical_name is not None:
            warnings.warn(f"The alias '{self._modname}.{name}' is deprecated, "
                          f"use '{canonical_name}' instead. "
                          "Check CHANGES for Sphinx API modifications.",
                          self._warning, stacklevel=3)
        else:
            warnings.warn(f"{self._modname}.{name} is deprecated. "
                          "Check CHANGES for Sphinx API modifications.",
                          self._warning, stacklevel=3)
        return self._objects[name]


class DeprecatedDict(Dict[str, Any]):
    """A deprecated dict which warns on each access."""

    def __init__(self, data: dict[str, Any], message: str, warning: type[Warning]) -> None:
        self.message = message
        self.warning = warning
        super().__init__(data)

    def __setitem__(self, key: str, value: Any) -> None:
        warnings.warn(self.message, self.warning, stacklevel=2)
        super().__setitem__(key, value)

    def setdefault(self, key: str, default: Any = None) -> Any:
        warnings.warn(self.message, self.warning, stacklevel=2)
        return super().setdefault(key, default)

    def __getitem__(self, key: str) -> Any:
        warnings.warn(self.message, self.warning, stacklevel=2)
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        warnings.warn(self.message, self.warning, stacklevel=2)
        return super().get(key, default)

    def update(self, other: dict[str, Any]) -> None:  # type: ignore
        warnings.warn(self.message, self.warning, stacklevel=2)
        super().update(other)
