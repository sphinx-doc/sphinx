# -*- coding: utf-8 -*-
"""
    test_intl
    ~~~~~~~~~

    Test message patching for internationalization purposes.  Runs the text
    builder in the test root.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
from StringIO import StringIO
from subprocess import Popen, PIPE
from xml.etree import ElementTree

from sphinx.util.pycompat import relpath

from util import test_roots, path, with_app, SkipTest


warnfile = StringIO()
root = test_roots / 'test-intl'
doctreedir = root / '_build' / 'doctree'


def with_intl_app(*args, **kw):
    default_kw = {
        'srcdir': root,
        'doctreedir': doctreedir,
        'confoverrides': {
            'language': 'xx', 'locale_dirs': ['.'],
            'gettext_compact': False,
        },
    }
    default_kw.update(kw)
    return with_app(*args, **default_kw)


def setup_module():
    # Delete remnants left over after failed build
    (root / 'xx').rmtree(True)
    (root / 'xx' / 'LC_MESSAGES').makedirs()
    # Compile all required catalogs into binary format (*.mo).
    for dirpath, dirs, files in os.walk(root):
        dirpath = path(dirpath)
        for f in [f for f in files if f.endswith('.po')]:
            po = dirpath / f
            mo = root / 'xx' / 'LC_MESSAGES' / (
                    relpath(po[:-3], root) + '.mo')
            if not mo.parent.exists():
                mo.parent.makedirs()
            try:
                p = Popen(['msgfmt', po, '-o', mo],
                    stdout=PIPE, stderr=PIPE)
            except OSError:
                raise SkipTest  # most likely msgfmt was not found
            else:
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    print stdout
                    print stderr
                    assert False, \
                        'msgfmt exited with return code %s' % p.returncode
                assert mo.isfile(), 'msgfmt failed'


def teardown_module():
    (root / '_build').rmtree(True)
    (root / 'xx').rmtree(True)


@with_intl_app(buildername='text')
def test_simple(app):
    app.builder.build(['bom'])
    result = (app.outdir / 'bom.txt').text(encoding='utf-8')
    expect = (u"\nDatei mit UTF-8"
              u"\n***************\n" # underline matches new translation
              u"\nThis file has umlauts: äöü.\n")
    assert result == expect


@with_intl_app(buildername='text')
def test_subdir(app):
    app.builder.build(['subdir/contents'])
    result = (app.outdir / 'subdir' / 'contents.txt').text(encoding='utf-8')
    assert result.startswith(u"\nsubdir contents\n***************\n")


@with_intl_app(buildername='text', warning=warnfile)
def test_i18n_warnings_in_translation(app):
    app.builddir.rmtree(True)
    app.builder.build(['warnings'])
    result = (app.outdir / 'warnings.txt').text(encoding='utf-8')
    expect = (u"\nI18N WITH REST WARNINGS"
              u"\n***********************\n"
              u"\nLINE OF >>``<<BROKEN LITERAL MARKUP.\n")

    assert result == expect

    warnings = warnfile.getvalue().replace(os.sep, '/')
    warning_expr = u'.*/warnings.txt:4: ' \
            u'WARNING: Inline literal start-string without end-string.\n'
    assert re.search(warning_expr, warnings)


@with_intl_app(buildername='html', cleanenv=True)
def test_i18n_footnote_break_refid(app):
    """test for #955 cant-build-html-with-footnotes-when-using"""
    app.builder.build(['footnote'])
    result = (app.outdir / 'footnote.html').text(encoding='utf-8')
    # expect no error by build


@with_intl_app(buildername='text', warning=warnfile)
def test_i18n_footnote_regression(app):
    """regression test for fix #955"""
    app.builddir.rmtree(True)
    app.builder.build(['footnote'])
    result = (app.outdir / 'footnote.txt').text(encoding='utf-8')
    expect = (u"\nI18N WITH FOOTNOTE"
              u"\n******************\n"  # underline matches new translation
              u"\nI18N WITH FOOTNOTE INCLUDE THIS CONTENTS [ref] [1] [100]\n"
              u"\n[1] THIS IS A AUTO NUMBERED FOOTNOTE.\n"
              u"\n[ref] THIS IS A NAMED FOOTNOTE.\n"
              u"\n[100] THIS IS A NUMBERED FOOTNOTE.\n")
    assert result == expect

    warnings = warnfile.getvalue().replace(os.sep, '/')
    warning_expr = u'.*/footnote.txt:\\d*: SEVERE: Duplicate ID: ".*".\n'
    assert not re.search(warning_expr, warnings)


