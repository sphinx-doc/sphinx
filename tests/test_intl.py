# -*- coding: utf-8 -*-
"""
    test_intl
    ~~~~~~~~~

    Test message patching for internationalization purposes.  Runs the text
    builder in the test root.

    :copyright: Copyright 2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from subprocess import Popen, PIPE
import re
import os
from StringIO import StringIO

from util import *
from util import SkipTest


warnfile = StringIO()


def setup_module():
    (test_root / 'xx' / 'LC_MESSAGES').makedirs()
    # Compile all required catalogs into binary format (*.mo).
    for dirpath, dirs, files in os.walk(test_root):
        dirpath = path(dirpath)
        for f in [f for f in files if f.endswith('.po')]:
            po = dirpath / f
            mo = test_root / 'xx' / 'LC_MESSAGES' / (
                    os.path.relpath(po[:-3], test_root) + '.mo')
            if not mo.parent.exists():
                mo.parent.makedirs()
            try:
                p = Popen(['msgfmt', po, '-o', mo],
                    stdout=PIPE, stderr=PIPE)
            except OSError:
                # The test will fail the second time it's run if we don't
                # tear down here. Not sure if there's a more idiomatic way
                # of ensuring that teardown gets run in the event of an
                # exception from the setup function.
                teardown_module()
                raise SkipTest  # most likely msgfmt was not found
            else:
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    print stdout
                    print stderr
                    assert False, 'msgfmt exited with return code %s' % p.returncode
                assert mo.isfile(), 'msgfmt failed'


def teardown_module():
    (test_root / '_build').rmtree(True)
    (test_root / 'xx').rmtree(True)


@with_app(buildername='text',
          confoverrides={'language': 'xx', 'locale_dirs': ['.']})
def test_simple(app):
    app.builder.build(['bom'])
    result = (app.outdir / 'bom.txt').text(encoding='utf-8')
    expect = (u"\nDatei mit UTF-8"
              u"\n***************\n" # underline matches new translation
              u"\nThis file has umlauts: äöü.\n")
    assert result == expect


@with_app(buildername='text',
          confoverrides={'language': 'xx', 'locale_dirs': ['.']})
def test_subdir(app):
    app.builder.build(['subdir/includes'])
    result = (app.outdir / 'subdir' / 'includes.txt').text(encoding='utf-8')
    assert result.startswith(u"\ntranslation\n***********\n\n")


@with_app(buildername='html', cleanenv=True,
          confoverrides={'language': 'xx', 'locale_dirs': ['.'],
                         'gettext_compact': False})
def test_i18n_footnote_break_refid(app):
    """test for #955 cant-build-html-with-footnotes-when-using"""
    app.builder.build(['i18n/footnote'])
    result = (app.outdir / 'i18n' / 'footnote.html').text(encoding='utf-8')
    # expect no error by build


@with_app(buildername='text', cleanenv=True,
          confoverrides={'language': 'xx', 'locale_dirs': ['.'],
                         'gettext_compact': False})
def test_i18n_footnote_regression(app):
    """regression test for fix #955"""
    app.builder.build(['i18n/footnote'])
    result = (app.outdir / 'i18n' / 'footnote.txt').text(encoding='utf-8')
    expect = (u"\nI18N WITH FOOTNOTE"
              u"\n******************\n"  # underline matches new translation
              u"\nI18N WITH FOOTNOTE INCLUDE THIS CONTENTS [ref] [1] [100]\n"
              u"\n[1] THIS IS A AUTO NUMBERED FOOTNOTE.\n"
              u"\n[ref] THIS IS A NAMED FOOTNOTE.\n"
              u"\n[100] THIS IS A NUMBERED FOOTNOTE.\n")
    assert result == expect


@with_app(buildername='text', warning=warnfile, cleanenv=True,
          confoverrides={'language': 'xx', 'locale_dirs': ['.'],
                         'gettext_compact': False})
