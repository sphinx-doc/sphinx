"""Test message patching for internationalization purposes.

Runs the text builder in the test root.
"""

from __future__ import annotations

import os
import re
import shutil
import time
from typing import TYPE_CHECKING

import pygments
import pytest
from babel.messages import mofile, pofile
from babel.messages.catalog import Catalog
from docutils import nodes

from sphinx import locale
from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.testing.util import assert_node, etree_parse
from sphinx.util.nodes import NodeMatcher

from tests.utils import extract_element, extract_node

if TYPE_CHECKING:
    import xml.etree.ElementTree as ET
    from collections.abc import Callable, Iterator
    from io import StringIO
    from pathlib import Path

    from sphinx.testing.fixtures import _app_params
    from sphinx.testing.util import SphinxTestApp

_CATALOG_LOCALE = 'xx'

sphinx_intl = pytest.mark.sphinx(
    confoverrides={
        'language': _CATALOG_LOCALE,
        'locale_dirs': ['.'],
        'gettext_compact': False,
        'html_sidebars': {'**': ['globaltoc.html']},  # for test_html_meta
    },
)


def read_po(pathname: Path) -> Catalog:
    with open(pathname, encoding='utf-8') as f:
        return pofile.read_po(f)


def write_mo(pathname: Path, po: Catalog) -> None:
    with open(pathname, 'wb') as f:
        mofile.write_mo(f, po)


def _set_mtime_ns(target: Path, value: int) -> int:
    os.utime(target, ns=(value, value))
    return target.stat().st_mtime_ns


def _get_bom_intl_path(srcdir: Path) -> tuple[Path, Path]:
    basedir = srcdir / _CATALOG_LOCALE / 'LC_MESSAGES'
    return basedir / 'bom.po', basedir / 'bom.mo'


def _get_update_targets(app: SphinxTestApp) -> tuple[set[str], set[str], set[str]]:
    app.env.find_files(app.config, app.builder)
    added, changed, removed = app.env.get_outdated_files(config_changed=False)
    return added, changed, removed


@pytest.fixture(autouse=True)
def _info(app: SphinxTestApp) -> Iterator[None]:
    yield
    print(f'# language: {app.config.language}')
    print(f'# locale_dirs: {app.config.locale_dirs}')


def elem_gettexts(elem: ET.Element) -> list[str]:
    return list(filter(None, map(str.strip, elem.itertext())))


def elem_getref(elem: ET.Element) -> str | None:
    return elem.attrib.get('refid') or elem.attrib.get('refuri')


def assert_elem(
    elem: ET.Element,
    *,
    texts: list[str] | None = None,
    refs: list[str] | None = None,
    names: list[str] | None = None,
) -> None:
    if texts is not None:
        _texts = elem_gettexts(elem)
        assert _texts == texts
    if refs is not None:
        _refs = [elem_getref(x) for x in elem.findall('reference')]
        assert _refs == refs
    if names is not None:
        _names = elem.attrib['names'].split()
        assert _names == names


def assert_count(expected_expr: str, result: str, count: int) -> None:
    find_pair = (expected_expr, result)
    assert len(re.findall(*find_pair)) == count, find_pair


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_emit_warnings(app: SphinxTestApp) -> None:
    app.build()
    # test warnings in translation
    warnings = getwarning(app.warning)
    warning_expr = (
        '.*/warnings.txt:4:<translated>:1: '
        'WARNING: Inline literal start-string without end-string. \\[docutils\\]\n'
    )
    assert re.search(warning_expr, warnings), (
        f'{warning_expr!r} did not match {warnings!r}'
    )


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_warning_node(app: SphinxTestApp) -> None:
    app.build()
    # test warnings in translation
    result = (app.outdir / 'warnings.txt').read_text(encoding='utf8')
    expect = (
        '3. I18N WITH REST WARNINGS'
        '\n**************************\n'
        '\nLINE OF >>``<<BROKEN LITERAL MARKUP.\n'
    )
    assert result == expect


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_title_underline(app: SphinxTestApp) -> None:
    app.build()
    # --- simple translation; check title underlines
    result = (app.outdir / 'bom.txt').read_text(encoding='utf8')
    expect = (
        '2. Datei mit UTF-8'
        '\n******************\n'  # underline matches new translation
        '\nThis file has umlauts: äöü.\n'
    )
    assert result == expect


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_subdirs(app: SphinxTestApp) -> None:
    app.build()
    # --- check translation in subdirs
    result = (app.outdir / 'subdir' / 'index.txt').read_text(encoding='utf8')
    assert result.startswith('1. subdir contents\n******************\n')


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_inconsistency_warnings(app: SphinxTestApp) -> None:
    app.build()
    # --- check warnings for inconsistency in number of references
    result = (app.outdir / 'refs_inconsistency.txt').read_text(encoding='utf8')
    expect = (
        '8. I18N WITH REFS INCONSISTENCY'
        '\n*******************************\n'
        '\n* FOR CITATION [ref3].\n'
        '\n* reference FOR reference.\n'
        '\n* ORPHAN REFERENCE: I18N WITH REFS INCONSISTENCY.\n'
        '\n* the [refs] [translations] [order] is ignored.\n'
        '\n[1] THIS IS A AUTO NUMBERED FOOTNOTE.\n'
        '\n[ref2] THIS IS A CITATION.\n'
        '\n[100] THIS IS A NUMBERED FOOTNOTE.\n'
        '\n[order] order\n'
        '\n[refs] references\n'
        '\n[translations] translations\n'
    )
    assert result == expect

    warnings = getwarning(app.warning)
    warning_fmt = (
        '.*/refs_inconsistency.txt:\\d+: '
        'WARNING: inconsistent %(reftype)s in translated message.'
        ' original: %(original)s, translated: %(translated)s \\[i18n.inconsistent_references\\]\n'
    )
    expected_warning_expr = (
        warning_fmt
        % {
            'reftype': 'footnote references',
            'original': "\\['\\[#\\]_'\\]",
            'translated': '\\[\\]',
        }
        + warning_fmt
        % {
            'reftype': 'footnote references',
            'original': "\\['\\[100\\]_'\\]",
            'translated': '\\[\\]',
        }
        + warning_fmt
        % {
            'reftype': 'citation references',
            'original': "\\['\\[ref2\\]_'\\]",
            'translated': "\\['\\[ref3\\]_'\\]",
        }
        + warning_fmt
        % {
            'reftype': 'references',
            'original': "\\['reference_'\\]",
            'translated': "\\['reference_', 'reference_'\\]",
        }
        + warning_fmt
        % {
            'reftype': 'references',
            'original': '\\[\\]',
            'translated': "\\['`I18N WITH REFS INCONSISTENCY`_'\\]",
        }
    )
    assert re.search(expected_warning_expr, warnings), (
        f'{expected_warning_expr!r} did not match {warnings!r}'
    )

    expected_citation_ref_warning_expr = '.*/refs_inconsistency.txt:\\d+: WARNING: Citation \\[ref2\\] is not referenced.'
    assert re.search(expected_citation_ref_warning_expr, warnings), (
        f'{expected_citation_ref_warning_expr!r} did not match {warnings!r}'
    )

    expected_citation_warning_expr = (
        '.*/refs_inconsistency.txt:\\d+: WARNING: citation not found: ref3'
    )
    assert re.search(expected_citation_warning_expr, warnings), (
        f'{expected_citation_warning_expr!r} did not match {warnings!r}'
    )


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_noqa(app: SphinxTestApp) -> None:
    app.build()
    result = (app.outdir / 'noqa.txt').read_text(encoding='utf8')
    expect = r"""FIRST SECTION
*************

TRANSLATED TEXT WITHOUT REFERENCE.

TEST noqa WHITESPACE INSENSITIVITY.

"#noqa" IS ESCAPED AT THE END OF THIS STRING. #noqa


NEXT SECTION WITH PARAGRAPH TO TEST BARE noqa
*********************************************

Some text, again referring to the section: NEXT SECTION WITH PARAGRAPH
TO TEST BARE noqa.
"""
    assert result == expect
    assert 'next-section' not in getwarning(app.warning)


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_literalblock_warnings(app: SphinxTestApp) -> None:
    app.build()
    # --- check warning for literal block
    result = (app.outdir / 'literalblock.txt').read_text(encoding='utf8')
    expect = (
        '9. I18N WITH LITERAL BLOCK'
        '\n**************************\n'
        '\nCORRECT LITERAL BLOCK:\n'
        '\n   this is'
        '\n   literal block\n'
        '\nMISSING LITERAL BLOCK:\n'
        '\n<SYSTEM MESSAGE:'
    )
    assert result.startswith(expect)

    warnings = getwarning(app.warning)
    expected_warning_expr = (
        '.*/literalblock.txt:\\d+: WARNING: Literal block expected; none found.'
    )
    assert re.search(expected_warning_expr, warnings), (
        f'{expected_warning_expr!r} did not match {warnings!r}'
    )


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_definition_terms(app: SphinxTestApp) -> None:
    app.build()
    # --- definition terms: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/975,
    # https://github.com/sphinx-doc/sphinx/issues/2198, and
    # https://github.com/sphinx-doc/sphinx/issues/2205
    result = (app.outdir / 'definition_terms.txt').read_text(encoding='utf8')
    expect = (
        '13. I18N WITH DEFINITION TERMS'
        '\n******************************\n'
        '\nSOME TERM'
        '\n   THE CORRESPONDING DEFINITION\n'
        '\nSOME *TERM* WITH LINK'
        '\n   THE CORRESPONDING DEFINITION #2\n'
        '\nSOME **TERM** WITH : CLASSIFIER1 : CLASSIFIER2'
        '\n   THE CORRESPONDING DEFINITION\n'
        '\nSOME TERM WITH : CLASSIFIER[]'
        '\n   THE CORRESPONDING DEFINITION\n'
    )
    assert result == expect


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_glossary_term(app: SphinxTestApp) -> None:
    app.build()
    # --- glossary terms: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/1090
    result = (app.outdir / 'glossary_terms.txt').read_text(encoding='utf8')
    expect = r"""18. I18N WITH GLOSSARY TERMS
****************************

SOME NEW TERM
   THE CORRESPONDING GLOSSARY

SOME OTHER NEW TERM
   THE CORRESPONDING GLOSSARY #2

LINK TO *SOME NEW TERM*.

TRANSLATED GLOSSARY SHOULD BE SORTED BY TRANSLATED TERMS:

TRANSLATED TERM XXX
   DEFINE XXX

TRANSLATED TERM YYY
   DEFINE YYY

TRANSLATED TERM ZZZ
VVV
   DEFINE ZZZ
"""
    assert result == expect
    warnings = getwarning(app.warning)
    assert warnings.count('term not in glossary') == 1


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_glossary_term_inconsistencies(app: SphinxTestApp) -> None:
    app.build()
    # --- glossary term inconsistencies: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/1090
    result = (app.outdir / 'glossary_terms_inconsistency.txt').read_text(
        encoding='utf8'
    )
    expect = (
        '19. I18N WITH GLOSSARY TERMS INCONSISTENCY'
        '\n******************************************\n'
        '\n1. LINK TO *SOME NEW TERM*.\n'
        '\n2. LINK TO *TERM NOT IN GLOSSARY*.\n'
    )
    assert result == expect

    warnings = getwarning(app.warning)
    expected_warning_expr = (
        '.*/glossary_terms_inconsistency.txt:\\d+: '
        'WARNING: inconsistent term references in translated message.'
        " original: \\[':term:`Some term`', ':term:`Some other term`'\\],"
        " translated: \\[':term:`SOME NEW TERM`'\\] \\[i18n.inconsistent_references\\]\n"
    )
    assert re.search(expected_warning_expr, warnings), (
        f'{expected_warning_expr!r} did not match {warnings!r}'
    )
    expected_warning_expr = (
        '.*/glossary_terms_inconsistency.txt:\\d+:<translated>:1: '
        "WARNING: term not in glossary: 'TERM NOT IN GLOSSARY'"
    )
    assert re.search(expected_warning_expr, warnings), (
        f'{expected_warning_expr!r} did not match {warnings!r}'
    )


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_refs_reordered_no_warning(app: SphinxTestApp) -> None:
    app.build()
    # --- refs_reordered: verify no inconsistency warnings
    result = (app.outdir / 'refs_reordered.txt').read_text(encoding='utf8')
    # Verify the translation was applied
    assert 'MULTIPLE REFS REORDERED' in result
    assert 'SINGLE REF WITH TRANSLATED DISPLAY TEXT' in result

    warnings = getwarning(app.warning)
    # Should NOT have any inconsistent_references warnings for refs_reordered.txt
    unexpected_warning_expr = '.*/refs_reordered.txt.*inconsistent.*references'
    assert not re.search(unexpected_warning_expr, warnings), (
        f'Unexpected warning found: {warnings!r}'
    )


