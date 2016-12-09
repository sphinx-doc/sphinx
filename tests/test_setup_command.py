# -*- coding: utf-8 -*-
"""
    test_setup_command
    ~~~~~~~~~~~~~~~~~~~

    Test setup_command for distutils.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import sys
import subprocess
from functools import wraps
import tempfile
import sphinx

from util import rootdir, tempdir, SkipTest
from path import path
from textwrap import dedent

root = tempdir / 'test-setup'


def setup_module():
    if not root.exists():
        (rootdir / 'roots' / 'test-setup').copytree(root)


def with_setup_command(root, *args, **kwds):
    """
    Run `setup.py build_sphinx` with args and kwargs,
    pass it to the test and clean up properly.
    """
    def generator(func):
        @wraps(func)
        def deco(*args2, **kwargs2):
            tempdir = path(tempfile.mkdtemp())
            pkgrootdir = (tempdir / 'root')
            root.copytree(pkgrootdir)
            cwd = os.getcwd()
            os.chdir(pkgrootdir)
            pythonpath = os.path.dirname(os.path.dirname(sphinx.__file__))
            if os.getenv('PYTHONPATH'):
                pythonpath = os.getenv('PYTHONPATH') + os.pathsep + pythonpath
            command = [sys.executable, 'setup.py', 'build_sphinx']
            command.extend(args)
            try:
                proc = subprocess.Popen(
                    command,
                    env=dict(os.environ, PYTHONPATH=pythonpath),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                func(pkgrootdir, proc)
            finally:
                tempdir.rmtree(ignore_errors=True)
                os.chdir(cwd)
        return deco
    return generator


@with_setup_command(root)
def test_build_sphinx(pkgroot, proc):
    out, err = proc.communicate()
    print(out)
    print(err)
    assert proc.returncode == 0


@with_setup_command(root)
def test_build_sphinx_with_nonascii_path(pkgroot, proc):
    mb_name = u'\u65e5\u672c\u8a9e'
    srcdir = (pkgroot / 'doc')
    try:
        (srcdir / mb_name).makedirs()
    except UnicodeEncodeError:
        from path import FILESYSTEMENCODING
        raise SkipTest(
            'non-ASCII filename not supported on this filesystem encoding: '
            '%s', FILESYSTEMENCODING)

    (srcdir / mb_name / (mb_name + '.txt')).write_text(dedent("""
        multi byte file name page
        ==========================
        """))

    master_doc = srcdir / 'contents.txt'
    master_doc.write_bytes((master_doc.text() + dedent("""
            .. toctree::

               %(mb_name)s/%(mb_name)s
            """ % locals())
    ).encode('utf-8'))

    out, err = proc.communicate()
    print(out)
    print(err)
    assert proc.returncode == 0


@with_setup_command(root, '-b', 'linkcheck')
def test_build_sphinx_return_nonzero_status(pkgroot, proc):
    srcdir = (pkgroot / 'doc')
    (srcdir / 'contents.txt').write_text(
        'http://localhost.unexistentdomain/index.html')
    out, err = proc.communicate()
    print(out)
    print(err)
    assert proc.returncode != 0, 'expect non-zero status for setup.py'


@with_setup_command(root)
def test_build_sphinx_warning_return_zero_status(pkgroot, proc):
    srcdir = (pkgroot / 'doc')
    (srcdir / 'contents.txt').write_text(
        'See :ref:`unexisting-reference-label`')
    out, err = proc.communicate()
    print(out)
    print(err)
    assert proc.returncode == 0


@with_setup_command(root, '--warning-is-error')
def test_build_sphinx_warning_is_error_return_nonzero_status(pkgroot, proc):
    srcdir = (pkgroot / 'doc')
    (srcdir / 'contents.txt').write_text(
        'See :ref:`unexisting-reference-label`')
    out, err = proc.communicate()
    print(out)
    print(err)
    assert proc.returncode != 0, 'expect non-zero status for setup.py'