def test_i18n_warn_for_number_of_references_inconsistency(app):
    app.builddir.rmtree(True)
    app.builder.build(['i18n/refs_inconsistency'])
    result = (app.outdir / 'i18n' / 'refs_inconsistency.txt').text(encoding='utf-8')
    expect = (u"\nI18N WITH REFS INCONSISTENCY"
              u"\n****************************\n"
              u"\n* FOR FOOTNOTE [ref2].\n"
              u"\n* reference FOR reference.\n"
              u"\n* ORPHAN REFERENCE: I18N WITH REFS INCONSISTENCY.\n"
              u"\n[1] THIS IS A AUTO NUMBERED FOOTNOTE.\n"
              u"\n[ref2] THIS IS A NAMED FOOTNOTE.\n"
              u"\n[100] THIS IS A NUMBERED FOOTNOTE.\n")
    assert result == expect

    warnings = warnfile.getvalue().replace(os.sep, '/')
    warning_fmt = u'.*/i18n/refs_inconsistency.txt:\\d+: ' \
          u'WARNING: inconsistent %s in translated message\n'
    expected_warning_expr = (
        warning_fmt % 'footnote references' +
        warning_fmt % 'references' +
        warning_fmt % 'references')
    assert re.search(expected_warning_expr, warnings)


@with_app(buildername='html', cleanenv=True,
          confoverrides={'language': 'xx', 'locale_dirs': ['.'],
                         'gettext_compact': False})
def test_i18n_link_to_undefined_reference(app):
    app.builder.build(['i18n/refs_inconsistency'])
    result = (app.outdir / 'i18n' / 'refs_inconsistency.html').text(encoding='utf-8')

    expected_expr = """<a class="reference external" href="http://www.example.com">reference</a>"""
    assert len(re.findall(expected_expr, result)) == 2

    expected_expr = """<a class="reference internal" href="#reference">reference</a>"""
    assert len(re.findall(expected_expr, result)) == 0

    expected_expr = """<a class="reference internal" href="#i18n-with-refs-inconsistency">I18N WITH REFS INCONSISTENCY</a>"""
    assert len(re.findall(expected_expr, result)) == 1


@with_app(buildername='html', cleanenv=True,
          confoverrides={'language': 'xx', 'locale_dirs': ['.'],
                         'gettext_compact': False})
def test_i18n_keep_external_links(app):
    """regression test for #1044"""
    app.builder.build(['i18n/external_links'])
    result = (app.outdir / 'i18n' / 'external_links.html').text(encoding='utf-8')

    # external link check
    expect_line = u"""<li>EXTERNAL LINK TO <a class="reference external" href="http://python.org">Python</a>.</li>"""
    matched = re.search('^<li>EXTERNAL LINK TO .*$', result, re.M)
    matched_line = ''
    if matched:
        matched_line = matched.group()
    assert expect_line == matched_line

    # internal link check
    expect_line = u"""<li><a class="reference internal" href="#i18n-with-external-links">EXTERNAL LINKS</a> IS INTERNAL LINK.</li>"""
    matched = re.search('^<li><a .* IS INTERNAL LINK.</li>$', result, re.M)
    matched_line = ''
    if matched:
        matched_line = matched.group()
    assert expect_line == matched_line

    # inline link check
    expect_line = u"""<li>INLINE LINK BY <a class="reference external" href="http://sphinx-doc.org">SPHINX</a>.</li>"""
    matched = re.search('^<li>INLINE LINK BY .*$', result, re.M)
    matched_line = ''
    if matched:
        matched_line = matched.group()
    assert expect_line == matched_line

    # unnamed link check
    expect_line = u"""<li>UNNAMED <a class="reference external" href="http://google.com">LINK</a>.</li>"""
    matched = re.search('^<li>UNNAMED .*$', result, re.M)
    matched_line = ''
    if matched:
        matched_line = matched.group()
    assert expect_line == matched_line
