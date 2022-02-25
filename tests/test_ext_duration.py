"""
    test_ext_duration
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.duration extension.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest


@pytest.mark.sphinx('dummy', testroot='basic',
                    confoverrides={'extensions': ['sphinx.ext.duration']})
def test_githubpages(app, status, warning):
    app.build()

    assert 'slowest reading durations' in status.getvalue()
    assert re.search('\\d+\\.\\d{3} index\n', status.getvalue())