@with_intl_app(buildername='html', cleanenv=True)
def test_i18n_footnote_backlink(app):
    """i18n test for #1058"""
    app.builder.build(['footnote'])
    result = (app.outdir / 'footnote.html').text(encoding='utf-8')
    expects = [
        '<a class="footnote-reference" href="#id5" id="id1">[100]</a>',
        '<a class="footnote-reference" href="#id4" id="id2">[1]</a>',
        '<a class="reference internal" href="#ref" id="id3">[ref]</a>',
        '<a class="fn-backref" href="#id2">[1]</a>',
        '<a class="fn-backref" href="#id3">[ref]</a>',
        '<a class="fn-backref" href="#id1">[100]</a>',
        ]
    for expect in expects:
        matches = re.findall(re.escape(expect), result)
        assert len(matches) == 1


@with_intl_app(buildername='text', warning=warnfile, cleanenv=True)
def test_i18n_warn_for_number_of_references_inconsistency(app):
    app.builddir.rmtree(True)
    app.builder.build(['refs_inconsistency'])
    result = (app.outdir / 'refs_inconsistency.txt').text(encoding='utf-8')
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
    warning_fmt = u'.*/refs_inconsistency.txt:\\d+: ' \
          u'WARNING: inconsistent %s in translated message\n'
    expected_warning_expr = (
        warning_fmt % 'footnote references' +
        warning_fmt % 'references' +
        warning_fmt % 'references')
    assert re.search(expected_warning_expr, warnings)


@with_intl_app(buildername='html', cleanenv=True)
def test_i18n_link_to_undefined_reference(app):
    app.builder.build(['refs_inconsistency'])
    result = (app.outdir / 'refs_inconsistency.html').text(encoding='utf-8')

    expected_expr = ('<a class="reference external" '
                     'href="http://www.example.com">reference</a>')
    assert len(re.findall(expected_expr, result)) == 2

    expected_expr = ('<a class="reference internal" '
                     'href="#reference">reference</a>')
    assert len(re.findall(expected_expr, result)) == 0

    expected_expr = ('<a class="reference internal" '
                     'href="#i18n-with-refs-inconsistency">I18N WITH '
                     'REFS INCONSISTENCY</a>')
    assert len(re.findall(expected_expr, result)) == 1


@with_intl_app(buildername='html', cleanenv=True)
def test_i18n_keep_external_links(app):
    """regression test for #1044"""
    app.builder.build(['external_links'])
    result = (app.outdir / 'external_links.html').text(encoding='utf-8')

    # external link check
    expect_line = (u'<li>EXTERNAL LINK TO <a class="reference external" '
                   u'href="http://python.org">Python</a>.</li>')
    matched = re.search('^<li>EXTERNAL LINK TO .*$', result, re.M)
    matched_line = ''
    if matched:
        matched_line = matched.group()
    assert expect_line == matched_line

    # internal link check
    expect_line = (u'<li><a class="reference internal" '
                   u'href="#i18n-with-external-links">EXTERNAL '
                   u'LINKS</a> IS INTERNAL LINK.</li>')
    matched = re.search('^<li><a .* IS INTERNAL LINK.</li>$', result, re.M)
    matched_line = ''
    if matched:
        matched_line = matched.group()
    assert expect_line == matched_line

    # inline link check
    expect_line = (u'<li>INLINE LINK BY <a class="reference external" '
                   u'href="http://sphinx-doc.org">SPHINX</a>.</li>')
    matched = re.search('^<li>INLINE LINK BY .*$', result, re.M)
    matched_line = ''
    if matched:
        matched_line = matched.group()
    assert expect_line == matched_line

    # unnamed link check
    expect_line = (u'<li>UNNAMED <a class="reference external" '
                   u'href="http://google.com">LINK</a>.</li>')
    matched = re.search('^<li>UNNAMED .*$', result, re.M)
    matched_line = ''
    if matched:
        matched_line = matched.group()
    assert expect_line == matched_line


