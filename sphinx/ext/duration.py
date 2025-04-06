"""Measure document reading durations."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from itertools import islice
from operator import itemgetter
from pathlib import Path
from typing import TYPE_CHECKING

import sphinx
from sphinx.domains import Domain
from sphinx.locale import __
from sphinx.util import logging

if TYPE_CHECKING:
    from collections.abc import Set
    from typing import TypedDict

    from docutils import nodes

    from sphinx.application import Sphinx

    class _DurationDomainData(TypedDict):
        reading_durations: dict[str, float]


DEFAULT_OPTIONS = {
    'print_total': True,
    'print_slowest': True,
    'n_slowest': 5,
    'write_durations': True,
}

logger = logging.getLogger(__name__)


class DurationDomain(Domain):
    """A domain for durations of Sphinx processing."""

    name = 'duration'

    @property
    def reading_durations(self) -> dict[str, float]:
        return self.data.setdefault('reading_durations', {})

    def note_reading_duration(self, duration: float) -> None:
        self.reading_durations[self.env.docname] = duration

    def clear(self) -> None:
        self.reading_durations.clear()

    def clear_doc(self, docname: str) -> None:
        self.reading_durations.pop(docname, None)

    def merge_domaindata(  # type: ignore[override]
        self, docnames: Set[str], otherdata: _DurationDomainData
    ) -> None:
        other_reading_durations = otherdata.get('reading_durations', {})
        docnames_set = frozenset(docnames)
        for docname, duration in other_reading_durations.items():
            if docname in docnames_set:
                self.reading_durations[docname] = duration


def on_builder_inited(app: Sphinx) -> None:
    """Initialize DurationDomain on bootstrap.

    This clears the results of the last build.
    """
    domain = app.env.domains['duration']
    domain.clear()


def on_source_read(app: Sphinx, docname: str, content: list[str]) -> None:
    """Start to measure reading duration."""
    app.env.current_document.reading_started_at = time.monotonic()


def on_doctree_read(app: Sphinx, doctree: nodes.document) -> None:
    """Record a reading duration."""
    duration = time.monotonic() - app.env.current_document.reading_started_at
    domain = app.env.domains['duration']
    domain.note_reading_duration(duration)


def on_build_finished(app: Sphinx, error: Exception) -> None:
    """Display duration ranking on the current build."""
    domain = app.env.domains['duration']
    reading_durations = domain.reading_durations
    if not reading_durations:
        return

    # Get default options and update with user-specified values
    options = DEFAULT_OPTIONS.copy()
    user_options = getattr(app.config, 'duration_options', DEFAULT_OPTIONS)
    options.update(user_options)

    if options['print_total']:
        logger.info('')
        logger.info(
            __(
                '====================== total reading duration =========================='
            )
        )

        n_files = len(reading_durations)
        s = '' if n_files == 1 else 's'

        total = sum(reading_durations.values())
        logger.info('Total time reading %d file%s:\n', n_files, s)
        logger.info(_format_seconds(total, multiline=True))

    if options['print_slowest']:
        logger.info('')
        logger.info(
            __(
                '====================== slowest reading durations ======================='
            )
        )
        sorted_durations = sorted(
            reading_durations.items(), key=itemgetter(1), reverse=True
        )
        n_slowest = options['n_slowest']
        n_slowest = len(sorted_durations) if n_slowest == -1 else n_slowest
        for docname, d in islice(sorted_durations, n_slowest):
            logger.info('%s %s', _format_seconds(d), docname)

    if options['write_durations']:
        # Write to JSON
        out_file = Path(app.builder.outdir) / 'sphinx_durations.json'
        with out_file.open('w', encoding='utf-8') as fid:
            json.dump(reading_durations, fid, indent=4)  # indent makes it more readable


def setup(app: Sphinx) -> dict[str, bool | str]:
    app.add_domain(DurationDomain)
    app.connect('builder-inited', on_builder_inited)
    app.connect('source-read', on_source_read)
    app.connect('doctree-read', on_doctree_read)
    app.connect('build-finished', on_build_finished)

    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }


def _format_seconds(seconds: float, multiline: bool = False) -> str:
    """Convert seconds to a formatted string."""
    dt = datetime(1, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)  # noqa: UP017
    minutes = dt.hour * 60 + dt.minute
    seconds = dt.second
    milliseconds = round(dt.microsecond / 1000.0)
    if multiline:
        return (
            f'minutes:      {minutes:>3}\n'
            f'seconds:      {seconds:>3}\n'
            f'milliseconds: {milliseconds:>3}'
        )
    else:
        return f'{minutes:02d}:{seconds:02d}.{milliseconds:03d}'
