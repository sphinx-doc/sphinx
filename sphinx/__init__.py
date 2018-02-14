# -*- coding: utf-8 -*-
"""
    Sphinx
    ~~~~~~

    The Sphinx documentation toolchain.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# Keep this file executable as-is in Python 3!
# (Otherwise getting the version out of it from setup.py is impossible.)

from __future__ import absolute_import

import os
import warnings
from os import path

from .cmd import build
from .deprecation import RemovedInNextVersionWarning
from .deprecation import RemovedInSphinx20Warning

if False:
    # For type annotation
    from typing import Any  # NOQA


# by default, all DeprecationWarning under sphinx package will be emit.
# Users can avoid this by using environment variable: PYTHONWARNINGS=
if 'PYTHONWARNINGS' not in os.environ:
    warnings.filterwarnings('default',
                            category=RemovedInNextVersionWarning, module='sphinx')
# docutils.io using mode='rU' for open
warnings.filterwarnings('ignore', "'U' mode is deprecated",
                        DeprecationWarning, module='docutils.io')

__version__ = '1.8.0+'
__released__ = '1.8.0'  # used when Sphinx builds its own docs

#: Version info for better programmatic use.
#:
#: A tuple of five elements; for Sphinx version 1.2.1 beta 3 this would be
#: ``(1, 2, 1, 'beta', 3)``. The fourth element can be one of: ``alpha``,
#: ``beta``, ``rc``, ``final``. ``final`` always has 0 as the last element.
#:
#: .. versionadded:: 1.2
#:    Before version 1.2, check the string ``sphinx.__version__``.
version_info = (1, 8, 0, 'beta', 0)

package_dir = path.abspath(path.dirname(__file__))

__display_version__ = __version__  # used for command line version
if __version__.endswith('+'):
    # try to find out the commit hash if checked out from git, and append
    # it to __version__ (since we use this value from setup.py, it gets
    # automatically propagated to an installed copy as well)
    __display_version__ = __version__
    __version__ = __version__[:-1]  # remove '+' for PEP-440 version spec.
    try:
        import subprocess
        p = subprocess.Popen(['git', 'show', '-s', '--pretty=format:%h',
                              path.join(package_dir, '..')],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            __display_version__ += '/' + out.decode().strip()
    except Exception:
        pass


def main(*args, **kwargs):
    # type: (Any, Any) -> int
    warnings.warn(
        '`sphinx.main()` has moved to `sphinx.cmd.build.main()`.',
        RemovedInSphinx20Warning,
        stacklevel=2,
    )
    return build.main(*args, **kwargs)


if __name__ == '__main__':
    warnings.warn(
        '`sphinx` has moved to `sphinx.build`.',
        RemovedInSphinx20Warning,
        stacklevel=2,
    )
    build.main()