@sphinx_intl
@pytest.mark.sphinx('gettext', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_gettext')
def test_gettext_section(app: SphinxTestApp) -> None:
    app.build()
    # --- section
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'section.po')
    actual = read_po(app.outdir / 'section.pot')
    actual_msg_ids = {msg.id for msg in actual if msg.id}  # pyright: ignore[reportUnhashable]
    for expect_msg in (msg for msg in expect if msg.id):
        assert expect_msg.id in actual_msg_ids


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_section(app: SphinxTestApp) -> None:
    app.build()
    # --- section
    result = (app.outdir / 'section.txt').read_text(encoding='utf8')
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'section.po')
    for expect_msg in expect:
        if not expect_msg.id:
            continue
        assert isinstance(expect_msg.string, str)
        assert expect_msg.string in result


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_seealso(app: SphinxTestApp) -> None:
    app.build()
    # --- seealso
    result = (app.outdir / 'seealso.txt').read_text(encoding='utf8')
    expect = (
        '12. I18N WITH SEEALSO'
        '\n*********************\n'
        '\nSee also: SHORT TEXT 1\n'
        '\nSee also: LONG TEXT 1\n'
        '\nSee also:\n'
        '\n  SHORT TEXT 2\n'
        '\n  LONG TEXT 2\n'
    )
    assert result == expect


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_figure_captions(app: SphinxTestApp) -> None:
    app.build()
    # --- figure captions: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/940
    result = (app.outdir / 'figure.txt').read_text(encoding='utf8')
    expect = (
        '14. I18N WITH FIGURE CAPTION'
        '\n****************************\n'
        '\n   [image]MY CAPTION OF THE FIGURE\n'
        '\n   MY DESCRIPTION PARAGRAPH1 OF THE FIGURE.\n'
        '\n   MY DESCRIPTION PARAGRAPH2 OF THE FIGURE.\n'
        '\n'
        '\n14.1. FIGURE IN THE BLOCK'
        '\n=========================\n'
        '\nBLOCK\n'
        '\n      [image]MY CAPTION OF THE FIGURE\n'
        '\n      MY DESCRIPTION PARAGRAPH1 OF THE FIGURE.\n'
        '\n      MY DESCRIPTION PARAGRAPH2 OF THE FIGURE.\n'
        '\n'
        '\n'
        '14.2. IMAGE URL AND ALT\n'
        '=======================\n'
        '\n'
        '[image: I18N -> IMG][image]\n'
        '\n'
        '   [image: IMG -> I18N][image]\n'
        '\n'
        '\n'
        '14.3. IMAGE ON SUBSTITUTION\n'
        '===========================\n'
        '\n'
        '\n'
        '14.4. IMAGE UNDER NOTE\n'
        '======================\n'
        '\n'
        'Note:\n'
        '\n'
        '  [image: i18n under note][image]\n'
        '\n'
        '     [image: img under note][image]\n'
    )
    assert result == expect


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_rubric(app: SphinxTestApp) -> None:
    app.build()
    # --- rubric: regression test for pull request
    # https://github.com/sphinx-doc/sphinx/issues/190
    result = (app.outdir / 'rubric.txt').read_text(encoding='utf8')
    expect = (
        'I18N WITH RUBRIC'
        '\n****************\n'
        '\n-[ RUBRIC TITLE ]-\n'
        '\n'
        '\nRUBRIC IN THE BLOCK'
        '\n===================\n'
        '\nBLOCK\n'
        '\n   -[ RUBRIC TITLE ]-\n'
    )
    assert result == expect


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_docfields(app: SphinxTestApp) -> None:
    app.build()
    # --- docfields
    result = (app.outdir / 'docfields.txt').read_text(encoding='utf8')
    expect = (
        '21. I18N WITH DOCFIELDS'
        '\n***********************\n'
        '\nclass Cls1\n'
        '\n   Parameters:'
        '\n      **param** -- DESCRIPTION OF PARAMETER param\n'
        '\nclass Cls2\n'
        '\n   Parameters:'
        '\n      * **foo** -- DESCRIPTION OF PARAMETER foo\n'
        '\n      * **bar** -- DESCRIPTION OF PARAMETER bar\n'
        '\nclass Cls3(values)\n'
        '\n   Raises:'
        '\n      **ValueError** -- IF THE VALUES ARE OUT OF RANGE\n'
        '\nclass Cls4(values)\n'
        '\n   Raises:'
        '\n      * **TypeError** -- IF THE VALUES ARE NOT VALID\n'
        '\n      * **ValueError** -- IF THE VALUES ARE OUT OF RANGE\n'
        '\nclass Cls5\n'
        '\n   Returns:'
        '\n      A NEW "Cls3" INSTANCE\n'
    )
    assert result == expect


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_admonitions(app: SphinxTestApp) -> None:
    app.build()
    # --- admonitions
    # https://github.com/sphinx-doc/sphinx/issues/1206:
    # gettext did not translate admonition directive's title
    # see https://docutils.sourceforge.io/docs/ref/rst/directives.html#admonitions
    result = (app.outdir / 'admonitions.txt').read_text(encoding='utf8')
    directives = (
        'attention',
        'caution',
        'danger',
        'error',
        'hint',
        'important',
        'note',
        'tip',
        'warning',
        'admonition',
    )
    for d in directives:
        assert d.upper() + ' TITLE' in result
        assert d.upper() + ' BODY' in result

    # https://github.com/sphinx-doc/sphinx/issues/4938
    # `1. ` prefixed admonition title
    assert '1. ADMONITION TITLE' in result