@with_intl_app(buildername='text', warning=warnfile, cleanenv=True)
def test_i18n_literalblock_warning(app):
    app.builddir.rmtree(True)  #for warnings acceleration
    app.builder.build(['literalblock'])
    result = (app.outdir / 'literalblock.txt').text(encoding='utf-8')
    expect = (u"\nI18N WITH LITERAL BLOCK"
              u"\n***********************\n"
              u"\nCORRECT LITERAL BLOCK:\n"
              u"\n   this is"
              u"\n   literal block\n"
              u"\nMISSING LITERAL BLOCK:\n"
              u"\n<SYSTEM MESSAGE:")
    assert result.startswith(expect)

    warnings = warnfile.getvalue().replace(os.sep, '/')
    expected_warning_expr = u'.*/literalblock.txt:\\d+: ' \
            u'WARNING: Literal block expected; none found.'
    assert re.search(expected_warning_expr, warnings)


@with_intl_app(buildername='text')
def test_i18n_definition_terms(app):
    # regression test for #975
    app.builder.build(['definition_terms'])
    result = (app.outdir / 'definition_terms.txt').text(encoding='utf-8')
    expect = (u"\nI18N WITH DEFINITION TERMS"
              u"\n**************************\n"
              u"\nSOME TERM"
              u"\n   THE CORRESPONDING DEFINITION\n"
              u"\nSOME OTHER TERM"
              u"\n   THE CORRESPONDING DEFINITION #2\n")

    assert result == expect


@with_intl_app(buildername='text', warning=warnfile)
def test_i18n_glossary_terms(app):
    # regression test for #1090
    app.builddir.rmtree(True)  #for warnings acceleration
    app.builder.build(['glossary_terms'])
    result = (app.outdir / 'glossary_terms.txt').text(encoding='utf-8')
    expect = (u"\nI18N WITH GLOSSARY TERMS"
              u"\n************************\n"
              u"\nSOME NEW TERM"
              u"\n   THE CORRESPONDING GLOSSARY\n"
              u"\nSOME OTHER NEW TERM"
              u"\n   THE CORRESPONDING GLOSSARY #2\n"
              u"\nLINK TO *SOME NEW TERM*.\n")
    assert result == expect

    warnings = warnfile.getvalue().replace(os.sep, '/')
    assert 'term not in glossary' not in warnings


@with_intl_app(buildername='xml', warning=warnfile)
def test_i18n_role_xref(app):
    # regression test for #1090

    def gettexts(elem):
        def itertext(self):
            # this function copied from Python-2.7 'ElementTree.itertext'.
            # for compatibility to Python-2.5, 2.6, 3.1
            tag = self.tag
            if not isinstance(tag, basestring) and tag is not None:
                return
            if self.text:
                yield self.text
            for e in self:
                for s in itertext(e):
                    yield s
                if e.tail:
                    yield e.tail
        return filter(None, [s.strip() for s in itertext(elem)])

    def getref(elem):
        return elem.attrib.get('refid') or elem.attrib.get('refuri')

    def assert_text_refs(elem, text, refs):
        _text = gettexts(elem)
        assert _text == text
        _refs = map(getref, elem.findall('reference'))
        assert _refs == refs

    app.builddir.rmtree(True)  #for warnings acceleration
    app.builder.build(['role_xref'])
    et = ElementTree.parse(app.outdir / 'role_xref.xml')
    sec1, sec2 = et.findall('section')

    para1, = sec1.findall('paragraph')
    assert_text_refs(
            para1,
            ['LINK TO', "I18N ROCK'N ROLE XREF", ',', 'CONTENTS', ',',
             'SOME NEW TERM', '.'],
            ['i18n-role-xref',
             'contents',
             'glossary_terms#term-some-new-term'])

    para2 = sec2.findall('paragraph')
    assert_text_refs(
            para2[0],
            ['LINK TO', 'SOME OTHER NEW TERM', 'AND', 'SOME NEW TERM', '.'],
            ['glossary_terms#term-some-other-new-term',
             'glossary_terms#term-some-new-term'])
    assert_text_refs(
            para2[1],
            ['LINK TO', 'SAME TYPE LINKS', 'AND', "I18N ROCK'N ROLE XREF", '.'],
            ['same-type-links', 'i18n-role-xref'])
    assert_text_refs(
            para2[2],
            ['LINK TO', 'I18N WITH GLOSSARY TERMS', 'AND', 'CONTENTS', '.'],
            ['glossary_terms', 'contents'])
    assert_text_refs(
            para2[3],
            ['LINK TO', '--module', 'AND', '-m', '.'],
            ['cmdoption--module', 'cmdoption-m'])
    assert_text_refs(
            para2[4],
            ['LINK TO', 'env2', 'AND', 'env1', '.'],
            ['envvar-env2', 'envvar-env1'])
    assert_text_refs(
            para2[5],
            ['LINK TO', 'token2', 'AND', 'token1', '.'],
            [])  #TODO: how do I link token role to productionlist?
    assert_text_refs(
            para2[6],
            ['LINK TO', 'same-type-links', 'AND', "i18n-role-xref", '.'],
            ['same-type-links', 'i18n-role-xref'])

    #warnings
    warnings = warnfile.getvalue().replace(os.sep, '/')
    assert 'term not in glossary' not in warnings
    assert 'undefined label' not in warnings
    assert 'unknown document' not in warnings


