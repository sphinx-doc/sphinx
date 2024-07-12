#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

script_dir = Path(__file__).parent
package_dir = script_dir.parent

RELEASE_TYPE = {'a': 'alpha', 'b': 'beta'}

VersionInfo: TypeAlias = tuple[int, int, int, str, int]


def stringify_version(version_info: VersionInfo, in_develop: bool = True) -> str:
    version = '.'.join(str(v) for v in version_info[:3])
    if not in_develop and version_info[3] != 'final':
        version += version_info[3][0] + str(version_info[4])

    return version


def bump_version(path: Path, version_info: VersionInfo, in_develop: bool = True) -> None:
    version = stringify_version(version_info, in_develop)

    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()

    for i, line in enumerate(lines):
        if line.startswith('__version__ = '):
            lines[i] = f"__version__ = '{version}'"
            continue
        if line.startswith('version_info = '):
            lines[i] = f'version_info = {version_info}'
            continue
        if line.startswith('_in_development = '):
            lines[i] = f'_in_development = {in_develop}'
            continue

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def parse_version(version: str) -> VersionInfo:
    matched = re.search(r'^(\d+)\.(\d+)$', version)
    if matched:
        major, minor = matched.groups()
        return (int(major), int(minor), 0, 'final', 0)

    matched = re.search(r'^(\d+)\.(\d+)\.(\d+)$', version)
    if matched:
        major, minor, rev = matched.groups()
        return (int(major), int(minor), int(rev), 'final', 0)

    matched = re.search(r'^(\d+)\.(\d+)\s*(a|b|alpha|beta)(\d+)$', version)
    if matched:
        major, minor, typ, relver = matched.groups()
        release = RELEASE_TYPE.get(typ, typ)
        return (int(major), int(minor), 0, release, int(relver))

    matched = re.search(r'^(\d+)\.(\d+)\.(\d+)\s*(a|b|alpha|beta)(\d+)$', version)
    if matched:
        major, minor, rev, typ, relver = matched.groups()
        release = RELEASE_TYPE.get(typ, typ)
        return (int(major), int(minor), int(rev), release, int(relver))

    raise RuntimeError('Unknown version: %s' % version)


class Skip(Exception):
    pass


@contextmanager
def processing(message: str) -> Iterator[None]:
    try:
        print(message + ' ... ', end='')
        yield
    except Skip as exc:
        print('skip: %s' % exc)
    except Exception:
        print('error')
        raise
    else:
        print('done')


class Changes:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.fetch_version()

    def fetch_version(self) -> None:
        with open(self.path, encoding='utf-8') as f:
            version = f.readline().strip()
            matched = re.search(r'^Release (.*) \((.*)\)$', version)
            if matched is None:
                raise RuntimeError('Unknown CHANGES format: %s' % version)

            self.version, self.release_date = matched.groups()
            self.version_info = parse_version(self.version)
            if self.release_date == 'in development':
                self.in_development = True
            else:
                self.in_development = False

    def finalize_release_date(self) -> None:
        release_date = time.strftime('%b %d, %Y')
        heading = f'Release {self.version} (released {release_date})'

        with open(self.path, 'r+', encoding='utf-8') as f:
            f.readline()  # skip first two lines
            f.readline()
            body = f.read()

            f.seek(0)
            f.truncate(0)
            f.write(heading + '\n')
            f.write('=' * len(heading) + '\n')
            f.write(self.filter_empty_sections(body))

    def add_release(self, version_info: VersionInfo) -> None:
        if version_info[-2:] in (('beta', 0), ('final', 0)):
            version = stringify_version(version_info)
        else:
            reltype = version_info[3]
            version = (
                f'{stringify_version(version_info)} '
                f'{RELEASE_TYPE.get(reltype, reltype)}{version_info[4] or ""}'
            )
        heading = 'Release %s (in development)' % version

        with open(script_dir / 'CHANGES_template.rst', encoding='utf-8') as f:
            f.readline()  # skip first two lines
            f.readline()
            tmpl = f.read()

        with open(self.path, 'r+', encoding='utf-8') as f:
            body = f.read()

            f.seek(0)
            f.truncate(0)
            f.write(heading + '\n')
            f.write('=' * len(heading) + '\n')
            f.write(tmpl)
            f.write('\n')
            f.write(body)

    def filter_empty_sections(self, body: str) -> str:
        return re.sub('^\n.+\n-{3,}\n+(?=\n.+\n[-=]{3,}\n)', '', body, flags=re.MULTILINE)


def parse_options(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('version', help='A version number (cf. 1.6b0)')
    parser.add_argument('--in-develop', action='store_true')
    options = parser.parse_args(argv)
    options.version = parse_version(options.version)
    return options


def main() -> None:
    options = parse_options(sys.argv[1:])

    with processing('Rewriting sphinx/__init__.py'):
        bump_version(
            package_dir / 'sphinx' / '__init__.py', options.version, options.in_develop
        )

    with processing('Rewriting CHANGES'):
        changes = Changes(package_dir / 'CHANGES.rst')
        if changes.version_info == options.version:
            if changes.in_development:
                changes.finalize_release_date()
            else:
                reason = 'version not changed'
                raise Skip(reason)
        else:
            if changes.in_development:
                print('WARNING: last version is not released yet: %s' % changes.version)
            changes.add_release(options.version)


if __name__ == '__main__':
    main()