@sphinx_intl
@pytest.mark.sphinx('gettext', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_gettext')
def test_gettext_toctree(app: SphinxTestApp) -> None:
    app.build()
    # --- toctree (index.rst)
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'index.po')
    actual = read_po(app.outdir / 'index.pot')
    actual_msg_ids = {msg.id for msg in actual if msg.id}  # pyright: ignore[reportUnhashable]
    for expect_msg in (msg for msg in expect if msg.id):
        assert expect_msg.id in actual_msg_ids
    # --- toctree (toctree.rst)
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'toctree.po')
    actual = read_po(app.outdir / 'toctree.pot')
    actual_msg_ids = {msg.id for msg in actual if msg.id}  # pyright: ignore[reportUnhashable]
    for expect_msg in (msg for msg in expect if msg.id):
        assert expect_msg.id in actual_msg_ids


@sphinx_intl
@pytest.mark.sphinx('gettext', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_gettext')
def test_gettext_table(app: SphinxTestApp) -> None:
    app.build()
    # --- toctree
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'table.po')
    actual = read_po(app.outdir / 'table.pot')
    actual_msg_ids = {msg.id for msg in actual if msg.id}  # pyright: ignore[reportUnhashable]
    for expect_msg in (msg for msg in expect if msg.id):
        assert expect_msg.id in actual_msg_ids


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_table(app: SphinxTestApp) -> None:
    app.build()
    # --- toctree
    result = (app.outdir / 'table.txt').read_text(encoding='utf8')
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'table.po')
    for expect_msg in expect:
        if not expect_msg.id:
            continue
        assert isinstance(expect_msg.string, str)
        assert expect_msg.string in result


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_toctree(app: SphinxTestApp) -> None:
    app.build()
    # --- toctree (index.rst)
    # Note: index.rst contains contents that is not shown in text.
    result = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert 'CONTENTS' in result
    assert 'TABLE OF CONTENTS' in result
    # --- toctree (toctree.rst)
    result = (app.outdir / 'toctree.txt').read_text(encoding='utf8')
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'toctree.po')
    for expect_msg in expect:
        if not expect_msg.id:
            continue
        assert isinstance(expect_msg.string, str)
        assert expect_msg.string in result


@sphinx_intl
@pytest.mark.sphinx('gettext', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_gettext')
def test_gettext_topic(app: SphinxTestApp) -> None:
    app.build()
    # --- topic
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'topic.po')
    actual = read_po(app.outdir / 'topic.pot')
    actual_msg_ids = {msg.id for msg in actual if msg.id}  # pyright: ignore[reportUnhashable]
    for expect_msg in (msg for msg in expect if msg.id):
        assert expect_msg.id in actual_msg_ids


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_topic(app: SphinxTestApp) -> None:
    app.build()
    # --- topic
    result = (app.outdir / 'topic.txt').read_text(encoding='utf8')
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'topic.po')
    for expect_msg in expect:
        if not expect_msg.id:
            continue
        assert isinstance(expect_msg.string, str)
        assert expect_msg.string in result


@sphinx_intl
@pytest.mark.sphinx('gettext', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_gettext')
def test_gettext_definition_terms(app: SphinxTestApp) -> None:
    app.build()
    # --- definition terms: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/2198,
    # https://github.com/sphinx-doc/sphinx/issues/2205
    expect = read_po(
        app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'definition_terms.po'
    )
    actual = read_po(app.outdir / 'definition_terms.pot')
    actual_msg_ids = {msg.id for msg in actual if msg.id}  # pyright: ignore[reportUnhashable]
    for expect_msg in (msg for msg in expect if msg.id):
        assert expect_msg.id in actual_msg_ids


@sphinx_intl
@pytest.mark.sphinx('gettext', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_gettext')
def test_gettext_glossary_terms(app: SphinxTestApp) -> None:
    app.build()
    # --- glossary terms: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/1090
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'glossary_terms.po')
    actual = read_po(app.outdir / 'glossary_terms.pot')
    actual_msg_ids = {msg.id for msg in actual if msg.id}  # pyright: ignore[reportUnhashable]
    for expect_msg in (msg for msg in expect if msg.id):
        assert expect_msg.id in actual_msg_ids
    warnings = app.warning.getvalue().replace(os.sep, '/')
    assert 'term not in glossary' not in warnings


@sphinx_intl
@pytest.mark.sphinx('gettext', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_gettext')
def test_gettext_glossary_term_inconsistencies(app: SphinxTestApp) -> None:
    app.build()
    # --- glossary term inconsistencies: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/1090
    expect = read_po(
        app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'glossary_terms_inconsistency.po'
    )
    actual = read_po(app.outdir / 'glossary_terms_inconsistency.pot')
    actual_msg_ids = {msg.id for msg in actual if msg.id}  # pyright: ignore[reportUnhashable]
    for expect_msg in (msg for msg in expect if msg.id):
        assert expect_msg.id in actual_msg_ids


@sphinx_intl
@pytest.mark.sphinx('gettext', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_gettext')
def test_gettext_literalblock(app: SphinxTestApp) -> None:
    app.build()
    # --- gettext builder always ignores ``only`` directive
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'literalblock.po')
    actual = read_po(app.outdir / 'literalblock.pot')
    actual_msg_ids = {msg.id for msg in actual if msg.id}  # pyright: ignore[reportUnhashable]
    for expect_msg in expect:
        if not expect_msg.id:
            continue
        assert isinstance(expect_msg.id, str)
        if len(expect_msg.id.splitlines()) == 1:
            # compare translations only labels
            assert expect_msg.id in actual_msg_ids
        else:
            pass  # skip code-blocks and literalblocks


@sphinx_intl
@pytest.mark.sphinx('gettext', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_gettext')
def test_gettext_buildr_ignores_only_directive(app: SphinxTestApp) -> None:
    app.build()
    # --- gettext builder always ignores ``only`` directive
    expect = read_po(app.srcdir / _CATALOG_LOCALE / 'LC_MESSAGES' / 'only.po')
    actual = read_po(app.outdir / 'only.pot')
    actual_msg_ids = {msg.id for msg in actual if msg.id}  # pyright: ignore[reportUnhashable]
    for expect_msg in (msg for msg in expect if msg.id):
        assert expect_msg.id in actual_msg_ids


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl', copy_test_root=True)
def test_node_translated_attribute(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'translation_progress.txt'])

    doctree = app.env.get_doctree('translation_progress')

    translated_nodes = sum(1 for _ in doctree.findall(NodeMatcher(translated=True)))
    assert translated_nodes == 10 + 1  # 10 lines + title

    untranslated_nodes = sum(1 for _ in doctree.findall(NodeMatcher(translated=False)))
    assert untranslated_nodes == 2 + 2 + 1  # 2 lines + 2 lines + substitution reference


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl', copy_test_root=True)
def test_translation_progress_substitution(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'translation_progress.txt'])

    doctree = app.env.get_doctree('translation_progress')

    # 11 out of 16 lines are translated
    assert extract_node(doctree, 0, 19, 0) == '68.75%'


@pytest.mark.sphinx(
    'html',
    testroot='intl',
    freshenv=True,
    confoverrides={
        'language': _CATALOG_LOCALE,
        'locale_dirs': ['.'],
        'gettext_compact': False,
        'translation_progress_classes': True,
    },
    copy_test_root=True,
)
def test_translation_progress_classes_true(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'translation_progress.txt'])

    doctree = app.env.get_doctree('translation_progress')

    # title
    assert 'translated' in extract_element(doctree, 0, 0)['classes']

    # translated lines
    assert 'translated' in extract_element(doctree, 0, 1)['classes']
    assert 'translated' in extract_element(doctree, 0, 2)['classes']
    assert 'translated' in extract_element(doctree, 0, 3)['classes']
    assert 'translated' in extract_element(doctree, 0, 4)['classes']
    assert 'translated' in extract_element(doctree, 0, 5)['classes']
    assert 'translated' in extract_element(doctree, 0, 6)['classes']
    assert 'translated' in extract_element(doctree, 0, 7)['classes']
    assert 'translated' in extract_element(doctree, 0, 8)['classes']

    assert extract_element(doctree, 0, 9)['classes'] == []  # comment node

    # idempotent
    assert 'translated' in extract_element(doctree, 0, 10)['classes']
    assert 'translated' in extract_element(doctree, 0, 11)['classes']

    assert extract_element(doctree, 0, 12)['classes'] == []  # comment node

    # untranslated
    assert 'untranslated' in extract_element(doctree, 0, 13)['classes']
    assert 'untranslated' in extract_element(doctree, 0, 14)['classes']

    assert extract_element(doctree, 0, 15)['classes'] == []  # comment node

    # missing
    assert 'untranslated' in extract_element(doctree, 0, 16)['classes']
    assert 'untranslated' in extract_element(doctree, 0, 17)['classes']

    assert extract_element(doctree, 0, 18)['classes'] == []  # comment node

    # substitution reference
    assert 'untranslated' in extract_element(doctree, 0, 19)['classes']

    assert isinstance(doctree[0], nodes.Element)
    assert len(doctree[0]) == 20


