"""
    sphinx.util.pycompat
    ~~~~~~~~~~~~~~~~~~~~

    Stuff for Python version compatibility.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import html
import io
import sys
import textwrap
import warnings
from typing import Any, Callable

from sphinx.deprecation import RemovedInSphinx40Warning, deprecated_alias
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.console import terminal_safe
from sphinx.util.typing import NoneType


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Python 2/3 compatibility

# convert_with_2to3():
# support for running 2to3 over config files
def convert_with_2to3(filepath: str) -> str:
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
    return str(tree)


class UnicodeMixin:
    """Mixin class to handle defining the proper __str__/__unicode__
    methods in Python 2 or 3.

    .. deprecated:: 2.0
    """
    def __str__(self):
        warnings.warn('UnicodeMixin is deprecated',
                      RemovedInSphinx40Warning, stacklevel=2)
        return self.__unicode__()  # type: ignore


def execfile_(filepath: str, _globals: Any, open: Callable = open) -> None:
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


deprecated_alias('sphinx.util.pycompat',
                 {
                     'NoneType': NoneType,  # type: ignore
                     'TextIOWrapper': io.TextIOWrapper,
                     'htmlescape': html.escape,
                     'indent': textwrap.indent,
                     'terminal_safe': terminal_safe,
                     'sys_encoding': sys.getdefaultencoding(),
                     'u': '',
                 },
                 RemovedInSphinx40Warning)
