from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from sphinx.util._pathlib import _StrPath

if TYPE_CHECKING:
    import os
    from collections.abc import Set


class FilenameUniqDict(dict[str, tuple[set[str], str]]):  # NoQA: FURB189
    """A dictionary that automatically generates unique names for its keys,
    interpreted as filenames, and keeps track of a set of docnames they
    appear in.  Used for images and downloadable files in the environment.
    """

    def __init__(self) -> None:
        super().__init__()
        self._existing: set[str] = set()

    def add_file(self, docname: str, newfile: str | os.PathLike[str]) -> str:
        newfile = str(newfile)
        if newfile in self:
            docnames, unique_name = self[newfile]
            docnames.add(docname)
            return unique_name

        new_file = Path(newfile)
        unique_name = new_file.name
        base = new_file.stem
        ext = new_file.suffix
        i = 0
        while unique_name in self._existing:
            i += 1
            unique_name = f'{base}{i}{ext}'
        self[newfile] = ({docname}, unique_name)
        self._existing.add(unique_name)
        return unique_name

    def purge_doc(self, docname: str) -> None:
        for filename, (docs, unique) in list(self.items()):
            docs.discard(docname)
            if not docs:
                del self[filename]
                self._existing.discard(unique)

    def merge_other(
        self, docnames: Set[str], other: dict[str, tuple[set[str], str]]
    ) -> None:
        for filename, (docs, _unique) in other.items():
            for doc in docs & set(docnames):
                self.add_file(doc, filename)

    def __getstate__(self) -> set[str]:
        return self._existing

    def __setstate__(self, state: set[str]) -> None:
        self._existing = state


class DownloadFiles(dict[Path, tuple[set[str], _StrPath]]):  # NoQA: FURB189
    """A special dictionary for download files.

    .. important:: This class would be refactored in nearly future.
                   Hence don't hack this directly.
    """

    def add_file(self, docname: str, filename: str | os.PathLike[str]) -> _StrPath:
        filename = Path(filename)
        if filename not in self:
            digest = hashlib.md5(
                filename.as_posix().encode(), usedforsecurity=False
            ).hexdigest()
            dest_path = _StrPath(digest, filename.name)
            self[filename] = ({docname}, dest_path)
            return dest_path

        docnames, dest_path = self[filename]
        docnames.add(docname)
        return dest_path

    def purge_doc(self, docname: str) -> None:
        for filename, (docs, _dest) in list(self.items()):
            docs.discard(docname)
            if not docs:
                del self[filename]

    def merge_other(
        self, docnames: Set[str], other: dict[Path, tuple[set[str], _StrPath]]
    ) -> None:
        for filename, (docs, _dest) in other.items():
            for docname in docs & set(docnames):
                self.add_file(docname, filename)
