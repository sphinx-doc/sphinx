"""
    sphinx.cmd.base
    ~~~~~~~~~~~~~~~

    Base command class to be used elsewhere.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import abc
import argparse
import inspect
import sys
from typing import Dict, List, Type

import pkg_resources

from sphinx import __display_version__
from sphinx.util.console import color_terminal, nocolor


class SphinxApplication:

    namespace = 'sphinx.commands'
    epilog = 'For more information, visit <http://sphinx-doc.org/>.'

    def __init__(self) -> None:
        self.commands = {}  # type: Dict[str, Type[SphinxCommand]]
        self._load_commands()

    def _load_commands(self) -> None:
        for entry_point in pkg_resources.iter_entry_points(self.namespace):
            self.commands[entry_point.name] = entry_point.load()

    def get_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self.epilog)

        parser.add_argument('--version', action='version', dest='show_version',
                            version='%%(prog)s %s' % __display_version__)

        subparsers = parser.add_subparsers(title='subcommands')

        for name, command in self.commands.items():
            obj = command()

            description = None
            summary = None
            if command.__doc__:
                description = inspect.cleandoc(command.__doc__)
                summary = description.partition('\n\n')[0]

            command_parser = subparsers.add_parser(
                name=name,
                help=summary,
                description=description,
                epilog=self.epilog,
                formatter_class=argparse.RawDescriptionHelpFormatter
            )
            obj.add_parser(command_parser)
            command_parser.set_defaults(run=obj.run)

        return parser

    def run(self, argv: List[str]) -> int:
        if not color_terminal():
            nocolor()

        parser = self.get_parser()

        try:
            args = parser.parse_args(argv)
        except SystemExit as err:
            return err.code

        return args.run(args)


class SphinxCommand(abc.ABC):

    @abc.abstractmethod
    def add_parser(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """Generate the subparser for the command."""
        pass

    @abc.abstractmethod
    def run(self, args: argparse.Namespace) -> int:
        """Main entry point for the command.

        Run the command including any subcommands.
        """
        pass


def main(argv=None):
    argv = argv or sys.argv[1:]
    return SphinxApplication().run(argv)


if __name__ == '__main__':
    main()
