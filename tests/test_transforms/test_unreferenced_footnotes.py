"""Test the ``UnreferencedFootnotesDetector`` transform."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.testing.util import SphinxTestApp

if TYPE_CHECKING:
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp


def test_warnings(make_app: type[SphinxTestApp], tmp_path: Path) -> None:
    """Test that warnings are emitted for unreferenced footnotes."""
    tmp_path.joinpath('conf.py').touch()
    tmp_path.joinpath('index.rst').write_text(
        """
Title
=====
[1]_ [#label2]_

.. [1] This is a normal footnote.
.. [2] This is a normal footnote.
.. [2] This is a normal footnote.
.. [3] This is a normal footnote.
.. [*] This is a symbol footnote.
.. [#] This is an auto-numbered footnote.
.. [#label1] This is an auto-numbered footnote with a label.
.. [#label1] This is an auto-numbered footnote with a label.
.. [#label2] This is an auto-numbered footnote with a label.
        """,
        encoding='utf8',
    )
    app = make_app(srcdir=tmp_path)
    app.build()
    warnings = strip_escape_sequences(app.warning.getvalue()).lstrip()
    warnings = warnings.replace(str(tmp_path / 'index.rst'), 'source/index.rst')
    assert (
        warnings
        == """\
source/index.rst:8: WARNING: Duplicate explicit target name: "2". [docutils]
source/index.rst:13: WARNING: Duplicate explicit target name: "label1". [docutils]
source/index.rst:9: WARNING: Footnote [3] is not referenced. [ref.footnote]
source/index.rst:10: WARNING: Footnote [*] is not referenced. [ref.footnote]
source/index.rst:11: WARNING: Footnote [#] is not referenced. [ref.footnote]
"""
    )
