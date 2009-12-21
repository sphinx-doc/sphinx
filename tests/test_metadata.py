# -*- coding: utf-8 -*-
"""
    test_metadata
    ~~~~~~~~~~~~~

    Test our ahndling of metadata in files with bibliographic metadata

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""



# adapted from an example of bibliographic metadata at http://docutils.sourceforge.net/docs/user/rst/demo.txt
BIBLIOGRAPHIC_FIELDS_REST = """:Author: David Goodger
:Address: 123 Example Street
          Example, EX  Canada
          A1B 2C3
:Contact: goodger@python.org
:Authors: Me; Myself; I
:organization: humankind
:date: $Date: 2006-05-21 22:44:42 +0200 (Son, 21 Mai 2006) $
:status: This is a "work in progress"
:revision: $Revision: 4564 $
:version: 1
:copyright: This document has been placed in the public domain. You
            may do with it as you wish. You may copy, modify,
            redistribute, reattribute, sell, buy, rent, lease,
            destroy, or improve it, quote it at length, excerpt,
            incorporate, collate, fold, staple, or mutilate it, or do
            anything else to it that your or anyone else's heart
            desires.
:field name: This is a generic bibliographic field.
:field name 2:
    Generic bibliographic fields may contain multiple body elements.

    Like this.

:Dedication:

    For Docutils users & co-developers.

:abstract:

    This document is a demonstration of the reStructuredText markup
    language, containing examples of all basic reStructuredText
    constructs and many advanced constructs.

.. meta::
   :keywords: reStructuredText, demonstration, demo, parser
   :description lang=en: A demonstration of the reStructuredText
       markup language, containing examples of all basic
       constructs and many advanced constructs.

================================
reStructuredText Demonstration
================================

Above is the document title.
"""

from util import *

from sphinx.environment import BuildEnvironment
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.latex import LaTeXBuilder

app = env = None
warnings = []

def setup_module():
    global app, env
    app = TestApp(srcdir='(temp)')
    env = BuildEnvironment(app.srcdir, app.doctreedir, app.config)
    env.set_warnfunc(lambda *args: warnings.append(args))
    msg, num, it = env.update(app.config, app.srcdir, app.doctreedir, app)
    for docname in it:
        pass

def teardown_module():
    app.cleanup()


def test_second_update():
    # delete, add and "edit" (change saved mtime) some files and update again
    env.all_docs['contents'] = 0
    root = path(app.srcdir)
    # important: using "autodoc" because it is the last one to be included in
    # the contents.txt toctree; otherwise section numbers would shift
    (root / 'autodoc.txt').unlink()
    (root / 'new.txt').write_text('New file\n========\n')
    msg, num, it = env.update(app.config, app.srcdir, app.doctreedir, app)
    assert '1 added, 3 changed, 1 removed' in msg
    docnames = set()
    for docname in it:
        docnames.add(docname)
    # "includes" and "images" are in there because they contain references
    # to nonexisting downloadable or image files, which are given another
    # chance to exist
    assert docnames == set(['contents', 'new', 'includes', 'images'])
    assert 'autodoc' not in env.all_docs
    assert 'autodoc' not in env.found_docs
