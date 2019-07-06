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
from typing import Any, Dict, IO, List, Tuple
from zipfile import ZipFile

from sphinx.errors import PycodeError
from sphinx.pycode.parser import Parser
from sphinx.util import get_module_source, detect_encoding


class ModuleAnalyzer:
    # cache for analyzer objects -- caches both by module and file name
    cache = {}  # type: Dict[Tuple[str, str], Any]

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
            type, source = get_module_source(modname)
            if type == 'string':
                obj = cls.for_string(source, modname)
            else:
                obj = cls.for_file(source, modname)
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