class _MockClock:
    """Object for mocking :func:`time.time_ns` (if needed).

    Use :meth:`sleep` to make this specific clock sleep for some time.
    """

    def time(self) -> int:
        """Nanosecond since 'fake' epoch."""
        raise NotImplementedError

    def sleep(self, ds: float) -> None:
        """Sleep *ds* seconds."""
        raise NotImplementedError


class _MockWindowsClock(_MockClock):
    """Object for mocking :func:`time.time_ns` on Windows platforms.

    The result is in 'nanoseconds' but with a microsecond resolution
    so that the division by 1_000 does not cause rounding issues.
    """

    def __init__(self) -> None:
        self.us: int = 0  # current microsecond 'tick'

    def time(self) -> int:
        ret = 1_000 * self.us
        self.us += 1
        return ret

    def sleep(self, ds: float) -> None:
        self.us += int(ds * 1e6)


class _MockUnixClock(_MockClock):
    """Object for mocking :func:`time.time_ns` on Unix platforms.

    Since nothing is needed for Unix platforms, this object acts as
    a proxy so that the API is the same as :class:`_MockWindowsClock`.
    """

    def time(self) -> int:
        return time.time_ns()

    def sleep(self, ds: float) -> None:
        time.sleep(ds)


@pytest.fixture
def mock_time_and_i18n() -> Iterator[tuple[pytest.MonkeyPatch, _MockClock]]:
    from sphinx.util.i18n import CatalogInfo

    # save the 'original' definition
    catalog_write_mo = CatalogInfo.write_mo

    def mock_write_mo(self: CatalogInfo, locale: str, use_fuzzy: bool = False) -> None:
        catalog_write_mo(self, locale, use_fuzzy)
        # ensure that the .mo file being written has a correct fake timestamp
        _set_mtime_ns(self.mo_path, time.time_ns())

    # see: https://github.com/pytest-dev/pytest/issues/363
    # see: https://github.com/astral-sh/ty/issues/1787
    with pytest.MonkeyPatch.context() as mock:  # ty: ignore[missing-argument]
        clock: _MockClock
        if os.name == 'posix':
            clock = _MockUnixClock()
        else:
            # When using pytest.mark.parametrize() to emulate test repetition,
            # the teardown phase on Windows fails due to an error apparently in
            # the colorama.ansitowin32 module, so we forcibly disable colors.
            mock.setenv('NO_COLOR', '1')
            # apply the patch only for Windows
            clock = _MockWindowsClock()
            mock.setattr('time.time_ns', clock.time)
            # Use clock.sleep() to emulate time.sleep() but do not try
            # to mock the latter since this might break other libraries.
            mock.setattr('sphinx.util.i18n.CatalogInfo.write_mo', mock_write_mo)
        yield mock, clock


# use the same testroot as 'gettext' since the latter contains less PO files
@sphinx_intl
@pytest.mark.sphinx(
    'dummy',
    testroot='builder-gettext-dont-rebuild-mo',
    freshenv=True,
    copy_test_root=True,
)
def test_dummy_should_rebuild_mo(
    mock_time_and_i18n: tuple[pytest.MonkeyPatch, _MockClock],
    make_app: Callable[..., SphinxTestApp],
    app_params: _app_params,
) -> None:
    mock, clock = mock_time_and_i18n
    assert os.name == 'posix' or clock.time() == 0

    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    po_path, mo_path = _get_bom_intl_path(app.srcdir)

    # creation time of the those files (order does not matter)
    bom_rst = app.srcdir / 'bom.rst'
    bom_rst_time = time.time_ns()

    index_rst = app.srcdir / 'index.rst'
    index_rst_time = time.time_ns()
    po_time = time.time_ns()

    # patch the 'creation time' of the source files
    assert _set_mtime_ns(po_path, po_time) == po_time
    assert _set_mtime_ns(bom_rst, bom_rst_time) == bom_rst_time
    assert _set_mtime_ns(index_rst, index_rst_time) == index_rst_time

    assert not mo_path.exists()
    # when writing mo files, the counter is updated by calling
    # patch_write_mo which is called to create .mo files (and
    # thus the timestamp of the files are not those given by
    # the OS but our fake ones)
    app.build()
    assert mo_path.exists()
    # Do a real sleep on POSIX, or simulate a sleep on Windows
    # to ensure that calls to time.time_ns() remain consistent.
    clock.sleep(0.1 if os.name == 'posix' else 1)

    # check that the source files were not modified
    assert bom_rst.stat().st_mtime_ns == bom_rst_time
    assert index_rst.stat().st_mtime_ns == index_rst_time
    # check that the 'bom' document is discovered after the .mo
    # file has been written on the disk (i.e., read_doc() is called
    # after the creation of the .mo files)
    assert app.env.all_docs['bom'] > mo_path.stat().st_mtime_ns // 1000

    # Since it is after the build, the number of documents to be updated is 0
    update_targets = _get_update_targets(app)
    assert update_targets[1] == set()
    # When rewriting the timestamp of mo file, the number of documents to be
    # updated will be changed.
    new_mo_time = time.time_ns()
    assert _set_mtime_ns(mo_path, new_mo_time) == new_mo_time
    update_targets = _get_update_targets(app)
    assert update_targets[1] == {'bom'}
    mock.undo()  # explicit call since it's not a context

    # remove all sources for the next test
    shutil.rmtree(app.srcdir, ignore_errors=True)
    time.sleep(0.1 if os.name == 'posix' else 0.5)  # real sleep


