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


def elem_gettexts(elem):
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


def elem_getref(elem):
    return elem.attrib.get('refid') or elem.attrib.get('refuri')


def assert_elem(elem, texts=None, refs=None, names=None):
    if texts is not None:
        _texts = elem_gettexts(elem)
        assert _texts == texts
    if refs is not None:
        _refs = map(elem_getref, elem.findall('reference'))
        assert _refs == refs
    if names is not None:
        _names = elem.attrib.get('names').split()
        assert _names == names


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


@with_intl_app(buildername='xml', warning=warnfile)
def test_i18n_footnote_regression(app):
    # regression test for fix #955, #1176
    app.builddir.rmtree(True)
    app.builder.build(['footnote'])
    et = ElementTree.parse(app.outdir / 'footnote.xml')
    secs = et.findall('section')

    para0 = secs[0].findall('paragraph')
    assert_elem(
            para0[0],
            texts=['I18N WITH FOOTNOTE', 'INCLUDE THIS CONTENTS',
                  '2', '[ref]', '1', '100', '.'],
            refs=['i18n-with-footnote', 'ref'])

    footnote0 = secs[0].findall('footnote')
    assert_elem(
            footnote0[0],
            texts=['1','THIS IS A AUTO NUMBERED FOOTNOTE.'],
            names=['1'])
    assert_elem(
            footnote0[1],
            texts=['100','THIS IS A NUMBERED FOOTNOTE.'],
            names=['100'])
    assert_elem(
            footnote0[2],
            texts=['2','THIS IS A AUTO NUMBERED NAMED FOOTNOTE.'],
            names=['named'])

    citation0 = secs[0].findall('citation')
    assert_elem(
            citation0[0],
            texts=['ref','THIS IS A NAMED FOOTNOTE.'],
            names=['ref'])

    warnings = warnfile.getvalue().replace(os.sep, '/')
    warning_expr = u'.*/footnote.xml:\\d*: SEVERE: Duplicate ID: ".*".\n'
    assert not re.search(warning_expr, warnings)


@with_intl_app(buildername='xml', cleanenv=True)
def test_i18n_footnote_backlink(app):
    # i18n test for #1058
    app.builder.build(['footnote'])
    et = ElementTree.parse(app.outdir / 'footnote.xml')
    secs = et.findall('section')

    para0 = secs[0].findall('paragraph')
    refs0 = para0[0].findall('footnote_reference')
    refid2id = dict([
        (r.attrib.get('refid'), r.attrib.get('ids')) for r in refs0])

    footnote0 = secs[0].findall('footnote')
    for footnote in footnote0:
        ids = footnote.attrib.get('ids')
        backrefs = footnote.attrib.get('backrefs')
        assert refid2id[ids] == backrefs


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


