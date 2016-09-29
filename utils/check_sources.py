#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Checker for file headers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Make sure each Python file has a correct file header
    including copyright and license information.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import re
import sys
from optparse import OptionParser
from os.path import join, splitext, abspath


checkers = {}


def checker(*suffixes, **kwds):
    only_pkg = kwds.pop('only_pkg', False)

    def deco(func):
        for suffix in suffixes:
            checkers.setdefault(suffix, []).append(func)
        func.only_pkg = only_pkg
        return func
    return deco


# this one is a byte regex since it is applied before decoding
coding_re    = re.compile(br'coding[:=]\s*([-\w.]+)')

uni_coding_re = re.compile(r'^#.*coding[:=]\s*([-\w.]+).*')
name_mail_re = r'[\w ]+(<.*?>)?'
copyright_re = re.compile(r'^    :copyright: Copyright 200\d(-20\d\d)? '
                          r'by %s(, %s)*[,.]$' %
                          (name_mail_re, name_mail_re))
license_re = re.compile(r"    :license: (.*?).\n")
copyright_2_re = re.compile(r'^                %s(, %s)*[,.]$' %
                            (name_mail_re, name_mail_re))
not_ix_re    = re.compile(r'\bnot\s+\S+?\s+i[sn]\s\S+')
is_const_re  = re.compile(r'if.*?==\s+(None|False|True)\b')

misspellings = ["developement", "adress",  # ALLOW-MISSPELLING
                "verificate", "informations"]  # ALLOW-MISSPELLING


def decode_source(fn, lines):
    encoding = 'ascii' if fn.endswith('.py') else 'utf-8'
    decoded_lines = []
    for lno, line in enumerate(lines):
        if lno < 2:
            co = coding_re.search(line)
            if co:
                encoding = co.group(1).decode()
        try:
            decoded_lines.append(line.decode(encoding))
        except UnicodeDecodeError as err:
            raise UnicodeError("%s:%d: not decodable: %s\n   Line: %r" %
                               (fn, lno+1, err, line))
        except LookupError as err:
            raise LookupError("unknown encoding: %s" % encoding)
    return decoded_lines


@checker('.py')
def check_syntax(fn, lines):
    lines = [uni_coding_re.sub('', line) for line in lines]
    try:
        compile(''.join(lines), fn, "exec")
    except SyntaxError as err:
        yield 0, "not compilable: %s" % err


@checker('.py')
def check_style(fn, lines):
    for lno, line in enumerate(lines):
        if len(line.rstrip('\n')) > 95:
            yield lno+1, "line too long"
        if line.strip().startswith('#'):
            continue
        # m = not_ix_re.search(line)
        # if m:
        #     yield lno+1, '"' + m.group() + '"'
        if is_const_re.search(line):
            yield lno+1, 'using == None/True/False'


@checker('.py', only_pkg=True)
def check_fileheader(fn, lines):
    # line number correction
    c = 1
    if lines[0:1] == ['#!/usr/bin/env python\n']:
        lines = lines[1:]
        c = 2

    llist = []
    docopen = False
    for lno, l in enumerate(lines):
        llist.append(l)
        if lno == 0:
            if l != '# -*- coding: utf-8 -*-\n':
                yield 1, "missing coding declaration"
        elif lno == 1:
            if l != '"""\n' and l != 'r"""\n':
                yield 2, 'missing docstring begin (""")'
            else:
                docopen = True
        elif docopen:
            if l == '"""\n':
                # end of docstring
                if lno <= 4:
                    yield lno+c, "missing module name in docstring"
                break

            if l != '\n' and l[:4] != '    ' and docopen:
                yield lno+c, "missing correct docstring indentation"

            if lno == 2:
                # if not in package, don't check the module name
                modname = fn[:-3].replace('/', '.').replace('.__init__', '')
                while modname:
                    if l.lower()[4:-1] == modname:
                        break
                    modname = '.'.join(modname.split('.')[1:])
                else:
                    yield 3, "wrong module name in docstring heading"
                modnamelen = len(l.strip())
            elif lno == 3:
                if l.strip() != modnamelen * '~':
                    yield 4, "wrong module name underline, should be ~~~...~"

    else:
        yield 0, "missing end and/or start of docstring..."

    # check for copyright and license fields
    license = llist[-2:-1]
    if not license or not license_re.match(license[0]):
        yield 0, "no correct license info"

    ci = -3
    copyright = llist[ci:ci+1]
    while copyright and copyright_2_re.match(copyright[0]):
        ci -= 1
        copyright = llist[ci:ci+1]
    if not copyright or not copyright_re.match(copyright[0]):
        yield 0, "no correct copyright info"


@checker('.py', '.html', '.rst')
def check_whitespace_and_spelling(fn, lines):
    for lno, line in enumerate(lines):
        if '\t' in line:
            yield lno+1, "OMG TABS!!!1 "
        if line[:-1].rstrip(' \t') != line[:-1]:
            yield lno+1, "trailing whitespace"
        for word in misspellings:
            if word in line and 'ALLOW-MISSPELLING' not in line:
                yield lno+1, '"%s" used' % word


bad_tags = ['<u>', '<s>', '<strike>', '<center>', '<font']


@checker('.html')
def check_xhtml(fn, lines):
    for lno, line in enumerate(lines):
        for bad_tag in bad_tags:
            if bad_tag in line:
                yield lno+1, "used " + bad_tag


def main(argv):
    parser = OptionParser(usage='Usage: %prog [-v] [-i ignorepath]* [path]')
    parser.add_option('-v', '--verbose', dest='verbose', default=False,
                      action='store_true')
    parser.add_option('-i', '--ignore-path', dest='ignored_paths',
                      default=[], action='append')
    options, args = parser.parse_args(argv[1:])

    if len(args) == 0:
        path = '.'
    elif len(args) == 1:
        path = args[0]
    else:
        print(args)
        parser.error('No more then one path supported')

    verbose = options.verbose
    ignored_paths = set(abspath(p) for p in options.ignored_paths)

    num = 0

    for root, dirs, files in os.walk(path):
        for vcs_dir in ['.svn', '.hg', '.git']:
            if vcs_dir in dirs:
                dirs.remove(vcs_dir)
        if abspath(root) in ignored_paths:
            del dirs[:]
            continue
        in_check_pkg = root.startswith('./sphinx')
        for fn in files:

            fn = join(root, fn)
            if fn[:2] == './':
                fn = fn[2:]

            if abspath(fn) in ignored_paths:
                continue

            ext = splitext(fn)[1]
            checkerlist = checkers.get(ext, None)
            if not checkerlist:
                continue

            if verbose:
                print("Checking %s..." % fn)

            try:
                with open(fn, 'rb') as f:
                    lines = list(f)
            except (IOError, OSError) as err:
                print("%s: cannot open: %s" % (fn, err))
                num += 1
                continue

            try:
                lines = decode_source(fn, lines)
            except Exception as err:
                print(err)
                num += 1
                continue

            for checker in checkerlist:
                if not in_check_pkg and checker.only_pkg:
                    continue
                for lno, msg in checker(fn, lines):
                    print("%s:%d: %s" % (fn, lno, msg))
                    num += 1
    if verbose:
        print()
    if num == 0:
        print("No errors found.")
    else:
        print("%d error%s found." % (num, num > 1 and "s" or ""))
    return int(num > 0)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
