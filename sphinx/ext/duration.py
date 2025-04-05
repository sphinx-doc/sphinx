"""Measure document reading durations."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
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
    'n_durations' : 5,
    'write_durations' : True,
}

DURATION_REF = 'sphinx_reading_times'

ORPHAN_FORMAT = """
:orphan:

.. _{}:

"""

HEADER_FORMAT = (
        ORPHAN_FORMAT
        + """
Computation times
=================
"""
)
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
    sorted_durations = sorted(
        reading_durations.items(), key=itemgetter(1), reverse=True
    )

    logger.info('')
    logger.info(
        __('====================== slowest reading durations =======================')
    )
    # Get default options and update with user-specified values
    options = DEFAULT_OPTIONS.copy()
    user_options = getattr(app.config, 'duration_options', DEFAULT_OPTIONS)
    options.update(user_options)

    # Log the durations
    n_durations = options['n_durations']
    durations_out = {}
    n_durations = len(sorted_durations) if n_durations == -1 else n_durations
    for docname, d in islice(sorted_durations, n_durations):
        durations_out[docname] = d
        logger.info(f'{_sec_to_readable(d)} {docname}')  # NoQA: G004

    if options['write_durations']:
        write_durations(app.builder.srcdir, reading_durations)


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


def _sec_to_readable(t):
    """Convert a number of seconds to a more readable representation."""
    # This will only work for < 1 day execution time
    # And we reserve 2 digits for minutes because presumably
    # there aren't many > 99 minute scripts, but occasionally some
    # > 9 minute ones
    t = datetime(1, 1, 1) + timedelta(seconds=t)
    t = f'{t.hour * 60 + t.minute:02d}:{t.second:02d}.{int(round(t.microsecond / 1000.0)):03d}'
    return t


def write_durations(target_dir, reading_durations):
    """Write durations to `sphinx_reading_times.rst`."""
    total_time = sum(reading_durations.values())
    out_file = Path(target_dir) / f'{DURATION_REF}.rst'
    if out_file.is_file() and total_time == 0:  # a re-run
        return
    with out_file.open('w', encoding='utf-8') as fid:
        fid.write(HEADER_FORMAT.format(DURATION_REF))
        fid.write(
            f'**{_sec_to_readable(total_time)}** total reading time for '
            f'{len(reading_durations)} file{"s" if len(reading_durations) != 1 else ""}:\n\n'
        )
        fid.write("""\
.. list-table::
   :header-rows: 1
   :class: table table-striped sg-datatable

   * - File
     - Time (mm:ss.SSS)
""")
        # Need at least one entry or Sphinx complains
        for file, duration in reading_durations.items() or [['N/A', 'N/A']]:
            fid.write(
                f"""\
   * - {file}
     - {_sec_to_readable(duration)}
"""
            )