"""Add a note with the translation progress of a document."""

from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes

import sphinx
from sphinx.locale import _
from sphinx.transforms import _calculate_translation_progress

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


def add_translation_progress_note(
    app: Sphinx, doctree: nodes.document, docname: str
) -> None:
    """Add a note after the title when a document is not fully translated."""
    del app, docname

    try:
        translation_progress = doctree['translation_progress']
    except KeyError:
        return

    total = translation_progress['total']
    translated = translation_progress['translated']
    if total <= 0 or translated >= total:
        return

    percentage = _calculate_translation_progress(doctree)
    note = nodes.note(classes=['translation-progress'])
    note += nodes.title(text=_('Translation progress'))
    note += nodes.paragraph(
        text=_('This page is %(percentage)s translated.') % {'percentage': percentage}
    )

    for child in doctree.children:
        if isinstance(child, nodes.section):
            for index, section_child in enumerate(child.children):
                if isinstance(section_child, nodes.title):
                    child.insert(index + 1, note)
                    return
            child.insert(0, note)
            return

    doctree.insert(0, note)


def setup(app: Sphinx) -> ExtensionMetadata:
    app.connect('doctree-resolved', add_translation_progress_note)
    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
    }
