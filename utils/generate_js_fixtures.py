#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

SPHINX_ROOT = Path(__file__).resolve().parent.parent
TEST_JS_FIXTURES = SPHINX_ROOT / 'tests' / 'js' / 'fixtures'
TEST_JS_ROOTS = [
    directory
    for directory in (SPHINX_ROOT / 'tests' / 'js' / 'roots').iterdir()
    if (directory / 'conf.py').exists()
]


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


for directory in TEST_JS_ROOTS:
    searchindex = directory / '_build' / 'searchindex.js'
    destination = TEST_JS_FIXTURES / directory.name / 'searchindex.js'

    print(f'Building {directory} ... ', end='')
    build(directory)
    print('done')

    print(f'Copying {searchindex} to {destination} ... ', end='')
    destination.parent.mkdir(exist_ok=True, parents=True)
    shutil.copy2(searchindex, destination)
    print('done')
