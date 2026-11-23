"""Add a note with the translation progress of a document."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from docutils import nodes
from docutils.parsers.rst import languages
from docutils.parsers.rst.states import Inliner

import sphinx
from sphinx.locale import _

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


# Keep the message IDs until the active application's language is available.
# The unreachable calls allow Babel to extract the default messages.
if False:
    _('Translation progress')
    _(
        'This page is {percentage} translated. Some content is still in the original language.'
    )
    _(
        'This page has not been translated yet and is displayed in the original language.'
    )

_DEFAULT_TITLE = 'Translation progress'
_DEFAULT_MESSAGE = (
    'This page is {percentage} translated. '
    'Some content is still in the original language.'
)
_DEFAULT_UNTRANSLATED_MESSAGE = (
    'This page has not been translated yet and is displayed in the original language.'
)


def add_translation_progress_note(app: Sphinx, doctree: nodes.document) -> None:
    """Add a note after the title when a document is not fully translated."""
    try:
        translation_progress = doctree['translation_progress']
    except KeyError:
        return

    total = translation_progress['total_words']
    translated = translation_progress['translated_words']
    if total <= 0 or translated >= total:
        return

    percentage = f'{translated / total:.2%}'
    if translated == 0:
        note: nodes.Element = nodes.warning(classes=['translation-progress'])
        message = app.config.translation_progress_untranslated_message
    else:
        note = nodes.admonition(classes=['translation-progress'])
        note += nodes.title(text=_(app.config.translation_progress_title))
        message = app.config.translation_progress_message
    text = _(message).format(percentage=percentage)
    paragraph = nodes.paragraph(text)
    inliner = Inliner()
    inliner.init_customizations(doctree.settings)
    memo = SimpleNamespace(
        document=doctree,
        reporter=doctree.reporter,
        language=languages.get_language(doctree.settings.language_code),
    )
    children, messages = inliner.parse(text, 1, memo, paragraph)
    paragraph.extend(children)
    note += paragraph
    note.extend(messages)

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
    app.add_config_value(
        'translation_progress_untranslated_message',
        _DEFAULT_UNTRANSLATED_MESSAGE,
        'env',
        types=frozenset({str}),
    )
    app.connect('doctree-read', add_translation_progress_note)
    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
    }
