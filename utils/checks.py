# -*- coding: utf-8 -*-
"""
    utils.checks
    ~~~~~~~~~~~~

    Custom, Sphinx-only flake8 plugins.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re

import sphinx

name_mail_re = r'[\w ]+(<.*?>)?'
copyright_re = re.compile(r'^    :copyright: Copyright 200\d(-20\d\d)? '
                          r'by %s(, %s)*[,.]$' % (name_mail_re, name_mail_re))
copyright_2_re = re.compile(r'^                %s(, %s)*[,.]$' %
                            (name_mail_re, name_mail_re))
license_re = re.compile(r'    :license: (.*?).\n')


def flake8ext(_func):
    """Decorate flake8_asserts functions"""
    _func.name = _func.__name__
    _func.version = sphinx.__version__
    _func.code = _func.__name__.upper()

    return _func


@flake8ext
def sphinx_has_header(physical_line, filename, lines, line_number):
    """Check for correct headers.

    Make sure each Python file has a correct file header including
    copyright and license information.

    X101 invalid header found
    """
    # we have a state machine of sorts so we need to start on line 1. Also,
    # there's no point checking really short files
    if line_number != 1 or len(lines) < 10:
        return

    # this file uses a funky license but unfortunately it's not possible to
    # ignore specific errors on a file-level basis yet [1]. Simply skip it.
    #
    # [1] https://gitlab.com/pycqa/flake8/issues/347
    if os.path.samefile(filename, './sphinx/util/smartypants.py'):
        return

    # if the top-level package or not inside the package, ignore
    mod_name = os.path.splitext(filename)[0].strip('./\\').replace(
        '/', '.').replace('.__init__', '')
    if mod_name == 'sphinx' or not mod_name.startswith('sphinx.'):
        return

    # line number correction
    offset = 1
    if lines[0:1] == ['#!/usr/bin/env python\n']:
        lines = lines[1:]
        offset = 2

    llist = []
    doc_open = False

    for lno, line in enumerate(lines):
        llist.append(line)
        if lno == 0:
            if line != '# -*- coding: utf-8 -*-\n':
                return 0, 'X101 missing coding declaration'
        elif lno == 1:
            if line != '"""\n' and line != 'r"""\n':
                return 0, 'X101 missing docstring begin (""")'
            else:
                doc_open = True
        elif doc_open:
            if line == '"""\n':
                # end of docstring
                if lno <= 4:
                    return 0, 'X101 missing module name in docstring'
                break

            if line != '\n' and line[:4] != '    ' and doc_open:
                return 0, 'X101 missing correct docstring indentation'

            if lno == 2:
                mod_name_len = len(line.strip())
                if line.strip() != mod_name:
                    return 4, 'X101 wrong module name in docstring heading'
            elif lno == 3:
                if line.strip() != mod_name_len * '~':
                    return (4, 'X101 wrong module name underline, should be '
                            '~~~...~')
    else:
        return 0, 'X101 missing end and/or start of docstring...'

    # check for copyright and license fields
    license = llist[-2:-1]
    if not license or not license_re.match(license[0]):
        return 0, 'X101 no correct license info'

    offset = -3
    copyright = llist[offset:offset + 1]
    while copyright and copyright_2_re.match(copyright[0]):
        offset -= 1
        copyright = llist[offset:offset + 1]
    if not copyright or not copyright_re.match(copyright[0]):
        return 0, 'X101 no correct copyright info'