@with_intl_app(buildername='xml', cleanenv=True)
def test_i18n_keep_external_links(app):
    # regression test for #1044
    app.builder.build(['external_links'])
    et = ElementTree.parse(app.outdir / 'external_links.xml')
    secs = et.findall('section')

    para0 = secs[0].findall('paragraph')
    # external link check
    assert_elem(
            para0[0],
            texts=['EXTERNAL LINK TO', 'Python', '.'],
            refs=['http://python.org/index.html'])

    # internal link check
    assert_elem(
            para0[1],
            texts=['EXTERNAL LINKS', 'IS INTERNAL LINK.'],
            refs=['i18n-with-external-links'])

    # inline link check
    assert_elem(
            para0[2],
            texts=['INLINE LINK BY', 'THE SPHINX SITE', '.'],
            refs=['http://sphinx-doc.org'])

    # unnamed link check
    assert_elem(
            para0[3],
            texts=['UNNAMED', 'LINK', '.'],
            refs=['http://google.com'])

    # link target swapped translation
    para1 = secs[1].findall('paragraph')
    assert_elem(
            para1[0],
            texts=['LINK TO', 'external2', 'AND', 'external1', '.'],
            refs=['http://example.com/external2',
                  'http://example.com/external1'])
    assert_elem(
            para1[1],
            texts=['LINK TO', 'THE PYTHON SITE', 'AND', 'THE SPHINX SITE',
                   '.'],
            refs=['http://python.org', 'http://sphinx-doc.org'])

    # multiple references in the same line
    para2 = secs[2].findall('paragraph')
    assert_elem(
            para2[0],
            texts=['LINK TO', 'EXTERNAL LINKS', ',', 'Python', ',',
                   'THE SPHINX SITE', ',', 'UNNAMED', 'AND',
                   'THE PYTHON SITE', '.'],
            refs=['i18n-with-external-links', 'http://python.org/index.html',
                  'http://sphinx-doc.org', 'http://google.com',
                  'http://python.org'])


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
    # regression test for #1090, #1193
    app.builddir.rmtree(True)  #for warnings acceleration
    app.builder.build(['role_xref'])
    et = ElementTree.parse(app.outdir / 'role_xref.xml')
    sec1, sec2 = et.findall('section')

    para1, = sec1.findall('paragraph')
    assert_elem(
            para1,
            texts=['LINK TO', "I18N ROCK'N ROLE XREF", ',', 'CONTENTS', ',',
                   'SOME NEW TERM', '.'],
            refs=['i18n-role-xref', 'contents',
                  'glossary_terms#term-some-term'])

    para2 = sec2.findall('paragraph')
    assert_elem(
            para2[0],
            texts=['LINK TO', 'SOME OTHER NEW TERM', 'AND', 'SOME NEW TERM',
                   '.'],
            refs=['glossary_terms#term-some-other-term',
                  'glossary_terms#term-some-term'])
    assert_elem(
            para2[1],
            texts=['LINK TO', 'SAME TYPE LINKS', 'AND',
                   "I18N ROCK'N ROLE XREF", '.'],
            refs=['same-type-links', 'i18n-role-xref'])
    assert_elem(
            para2[2],
            texts=['LINK TO', 'I18N WITH GLOSSARY TERMS', 'AND', 'CONTENTS',
                   '.'],
            refs=['glossary_terms', 'contents'])
    assert_elem(
            para2[3],
            texts=['LINK TO', '--module', 'AND', '-m', '.'],
            refs=['cmdoption--module', 'cmdoption-m'])
    assert_elem(
            para2[4],
            texts=['LINK TO', 'env2', 'AND', 'env1', '.'],
            refs=['envvar-env2', 'envvar-env1'])
    assert_elem(
            para2[5],
            texts=['LINK TO', 'token2', 'AND', 'token1', '.'],
            refs=[])  #TODO: how do I link token role to productionlist?
    assert_elem(
            para2[6],
            texts=['LINK TO', 'same-type-links', 'AND', "i18n-role-xref", '.'],
            refs=['same-type-links', 'i18n-role-xref'])

    #warnings
    warnings = warnfile.getvalue().replace(os.sep, '/')
    assert 'term not in glossary' not in warnings
    assert 'undefined label' not in warnings
    assert 'unknown document' not in warnings


@with_intl_app(buildername='xml', warning=warnfile)
def test_i18n_label_target(app):
    # regression test for #1193
    app.builder.build(['label_target'])
    et = ElementTree.parse(app.outdir / 'label_target.xml')
    secs = et.findall('section')

    para0 = secs[0].findall('paragraph')
    assert_elem(
            para0[0],
            texts=['X SECTION AND LABEL', 'POINT TO', 'implicit-target', 'AND',
                   'X SECTION AND LABEL', 'POINT TO', 'section-and-label', '.'],
            refs=['implicit-target', 'section-and-label'])

    para1 = secs[1].findall('paragraph')
    assert_elem(
            para1[0],
            texts=['X EXPLICIT-TARGET', 'POINT TO', 'explicit-target', 'AND',
                   'X EXPLICIT-TARGET', 'POINT TO DUPLICATED ID LIKE', 'id1',
                   '.'],
            refs=['explicit-target', 'id1'])

    para2 = secs[2].findall('paragraph')
    assert_elem(
            para2[0],
            texts=['X IMPLICIT SECTION NAME', 'POINT TO',
                   'implicit-section-name', '.'],
            refs=['implicit-section-name'])

    sec2 = secs[2].findall('section')

    para2_0 = sec2[0].findall('paragraph')
    assert_elem(
            para2_0[0],
            texts=['`X DUPLICATED SUB SECTION`_', 'IS BROKEN LINK.'],
            refs=[])


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


@with_intl_app(buildername='text', cleanenv=True)
def test_i18n_admonitions(app):
    # #1206: gettext did not translate admonition directive's title
    # seealso: http://docutils.sourceforge.net/docs/ref/rst/directives.html#admonitions
    app.builder.build(['admonitions'])
    result = (app.outdir / 'admonitions.txt').text(encoding='utf-8')
    directives = (
            "attention", "caution", "danger", "error", "hint",
            "important", "note", "tip", "warning", "admonition",)
    for d in directives:
        assert d.upper() + " TITLE" in result
        assert d.upper() + " BODY" in result


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
