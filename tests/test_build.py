# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test all builders that have no special checks.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import *


def teardown_module():
    (test_root / '_build').rmtree(True)

# just let the remaining ones run for now

@with_app(buildername='pickle')
def test_pickle(app):
    app.builder.build_all()

@with_app(buildername='json')
def test_json(app):
    app.builder.build_all()

@with_app(buildername='linkcheck')
def test_linkcheck(app):
    app.builder.build_all()

@with_app(buildername='text')
def test_text(app):
    app.builder.build_all()

@with_app(buildername='htmlhelp')
def test_htmlhelp(app):
    app.builder.build_all()

@with_app(buildername='qthelp')
def test_qthelp(app):
    app.builder.build_all()

@with_app(buildername='epub')
def test_epub(app):
    app.builder.build_all()

@with_app(buildername='changes')
def test_changes(app):
    app.builder.build_all()

try:
    from docutils.writers.manpage import Writer
except ImportError:
    pass
else:
    @with_app(buildername='man')
    def test_man(app):
        app.builder.build_all()

@with_app(buildername='singlehtml', cleanenv=True)
def test_singlehtml(app):
    app.builder.build_all()
