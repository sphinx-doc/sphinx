"""What follows is awful and will be gone in Sphinx 8"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path, PosixPath, WindowsPath

from sphinx.deprecation import RemovedInSphinx80Warning

_STR_METHODS = frozenset(str.__dict__)
_PATH_NAME = Path().__class__.__name__


if sys.platform == 'win32':
    class _StrPath(WindowsPath):
        def replace(self, old, new, count=-1, /):
            # replace exists in both Path and str;
            # in Path it makes filesystem changes, so we use the safer str version
            warnings.warn('Sphinx 8 will drop support for representing paths as strings. '
                          'Use "pathlib.Path" or "os.fspath" instead.',
                          RemovedInSphinx80Warning, stacklevel=2)
            return str(self).replace(old, new, count)

        def __getattr__(self, item):
            if item in _STR_METHODS:
                warnings.warn('Sphinx 8 will drop support for representing paths as strings. '
                              'Use "pathlib.Path" or "os.fspath" instead.',
                              RemovedInSphinx80Warning, stacklevel=2)
                return getattr(str(self), item)
            msg = f'{_PATH_NAME!r} has no attribute {item!r}'
            raise AttributeError(msg)
else:
    class _StrPath(PosixPath):
        def replace(self, old, new, count=-1, /):
            warnings.warn('Sphinx 8 will drop support for representing paths as strings. '
                          'Use "pathlib.Path" or "os.fspath" instead.',
                          RemovedInSphinx80Warning, stacklevel=2)
            return str(self).replace(old, new, count)

        def __getattr__(self, item):
            if item in _STR_METHODS:
                warnings.warn('Sphinx 8 will drop support for representing paths as strings. '
                              'Use "pathlib.Path" or "os.fspath" instead.',
                              RemovedInSphinx80Warning, stacklevel=2)
                return getattr(str(self), item)
            msg = f'{_PATH_NAME!r} has no attribute {item!r}'
            raise AttributeError(msg)
