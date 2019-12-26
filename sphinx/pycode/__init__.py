"""
    sphinx.pycode
    ~~~~~~~~~~~~~

    Utilities parsing and analyzing Python code.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
from io import StringIO
from os import path
from typing import Any, Dict, IO, List, Tuple, Optional
from zipfile import ZipFile
from importlib import import_module

from sphinx.errors import PycodeError
from sphinx.pycode.parser import Parser
from sphinx.util import get_module_source, detect_encoding


class ModuleAnalyzer:
    # cache for analyzer objects -- caches both by module and file name
    cache = {}  # type: Dict[Tuple[str, str], Any]

    @staticmethod
    def get_module_source(modname: str) -> Tuple[Optional[str], Optional[str]]:
        """Try to find the source code for a module.

        Returns ('filename', 'source'). One of it can be None if
        no filename or source found
        """
        try:
            mod = import_module(modname)
        except Exception as err:
            raise PycodeError('error importing %r' % modname, err)
        loader = getattr(mod, '__loader__', None)
        filename = getattr(mod, '__file__', None)
        if loader and getattr(loader, 'get_source', None):
            # prefer Native loader, as it respects #coding directive
            try:  
                source = loader.get_source(modname)
                if source:
                    # no exception and not None - it must be module source
                    return filename, source
            except ImportError as err:
                pass  # Try other "source-mining" methods
        if filename is None and loader and getattr(loader, 'get_filename', None):
            # have loader, but no filename
            try:
                filename = loader.get_filename(modname)
            except ImportError as err:
                raise PycodeError('error getting filename for %r' % modname, err)
        if filename is None:
            # all methods for getting filename failed, so raise...
            raise PycodeError('no source found for module %r' % modname)
        filename = path.normpath(path.abspath(filename))
        lfilename = filename.lower()
        if lfilename.endswith('.pyo') or lfilename.endswith('.pyc'):
            filename = filename[:-1]
            if not path.isfile(filename) and path.isfile(filename + 'w'):
                filename += 'w'
        elif not (lfilename.endswith('.py') or lfilename.endswith('.pyw')):
            raise PycodeError('source is not a .py file: %r' % filename)
        elif ('.egg' + os.path.sep) in filename:
            pat = '(?<=\\.egg)' + re.escape(os.path.sep)
            eggpath, _ = re.split(pat, filename, 1)
            if path.isfile(eggpath):
                return filename, None

        if not path.isfile(filename):
            raise PycodeError('source file is not present: %r' % filename)
        return filename, None
    
    @classmethod
    def for_string(cls, string: str, modname: str, srcname: str = '<string>'
                   ) -> "ModuleAnalyzer":
        return cls(StringIO(string), modname, srcname, decoded=True)

    @classmethod
    def for_file(cls, filename: str, modname: str) -> "ModuleAnalyzer":
        if ('file', filename) in cls.cache:
            return cls.cache['file', filename]
        try:
            with open(filename, 'rb') as f:
                obj = cls(f, modname, filename)
                cls.cache['file', filename] = obj
        except Exception as err:
            if '.egg' + path.sep in filename:
                obj = cls.cache['file', filename] = cls.for_egg(filename, modname)
            else:
                raise PycodeError('error opening %r' % filename, err)
        return obj

    @classmethod
    def for_egg(cls, filename: str, modname: str) -> "ModuleAnalyzer":
        SEP = re.escape(path.sep)
        eggpath, relpath = re.split('(?<=\\.egg)' + SEP, filename)
        try:
            with ZipFile(eggpath) as egg:
                code = egg.read(relpath).decode()
                return cls.for_string(code, modname, filename)
        except Exception as exc:
            raise PycodeError('error opening %r' % filename, exc)

    @classmethod
    def for_module(cls, modname: str) -> "ModuleAnalyzer":
        if ('module', modname) in cls.cache:
            entry = cls.cache['module', modname]
            if isinstance(entry, PycodeError):
                raise entry
            return entry

        try:
            filename, source = cls.get_module_source(modname)
            if source is not None:
                obj = cls.for_string(source, modname, filename if filename is not None else '<string>')
            elif filename is not None:
                obj = cls.for_file(filename, modname)
        except PycodeError as err:
            cls.cache['module', modname] = err
            raise
        cls.cache['module', modname] = obj
        return obj

    def __init__(self, source: IO, modname: str, srcname: str, decoded: bool = False) -> None:
        self.modname = modname  # name of the module
        self.srcname = srcname  # name of the source file

        # cache the source code as well
        pos = source.tell()
        if not decoded:
            self.encoding = detect_encoding(source.readline)
            source.seek(pos)
            self.code = source.read().decode(self.encoding)
        else:
            self.encoding = None
            self.code = source.read()

        # will be filled by parse()
        self.attr_docs = None   # type: Dict[Tuple[str, str], List[str]]
        self.tagorder = None    # type: Dict[str, int]
        self.tags = None        # type: Dict[str, Tuple[str, int, int]]

    def parse(self) -> None:
        """Parse the source code."""
        try:
            parser = Parser(self.code, self.encoding)
            parser.parse()

            self.attr_docs = {}
            for (scope, comment) in parser.comments.items():
                if comment:
                    self.attr_docs[scope] = comment.splitlines() + ['']
                else:
                    self.attr_docs[scope] = ['']

            self.tags = parser.definitions
            self.tagorder = parser.deforders
        except Exception as exc:
            raise PycodeError('parsing %r failed: %r' % (self.srcname, exc))

    def find_attr_docs(self) -> Dict[Tuple[str, str], List[str]]:
        """Find class and module-level attributes and their documentation."""
        if self.attr_docs is None:
            self.parse()

        return self.attr_docs

    def find_tags(self) -> Dict[str, Tuple[str, int, int]]:
        """Find class, function and method definitions and their location."""
        if self.tags is None:
            self.parse()

        return self.tags