@sphinx_intl
@pytest.mark.sphinx(
    'gettext',
    testroot='builder-gettext-dont-rebuild-mo',
    freshenv=True,
    copy_test_root=True,
)
def test_gettext_dont_rebuild_mo(
    mock_time_and_i18n: tuple[pytest.MonkeyPatch, _MockClock], app: SphinxTestApp
) -> None:
    mock, clock = mock_time_and_i18n
    assert os.name == 'posix' or clock.time() == 0

    assert app.srcdir.exists()

    # patch the 'creation time' of the source files
    bom_rst = app.srcdir / 'bom.rst'
    bom_rst_time = time.time_ns()
    assert _set_mtime_ns(bom_rst, bom_rst_time) == bom_rst_time

    index_rst = app.srcdir / 'index.rst'
    index_rst_time = time.time_ns()
    assert _set_mtime_ns(index_rst, index_rst_time) == index_rst_time

    # phase 1: create fake MO file in the src directory
    po_path, mo_path = _get_bom_intl_path(app.srcdir)
    write_mo(mo_path, read_po(po_path))
    po_time = time.time_ns()
    assert _set_mtime_ns(po_path, po_time) == po_time

    # phase 2: build document with gettext builder.
    # The mo file in the srcdir directory is retained.
    app.build()
    # Do a real sleep on POSIX, or simulate a sleep on Windows
    # to ensure that calls to time.time_ns() remain consistent.
    clock.sleep(0.5 if os.name == 'posix' else 1)
    # Since it is after the build, the number of documents to be updated is 0
    update_targets = _get_update_targets(app)
    assert update_targets[1] == set()
    # Even if the timestamp of the mo file is updated, the number of documents
    # to be updated is 0. gettext builder does not rebuild because of mo update.
    new_mo_time = time.time_ns()
    assert _set_mtime_ns(mo_path, new_mo_time) == new_mo_time
    update_targets = _get_update_targets(app)
    assert update_targets[1] == set()
    mock.undo()  # remove the patch

    # remove all sources for the next test
    shutil.rmtree(app.srcdir, ignore_errors=True)
    time.sleep(0.1 if os.name == 'posix' else 0.5)  # real sleep


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_html_meta(app: SphinxTestApp) -> None:
    app.build()
    # --- test for meta
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    expected_expr = (
        '<meta content="TESTDATA FOR I18N" name="description" translated="True" />'
    )
    assert expected_expr in result
    expected_expr = (
        '<meta content="I18N, SPHINX, MARKUP" name="keywords" translated="True" />'
    )
    assert expected_expr in result
    expected_expr = '<p class="caption" role="heading"><span class="caption-text">HIDDEN TOC</span></p>'
    assert expected_expr in result


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_html_footnotes(app: SphinxTestApp) -> None:
    app.build()
    # --- test for
    # https://github.com/sphinx-doc/sphinx/issues/955
    # cant-build-html-with-footnotes-when-using
    # expect no error by build
    (app.outdir / 'footnote.html').read_text(encoding='utf8')


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_html_undefined_refs(app: SphinxTestApp) -> None:
    app.build()
    # --- links to undefined reference
    result = (app.outdir / 'refs_inconsistency.html').read_text(encoding='utf8')

    expected_expr = (
        '<a class="reference external" href="https://www.example.com">reference</a>'
    )
    assert len(re.findall(expected_expr, result)) == 2

    expected_expr = '<a class="reference internal" href="#reference">reference</a>'
    assert len(re.findall(expected_expr, result)) == 0

    expected_expr = (
        '<a class="reference internal" '
        'href="#i18n-with-refs-inconsistency">I18N WITH '
        'REFS INCONSISTENCY</a>'
    )
    assert len(re.findall(expected_expr, result)) == 1


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_html_index_entries(app: SphinxTestApp) -> None:
    app.build()
    # --- index entries: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/976
    result = (app.outdir / 'genindex.html').read_text(encoding='utf8')

    def wrap(tag: str, keyword: str) -> str:
        start_tag = '<%s[^>]*>' % tag
        end_tag = '</%s>' % tag
        return rf'{start_tag}\s*{keyword}\s*{end_tag}'

    def wrap_nest(parenttag: str, childtag: str, keyword: str) -> str:
        start_tag1 = f'<{parenttag}[^>]*>'
        start_tag2 = f'<{childtag}[^>]*>'
        return rf'{start_tag1}\s*{keyword}\s*{start_tag2}'

    expected_exprs = [
        wrap('h2', 'Symbols'),
        wrap('h2', 'C'),
        wrap('h2', 'E'),
        wrap('h2', 'F'),
        wrap('h2', 'M'),
        wrap('h2', 'N'),
        wrap('h2', 'R'),
        wrap('h2', 'S'),
        wrap('h2', 'T'),
        wrap('h2', 'V'),
        wrap('a', 'NEWSLETTER'),
        wrap('a', 'MAILING LIST'),
        wrap('a', 'RECIPIENTS LIST'),
        wrap('a', 'FIRST SECOND'),
        wrap('a', 'SECOND THIRD'),
        wrap('a', 'THIRD, FIRST'),
        wrap_nest('li', 'ul', 'ENTRY'),
        wrap_nest('li', 'ul', 'SEE'),
    ]
    for expr in expected_exprs:
        assert re.search(expr, result, re.MULTILINE), (
            f'{expr!r} did not match {result!r}'
        )


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_html_versionchanges(app: SphinxTestApp) -> None:
    app.build()
    # --- versionchanges
    result = (app.outdir / 'versionchange.html').read_text(encoding='utf8')

    def get_content(result: str, name: str) -> str:
        matched = re.search(rf'<div class="{name}">\n*(.*?)</div>', result, re.DOTALL)
        if matched:
            return matched.group(1)
        return ''

    expect1 = (
        """<p><span class="versionmodified deprecated">Deprecated since version 1.0: </span>"""
        """THIS IS THE <em>FIRST</em> PARAGRAPH OF VERSION-DEPRECATED.</p>\n"""
        """<p>THIS IS THE <em>SECOND</em> PARAGRAPH OF VERSION-DEPRECATED.</p>\n"""
    )
    matched_content = get_content(result, 'deprecated')
    assert matched_content == expect1

    expect2 = (
        """<p><span class="versionmodified added">Added in version 1.0: </span>"""
        """THIS IS THE <em>FIRST</em> PARAGRAPH OF VERSION-ADDED.</p>\n"""
    )
    matched_content = get_content(result, 'versionadded')
    assert matched_content == expect2

    expect3 = (
        """<p><span class="versionmodified changed">Changed in version 1.0: </span>"""
        """THIS IS THE <em>FIRST</em> PARAGRAPH OF VERSION-CHANGED.</p>\n"""
    )
    matched_content = get_content(result, 'versionchanged')
    assert matched_content == expect3

    expect4 = (
        """<p><span class="versionmodified removed">Removed in version 1.0: </span>"""
        """THIS IS THE <em>FIRST</em> PARAGRAPH OF VERSION-REMOVED.</p>\n"""
    )
    matched_content = get_content(result, 'versionremoved')
    assert matched_content == expect4


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_html_docfields(app: SphinxTestApp) -> None:
    app.build()
    # --- docfields
    # expect no error by build
    (app.outdir / 'docfields.html').read_text(encoding='utf8')


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_html_template(app: SphinxTestApp) -> None:
    app.build()
    # --- gettext template
    result = (app.outdir / 'contents.html').read_text(encoding='utf8')
    assert 'WELCOME' in result
    assert 'SPHINX 2013.120' in result


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_html_rebuild_mo(app: SphinxTestApp) -> None:
    app.build()
    # --- rebuild by .mo mtime
    app.build()
    _, updated, _ = _get_update_targets(app)
    assert updated == set()

    _, bom_file = _get_bom_intl_path(app.srcdir)
    old_mtime = bom_file.stat().st_mtime
    new_mtime = old_mtime + (dt := 5)
    os.utime(bom_file, (new_mtime, new_mtime))
    assert old_mtime + dt == new_mtime, (old_mtime + dt, new_mtime)
    _, updated, _ = _get_update_targets(app)
    assert updated == {'bom'}


