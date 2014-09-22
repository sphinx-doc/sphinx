# -*- coding: utf-8 -*-
"""
    test_env_read_docs
    ~~~~~~~~~~~~~~~~~~

    Test docnames read order modification using the env-read-docs event.

    :copyright: Copyright 2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pickle

from docutils.parsers.rst.directives.html import MetaBody

from sphinx import addnodes
from sphinx.versioning import add_uids, merge_doctrees, get_ratio

from util import test_root, TestApp

def setup_module():
    pass

def test_default_docnames_order():
    """By default, docnames are read in alphanumeric order"""
    def on_env_read_docs(app, env, docnames):
        pass

    app = TestApp(srcdir='(temp)', freshenv=True)
    env = app.env
    app.connect('env-read-docs', on_env_read_docs)

    msg, num, it = env.update(app.config, app.srcdir, app.doctreedir, app)
    read_docnames = [docname for docname in it]
    assert len(read_docnames) > 1 and read_docnames == sorted(read_docnames)

def test_inverse_docnames_order():
    """By default, docnames are read in alphanumeric order"""
    def on_env_read_docs(app, env, docnames):
        docnames.reverse()

    app = TestApp(srcdir='(temp)', freshenv=True)
    env = app.env
    app.connect('env-read-docs', on_env_read_docs)

    msg, num, it = env.update(app.config, app.srcdir, app.doctreedir, app)
    read_docnames = [docname for docname in it]
    reversed_read_docnames = sorted(read_docnames, reverse=True)
    assert len(read_docnames) > 1 and read_docnames == reversed_read_docnames

def teardown_module():
    (test_root / '_build').rmtree(True)
