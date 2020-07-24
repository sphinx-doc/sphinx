"""
    test_util_pycompat
    ~~~~~~~~~~~~~~~~~~

    Tests sphinx.util.pycompat functions.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.testing.util import strip_escseq
from sphinx.util import logging
from sphinx.util.pycompat import execfile_


def test_execfile_python2(capsys, app, status, warning, tempdir):
    logging.setup(app, status, warning)

    conf_py = tempdir / 'conf.py'
    conf_py.write_bytes(b'print "hello"\n')
    execfile_(conf_py, {})

    msg = (
        'Support for evaluating Python 2 syntax is deprecated '
        'and will be removed in Sphinx 4.0. '
        'Convert %s to Python 3 syntax.\n' % conf_py)
    assert msg in strip_escseq(warning.getvalue())
    captured = capsys.readouterr()
    assert captured.out == 'hello\n'


def test_execfile(capsys, tempdir):
    conf_py = tempdir / 'conf.py'
    conf_py.write_bytes(b'print("hello")\n')
    execfile_(conf_py, {})

    captured = capsys.readouterr()
    assert captured.out == 'hello\n'
