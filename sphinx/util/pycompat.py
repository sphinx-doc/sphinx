# -*- coding: utf-8 -*-
"""
    sphinx.util.pycompat
    ~~~~~~~~~~~~~~~~~~~~

    Stuff for Python version compatibility.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from html import escape as htmlescape  # NOQA
from io import TextIOWrapper  # NOQA
from textwrap import indent  # NOQA

from six import text_type

from sphinx.locale import __
from sphinx.util import logging

if False:
    # For type annotation
    from typing import Any, Callable, Generator  # NOQA
    from sphinx.util.typing import unicode  # NOQA


logger = logging.getLogger(__name__)


NoneType = type(None)

# ------------------------------------------------------------------------------
# Python 2/3 compatibility

# prefix for Unicode strings
u = ''  # RemovedInSphinx40Warning


# sys_encoding: some kind of default system encoding; should be used with
# a lenient error handler
sys_encoding = sys.getdefaultencoding()


# terminal_safe(): safely encode a string for printing to the terminal
def terminal_safe(s):
    # type: (unicode) -> unicode
    return s.encode('ascii', 'backslashreplace').decode('ascii')


# convert_with_2to3():
# support for running 2to3 over config files
def convert_with_2to3(filepath):
    # type: (unicode) -> unicode
    from lib2to3.refactor import RefactoringTool, get_fixers_from_package
    from lib2to3.pgen2.parse import ParseError
    fixers = get_fixers_from_package('lib2to3.fixes')
    refactoring_tool = RefactoringTool(fixers)
    source = refactoring_tool._read_python_source(filepath)[0]
    try:
        tree = refactoring_tool.refactor_string(source, 'conf.py')
    except ParseError as err:
        # do not propagate lib2to3 exceptions
        lineno, offset = err.context[1]
        # try to match ParseError details with SyntaxError details
        raise SyntaxError(err.msg, (filepath, lineno, offset, err.value))
    return text_type(tree)


class UnicodeMixin:
    """Mixin class to handle defining the proper __str__/__unicode__
    methods in Python 2 or 3."""

    def __str__(self):
        return self.__unicode__()


def execfile_(filepath, _globals, open=open):
    # type: (unicode, Any, Callable) -> None
    from sphinx.util.osutil import fs_encoding
    with open(filepath, 'rb') as f:
        source = f.read()

    # compile to a code object, handle syntax errors
    filepath_enc = filepath.encode(fs_encoding)
    try:
        code = compile(source, filepath_enc, 'exec')
    except SyntaxError:
        # maybe the file uses 2.x syntax; try to refactor to
        # 3.x syntax using 2to3
        source = convert_with_2to3(filepath)
        code = compile(source, filepath_enc, 'exec')
        # TODO: When support for evaluating Python 2 syntax is removed,
        # deprecate convert_with_2to3().
        logger.warning(__('Support for evaluating Python 2 syntax is deprecated '
                          'and will be removed in Sphinx 4.0. '
                          'Convert %s to Python 3 syntax.'),
                       filepath)
    exec(code, _globals)
