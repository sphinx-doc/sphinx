from pathlib import Path

import pytest


@pytest.mark.sphinx("gettext", testroot="notranslate")
def test_notranslate_extraction(app):
    app.build()
    out = Path(app.outdir)
    pot_files = {path.relative_to(out) for path in out.glob("*.pot")}
    assert pot_files == {Path("index.pot"), Path("translated.pot")}
