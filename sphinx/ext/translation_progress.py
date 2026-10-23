"""Add a note with the translation progress of a document."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from docutils import nodes

import sphinx
from sphinx.locale import _
from sphinx.util.nodes import NodeMatcher

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


_DEFAULT_TITLE = 'Translation progress'
_DEFAULT_MESSAGE = (
    'This page is {percentage} translated based on word count. '
    'Some content is still in the original language.'
)


def _calculate_word_progress(doctree: nodes.document) -> tuple[int, int]:
    """Return the translated and total source-language word counts."""
    total_words = translated_words = 0
    for node in NodeMatcher(nodes.Element, translated=Any).findall(doctree):
        source = node.rawsource or node.astext()
        word_count = len(source.split())
        total_words += word_count
        if node['translated']:
            translated_words += word_count
    return translated_words, total_words


def add_translation_progress_note(app: Sphinx, doctree: nodes.document) -> None:
    """Add a note after the title when a document is not fully translated."""
    try:
        translation_progress = doctree['translation_progress']
    except KeyError:
        return

    total = translation_progress['total']
    translated = translation_progress['translated']
    if total <= 0 or translated >= total:
        return

    translated_words, total_words = _calculate_word_progress(doctree)
    if total_words <= 0:
        return

    percentage = f'{translated_words / total_words:.2%}'
    note = nodes.note(classes=['translation-progress'])
    note += nodes.title(text=_(app.config.translation_progress_title))
    note += nodes.paragraph(
        text=_(app.config.translation_progress_message).format(percentage=percentage)
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
    app.add_config_value(
        'translation_progress_title', _DEFAULT_TITLE, 'env', types=frozenset({str})
    )
    app.add_config_value(
        'translation_progress_message', _DEFAULT_MESSAGE, 'env', types=frozenset({str})
    )
    app.connect('doctree-read', add_translation_progress_note)
    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
    }
