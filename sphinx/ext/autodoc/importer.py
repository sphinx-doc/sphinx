# -*- coding: utf-8 -*-
"""
    sphinx.ext.autodoc.importer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Importer utilities for autodoc

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from types import FunctionType, MethodType, ModuleType

from sphinx.util import logging

if False:
    # For type annotation
    from typing import Any, List, Set  # NOQA

logger = logging.getLogger(__name__)


class _MockObject(object):
    """Used by autodoc_mock_imports."""

    def __init__(self, *args, **kwargs):
        # type: (Any, Any) -> None
        pass

    def __len__(self):
        # type: () -> int
        return 0

    def __contains__(self, key):
        # type: (str) -> bool
        return False

    def __iter__(self):
        # type: () -> None
        pass

    def __getitem__(self, key):
        # type: (str) -> _MockObject
        return self

    def __getattr__(self, key):
        # type: (str) -> _MockObject
        return self

    def __call__(self, *args, **kw):
        # type: (Any, Any) -> Any
        if args and type(args[0]) in [FunctionType, MethodType]:
            # Appears to be a decorator, pass through unchanged
            return args[0]
        return self


class _MockModule(ModuleType):
    """Used by autodoc_mock_imports."""
    __file__ = '/dev/null'

    def __init__(self, name, loader):
        # type: (str, _MockImporter) -> None
        self.__name__ = self.__package__ = name
        self.__loader__ = loader
        self.__all__ = []  # type: List[str]
        self.__path__ = []  # type: List[str]

    def __getattr__(self, name):
        # type: (str) -> _MockObject
        o = _MockObject()
        o.__module__ = self.__name__
        return o


class _MockImporter(object):

    def __init__(self, names):
        # type: (List[str]) -> None
        self.base_packages = set()  # type: Set[str]
        for n in names:
            # Convert module names:
            #     ['a.b.c', 'd.e']
            # to a set of base packages:
            #     set(['a', 'd'])
            self.base_packages.add(n.split('.')[0])
        self.mocked_modules = []  # type: List[str]
        # enable hook by adding itself to meta_path
        sys.meta_path = sys.meta_path + [self]

    def disable(self):
        # remove `self` from `sys.meta_path` to disable import hook
        sys.meta_path = [i for i in sys.meta_path if i is not self]
        # remove mocked modules from sys.modules to avoid side effects after
        # running auto-documenter
        for m in self.mocked_modules:
            if m in sys.modules:
                del sys.modules[m]

    def find_module(self, name, path=None):
        # type: (str, str) -> Any
        base_package = name.split('.')[0]
        if base_package in self.base_packages:
            return self
        return None

    def load_module(self, name):
        # type: (str) -> ModuleType
        if name in sys.modules:
            # module has already been imported, return it
            return sys.modules[name]
        else:
            logger.debug('[autodoc] adding a mock module %s!', name)
            module = _MockModule(name, self)
            sys.modules[name] = module
            self.mocked_modules.append(name)
            return module