@with_intl_app(buildername='text', warning=warnfile)
def test_i18n_glossary_terms_inconsistency(app):
    # regression test for #1090
    app.builddir.rmtree(True)  #for warnings acceleration
    app.builder.build(['glossary_terms_inconsistency'])
    result = (app.outdir / 'glossary_terms_inconsistency.txt'
                ).text(encoding='utf-8')
    expect = (u"\nI18N WITH GLOSSARY TERMS INCONSISTENCY"
              u"\n**************************************\n"
              u"\n1. LINK TO *SOME NEW TERM*.\n")
    assert result == expect

    warnings = warnfile.getvalue().replace(os.sep, '/')
    expected_warning_expr = (
            u'.*/glossary_terms_inconsistency.txt:\\d+: '
            u'WARNING: inconsistent term references in translated message\n')
    assert re.search(expected_warning_expr, warnings)


@with_intl_app(buildername='text')
def test_seealso(app):
    app.builder.build(['seealso'])
    result = (app.outdir / 'seealso.txt').text(encoding='utf-8')
    expect = (u"\nI18N WITH SEEALSO"
              u"\n*****************\n"
              u"\nSee also: SHORT TEXT 1\n"
              u"\nSee also: LONG TEXT 1\n"
              u"\nSee also: SHORT TEXT 2\n"
              u"\n  LONG TEXT 2\n")
    assert result == expect


@with_intl_app(buildername='text')
def test_i18n_figure_caption(app):
    # regression test for #940
    app.builder.build(['figure_caption'])
    result = (app.outdir / 'figure_caption.txt').text(encoding='utf-8')
    expect = (u"\nI18N WITH FIGURE CAPTION"
              u"\n************************\n"
              u"\n   [image]MY CAPTION OF THE FIGURE\n"
              u"\n   MY DESCRIPTION PARAGRAPH1 OF THE FIGURE.\n"
              u"\n   MY DESCRIPTION PARAGRAPH2 OF THE FIGURE.\n")

    assert result == expect


@with_intl_app(buildername='html')
def test_i18n_index_entries(app):
    # regression test for #976
    app.builder.build(['index_entries'])
    result = (app.outdir / 'genindex.html').text(encoding='utf-8')

    def wrap(tag, keyword):
        start_tag = "<%s[^>]*>" % tag
        end_tag = "</%s>" % tag
        return r"%s\s*%s\s*%s" % (start_tag, keyword, end_tag)

    expected_exprs = [
        wrap('a', 'NEWSLETTER'),
        wrap('a', 'MAILING LIST'),
        wrap('a', 'RECIPIENTS LIST'),
        wrap('a', 'FIRST SECOND'),
        wrap('a', 'SECOND THIRD'),
        wrap('a', 'THIRD, FIRST'),
        wrap('dt', 'ENTRY'),
        wrap('dt', 'SEE'),
        wrap('a', 'MODULE'),
        wrap('a', 'KEYWORD'),
        wrap('a', 'OPERATOR'),
        wrap('a', 'OBJECT'),
        wrap('a', 'EXCEPTION'),
        wrap('a', 'STATEMENT'),
        wrap('a', 'BUILTIN'),
    ]
    for expr in expected_exprs:
        assert re.search(expr, result, re.M)


