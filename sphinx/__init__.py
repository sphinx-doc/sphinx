# -*- coding: utf-8 -*-
"""
    Sphinx
    ~~~~~~

    The Sphinx documentation toolchain.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# Keep this file executable as-is in Python 3!
# (Otherwise getting the version out of it from setup.py is impossible.)

from __future__ import absolute_import

import os
import sys
import warnings
from os import path

from .deprecation import RemovedInNextVersionWarning

if False:
    # For type annotation
    from typing import List  # NOQA

# by default, all DeprecationWarning under sphinx package will be emit.
# Users can avoid this by using environment variable: PYTHONWARNINGS=
if 'PYTHONWARNINGS' not in os.environ:
    warnings.filterwarnings('default',
                            category=RemovedInNextVersionWarning, module='sphinx')
# docutils.io using mode='rU' for open
warnings.filterwarnings('ignore', "'U' mode is deprecated",
                        DeprecationWarning, module='docutils.io')

__version__ = '1.7+'
__released__ = '1.7'  # used when Sphinx builds its own docs

# version info for better programmatic use
# possible values for 3rd element: 'alpha', 'beta', 'rc', 'final'
# 'final' has 0 as the last element
version_info = (1, 7, 0, 'beta', 0)

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


def main(argv=sys.argv[1:]):
    # type: (List[str]) -> int
    if sys.argv[1:2] == ['-M']:
        return make_main(argv)
    else:
        return build_main(argv)


def build_main(argv=sys.argv[1:]):
    # type: (List[str]) -> int
    """Sphinx build "main" command-line entry."""
    from sphinx import cmdline
    return cmdline.main(argv)  # type: ignore


def make_main(argv=sys.argv[1:]):
    # type: (List[str]) -> int
    """Sphinx build "make mode" entry."""
    from sphinx import make_mode
    return make_mode.run_make_mode(argv[1:])  # type: ignore


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
