"""Test the ``sphinx.ext.translation_progress`` extension."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from babel.messages import mofile, pofile

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


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

    locale_dir = app.srcdir / 'xx' / 'LC_MESSAGES'
    with (locale_dir / 'translation_progress.po').open(encoding='utf-8') as po_file:
        catalog = pofile.read_po(po_file)
    with (locale_dir / 'translation_progress.mo').open('wb') as mo_file:
        mofile.write_mo(mo_file, catalog)

    app.build(filenames=[app.srcdir / 'translation_progress.txt'])

    output = (app.outdir / 'translation_progress.html').read_text(encoding='utf-8')
    assert 'translation-progress' in output
    assert '68.75% translated.' in output


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
