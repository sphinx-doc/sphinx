# -*- coding: utf-8 -*-
"""
    sphinx.util.docstrings
    ~~~~~~~~~~~~~~~~~~~~~~

    Utilities for docstring processing.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys


def prepare_docstring(s):
    """
    Convert a docstring into lines of parseable reST.  Return it as a list of
    lines usable for inserting into a docutils ViewList (used as argument
    of nested_parse().)  An empty line is added to act as a separator between
    this docstring and following content.
    """
    lines = s.expandtabs().splitlines()
    # Find minimum indentation of any non-blank lines after first line.
    margin = sys.maxint
    for line in lines[1:]:
        content = len(line.lstrip())
        if content:
            indent = len(line) - content
            margin = min(margin, indent)
    # Remove indentation.
    if lines:
        lines[0] = lines[0].lstrip()
    if margin < sys.maxint:
        for i in range(1, len(lines)): lines[i] = lines[i][margin:]
    # Remove any leading blank lines.
    while lines and not lines[0]:
        lines.pop(0)
    # make sure there is an empty line at the end
    if lines and lines[-1]:
        lines.append('')
    return lines


def prepare_commentdoc(s):
    """
    Extract documentation comment lines (starting with #:) and return them as a
    list of lines.  Returns an empty list if there is no documentation.
    """
    result = []
    lines = [line.strip() for line in s.expandtabs().splitlines()]
    for line in lines:
        if line.startswith('#:'):
            line = line[2:]
            # the first space after the comment is ignored
            if line and line[0] == ' ':
                line = line[1:]
            result.append(line)
    if result and result[-1]:
        result.append('')
    return result
