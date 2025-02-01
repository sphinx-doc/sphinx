#!/usr/bin/env python3

"""Usage: bump_docker.py [VERSION]"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

VERSION_PATTERN = r'\d+\.\d+\.\d+'

if not sys.argv[1:] or re.match(VERSION_PATTERN, sys.argv[1]) is None:
    print(__doc__)
    raise SystemExit(1)

VERSION = sys.argv[1]

PROJECTS_ROOT = Path(__file__).resolve().parents[2]
DOCKER_ROOT = PROJECTS_ROOT / 'sphinx-docker-images'
DOCKERFILE_BASE = DOCKER_ROOT / 'base' / 'Dockerfile'
DOCKERFILE_LATEXPDF = DOCKER_ROOT / 'latexpdf' / 'Dockerfile'

OPENCONTAINERS_VERSION_PREFIX = 'LABEL org.opencontainers.image.version'
SPHINX_VERSION_PREFIX = 'Sphinx=='

for file in DOCKERFILE_BASE, DOCKERFILE_LATEXPDF:
    content = file.read_text(encoding='utf-8')
    content = re.sub(
        rf'{re.escape(OPENCONTAINERS_VERSION_PREFIX)}="{VERSION_PATTERN}"',
        rf'{OPENCONTAINERS_VERSION_PREFIX}="{VERSION}"',
        content,
    )
    content = re.sub(
        rf'{re.escape(SPHINX_VERSION_PREFIX)}{VERSION_PATTERN}',
        rf'{SPHINX_VERSION_PREFIX}{VERSION}',
        content,
    )
    file.write_text(content, encoding='utf-8')


def git(*args: str) -> None:
    subprocess.run(
        ('git', *args),
        cwd=DOCKER_ROOT,
        check=True,
        text=True,
        encoding='utf-8',
    )


git('checkout', 'master')
git('commit', '-am', f'Bump to {VERSION}')
git('tag', VERSION, '-m', f'Sphinx {VERSION}')
git('push', 'upstream', 'master')
git('push', 'upstream', VERSION)
