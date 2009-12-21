# -*- coding: utf-8 -*-
"""
    test_metadata
    ~~~~~~~~~~~~~

    Test our ahndling of metadata in files with bibliographic metadata

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""



# adapted from an example of bibliographic metadata at http://docutils.sourceforge.net/docs/user/rst/demo.txt

from util import *

from nose.tools import assert_equals

from sphinx.environment import BuildEnvironment
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.latex import LaTeXBuilder

app = env = None
warnings = []

def setup_module():
    # Is there a better way of generating this doctree than manually iterating?
    global app, env
    app = TestApp(srcdir='(temp)')
    env = BuildEnvironment(app.srcdir, app.doctreedir, app.config)
    # Huh. Why do I need to do this?
    env.set_warnfunc(lambda *args: warnings.append(args)) 
    msg, num, it = env.update(app.config, app.srcdir, app.doctreedir, app)
    for docname in it:
        pass

def teardown_module():
    app.cleanup()

def test_docinfo():
    exampledocinfo = env.metadata['metadata']
    expected_metadata = {
      'author': u'David Goodger',
      u'field name': u'This is a generic bibliographic field.',
      u'field name 2': u'Generic bibliographic fields may contain multiple body elements.\n\nLike this.'}
    # I like this way of comparing dicts - easier to see the error.
    for key in exampledocinfo:
        yield assert_equals, exampledocinfo[key], expected_metadata[key]
    #but then we still have to check for missing keys
    yield assert_equals, expected_metadata.keys(), exampledocinfo.keys()
