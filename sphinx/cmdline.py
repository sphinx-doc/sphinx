"""
    sphinx.cmdline
    ~~~~~~~~~~~~~~

    sphinx-build command-line handling.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import argparse
import sys
import warnings
from typing import Any, IO, List, Union

from sphinx.application import Sphinx
from sphinx.cmd import build
from sphinx.deprecation import RemovedInSphinx30Warning


def handle_exception(app: Sphinx, args: Any, exception: Union[Exception, KeyboardInterrupt],
                     stderr: IO = sys.stderr) -> None:
    warnings.warn('sphinx.cmdline module is deprecated. Use sphinx.cmd.build instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    build.handle_exception(app, args, exception, stderr)


def jobs_argument(value: str) -> int:
    warnings.warn('sphinx.cmdline module is deprecated. Use sphinx.cmd.build instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    return build.jobs_argument(value)


def get_parser() -> argparse.ArgumentParser:
    warnings.warn('sphinx.cmdline module is deprecated. Use sphinx.cmd.build instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    return build.get_parser()


def main(argv: List[str] = sys.argv[1:]) -> int:
    warnings.warn('sphinx.cmdline module is deprecated. Use sphinx.cmd.build instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    return build.main(argv)
