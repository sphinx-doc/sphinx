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

MAX_LINE_LENGTH = 85
LONG_INTERPRETED_TEXT = re.compile(r'^\s*\W*(:(\w+:)+)?`.*`\W*$')
CODE_BLOCK_DIRECTIVE = re.compile(r'^(\s*)\.\. code-block::')
LEADING_SPACES = re.compile(r'^(\s*)')


def lint(path: str) -> int:
    with open(path) as f:
        document = f.readlines()

    errors = 0
    in_code_block = False
    code_block_depth = 0
    for i, line in enumerate(document):
        if line.endswith(' '):
            print('%s:%d: the line ends with whitespace.' %
                  (path, i + 1))
            errors += 1

        matched = CODE_BLOCK_DIRECTIVE.match(line)
        if matched:
            in_code_block = True
            code_block_depth = len(matched.group(1))
        elif in_code_block:
            if line.strip() == '':
                pass
            else:
                spaces = LEADING_SPACES.match(line).group(1)
                if len(spaces) <= code_block_depth:
                    in_code_block = False
        elif LONG_INTERPRETED_TEXT.match(line):
            pass
        elif len(line) > MAX_LINE_LENGTH:
            if re.match(r'^\s*\.\. ', line):
                # ignore directives and hyperlink targets
                pass
            elif re.match(r'^\s*__ ', line):
                # ignore anonymous hyperlink targets
                pass
            elif re.match(r'^\s*``[^`]+``$', line):
                # ignore a very long literal string
                pass
            else:
                print('%s:%d: the line is too long (%d > %d).' %
                      (path, i + 1, len(line), MAX_LINE_LENGTH))
                errors += 1

    return errors


def main(args: List[str]) -> int:
    errors = 0
    for path in args:
        if os.path.isfile(path):
            errors += lint(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
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
