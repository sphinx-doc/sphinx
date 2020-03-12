"""
    test_build_linkcheck
    ~~~~~~~~~~~~~~~~~~~~

    Test the build process with manpage builder with the test root.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import json
import re
from unittest import mock
import pytest


@pytest.mark.sphinx('linkcheck', testroot='linkcheck', freshenv=True)
def test_defaults(app, status, warning):
    app.builder.build_all()

    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text()

    print(content)
    # looking for '#top' and '#does-not-exist' not found should fail
    assert "Anchor 'top' not found" in content
    assert "Anchor 'does-not-exist' not found" in content
    # looking for non-existent URL should fail
    assert " Max retries exceeded with url: /doesnotexist" in content
    # images should fail
    assert "Not Found for url: https://www.google.com/image.png" in content
    assert "Not Found for url: https://www.google.com/image2.png" in content
    assert len(content.splitlines()) == 5


@pytest.mark.sphinx('linkcheck', testroot='linkcheck', freshenv=True)
def test_defaults_json(app, status, warning):
    app.builder.build_all()

    assert (app.outdir / 'output.json').exists()
    content = (app.outdir / 'output.json').read_text()
    print(content)

    rows = [json.loads(x) for x in content.splitlines()]
    row = rows[0]
    for attr in ["filename", "lineno", "status", "code", "uri",
                 "info"]:
        assert attr in row

    assert len(content.splitlines()) == 8
    assert len(rows) == 8
    # the output order of the rows is not stable
    # due to possible variance in network latency
    rowsby = {row["uri"]:row for row in rows}
    assert rowsby["https://www.google.com#!bar"] == {
        'filename': 'links.txt',
        'lineno': 10,
        'status': 'working',
        'code': 0,
        'uri': 'https://www.google.com#!bar',
        'info': ''
    }
    # looking for non-existent URL should fail
    dnerow = rowsby['https://localhost:7777/doesnotexist']
    assert dnerow['filename'] == 'links.txt'
    assert dnerow['lineno'] == 13
    assert dnerow['status'] == 'broken'
    assert dnerow['code'] == 0
    assert dnerow['uri'] == 'https://localhost:7777/doesnotexist'
    assert rowsby['https://www.google.com/image2.png'] == {
        'filename': 'links.txt',
        'lineno': 16,
        'status': 'broken',
        'code': 0,
        'uri': 'https://www.google.com/image2.png',
        'info': '404 Client Error: Not Found for url: https://www.google.com/image2.png'
    }
    # looking for '#top' and '#does-not-exist' not found should fail
    assert "Anchor 'top' not found" == \
        rowsby["https://www.google.com/#top"]["info"]
    assert "Anchor 'does-not-exist' not found" == \
        rowsby["http://www.sphinx-doc.org/en/1.7/intro.html#does-not-exist"]["info"]
    # images should fail
    assert "Not Found for url: https://www.google.com/image.png" in \
        rowsby["https://www.google.com/image.png"]["info"]


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck', freshenv=True,
    confoverrides={'linkcheck_anchors_ignore': ["^!", "^top$"],
                   'linkcheck_ignore': [
                       'https://localhost:7777/doesnotexist',
                       'http://www.sphinx-doc.org/en/1.7/intro.html#',
                       'https://www.google.com/image.png',
                       'https://www.google.com/image2.png']
                   })
def test_anchors_ignored(app, status, warning):
    app.builder.build_all()

    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').read_text()

    # expect all ok when excluding #top
    assert not content


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck', freshenv=True,
    confoverrides={'linkcheck_auth': [
                        (r'.+google\.com/image.+', 'authinfo1'),
                        (r'.+google\.com.+', 'authinfo2'),
                   ]
                  })
def test_auth(app, status, warning):
    mock_req = mock.MagicMock()
    mock_req.return_value = 'fake-response'

    with mock.patch.multiple('requests', get=mock_req, head=mock_req):
        app.builder.build_all()
        for c_args, c_kwargs in mock_req.call_args_list:
            if 'google.com/image' in c_args[0]:
                assert c_kwargs['auth'] == 'authinfo1'
            elif 'google.com' in c_args[0]:
                assert c_kwargs['auth'] == 'authinfo2'
            else:
                assert not c_kwargs['auth']
