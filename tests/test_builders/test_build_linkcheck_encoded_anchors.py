"""Test the linkcheck builder's ability to handle encoded anchors."""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler
from typing import TYPE_CHECKING

import pytest

from tests.utils import serve_application

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

    from sphinx.testing.util import SphinxTestApp


class EncodedAnchorsHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def _chunk_content(self, content: str, *, max_chunk_size: int) -> Iterable[bytes]:
        """Split content into chunks of a maximum size."""

        def _encode_chunk(chunk: bytes) -> Iterable[bytes]:
            """Encode a bytestring into a format suitable for HTTP chunked-transfer."""
            yield f'{len(chunk):X}'.encode('ascii')
            yield b'\r\n'
            yield chunk
            yield b'\r\n'

        buffer = b''
        for char in content:
            buffer += char.encode('utf-8')
            if len(buffer) >= max_chunk_size:
                chunk, buffer = buffer[:max_chunk_size], buffer[max_chunk_size:]
                yield from _encode_chunk(chunk)

        # Flush remaining bytes, if any
        if buffer:
            yield from _encode_chunk(buffer)

        # Emit a final empty chunk to close the stream
        yield from _encode_chunk(b'')

    def _send_chunked(self, content: str) -> bool:
        """Send content in chunks."""
        for chunk in self._chunk_content(content, max_chunk_size=20):
            try:
                self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError) as e:
                self.log_message(str(e))
                return False
        return True

    def do_HEAD(self) -> None:
        """Handle HEAD requests."""
        print(f'HEAD request for path: {self.path}')
        if self.path in {'/standard-encoded-anchors', '/various-encoded-chars'}:
            self.send_response(200, 'OK')
        else:
            self.send_response(404, 'Not Found')
        self.end_headers()

    def do_GET(self) -> None:
        """Serve test pages with encoded anchors."""
        if self.path == '/standard-encoded-anchors':
            self.send_response(200, 'OK')
            # Note the ID has an encoded forward slash (%2F)
            content = """
            <!DOCTYPE html>
            <html>
            <head><title>Encoded Anchors Test</title></head>
            <body>
                <h1 id="standard-input%2Foutput-stdio">Standard I/O</h1>
                <h2 id="encoded%2Banchor">Encoded Plus</h2>
            </body>
            </html>
            """
        elif self.path == '/various-encoded-chars':
            self.send_response(200, 'OK')
            content = """
            <!DOCTYPE html>
            <html>
            <head><title>Various Encoded Characters</title></head>
            <body>
                <h1 id="encoded%21exclamation">Encoded Exclamation</h1>
                <h2 id="encoded%23hash">Encoded Hash</h2>
                <h3 id="encoded%25percent">Encoded Percent</h3>
                <h4 id="encoded%26ampersand">Encoded Ampersand</h4>
                <h5 id="encoded%3Fquestion">Encoded Question</h5>
                <h6 id="encoded%40at">Encoded At</h6>
            </body>
            </html>
            """
        else:
            self.send_response(404, 'Not Found')
            content = 'not found\n'
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()
        self._send_chunked(content)


@pytest.mark.sphinx(
    'linkcheck',
    testroot='linkcheck-encoded-anchors',
    freshenv=True,
)
def test_encoded_anchors_handling(app: SphinxTestApp, tmp_path: Any) -> None:
    """Test that linkcheck correctly handles URLs with encoded anchors."""
    with serve_application(app, EncodedAnchorsHandler) as address:
        # Create test file with encoded anchor links using the server address
        (app.srcdir / 'encoded_anchors.rst').write_text(
            f"""
Encoded Anchors Test
====================

Links with encoded anchors:

* `Standard I/O <http://{address}/standard-encoded-anchors#standard-input/output-stdio>`_
* `Encoded Plus <http://{address}/standard-encoded-anchors#encoded+anchor>`_
* `Encoded Exclamation <http://{address}/various-encoded-chars#encoded!exclamation>`_
* `Encoded Hash <http://{address}/various-encoded-chars#encoded#hash>`_
* `Encoded Percent <http://{address}/various-encoded-chars#encoded%percent>`_
* `Encoded Ampersand <http://{address}/various-encoded-chars#encoded&ampersand>`_
* `Encoded Question <http://{address}/various-encoded-chars#encoded?question>`_
* `Encoded At <http://{address}/various-encoded-chars#encoded@at>`_
""",
            encoding='utf-8',
        )

        app.build()

    # Parse the JSON output to check the results
    content = (app.outdir / 'output.json').read_text(encoding='utf8')
    data = [json.loads(record) for record in content.splitlines()]

    # Filter for our encoded anchor URLs
    encoded_anchor_results = [
        record
        for record in data
        if any(
            x in record['uri']
            for x in ['standard-encoded-anchors#', 'various-encoded-chars#']
        )
    ]

    # All links with encoded anchors should be working
    assert all(record['status'] == 'working' for record in encoded_anchor_results)

    # Verify specific links
    uri_pattern = re.compile(
        f'http://{re.escape(address)}/standard-encoded-anchors#standard-input/output-stdio'
    )
    stdio_link = next(
        record for record in encoded_anchor_results if uri_pattern.match(record['uri'])
    )
    assert stdio_link['status'] == 'working'

    # Check for encoded plus link
    plus_pattern = re.compile(
        f'http://{re.escape(address)}/standard-encoded-anchors#encoded\\+anchor'
    )
    plus_link = next(
        record for record in encoded_anchor_results if plus_pattern.match(record['uri'])
    )
    assert plus_link['status'] == 'working'
