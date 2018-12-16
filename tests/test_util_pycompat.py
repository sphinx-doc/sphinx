# -*- coding: utf-8 -*-
"""
    test_util_pycompat
    ~~~~~~~~~~~~~~~~~~

    Tests sphinx.util.pycompat functions.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import tempfile

from sphinx.testing.util import strip_escseq
from sphinx.util import logging
from sphinx.util.pycompat import execfile_


def test_execfile_python2(capsys, app, status, warning):
    logging.setup(app, status, warning)

    ns = {}
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(b'print "hello"\n')
        tmp.flush()
        execfile_(tmp.name, ns)
    msg = (
        'Support for evaluating Python 2 syntax is deprecated '
        'and will be removed in Sphinx 4.0. '
        'Convert %s to Python 3 syntax.\n' % tmp.name)
    assert msg in strip_escseq(warning.getvalue())
    captured = capsys.readouterr()
    assert captured.out == 'hello\n'


def test_execfile(capsys):
    ns = {}
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(b'print("hello")\n')
        tmp.flush()
        execfile_(tmp.name, ns)
    captured = capsys.readouterr()
    assert captured.out == 'hello\n'
