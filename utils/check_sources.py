#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Checker for file headers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Make sure each Python file has a correct file header
    including copyright and license information.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys, os, re
import cStringIO
from optparse import OptionParser
from os.path import join, splitext, abspath

if sys.version_info >= (3, 0):
    def b(s):
        return s.encode('utf-8')
else:
    b = str


checkers = {}

def checker(*suffixes, **kwds):
    only_pkg = kwds.pop('only_pkg', False)
    def deco(func):
        for suffix in suffixes:
            checkers.setdefault(suffix, []).append(func)
        func.only_pkg = only_pkg
        return func
    return deco


name_mail_re = r'[\w ]+(<.*?>)?'
copyright_re = re.compile(b(r'^    :copyright: Copyright 200\d(-20\d\d)? '
                            r'by %s(, %s)*[,.]$' %
                            (name_mail_re, name_mail_re)))
license_re = re.compile(b(r"    :license: (.*?).\n"))
copyright_2_re = re.compile(b(r'^                %s(, %s)*[,.]$' %
                             (name_mail_re, name_mail_re)))
coding_re    = re.compile(b(r'coding[:=]\s*([-\w.]+)'))
not_ix_re    = re.compile(b(r'\bnot\s+\S+?\s+i[sn]\s\S+'))
is_const_re  = re.compile(b(r'if.*?==\s+(None|False|True)\b'))

misspellings = [b("developement"), b("adress"), # ALLOW-MISSPELLING
                b("verificate"), b("informations")] # ALLOW-MISSPELLING

if sys.version_info < (3, 0):
    @checker('.py')
    def check_syntax(fn, lines):
        try:
            compile(b('').join(lines), fn, "exec")
        except SyntaxError, err:
            yield 0, "not compilable: %s" % err


@checker('.py')
def check_style_and_encoding(fn, lines):
    encoding = 'ascii'
    for lno, line in enumerate(lines):
        if len(line) > 81:
            yield lno+1, "line too long"
        if lno < 2:
            co = coding_re.search(line)
            if co:
                encoding = co.group(1).decode('ascii')
        if line.strip().startswith(b('#')):
            continue
        #m = not_ix_re.search(line)
        #if m:
        #    yield lno+1, '"' + m.group() + '"'
        if is_const_re.search(line):
            yield lno+1, 'using == None/True/False'
        try:
            line.decode(encoding)
        except UnicodeDecodeError, err:
            yield lno+1, "not decodable: %s\n   Line: %r" % (err, line)
        except LookupError, err:
            yield 0, "unknown encoding: %s" % encoding
            encoding = 'latin1'


@checker('.py', only_pkg=True)
def check_fileheader(fn, lines):
    # line number correction
    c = 1
    if lines[0:1] == [b('#!/usr/bin/env python\n')]:
        lines = lines[1:]
        c = 2

    llist = []
    docopen = False
    for lno, l in enumerate(lines):
        llist.append(l)
        if lno == 0:
            if l == b('# -*- coding: rot13 -*-\n'):
                # special-case pony package
                return
            elif l != b('# -*- coding: utf-8 -*-\n'):
                yield 1, "missing coding declaration"
        elif lno == 1:
            if l != b('"""\n') and l != b('r"""\n'):
                yield 2, 'missing docstring begin (""")'
            else:
                docopen = True
        elif docopen:
            if l == b('"""\n'):
                # end of docstring
                if lno <= 4:
                    yield lno+c, "missing module name in docstring"
                break

            if l != b("\n") and l[:4] != b('    ') and docopen:
                yield lno+c, "missing correct docstring indentation"

            if lno == 2:
                # if not in package, don't check the module name
                modname = fn[:-3].replace('/', '.').replace('.__init__', '')
                while modname:
                    if l.lower()[4:-1] == b(modname):
                        break
                    modname = '.'.join(modname.split('.')[1:])
                else:
                    yield 3, "wrong module name in docstring heading"
                modnamelen = len(l.strip())
            elif lno == 3:
                if l.strip() != modnamelen * b("~"):
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
        if b("\t") in line:
            yield lno+1, "OMG TABS!!!1 "
        if line[:-1].rstrip(b(' \t')) != line[:-1]:
            yield lno+1, "trailing whitespace"
        for word in misspellings:
            if word in line and b('ALLOW-MISSPELLING') not in line:
                yield lno+1, '"%s" used' % word


bad_tags = map(b, ['<u>', '<s>', '<strike>', '<center>', '<font'])

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
        print args
        parser.error('No more then one path supported')

    verbose = options.verbose
    ignored_paths = set(abspath(p) for p in options.ignored_paths)

    num = 0
    out = cStringIO.StringIO()

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
            if fn[:2] == './': fn = fn[2:]

            if abspath(fn) in ignored_paths:
                continue

            ext = splitext(fn)[1]
            checkerlist = checkers.get(ext, None)
            if not checkerlist:
                continue

            if verbose:
                print "Checking %s..." % fn

            try:
                f = open(fn, 'rb')
                try:
                    lines = list(f)
                finally:
                    f.close()
            except (IOError, OSError), err:
                print "%s: cannot open: %s" % (fn, err)
                num += 1
                continue

            for checker in checkerlist:
                if not in_check_pkg and checker.only_pkg:
                    continue
                for lno, msg in checker(fn, lines):
                    print >>out, "%s:%d: %s" % (fn, lno, msg)
                    num += 1
    if verbose:
        print
    if num == 0:
        print "No errors found."
    else:
        print out.getvalue().rstrip('\n')
        print "%d error%s found." % (num, num > 1 and "s" or "")
    return int(num > 0)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
