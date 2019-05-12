"""
    utils.doclinter
    ~~~~~~~~~~~~~~~

    A linter for Sphinx docs

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
from typing import List


MAX_LINE_LENGTH = 100


def lint(path: str) -> int:
    with open(path) as f:
        document = f.readlines()

    errors = 0
    for i, line in enumerate(document):
        if line.endswith(' '):
            print('%s:%d: the line ends with whitespace.' %
                  (path, i + 1))
            errors += 1

        if len(line) > MAX_LINE_LENGTH:
            if re.match(r'^\s*\.\. ', line):
                # ignore directives and hyperlink targets
                pass
            else:
                print('%s:%d: the line is too long (%d > %d).' %
                      (path, i + 1, len(line), MAX_LINE_LENGTH))
                errors += 1

    return errors


def main(args: List[str]) -> int:
    errors = 0
    for directory in args:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.rst'):
                    path = os.path.join(root, filename)
                    errors += lint(path)

    if errors:
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
