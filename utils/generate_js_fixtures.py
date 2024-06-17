#!/usr/bin/env python3

import subprocess
from pathlib import Path

SPHINX_ROOT = Path(__file__).resolve().parent.parent
TEST_JS_FIXTURES = SPHINX_ROOT / 'tests' / 'js' / 'fixtures'
TEST_JS_ROOTS = SPHINX_ROOT / 'tests' / 'js' / 'roots'


def build(srcdir: Path) -> None:
    cmd = (
        'sphinx-build',
        '--fresh-env',
        '--quiet',
        *('--builder', 'html'),
        f'{srcdir}',
        f'{srcdir}/_build',
    )
    subprocess.run(cmd, check=True, capture_output=True)


for directory in TEST_JS_ROOTS.iterdir():
    searchindex = directory / '_build' / 'searchindex.js'
    destination = TEST_JS_FIXTURES / directory.name / 'searchindex.js'

    print(f'Building {directory} ... ', end='')
    build(directory)
    print('done')

    print(f'Moving {searchindex} to {destination} ... ', end='')
    destination.parent.mkdir(exist_ok=True)
    searchindex.replace(destination)
    print('done')
