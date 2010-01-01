# -*- coding: utf-8 -*-
"""
    test_quickstart
    ~~~~~~~~~~~~~~~

    Test the sphinx.quickstart module.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import time
import __builtin__

from util import *

from sphinx import quickstart as qs
from sphinx.util.console import nocolor, coloron

def setup_module():
    nocolor()

def mock_raw_input(answers, needanswer=False):
    called = set()
    def raw_input(prompt):
        if prompt in called:
            raise AssertionError('answer for %r missing and no default '
                                 'present' % prompt)
        called.add(prompt)
        for question in answers:
            if prompt.startswith(qs.PROMPT_PREFIX + question):
                return answers[question]
        if needanswer:
            raise AssertionError('answer for %r missing' % prompt)
        return ''
    return raw_input

def teardown_module():
    qs.raw_input = __builtin__.raw_input
    qs.TERM_ENCODING = getattr(sys.stdin, 'encoding', None)
    coloron()


def test_do_prompt():
    d = {}
    answers = {
        'Q2': 'v2',
        'Q3': 'v3',
        'Q4': 'yes',
        'Q5': 'no',
        'Q6': 'foo',
    }
    qs.raw_input = mock_raw_input(answers)
    try:
        qs.do_prompt(d, 'k1', 'Q1')
    except AssertionError:
        assert 'k1' not in d
    else:
        assert False, 'AssertionError not raised'
    qs.do_prompt(d, 'k1', 'Q1', default='v1')
    assert d['k1'] == 'v1'
    qs.do_prompt(d, 'k3', 'Q3', default='v3_default')
    assert d['k3'] == 'v3'
    qs.do_prompt(d, 'k2', 'Q2')
    assert d['k2'] == 'v2'
    qs.do_prompt(d, 'k4', 'Q4', validator=qs.boolean)
    assert d['k4'] is True
    qs.do_prompt(d, 'k5', 'Q5', validator=qs.boolean)
    assert d['k5'] is False
    raises(AssertionError, qs.do_prompt, d, 'k6', 'Q6', validator=qs.boolean)


@with_tempdir
def test_quickstart_defaults(tempdir):
    answers = {
        'Root path': tempdir,
        'Project name': 'Sphinx Test',
        'Author name': 'Georg Brandl',
        'Project version': '0.1',
    }
    qs.raw_input = mock_raw_input(answers)
    qs.inner_main([])

    conffile = tempdir / 'conf.py'
    assert conffile.isfile()
    ns = {}
    execfile(conffile, ns)
    assert ns['extensions'] == []
    assert ns['templates_path'] == ['_templates']
    assert ns['source_suffix'] == '.rst'
    assert ns['master_doc'] == 'index'
    assert ns['project'] == 'Sphinx Test'
    assert ns['copyright'] == '%s, Georg Brandl' % time.strftime('%Y')
    assert ns['version'] == '0.1'
    assert ns['release'] == '0.1'
    assert ns['html_static_path'] == ['_static']
    assert ns['latex_documents'] == [
        ('index', 'SphinxTest.tex', 'Sphinx Test Documentation',
         'Georg Brandl', 'manual')]

    assert (tempdir / '_static').isdir()
    assert (tempdir / '_templates').isdir()
    assert (tempdir / 'index.rst').isfile()
    assert (tempdir / 'Makefile').isfile()
    assert (tempdir / 'make.bat').isfile()


@with_tempdir
def test_quickstart_all_answers(tempdir):
    answers = {
        'Root path': tempdir,
        'Separate source and build': 'y',
        'Name prefix for templates': '.',
        'Project name': 'STASI\xe2\x84\xa2',
        'Author name': 'Wolfgang Sch\xc3\xa4uble & G\'Beckstein',
        'Project version': '2.0',
        'Project release': '2.0.1',
        'Source file suffix': '.txt',
        'Name of your master document': 'contents',
        'autodoc': 'y',
        'doctest': 'yes',
        'intersphinx': 'no',
        'todo': 'n',
        'coverage': 'no',
        'pngmath': 'N',
        'jsmath': 'no',
        'ifconfig': 'no',
        'Create Makefile': 'no',
        'Create Windows command file': 'no',
    }
    qs.raw_input = mock_raw_input(answers, needanswer=True)
    qs.TERM_ENCODING = 'utf-8'
    qs.inner_main([])

    conffile = tempdir / 'source' / 'conf.py'
    assert conffile.isfile()
    ns = {}
    execfile(conffile, ns)
    assert ns['extensions'] == ['sphinx.ext.autodoc', 'sphinx.ext.doctest']
    assert ns['templates_path'] == ['.templates']
    assert ns['source_suffix'] == '.txt'
    assert ns['master_doc'] == 'contents'
    assert ns['project'] == u'STASI™'
    assert ns['copyright'] == u'%s, Wolfgang Schäuble & G\'Beckstein' % \
           time.strftime('%Y')
    assert ns['version'] == '2.0'
    assert ns['release'] == '2.0.1'
    assert ns['html_static_path'] == ['.static']
    assert ns['latex_documents'] == [
        ('contents', 'STASI.tex', u'STASI™ Documentation',
         u'Wolfgang Schäuble \\& G\'Beckstein', 'manual')]

    assert (tempdir / 'build').isdir()
    assert (tempdir / 'source' / '.static').isdir()
    assert (tempdir / 'source' / '.templates').isdir()
    assert (tempdir / 'source' / 'contents.txt').isfile()
