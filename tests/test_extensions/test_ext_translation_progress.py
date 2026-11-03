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
    'html',
    testroot='intl',
    confoverrides={
        'language': 'xx',
        'locale_dirs': ['.'],
        'gettext_compact': False,
        'gettext_additional_targets': ['literal-block'],
    },
    copy_test_root=True,
)
def test_progress_counts_source_words_of_a_translated_literal_block(
    app: SphinxTestApp,
) -> None:
    """A translated literal block keeps its source words: the ratio does not follow the
    length of its translation."""
    app.setup_extension('sphinx.ext.translation_progress')

    (app.srcdir / 'progress_literal.txt').write_text(
        'Short title\n===========\n\n'
        '.. code-block:: text\n\n'
        '   This literal block has ten source words in it.\n\n'
        'A paragraph that stays in the original language.\n',
        encoding='utf-8',
    )
    locale_dir = app.srcdir / 'xx' / 'LC_MESSAGES'
    (locale_dir / 'progress_literal.po').write_text(
        'msgid ""\nmsgstr ""\n'
        '"Language: xx\\n"\n'
        '"MIME-Version: 1.0\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n\n'
        'msgid "Short title"\nmsgstr "COURT"\n\n'
        'msgid "This literal block has ten source words in it."\nmsgstr "UN"\n',
        encoding='utf-8',
    )
    _compile_catalog(app, 'progress_literal')

    app.build(filenames=[app.srcdir / 'progress_literal.txt'])

    output = (app.outdir / 'progress_literal.html').read_text(encoding='utf-8')
    # 11 of 19 source words: the title (2) and the nine-word literal block are translated,
    # the eight-word paragraph is not. Counting the one-word translation would say 27.27%.
    assert '57.89% translated based on word count.' in output


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
