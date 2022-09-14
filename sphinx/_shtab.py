FILE = None
DIRECTORY = DIR = None


def add_argument_to(parser, *args, **kwargs):
    from argparse import Action
    Action.complete = None  # type: ignore
    return parser
