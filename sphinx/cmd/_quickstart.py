"""The module implementing the subcommand ``sphinx quickstart``.

This delegates everything to the module :mod:`sphinx.cmd.quickstart`, which
is the implementation for the historic standalone ``sphinx-quickstart`` command.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import quickstart

if TYPE_CHECKING:
    import argparse

parser_description = quickstart.COMMAND_DESCRIPTION.lstrip()


def set_up_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    return quickstart.set_up_parser(parser)


def run(args: argparse.Namespace) -> int:
    return quickstart.run(args)