@sphinx_intl
@pytest.mark.sphinx('xml', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_xml_footnotes(app: SphinxTestApp) -> None:
    app.build()
    # --- footnotes: regression test for fix
    # https://github.com/sphinx-doc/sphinx/issues/955,
    # https://github.com/sphinx-doc/sphinx/issues/1176
    et = etree_parse(app.outdir / 'footnote.xml')
    secs = et.findall('section')

    para0 = secs[0].findall('paragraph')
    assert_elem(
        para0[0],
        texts=[
            'I18N WITH FOOTNOTE',
            'INCLUDE THIS CONTENTS',
            '2',
            '[ref]',
            '1',
            '100',
            '*',
            '. SECOND FOOTNOTE_REF',
            '100',
            '.',
        ],
        refs=['i18n-with-footnote', 'ref'],
    )

    # check node_id for footnote_references which refer same footnote
    # See: https://github.com/sphinx-doc/sphinx/issues/3002
    assert para0[0][4].text == para0[0][6].text == '100'
    assert para0[0][4].attrib['ids'] != para0[0][6].attrib['ids']

    footnote0 = secs[0].findall('footnote')
    assert_elem(
        footnote0[0],
        texts=['1', 'THIS IS A AUTO NUMBERED FOOTNOTE.'],
        refs=None,
        names=['1'],
    )
    assert_elem(
        footnote0[1],
        texts=['100', 'THIS IS A NUMBERED FOOTNOTE.'],
        refs=None,
        names=['100'],
    )
    assert_elem(
        footnote0[2],
        texts=['2', 'THIS IS A AUTO NUMBERED NAMED FOOTNOTE.'],
        refs=None,
        names=['named'],
    )
    assert_elem(
        footnote0[3],
        texts=['*', 'THIS IS A AUTO SYMBOL FOOTNOTE.'],
        refs=None,
        names=None,
    )

    citation0 = secs[0].findall('citation')
    assert_elem(
        citation0[0],
        texts=['ref', 'THIS IS A NAMED FOOTNOTE.'],
        refs=None,
        names=['ref'],
    )

    warnings = getwarning(app.warning)
    warning_expr = '.*/footnote.xml:\\d*: SEVERE: Duplicate ID: ".*".\n'
    assert not re.search(warning_expr, warnings), (
        f'{warning_expr!r} did match {warnings!r}'
    )


@sphinx_intl
@pytest.mark.sphinx('xml', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_xml_footnote_backlinks(app: SphinxTestApp) -> None:
    app.build()
    # --- footnote backlinks: i18n test for
    # https://github.com/sphinx-doc/sphinx/issues/1058
    et = etree_parse(app.outdir / 'footnote.xml')
    secs = et.findall('section')

    para0 = secs[0].findall('paragraph')
    refs0 = para0[0].findall('footnote_reference')
    refid2id = {r.attrib.get('refid'): r.attrib.get('ids') for r in refs0}

    footnote0 = secs[0].findall('footnote')
    for footnote in footnote0:
        ids = footnote.attrib.get('ids')
        backrefs = footnote.attrib['backrefs'].split()
        assert refid2id[ids] in backrefs


@sphinx_intl
@pytest.mark.sphinx('xml', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_xml_refs_in_python_domain(app: SphinxTestApp) -> None:
    app.build()
    # --- refs in the Python domain
    et = etree_parse(app.outdir / 'refs_python_domain.xml')
    secs = et.findall('section')

    # regression test for fix
    # https://github.com/sphinx-doc/sphinx/issues/1363
    para0 = secs[0].findall('paragraph')
    assert_elem(
        para0[0],
        texts=['SEE THIS DECORATOR:', 'sensitive_variables()', '.'],
        refs=['sensitive.sensitive_variables'],
    )


@sphinx_intl
@pytest.mark.sphinx('xml', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_xml_keep_external_links(app: SphinxTestApp) -> None:
    app.build()
    # --- keep external links: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/1044
    et = etree_parse(app.outdir / 'external_links.xml')
    secs = et.findall('section')

    para0 = secs[0].findall('paragraph')
    # external link check
    assert_elem(
        para0[0],
        texts=['EXTERNAL LINK TO', 'Python', '.'],
        refs=['https://python.org/index.html'],
    )

    # internal link check
    assert_elem(
        para0[1],
        texts=['EXTERNAL LINKS', 'IS INTERNAL LINK.'],
        refs=['i18n-with-external-links'],
    )

    # inline link check
    assert_elem(
        para0[2],
        texts=['INLINE LINK BY', 'THE SPHINX SITE', '.'],
        refs=['https://sphinx-doc.org'],
    )

    # unnamed link check
    assert_elem(
        para0[3],
        texts=['UNNAMED', 'LINK', '.'],
        refs=['https://google.com'],
    )

    # link target swapped translation
    para1 = secs[1].findall('paragraph')
    assert_elem(
        para1[0],
        texts=['LINK TO', 'external2', 'AND', 'external1', '.'],
        refs=['https://www.google.com/external2', 'https://www.google.com/external1'],
    )
    assert_elem(
        para1[1],
        texts=['LINK TO', 'THE PYTHON SITE', 'AND', 'THE SPHINX SITE', '.'],
        refs=['https://python.org', 'https://sphinx-doc.org'],
    )

    # multiple references in the same line
    para2 = secs[2].findall('paragraph')
    assert_elem(
        para2[0],
        texts=[
            'LINK TO',
            'EXTERNAL LINKS',
            ',',
            'Python',
            ',',
            'THE SPHINX SITE',
            ',',
            'UNNAMED',
            'AND',
            'THE PYTHON SITE',
            '.',
        ],
        refs=[
            'i18n-with-external-links',
            'https://python.org/index.html',
            'https://sphinx-doc.org',
            'https://google.com',
            'https://python.org',
        ],
    )


@sphinx_intl
@pytest.mark.sphinx('xml', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_xml_role_xref(app: SphinxTestApp) -> None:
    app.build()
    # --- role xref: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/1090,
    # https://github.com/sphinx-doc/sphinx/issues/1193
    et = etree_parse(app.outdir / 'role_xref.xml')
    sec1, sec2 = et.findall('section')

    (para1,) = sec1.findall('paragraph')
    assert_elem(
        para1,
        texts=[
            'LINK TO',
            "I18N ROCK'N ROLE XREF",
            ',',
            'CONTENTS',
            ',',
            'SOME NEW TERM',
            '.',
        ],
        refs=['i18n-role-xref', 'index', 'glossary_terms#term-Some-term'],
    )

    (sec1_1,) = sec1.findall('section')
    (title,) = sec1_1.findall('title')
    assert_elem(
        title,
        texts=[
            'LINK TO',
            "I18N ROCK'N ROLE XREF",
            ',',
            'CONTENTS',
            ',',
            'SOME NEW TERM',
            '.',
        ],
        refs=['i18n-role-xref', 'index', 'glossary_terms#term-Some-term'],
    )

    para2 = sec2.findall('paragraph')
    assert_elem(
        para2[0],
        texts=['LINK TO', 'SOME OTHER NEW TERM', 'AND', 'SOME NEW TERM', '.'],
        refs=['glossary_terms#term-Some-other-term', 'glossary_terms#term-Some-term'],
    )
    assert_elem(
        para2[1],
        texts=[
            'LINK TO',
            'LABEL',
            'AND',
            'SAME TYPE LINKS',
            'AND',
            'SAME TYPE LINKS',
            '.',
        ],
        refs=['i18n-role-xref', 'same-type-links', 'same-type-links'],
    )
    assert_elem(
        para2[2],
        texts=['LINK TO', 'I18N WITH GLOSSARY TERMS', 'AND', 'CONTENTS', '.'],
        refs=['glossary_terms', 'index'],
    )
    assert_elem(
        para2[3],
        texts=['LINK TO', '--module', 'AND', '-m', '.'],
        refs=['cmdoption-module', 'cmdoption-m'],
    )
    assert_elem(
        para2[4],
        texts=['LINK TO', 'env2', 'AND', 'env1', '.'],
        refs=['envvar-env2', 'envvar-env1'],
    )
    # TODO: how do I link token role to productionlist?
    assert_elem(
        para2[5],
        texts=['LINK TO', 'token2', 'AND', 'token1', '.'],
        refs=[],
    )
    assert_elem(
        para2[6],
        texts=['LINK TO', 'same-type-links', 'AND', 'i18n-role-xref', '.'],
        refs=['same-type-links', 'i18n-role-xref'],
    )


@sphinx_intl
@pytest.mark.sphinx('xml', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_xml_warnings(app: SphinxTestApp) -> None:
    app.build()
    # warnings
    warnings = getwarning(app.warning)
    assert warnings.count('term not in glossary') == 1
    assert 'undefined label' not in warnings
    assert 'unknown document' not in warnings


@sphinx_intl
@pytest.mark.sphinx('xml', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_xml_label_targets(app: SphinxTestApp) -> None:
    app.build()
    # --- label targets: regression test for
    # https://github.com/sphinx-doc/sphinx/issues/1193,
    # https://github.com/sphinx-doc/sphinx/issues/1265
    et = etree_parse(app.outdir / 'label_target.xml')
    secs = et.findall('section')

    para0 = secs[0].findall('paragraph')
    assert_elem(
        para0[0],
        texts=[
            'X SECTION AND LABEL',
            'POINT TO',
            'implicit-target',
            'AND',
            'X SECTION AND LABEL',
            'POINT TO',
            'section-and-label',
            '.',
        ],
        refs=['implicit-target', 'section-and-label'],
    )

    para1 = secs[1].findall('paragraph')
    assert_elem(
        para1[0],
        texts=[
            'X EXPLICIT-TARGET',
            'POINT TO',
            'explicit-target',
            'AND',
            'X EXPLICIT-TARGET',
            'POINT TO DUPLICATED ID LIKE',
            'id1',
            '.',
        ],
        refs=['explicit-target', 'id1'],
    )

    para2 = secs[2].findall('paragraph')
    assert_elem(
        para2[0],
        texts=['X IMPLICIT SECTION NAME', 'POINT TO', 'implicit-section-name', '.'],
        refs=['implicit-section-name'],
    )

    sec2 = secs[2].findall('section')

    para2_0 = sec2[0].findall('paragraph')
    assert_elem(
        para2_0[0],
        texts=['`X DUPLICATED SUB SECTION`_', 'IS BROKEN LINK.'],
        refs=[],
    )

    para3 = secs[3].findall('paragraph')
    assert_elem(
        para3[0],
        texts=[
            'X',
            'bridge label',
            'IS NOT TRANSLATABLE BUT LINKED TO TRANSLATED SECTION TITLE.',
        ],
        refs=['label-bridged-target-section'],
    )
    assert_elem(
        para3[1],
        texts=[
            'X',
            'bridge label',
            'POINT TO',
            'LABEL BRIDGED TARGET SECTION',
            'AND',
            'bridge label2',
            'POINT TO',
            'SECTION AND LABEL',
            '. THE SECOND APPEARED',
            'bridge label2',
            'POINT TO CORRECT TARGET.',
        ],
        refs=['label-bridged-target-section', 'section-and-label', 'section-and-label'],
    )


@sphinx_intl
@pytest.mark.sphinx('xml', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_xml_strange_markup(app: SphinxTestApp) -> None:
    app.build()
    et = etree_parse(app.outdir / 'markup.xml')
    secs = et.findall('section')

    (subsec1,) = secs[0].findall('section')
    (title1,) = subsec1.findall('title')
    assert_elem(title1, texts=['1. TITLE STARTING WITH 1.'])


@sphinx_intl
@pytest.mark.sphinx('html', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_additional_targets_should_not_be_translated(app: SphinxTestApp) -> None:
    if tuple(map(int, pygments.__version__.split('.')[:2])) >= (2, 19):
        sp = '<span class="w"> </span>'
    else:
        sp = ' '

    app.build()
    # [literalblock.txt]
    result = (app.outdir / 'literalblock.html').read_text(encoding='utf8')

    # title should be translated
    expected_expr = 'CODE-BLOCKS'
    assert_count(expected_expr, result, 2)

    # ruby code block should not be translated but be highlighted
    expected_expr = """<span class="s1">&#39;result&#39;</span>"""
    assert_count(expected_expr, result, 1)

    # C code block without lang should not be translated and *ruby* highlighted
    expected_expr = """<span class="c1">#include &lt;stdlib.h&gt;</span>"""
    assert_count(expected_expr, result, 1)

    # C code block with lang should not be translated but be *C* highlighted
    expected_expr = (
        """<span class="cp">#include</span>"""
        """<span class="w"> </span>"""
        """<span class="cpf">&lt;stdio.h&gt;</span>"""
    )
    assert_count(expected_expr, result, 1)

    # literal block in list item should not be translated
    expected_expr = (
        """<span class="n">literal</span>"""
        """<span class="o">-</span>"""
        """<span class="n">block</span>\n"""
        """<span class="k">in</span>"""
        """<span class="w"> </span>"""
        """<span class="n">list</span>"""
    )
    assert_count(expected_expr, result, 1)

    # doctest block should not be translated but be highlighted
    expected_expr = (
        """<span class="gp">&gt;&gt;&gt; </span>"""
        f"""<span class="kn">import</span>{sp}<span class="nn">sys</span>  """
        """<span class="c1"># sys importing</span>"""
    )
    assert_count(expected_expr, result, 1)

    # [raw.txt]

    result = (app.outdir / 'raw.html').read_text(encoding='utf8')

    # raw block should not be translated
    expected_expr = """<iframe src="https://sphinx-doc.org"></iframe></section>"""
    assert_count(expected_expr, result, 1)

    # [figure.txt]

    result = (app.outdir / 'figure.html').read_text(encoding='utf8')

    # src for image block should not be translated (alt is translated)
    expected_expr = """<img alt="I18N -&gt; IMG" src="_images/i18n.png" />"""
    assert_count(expected_expr, result, 1)

    # src for figure block should not be translated (alt is translated)
    expected_expr = """<img alt="IMG -&gt; I18N" src="_images/img.png" />"""
    assert_count(expected_expr, result, 1)


@sphinx_intl
@pytest.mark.sphinx(
    'html',
    testroot='intl',
    srcdir='test_additional_targets_should_be_translated',
    confoverrides={
        'language': _CATALOG_LOCALE,
        'locale_dirs': ['.'],
        'gettext_compact': False,
        'gettext_additional_targets': [
            'index',
            'literal-block',
            'doctest-block',
            'raw',
            'image',
        ],
    },
)
def test_additional_targets_should_be_translated(app: SphinxTestApp) -> None:
    if tuple(map(int, pygments.__version__.split('.')[:2])) >= (2, 19):
        sp = '<span class="w"> </span>'
    else:
        sp = ' '

    app.build()
    # [literalblock.txt]
    result = (app.outdir / 'literalblock.html').read_text(encoding='utf8')

    # basic literal block should be translated
    expected_expr = (
        '<span class="n">THIS</span> <span class="n">IS</span>\n'
        '<span class="n">LITERAL</span> <span class="n">BLOCK</span>'
    )
    assert_count(expected_expr, result, 1)

    # literalinclude should be translated
    expected_expr = '<span class="s2">&quot;HTTPS://SPHINX-DOC.ORG&quot;</span>'
    assert_count(expected_expr, result, 1)

    # title should be translated
    expected_expr = 'CODE-BLOCKS'
    assert_count(expected_expr, result, 2)

    # ruby code block should be translated and be highlighted
    expected_expr = """<span class="s1">&#39;RESULT&#39;</span>"""
    assert_count(expected_expr, result, 1)

    # C code block without lang should be translated and *ruby* highlighted
    expected_expr = """<span class="c1">#include &lt;STDLIB.H&gt;</span>"""
    assert_count(expected_expr, result, 1)

    # C code block with lang should be translated and be *C* highlighted
    expected_expr = (
        """<span class="cp">#include</span>"""
        """<span class="w"> </span>"""
        """<span class="cpf">&lt;STDIO.H&gt;</span>"""
    )
    assert_count(expected_expr, result, 1)

    # literal block in list item should be translated
    expected_expr = (
        """<span class="no">LITERAL</span>"""
        """<span class="o">-</span>"""
        """<span class="no">BLOCK</span>\n"""
        """<span class="no">IN</span>"""
        """<span class="w"> </span>"""
        """<span class="no">LIST</span>"""
    )
    assert_count(expected_expr, result, 1)

    # doctest block should not be translated but be highlighted
    expected_expr = (
        """<span class="gp">&gt;&gt;&gt; </span>"""
        f"""<span class="kn">import</span>{sp}<span class="nn">sys</span>  """
        """<span class="c1"># SYS IMPORTING</span>"""
    )
    assert_count(expected_expr, result, 1)

    # 'noqa' comments should remain in literal blocks.
    assert_count('#noqa', result, 1)

    # [raw.txt]

    result = (app.outdir / 'raw.html').read_text(encoding='utf8')

    # raw block should be translated
    expected_expr = """<iframe src="HTTPS://SPHINX-DOC.ORG"></iframe></section>"""
    assert_count(expected_expr, result, 1)

    # [figure.txt]

    result = (app.outdir / 'figure.html').read_text(encoding='utf8')

    # alt and src for image block should be translated
    expected_expr = """<img alt="I18N -&gt; IMG" src="_images/img.png" />"""
    assert_count(expected_expr, result, 1)

    # alt and src for figure block should be translated
    expected_expr = """<img alt="IMG -&gt; I18N" src="_images/i18n.png" />"""
    assert_count(expected_expr, result, 1)


@pytest.mark.sphinx(
    'html',
    testroot='intl_substitution_definitions',
    confoverrides={
        'language': _CATALOG_LOCALE,
        'locale_dirs': ['.'],
        'gettext_compact': False,
        'gettext_additional_targets': [
            'index',
            'literal-block',
            'doctest-block',
            'raw',
            'image',
        ],
    },
    copy_test_root=True,
)
def test_additional_targets_should_be_translated_substitution_definitions(
    app: SphinxTestApp,
) -> None:
    app.build(force_all=True)

    # [prolog_epilog_substitution.txt]

    result = (app.outdir / 'prolog_epilog_substitution.html').read_text(encoding='utf8')

    # alt and src for image block should be translated
    expected_expr = """<img alt="SUBST_PROLOG_2 TRANSLATED" src="_images/i18n.png" />"""
    assert_count(expected_expr, result, 1)

    # alt and src for image block should be translated
    expected_expr = """<img alt="SUBST_EPILOG_2 TRANSLATED" src="_images/img.png" />"""
    assert_count(expected_expr, result, 1)


@sphinx_intl
@pytest.mark.sphinx('text', testroot='intl')
@pytest.mark.test_params(shared_result='test_intl_basic')
def test_text_references(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'refs.txt'])

    warnings = app.warning.getvalue().replace(os.sep, '/')
    warning_expr = 'refs.txt:\\d+: ERROR: Unknown target name:'
    assert_count(warning_expr, warnings, 0)


@pytest.mark.sphinx(
    'text',
    testroot='intl_substitution_definitions',
    confoverrides={
        'language': _CATALOG_LOCALE,
        'locale_dirs': ['.'],
        'gettext_compact': False,
    },
    copy_test_root=True,
)
def test_text_prolog_epilog_substitution(app: SphinxTestApp) -> None:
    app.build()

    result = (app.outdir / 'prolog_epilog_substitution.txt').read_text(encoding='utf8')

    assert result == (
        """\
1. I18N WITH PROLOGUE AND EPILOGUE SUBSTITUTIONS
************************************************

THIS IS CONTENT THAT CONTAINS prologue substitute text.

SUBSTITUTED IMAGE [image: SUBST_PROLOG_2 TRANSLATED][image] HERE.

THIS IS CONTENT THAT CONTAINS epilogue substitute text.

SUBSTITUTED IMAGE [image: SUBST_EPILOG_2 TRANSLATED][image] HERE.
"""
    )


@pytest.mark.usefixtures('_http_teapot')
@pytest.mark.sphinx(
    'dummy',
    testroot='images',
    srcdir='test_intl_images',
    confoverrides={'language': _CATALOG_LOCALE},
)
def test_image_glob_intl(app: SphinxTestApp) -> None:
    app.build()

    # index.rst
    doctree = app.env.get_doctree('index')
    assert_node(
        extract_node(doctree, 0, 1),
        nodes.image,
        uri='rimg.xx.png',
        candidates={'*': 'rimg.xx.png'},
    )

    assert isinstance(extract_node(doctree, 0, 2), nodes.figure)
    assert_node(
        extract_node(doctree, 0, 2, 0),
        nodes.image,
        uri='rimg.xx.png',
        candidates={'*': 'rimg.xx.png'},
    )

    assert_node(
        extract_node(doctree, 0, 3),
        nodes.image,
        uri='img.*',
        candidates={
            'application/pdf': 'img.pdf',
            'image/gif': 'img.gif',
            'image/png': 'img.png',
        },
    )

    assert isinstance(extract_node(doctree, 0, 4), nodes.figure)
    assert_node(
        extract_node(doctree, 0, 4, 0),
        nodes.image,
        uri='img.*',
        candidates={
            'application/pdf': 'img.pdf',
            'image/gif': 'img.gif',
            'image/png': 'img.png',
        },
    )

    # subdir/index.rst
    doctree = app.env.get_doctree('subdir/index')
    assert_node(
        extract_node(doctree, 0, 1),
        nodes.image,
        uri='subdir/rimg.xx.png',
        candidates={'*': 'subdir/rimg.xx.png'},
    )

    assert_node(
        extract_node(doctree, 0, 2),
        nodes.image,
        uri='subdir/svgimg.*',
        candidates={
            'application/pdf': 'subdir/svgimg.pdf',
            'image/svg+xml': 'subdir/svgimg.xx.svg',
        },
    )

    assert isinstance(extract_node(doctree, 0, 3), nodes.figure)
    assert_node(
        extract_node(doctree, 0, 3, 0),
        nodes.image,
        uri='subdir/svgimg.*',
        candidates={
            'application/pdf': 'subdir/svgimg.pdf',
            'image/svg+xml': 'subdir/svgimg.xx.svg',
        },
    )


@pytest.mark.usefixtures('_http_teapot')
@pytest.mark.sphinx(
    'dummy',
    testroot='images',
    srcdir='test_intl_images',
    confoverrides={
        'language': _CATALOG_LOCALE,
        'figure_language_filename': '{root}{ext}.{language}',
    },
)
def test_image_glob_intl_using_figure_language_filename(app: SphinxTestApp) -> None:
    app.build()

    # index.rst
    doctree = app.env.get_doctree('index')
    assert_node(
        extract_node(doctree, 0, 1),
        nodes.image,
        uri='rimg.png.xx',
        candidates={'*': 'rimg.png.xx'},
    )

    assert isinstance(extract_node(doctree, 0, 2), nodes.figure)
    assert_node(
        extract_node(doctree, 0, 2, 0),
        nodes.image,
        uri='rimg.png.xx',
        candidates={'*': 'rimg.png.xx'},
    )

    assert_node(
        extract_node(doctree, 0, 3),
        nodes.image,
        uri='img.*',
        candidates={
            'application/pdf': 'img.pdf',
            'image/gif': 'img.gif',
            'image/png': 'img.png',
        },
    )

    assert isinstance(extract_node(doctree, 0, 4), nodes.figure)
    assert_node(
        extract_node(doctree, 0, 4, 0),
        nodes.image,
        uri='img.*',
        candidates={
            'application/pdf': 'img.pdf',
            'image/gif': 'img.gif',
            'image/png': 'img.png',
        },
    )

    # subdir/index.rst
    doctree = app.env.get_doctree('subdir/index')
    assert_node(
        extract_node(doctree, 0, 1),
        nodes.image,
        uri='subdir/rimg.png',
        candidates={'*': 'subdir/rimg.png'},
    )

    assert_node(
        extract_node(doctree, 0, 2),
        nodes.image,
        uri='subdir/svgimg.*',
        candidates={
            'application/pdf': 'subdir/svgimg.pdf',
            'image/svg+xml': 'subdir/svgimg.svg',
        },
    )

    assert isinstance(extract_node(doctree, 0, 3), nodes.figure)
    assert_node(
        extract_node(doctree, 0, 3, 0),
        nodes.image,
        uri='subdir/svgimg.*',
        candidates={
            'application/pdf': 'subdir/svgimg.pdf',
            'image/svg+xml': 'subdir/svgimg.svg',
        },
    )


def getwarning(warnings: StringIO) -> str:
    return strip_escape_sequences(warnings.getvalue().replace(os.sep, '/'))


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    srcdir='gettext_allow_fuzzy_translations',
    confoverrides={
        'language': 'de',
        'gettext_allow_fuzzy_translations': True,
    },
)
def test_gettext_allow_fuzzy_translations(app: SphinxTestApp) -> None:
    locale_dir = app.srcdir / 'locales' / 'de' / 'LC_MESSAGES'
    locale_dir.mkdir(parents=True, exist_ok=True)
    with (locale_dir / 'index.po').open('wb') as f:
        catalog = Catalog()
        catalog.add('features', 'FEATURES', flags=('fuzzy',))
        pofile.write_po(f, catalog)

    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert 'FEATURES' in content


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    srcdir='gettext_disallow_fuzzy_translations',
    confoverrides={
        'language': 'de',
        'gettext_allow_fuzzy_translations': False,
    },
)
def test_gettext_disallow_fuzzy_translations(app: SphinxTestApp) -> None:
    locale_dir = app.srcdir / 'locales' / 'de' / 'LC_MESSAGES'
    locale_dir.mkdir(parents=True, exist_ok=True)
    with (locale_dir / 'index.po').open('wb') as f:
        catalog = Catalog()
        catalog.add('features', 'FEATURES', flags=('fuzzy',))
        pofile.write_po(f, catalog)

    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert 'FEATURES' not in content


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'language': 'de', 'html_sidebars': {'**': ['searchbox.html']}},
    copy_test_root=True,
)
def test_customize_system_message(
    make_app: Callable[..., SphinxTestApp], app_params: _app_params
) -> None:
    try:
        # clear translators cache
        locale.translators.clear()

        # prepare message catalog (.po)
        locale_dir = app_params.kwargs['srcdir'] / 'locales' / 'de' / 'LC_MESSAGES'
        locale_dir.mkdir(parents=True, exist_ok=True)
        with (locale_dir / 'sphinx.po').open('wb') as f:
            catalog = Catalog()
            catalog.add('Quick search', 'QUICK SEARCH')
            pofile.write_po(f, catalog)

        # construct application and convert po file to .mo
        args, kwargs = app_params
        app = make_app(*args, **kwargs)
        assert (locale_dir / 'sphinx.mo').exists()
        assert app.translator.gettext('Quick search') == 'QUICK SEARCH'

        app.build()
        content = (app.outdir / 'index.html').read_text(encoding='utf8')
        assert 'QUICK SEARCH' in content
    finally:
        locale.translators.clear()


@pytest.mark.sphinx(
    'html',
    testroot='intl',
    confoverrides={'today_fmt': '%Y-%m-%d'},
)
def test_customize_today_date_format(
    app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    with monkeypatch.context() as m:
        m.setenv('SOURCE_DATE_EPOCH', '1439131307')
        app.build()
        content = (app.outdir / 'refs.html').read_text(encoding='utf8')

    assert '2015-08-09' in content
