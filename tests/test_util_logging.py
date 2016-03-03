# -*- coding: utf-8 -*-
"""
    test_util_logging
    ~~~~~~~~~~~~~~~~~

    Test logging util.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

from sphinx.util.logging import is_suppressed_warning


def test_is_suppressed_warning():
    suppress_warnings = ["ref", "files.*", "rest.duplicated_labels"]

    assert is_suppressed_warning(None, None, suppress_warnings) is False
    assert is_suppressed_warning("ref", None, suppress_warnings) is True
    assert is_suppressed_warning("ref", "numref", suppress_warnings) is True
    assert is_suppressed_warning("ref", "option", suppress_warnings) is True
    assert is_suppressed_warning("files", "image", suppress_warnings) is True
    assert is_suppressed_warning("files", "stylesheet", suppress_warnings) is True
    assert is_suppressed_warning("rest", "syntax", suppress_warnings) is False
    assert is_suppressed_warning("rest", "duplicated_labels", suppress_warnings) is True
