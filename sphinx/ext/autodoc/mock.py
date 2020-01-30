"""
    sphinx.ext.autodoc.mock
    ~~~~~~~~~~~~~~~~~~~~~~~

    mock for autodoc

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import contextlib
import os
import sys
import warnings
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from types import FunctionType, MethodType, ModuleType
from typing import Any, Generator, Iterator, List, Sequence, Tuple, Union

from sphinx.deprecation import RemovedInSphinx30Warning
from sphinx.util import logging

logger = logging.getLogger(__name__)


class _MockObject:
    """Used by autodoc_mock_imports."""

    __display_name__ = '_MockObject'

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        if len(args) == 3 and isinstance(args[1], tuple):
            superclass = args[1][-1].__class__
            if superclass is cls:
                # subclassing MockObject
                return _make_subclass(args[0], superclass.__display_name__,
                                      superclass=superclass, attributes=args[2])

        return super().__new__(cls)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__qualname__ = ''

    def __len__(self) -> int:
        return 0

    def __contains__(self, key: str) -> bool:
        return False

    def __iter__(self) -> Iterator:
        return iter([])

    def __mro_entries__(self, bases: Tuple) -> Tuple:
        return (self.__class__,)

    def __getitem__(self, key: str) -> "_MockObject":
        return _make_subclass(key, self.__display_name__, self.__class__)()

    def __getattr__(self, key: str) -> "_MockObject":
        return _make_subclass(key, self.__display_name__, self.__class__)()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if args and type(args[0]) in [type, FunctionType, MethodType]:
            # Appears to be a decorator, pass through unchanged
            return args[0]
        return self

    def __repr__(self) -> str:
        return self.__display_name__


def _make_subclass(name: str, module: str, superclass: Any = _MockObject,
                   attributes: Any = None) -> Any:
    attrs = {'__module__': module, '__display_name__': module + '.' + name}
    attrs.update(attributes or {})

    return type(name, (superclass,), attrs)


class _MockModule(ModuleType):
    """Used by autodoc_mock_imports."""
    __file__ = os.devnull

    def __init__(self, name: str, loader: "_MockImporter" = None) -> None:
        super().__init__(name)
        self.__all__ = []  # type: List[str]
        self.__path__ = []  # type: List[str]

        if loader is not None:
            warnings.warn('The loader argument for _MockModule is deprecated.',
                          RemovedInSphinx30Warning)

    def __getattr__(self, name: str) -> _MockObject:
        return _make_subclass(name, self.__name__)()

    def __repr__(self) -> str:
        return self.__name__


class _MockImporter(MetaPathFinder):
    def __init__(self, names: List[str]) -> None:
        self.names = names
        self.mocked_modules = []  # type: List[str]
        # enable hook by adding itself to meta_path
        sys.meta_path.insert(0, self)

        warnings.warn('_MockImporter is now deprecated.',
                      RemovedInSphinx30Warning)

    def disable(self) -> None:
        # remove `self` from `sys.meta_path` to disable import hook
        sys.meta_path = [i for i in sys.meta_path if i is not self]
        # remove mocked modules from sys.modules to avoid side effects after
        # running auto-documenter
        for m in self.mocked_modules:
            if m in sys.modules:
                del sys.modules[m]

    def find_module(self, name: str, path: Sequence[Union[bytes, str]] = None) -> Any:
        # check if name is (or is a descendant of) one of our base_packages
        for n in self.names:
            if n == name or name.startswith(n + '.'):
                return self
        return None

    def load_module(self, name: str) -> ModuleType:
        if name in sys.modules:
            # module has already been imported, return it
            return sys.modules[name]
        else:
            logger.debug('[autodoc] adding a mock module %s!', name)
            module = _MockModule(name, self)
            sys.modules[name] = module
            self.mocked_modules.append(name)
            return module


class MockLoader(Loader):
    """A loader for mocking."""
    def __init__(self, finder: "MockFinder") -> None:
        super().__init__()
        self.finder = finder

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        logger.debug('[autodoc] adding a mock module as %s!', spec.name)
        self.finder.mocked_modules.append(spec.name)
        return _MockModule(spec.name)

    def exec_module(self, module: ModuleType) -> None:
        pass  # nothing to do


class MockFinder(MetaPathFinder):
    """A finder for mocking."""

    def __init__(self, modnames: List[str]) -> None:
        super().__init__()
        self.modnames = modnames
        self.loader = MockLoader(self)
        self.mocked_modules = []  # type: List[str]

    def find_spec(self, fullname: str, path: Sequence[Union[bytes, str]],
                  target: ModuleType = None) -> ModuleSpec:
        for modname in self.modnames:
            # check if fullname is (or is a descendant of) one of our targets
            if modname == fullname or fullname.startswith(modname + '.'):
                return ModuleSpec(fullname, self.loader)

        return None

    def invalidate_caches(self) -> None:
        """Invalidate mocked modules on sys.modules."""
        for modname in self.mocked_modules:
            sys.modules.pop(modname, None)


@contextlib.contextmanager
def mock(modnames: List[str]) -> Generator[None, None, None]:
    """Insert mock modules during context::

        with mock(['target.module.name']):
            # mock modules are enabled here
            ...
    """
    try:
        finder = MockFinder(modnames)
        sys.meta_path.insert(0, finder)
        yield
    finally:
        sys.meta_path.remove(finder)
        finder.invalidate_caches()
