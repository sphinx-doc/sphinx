#!/usr/bin/env python3

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from typing import Literal


script_dir = Path(__file__).resolve().parent
package_dir = script_dir.parent


@dataclasses.dataclass(frozen=True, slots=True)
class VersionInfo:
    major: int
    minor: int
    micro: int
    level: Literal['a', 'b', 'rc', 'final']
    serial: int

    @property
    def releaselevel(self) -> Literal['alpha', 'beta', 'candidate', 'final']:
        if self.level == 'final':
            return 'final'
        if self.level == 'a':
            return 'alpha'
        if self.level == 'b':
            return 'beta'
        if self.level == 'rc':
            return 'candidate'
        msg = f'Unknown release level: {self.level}'
        raise RuntimeError(msg)

    @property
    def is_final(self) -> bool:
        return self.level == 'final'

    @property
    def version(self) -> str:
        return f'{self.major}.{self.minor}.{self.micro}'

    @property
    def release(self) -> str:
        return f'{self.major}.{self.minor}.{self.micro}{self.level}{self.serial}'

    @property
    def version_tuple(self) -> tuple[int, int, int]:
        return self.major, self.minor, self.micro

    @property
    def release_tuple(self) -> tuple[int, int, int, str, int]:
        return self.major, self.minor, self.micro, self.releaselevel, self.serial


def parse_version(version: str) -> VersionInfo:
    # Final version:
    # - "X.Y.Z" -> (X, Y, Z, 'final', 0)
    # - "X.Y" -> (X, Y, 0, 'final', 0) [shortcut]
    if matched := re.fullmatch(r'(\d+)\.(\d+)(?:\.(\d+))?', version):
        major, minor, micro = matched.groups(default='0')
        return VersionInfo(int(major), int(minor), int(micro), 'final', 0)

    # Pre-release versions:
    # - "X.Y.ZaN" -> (X, Y, Z, 'alpha', N)
    # - "X.Y.ZbN" -> (X, Y, Z, 'beta', N)
    # - "X.Y.ZrcN" -> (X, Y, Z, 'candidate', N)
    if matched := re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(a|b|rc)(\d+)', version):
        major, minor, micro, level, serial = matched.groups()
        return VersionInfo(int(major), int(minor), int(micro), level, int(serial))  # type: ignore[arg-type]

    msg = f'Unknown version: {version}'
    raise RuntimeError(msg)


def bump_version(
    path: Path, version_info: VersionInfo, in_develop: bool = True
) -> None:
    if in_develop or version_info.is_final:
        version = version_info.version
    else:
        version = version_info.release

    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines(keepends=True)

    for i, line in enumerate(lines):
        if line.startswith('__version__: Final = '):
            lines[i] = f"__version__: Final = '{version}'\n"
            continue
        if line.startswith('version_info: Final = '):
            lines[i] = f'version_info: Final = {version_info.release_tuple}\n'
            continue
        if line.startswith('_in_development = '):
            lines[i] = f'_in_development = {in_develop}\n'
            continue

    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


class Changes:
    def __init__(self, path: Path) -> None:
        self.path = path

        with open(self.path, encoding='utf-8') as f:
            version = f.readline().strip()
            matched = re.fullmatch(r'Release (.*) \((.*)\)', version)
            if matched is None:
                msg = f'Unknown CHANGES format: {version}'
                raise RuntimeError(msg)

            self.version, release_date = matched.groups()
            self.in_development = release_date == 'in development'
            self.version_tuple = parse_version(self.version).version_tuple

    def finalise_release_date(self) -> None:
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
        heading = f'Release {version_info.version} (in development)'
        tmpl = (script_dir / 'CHANGES_template.rst').read_text(encoding='utf-8')
        with open(self.path, 'r+', encoding='utf-8') as f:
            body = f.read()

            f.seek(0)
            f.truncate(0)
            f.write(heading + '\n')
            f.write('=' * len(heading) + '\n')
            f.write('\n')
            f.write(tmpl)
            f.write('\n')
            f.write(body)

    @staticmethod
    def filter_empty_sections(body: str) -> str:
        return re.sub(
            '^\n.+\n-{3,}\n+(?=\n.+\n[-=]{3,}\n)', '', body, flags=re.MULTILINE
        )


class Skip(Exception):
    pass


@contextmanager
def processing(message: str) -> Iterator[None]:
    try:
        print(message + ' ... ', end='')
        yield
    except Skip as exc:
        print(f'skip: {exc}')
    except Exception:
        print('error')
        raise
    else:
        print('done')


def parse_options(argv: Sequence[str]) -> tuple[VersionInfo, bool]:
    parser = argparse.ArgumentParser()
    parser.add_argument('version', help='A version number (cf. 1.6.0b0)')
    parser.add_argument('--in-develop', action='store_true')
    options = parser.parse_args(argv)
    return parse_version(options.version), options.in_develop


def main() -> None:
    version, in_develop = parse_options(sys.argv[1:])

    with processing('Rewriting sphinx/__init__.py'):
        bump_version(package_dir / 'sphinx' / '__init__.py', version, in_develop)

    with processing('Rewriting CHANGES'):
        changes = Changes(package_dir / 'CHANGES.rst')
        if changes.version_tuple == version.version_tuple:
            if changes.in_development and version.is_final and not in_develop:
                changes.finalise_release_date()
            else:
                reason = 'version not changed'
                raise Skip(reason)
        else:
            if changes.in_development:
                print(f'WARNING: last version is not released yet: {changes.version}')
            changes.add_release(version)


if __name__ == '__main__':
    main()