@with_intl_app(buildername='html', cleanenv=True)
def test_versionchange(app):
    app.builder.build(['versionchange'])
    result = (app.outdir / 'versionchange.html').text(encoding='utf-8')

    def get_content(result, name):
        matched = re.search(r'<div class="%s">\n*(.*?)</div>' % name,
                            result, re.DOTALL)
        if matched:
            return matched.group(1)
        else:
            return ''

    expect1 = (
        u"""<p><span>Deprecated since version 1.0: </span>"""
        u"""THIS IS THE <em>FIRST</em> PARAGRAPH OF DEPRECATED.</p>\n"""
        u"""<p>THIS IS THE <em>SECOND</em> PARAGRAPH OF DEPRECATED.</p>\n""")
    matched_content = get_content(result, "deprecated")
    assert expect1 == matched_content

    expect2 = (
        u"""<p><span>New in version 1.0: </span>"""
        u"""THIS IS THE <em>FIRST</em> PARAGRAPH OF VERSIONADDED.</p>\n""")
    matched_content = get_content(result, "versionadded")
    assert expect2 == matched_content

    expect3 = (
        u"""<p><span>Changed in version 1.0: </span>"""
        u"""THIS IS THE <em>FIRST</em> PARAGRAPH OF VERSIONCHANGED.</p>\n""")
    matched_content = get_content(result, "versionchanged")
    assert expect3 == matched_content


@with_intl_app(buildername='text', cleanenv=True)
def test_i18n_docfields(app):
    app.builder.build(['docfields'])
    result = (app.outdir / 'docfields.txt').text(encoding='utf-8')
    expect = (u"\nI18N WITH DOCFIELDS"
              u"\n*******************\n"
              u"\nclass class Cls1\n"
              u"\n   Parameters:"
              u"\n      **param** -- DESCRIPTION OF PARAMETER param\n"
              u"\nclass class Cls2\n"
              u"\n   Parameters:"
              u"\n      * **foo** -- DESCRIPTION OF PARAMETER foo\n"
              u"\n      * **bar** -- DESCRIPTION OF PARAMETER bar\n"
              u"\nclass class Cls3(values)\n"
              u"\n   Raises ValueError:"
              u"\n      IF THE VALUES ARE OUT OF RANGE\n"
              u"\nclass class Cls4(values)\n"
              u"\n   Raises:"
              u"\n      * **TypeError** -- IF THE VALUES ARE NOT VALID\n"
              u"\n      * **ValueError** -- IF THE VALUES ARE OUT OF RANGE\n"
              u"\nclass class Cls5\n"
              u"\n   Returns:"
              u'\n      A NEW "Cls3" INSTANCE\n')
    assert result == expect


@with_intl_app(buildername='html', cleanenv=True)
def test_i18n_docfields_html(app):
    app.builder.build(['docfields'])
    result = (app.outdir / 'docfields.html').text(encoding='utf-8')
    # expect no error by build


@with_intl_app(buildername='html')
def test_gettext_template(app):
    app.builder.build_all()
    result = (app.outdir / 'index.html').text(encoding='utf-8')
    assert "WELCOME" in result
    assert "SPHINX 2013.120" in result


@with_intl_app(buildername='html')
def test_rebuild_by_mo_mtime(app):
    app.builder.build_update()
    _, count, _ = app.env.update(app.config, app.srcdir, app.doctreedir, app)
    assert count == 0

    mo = (app.srcdir / 'xx' / 'LC_MESSAGES' / 'bom.mo').bytes()
    (app.srcdir / 'xx' / 'LC_MESSAGES' / 'bom.mo').write_bytes(mo)
    _, count, _ = app.env.update(app.config, app.srcdir, app.doctreedir, app)
    assert count == 1
