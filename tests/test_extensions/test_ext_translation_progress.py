"""Test the ``sphinx.ext.translation_progress`` extension."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from babel.messages import mofile, pofile

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


def _compile_catalog(app: SphinxTestApp, docname: str) -> None:
    locale_dir = app.srcdir / 'xx' / 'LC_MESSAGES'
    with (locale_dir / f'{docname}.po').open(encoding='utf-8') as po_file:
        catalog = pofile.read_po(po_file)
    with (locale_dir / f'{docname}.mo').open('wb') as mo_file:
        mofile.write_mo(mo_file, catalog)


@pytest.mark.sphinx(
    'html',
    testroot='intl',
    confoverrides={
        'language': 'xx',
        'locale_dirs': ['.'],
        'gettext_compact': False,
    },
    copy_test_root=True,
)
def test_translation_progress_note(app: SphinxTestApp) -> None:
    app.setup_extension('sphinx.ext.translation_progress')

    _compile_catalog(app, 'translation_progress')

    app.build(filenames=[app.srcdir / 'translation_progress.txt'])

    output = (app.outdir / 'translation_progress.html').read_text(encoding='utf-8')
    assert 'translation-progress' in output
    assert '68.64% translated based on word count.' in output
    assert 'Some content is still in the original language.' in output


@pytest.mark.sphinx(
    'html',
    testroot='intl',
    confoverrides={
        'language': 'xx',
        'locale_dirs': ['.'],
        'gettext_compact': False,
        'translation_progress_title': 'Help translate this page',
        'translation_progress_message': 'Word progress: {percentage}',
    },
    copy_test_root=True,
)
def test_translation_progress_note_config(app: SphinxTestApp) -> None:
    app.setup_extension('sphinx.ext.translation_progress')
    _compile_catalog(app, 'translation_progress')

    app.build(filenames=[app.srcdir / 'translation_progress.txt'])

    output = (app.outdir / 'translation_progress.html').read_text(encoding='utf-8')
    assert 'Help translate this page' in output
    assert 'Word progress: 68.64%' in output


@pytest.mark.sphinx(
    'singlehtml',
    testroot='intl',
    confoverrides={
        'language': 'xx',
        'locale_dirs': ['.'],
        'gettext_compact': False,
        'extensions': ['sphinx.ext.translation_progress'],
    },
    copy_test_root=True,
)
def test_translation_progress_note_singlehtml_child(app: SphinxTestApp) -> None:
    _compile_catalog(app, 'translation_progress')

    app.build()

    output = (app.outdir / 'index.html').read_text(encoding='utf-8')
    assert '68.64% translated based on word count.' in output


@pytest.mark.sphinx(
    'latex',
    testroot='intl',
    confoverrides={
        'language': 'xx',
        'locale_dirs': ['.'],
        'gettext_compact': False,
        'extensions': ['sphinx.ext.translation_progress'],
    },
    copy_test_root=True,
)
def test_translation_progress_note_latex_child(app: SphinxTestApp) -> None:
    _compile_catalog(app, 'translation_progress')

    app.build()

    output = next(app.outdir.glob('*.tex')).read_text(encoding='utf-8')
    assert '68.64\\% translated based on word count.' in output


@pytest.mark.sphinx(
    'text',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.translation_progress']},
    freshenv=True,
)
def test_translation_progress_note_without_catalog(app: SphinxTestApp) -> None:
    app.build()

    output = (app.outdir / 'index.txt').read_text(encoding='utf-8')
    assert 'This page is' not in output
