"""Tests util functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import sphinx.util
from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.deprecation import RemovedInSphinx10Warning
from sphinx.util._files import DownloadFiles, FilenameUniqDict
from sphinx.util._importer import import_object
from sphinx.util._lines import parse_line_num_spec
from sphinx.util._uri import encode_uri, is_url
from sphinx.util.matching import patfilter
from sphinx.util.nodes import (
    caption_ref_re,
    explicit_title_re,
    nested_parse_with_titles,
    split_explicit_title,
)
from sphinx.util.osutil import (
    SEP,
    copyfile,
    ensuredir,
    make_filename,
    os_path,
    relative_uri,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_ensuredir(tmp_path: Path) -> None:
    # Does not raise an exception for an existing directory.
    ensuredir(tmp_path)

    path = tmp_path / 'a' / 'b' / 'c'
    ensuredir(path)
    assert path.is_dir()


def test_exported_attributes() -> None:
    # RemovedInSphinx10Warning
    with pytest.warns(RemovedInSphinx10Warning, match=r'deprecated.'):
        assert sphinx.util.FilenameUniqDict is FilenameUniqDict
    with pytest.warns(RemovedInSphinx10Warning, match=r'deprecated.'):
        assert sphinx.util.DownloadFiles is DownloadFiles

    # Re-exported for backwards compatibility,
    # but not currently deprecated
    assert sphinx.util.encode_uri is encode_uri
    assert sphinx.util.import_object is import_object
    assert sphinx.util.isurl is is_url
    assert sphinx.util.parselinenos is parse_line_num_spec
    assert sphinx.util.patfilter is patfilter
    assert sphinx.util.strip_escape_sequences is strip_escape_sequences
    assert sphinx.util.caption_ref_re is caption_ref_re
    assert sphinx.util.explicit_title_re is explicit_title_re
    assert sphinx.util.nested_parse_with_titles is nested_parse_with_titles
    assert sphinx.util.split_explicit_title is split_explicit_title
    assert sphinx.util.SEP is SEP
    assert sphinx.util.copyfile is copyfile
    assert sphinx.util.ensuredir is ensuredir
    assert sphinx.util.make_filename is make_filename
    assert sphinx.util.os_path is os_path
    assert sphinx.util.relative_uri is relative_uri
