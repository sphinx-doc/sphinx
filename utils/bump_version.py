#!/usr/bin/env python3

import argparse
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime

script_dir = os.path.dirname(__file__)
package_dir = os.path.abspath(os.path.join(script_dir, '..'))

RELEASE_TYPE = {'a': 'alpha', 'b': 'beta'}


def stringify_version(version_info, in_develop=True):
    version = '.'.join(str(v) for v in version_info[:3])
    if not in_develop and version_info[3] != 'final':
        version += version_info[3][0] + str(version_info[4])

    return version


def bump_version(path, version_info, in_develop=True):
    version = stringify_version(version_info, in_develop)
    release = version
    if in_develop:
        version += '+'

    with open(path, 'r+') as f:
        body = f.read()
        body = re.sub(r"(?<=__version__ = ')[^']+", version, body)
        body = re.sub(r"(?<=__released__ = ')[^']+", release, body)
        body = re.sub(r"(?<=version_info = )\(.*\)", str(version_info), body)

        f.seek(0)
        f.truncate(0)
        f.write(body)


def parse_version(version):
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
def processing(message):
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
    def __init__(self, path):
        self.path = path
        self.fetch_version()

    def fetch_version(self):
        with open(self.path) as f:
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

    def finalize_release_date(self):
        release_date = datetime.now().strftime('%b %d, %Y')
        heading = 'Release %s (released %s)' % (self.version, release_date)

        with open(self.path, 'r+') as f:
            f.readline()  # skip first two lines
            f.readline()
            body = f.read()

            f.seek(0)
            f.truncate(0)
            f.write(heading + '\n')
            f.write('=' * len(heading) + '\n')
            f.write(self.filter_empty_sections(body))

    def add_release(self, version_info):
        if version_info[-2:] in (('beta', 0), ('final', 0)):
            version = stringify_version(version_info)
        else:
            reltype = version_info[3]
            version = '%s %s%s' % (stringify_version(version_info),
                                   RELEASE_TYPE.get(reltype, reltype),
                                   version_info[4] or '')
        heading = 'Release %s (in development)' % version

        with open(os.path.join(script_dir, 'CHANGES_template')) as f:
            f.readline()  # skip first two lines
            f.readline()
            tmpl = f.read()

        with open(self.path, 'r+') as f:
            body = f.read()

            f.seek(0)
            f.truncate(0)
            f.write(heading + '\n')
            f.write('=' * len(heading) + '\n')
            f.write(tmpl)
            f.write('\n')
            f.write(body)

    def filter_empty_sections(self, body):
        return re.sub('^\n.+\n-{3,}\n+(?=\n.+\n[-=]{3,}\n)', '', body, flags=re.M)


def parse_options(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('version', help='A version number (cf. 1.6b0)')
    parser.add_argument('--in-develop', action='store_true')
    options = parser.parse_args(argv)
    options.version = parse_version(options.version)
    return options


def main():
    options = parse_options(sys.argv[1:])

    with processing("Rewriting sphinx/__init__.py"):
        bump_version(os.path.join(package_dir, 'sphinx/__init__.py'),
                     options.version, options.in_develop)

    with processing('Rewriting CHANGES'):
        changes = Changes(os.path.join(package_dir, 'CHANGES'))
        if changes.version_info == options.version:
            if changes.in_development:
                changes.finalize_release_date()
            else:
                raise Skip('version not changed')
        else:
            if changes.in_development:
                print('WARNING: last version is not released yet: %s' % changes.version)
            changes.add_release(options.version)


if __name__ == '__main__':
    main()
