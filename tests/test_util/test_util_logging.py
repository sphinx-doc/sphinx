"""Test logging util."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.cmd.build import build_main
from sphinx.util import logging
from sphinx.util.console import colorize
from sphinx.util.logging import is_suppressed_warning, prefixed_warnings
from sphinx.util.parallel import ParallelTasks

from tests.utils import TEST_ROOTS_DIR

if TYPE_CHECKING:
    import io
    from collections.abc import Iterator

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='root')
def test_info_and_warning(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning, verbosity=2)
    logger = logging.getLogger(__name__)

    logger.debug('message1')
    logger.info('message2')
    logger.warning('message3')
    logger.critical('message4')
    logger.error('message5')

    assert 'message1' in app.status.getvalue()
    assert 'message2' in app.status.getvalue()
    assert 'message3' not in app.status.getvalue()
    assert 'message4' not in app.status.getvalue()
    assert 'message5' not in app.status.getvalue()

    assert 'message1' not in app.warning.getvalue()
    assert 'message2' not in app.warning.getvalue()
    assert 'WARNING: message3' in app.warning.getvalue()
    assert 'CRITICAL: message4' in app.warning.getvalue()
    assert 'ERROR: message5' in app.warning.getvalue()


@pytest.mark.sphinx('html', testroot='root')
def test_Exception(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    logger.info(Exception)
    assert "<class 'Exception'>" in app.status.getvalue()


@pytest.mark.sphinx('html', testroot='root')
def test_verbosity_filter(app: SphinxTestApp) -> None:
    # verbosity = 0: INFO
    logging.setup(app, app.status, app.warning, verbosity=0)
    logger = logging.getLogger(__name__)

    logger.info('message1')
    logger.verbose('message2')
    logger.debug('message3')

    assert 'message1' in app.status.getvalue()
    assert 'message2' not in app.status.getvalue()
    assert 'message3' not in app.status.getvalue()
    assert 'message4' not in app.status.getvalue()

    # verbosity = 1: VERBOSE
    logging.setup(app, app.status, app.warning, verbosity=1)
    logger = logging.getLogger(__name__)

    logger.info('message1')
    logger.verbose('message2')
    logger.debug('message3')

    assert 'message1' in app.status.getvalue()
    assert 'message2' in app.status.getvalue()
    assert 'message3' not in app.status.getvalue()
    assert 'message4' not in app.status.getvalue()

    # verbosity = 2: DEBUG
    logging.setup(app, app.status, app.warning, verbosity=2)
    logger = logging.getLogger(__name__)

    logger.info('message1')
    logger.verbose('message2')
    logger.debug('message3')

    assert 'message1' in app.status.getvalue()
    assert 'message2' in app.status.getvalue()
    assert 'message3' in app.status.getvalue()
    assert 'message4' not in app.status.getvalue()


@pytest.mark.sphinx('html', testroot='root')
def test_nonl_info_log(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    logger.info('message1', nonl=True)
    logger.info('message2')
    logger.info('message3')

    assert 'message1message2\nmessage3' in app.status.getvalue()


@pytest.mark.sphinx('html', testroot='root')
def test_once_warning_log(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    logger.warning('message: %d', 1, once=True)
    logger.warning('message: %d', 1, once=True)
    logger.warning('message: %d', 2, once=True)

    warnings = strip_escape_sequences(app.warning.getvalue())
    assert 'WARNING: message: 1\nWARNING: message: 2\n' in warnings


def test_is_suppressed_warning() -> None:
    suppress_warnings = ['ref', 'files.*', 'rest.duplicated_labels']

    assert is_suppressed_warning(None, None, suppress_warnings) is False  # type: ignore[arg-type]
    assert is_suppressed_warning('ref', None, suppress_warnings) is True  # type: ignore[arg-type]
    assert is_suppressed_warning('ref', 'numref', suppress_warnings) is True
    assert is_suppressed_warning('ref', 'option', suppress_warnings) is True
    assert is_suppressed_warning('files', 'image', suppress_warnings) is True
    assert is_suppressed_warning('files', 'stylesheet', suppress_warnings) is True
    assert is_suppressed_warning('rest', None, suppress_warnings) is False  # type: ignore[arg-type]
    assert is_suppressed_warning('rest', 'syntax', suppress_warnings) is False
    assert is_suppressed_warning('rest', 'duplicated_labels', suppress_warnings) is True


@pytest.mark.sphinx('html', testroot='root')
def test_suppress_warnings(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    app._warncount = 0  # force reset

    app.config.suppress_warnings = []
    app.warning.truncate(0)
    logger.warning('message0', type='test')
    logger.warning('message1', type='test', subtype='logging')
    logger.warning('message2', type='test', subtype='crash')
    logger.warning('message3', type='actual', subtype='logging')
    assert 'message0' in app.warning.getvalue()
    assert 'message1' in app.warning.getvalue()
    assert 'message2' in app.warning.getvalue()
    assert 'message3' in app.warning.getvalue()
    assert app._warncount == 4

    app.config.suppress_warnings = ['test']
    app.warning.truncate(0)
    logger.warning('message0', type='test')
    logger.warning('message1', type='test', subtype='logging')
    logger.warning('message2', type='test', subtype='crash')
    logger.warning('message3', type='actual', subtype='logging')
    assert 'message0' not in app.warning.getvalue()
    assert 'message1' not in app.warning.getvalue()
    assert 'message2' not in app.warning.getvalue()
    assert 'message3' in app.warning.getvalue()
    assert app._warncount == 5

    app.config.suppress_warnings = ['test.logging']
    app.warning.truncate(0)
    logger.warning('message0', type='test')
    logger.warning('message1', type='test', subtype='logging')
    logger.warning('message2', type='test', subtype='crash')
    logger.warning('message3', type='actual', subtype='logging')
    assert 'message0' in app.warning.getvalue()
    assert 'message1' not in app.warning.getvalue()
    assert 'message2' in app.warning.getvalue()
    assert 'message3' in app.warning.getvalue()
    assert app._warncount == 8


@pytest.mark.sphinx('html', testroot='root')
def test_info_location(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    logger.info('message1', location='index')
    assert 'index.txt: message1' in app.status.getvalue()

    logger.info('message2', location=('index', 10))
    assert 'index.txt:10: message2' in app.status.getvalue()

    logger.info('message3', location=None)
    assert '\nmessage3' in app.status.getvalue()

    node = nodes.Element()
    node.source, node.line = ('index.txt', 10)
    logger.info('message4', location=node)
    assert 'index.txt:10: message4' in app.status.getvalue()

    node.source, node.line = ('index.txt', None)
    logger.info('message5', location=node)
    assert 'index.txt:: message5' in app.status.getvalue()

    node.source, node.line = (None, 10)
    logger.info('message6', location=node)
    assert '<unknown>:10: message6' in app.status.getvalue()

    node.source, node.line = (None, None)
    logger.info('message7', location=node)
    assert '\nmessage7' in app.status.getvalue()


@pytest.mark.sphinx('html', testroot='root')
def test_warning_location(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    logger.warning('message1', location='index')
    assert 'index.txt: WARNING: message1' in app.warning.getvalue()

    logger.warning('message2', location=('index', 10))
    assert 'index.txt:10: WARNING: message2' in app.warning.getvalue()

    logger.warning('message3', location=None)
    assert colorize('red', 'WARNING: message3') in app.warning.getvalue()

    node = nodes.Element()
    node.source, node.line = ('index.txt', 10)
    logger.warning('message4', location=node)
    assert 'index.txt:10: WARNING: message4' in app.warning.getvalue()

    node.source, node.line = ('index.txt', None)
    logger.warning('message5', location=node)
    assert 'index.txt:: WARNING: message5' in app.warning.getvalue()

    node.source, node.line = (None, 10)
    logger.warning('message6', location=node)
    assert '<unknown>:10: WARNING: message6' in app.warning.getvalue()

    node.source, node.line = (None, None)
    logger.warning('message7', location=node)
    assert colorize('red', 'WARNING: message7') in app.warning.getvalue()


@pytest.mark.sphinx('html', testroot='root')
def test_suppress_logging(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    logger.warning('message1')
    with logging.suppress_logging():
        logger.warning('message2')
        assert 'WARNING: message1' in app.warning.getvalue()
        assert 'WARNING: message2' not in app.warning.getvalue()

    assert 'WARNING: message1' in app.warning.getvalue()
    assert 'WARNING: message2' not in app.warning.getvalue()


@pytest.mark.sphinx('html', testroot='root')
def test_pending_warnings(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    logger.warning('message1')
    with logging.pending_warnings():
        # not logged yet (buffered) in here
        logger.warning('message2')
        logger.warning('message3')
        assert 'WARNING: message1' in app.warning.getvalue()
        assert 'WARNING: message2' not in app.warning.getvalue()
        assert 'WARNING: message3' not in app.warning.getvalue()

    # actually logged as ordered
    warnings = strip_escape_sequences(app.warning.getvalue())
    assert 'WARNING: message2\nWARNING: message3' in warnings


@contextmanager
def force_colors() -> Iterator[None]:
    forcecolor = os.environ.get('FORCE_COLOR', None)

    try:
        os.environ['FORCE_COLOR'] = '1'
        yield
    finally:
        if forcecolor is None:
            os.environ.pop('FORCE_COLOR', None)
        else:
            os.environ['FORCE_COLOR'] = forcecolor


def test_log_no_ansi_colors(tmp_path: Path) -> None:
    with force_colors():
        wfile = tmp_path / 'warnings.txt'
        srcdir = TEST_ROOTS_DIR / 'test-nitpicky-warnings'
        argv = list(map(str, ['-b', 'html', srcdir, tmp_path, '-n', '-w', wfile]))
        retcode = build_main(argv)
        assert retcode == 0

        content = wfile.read_text(encoding='utf8')
        assert '\x1b[91m' not in content


@pytest.mark.sphinx('html', testroot='root')
def test_colored_logs(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning, verbosity=2)
    logger = logging.getLogger(__name__)

    # default colors
    logger.debug('message1')
    logger.verbose('message2')
    logger.info('message3')
    logger.warning('message4')
    logger.critical('message5')
    logger.error('message6')

    assert colorize('darkgray', 'message1') in app.status.getvalue()
    assert 'message2\n' in app.status.getvalue()  # not colored
    assert 'message3\n' in app.status.getvalue()  # not colored
    assert colorize('red', 'WARNING: message4') in app.warning.getvalue()
    assert 'CRITICAL: message5\n' in app.warning.getvalue()  # not colored
    assert colorize('darkred', 'ERROR: message6') in app.warning.getvalue()

    # color specification
    logger.debug('message7', color='white')
    logger.info('message8', color='red')
    assert colorize('white', 'message7') in app.status.getvalue()
    assert colorize('red', 'message8') in app.status.getvalue()


@pytest.mark.xfail(
    os.name != 'posix',
    reason='Parallel mode does not work on Windows',
)
def test_logging_in_ParallelTasks(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    def child_process() -> None:
        logger.info('message1')
        logger.warning('message2', location='index')

    tasks = ParallelTasks(1)
    tasks.add_task(child_process)
    tasks.join()
    assert 'message1' in app.status.getvalue()
    assert 'index.txt: WARNING: message2' in app.warning.getvalue()


@pytest.mark.sphinx('html', testroot='root')
def test_output_with_unencodable_char(app: SphinxTestApp) -> None:
    class StreamWriter:
        def __init__(self, stream: io.StringIO) -> None:
            self.stream = stream

        def write(self, object: str) -> None:
            self.stream.write(object.encode('cp1252').decode('cp1252'))

    logging.setup(app, StreamWriter(app.status), app.warning, verbosity=0)  # type: ignore[arg-type]
    logger = logging.getLogger(__name__)

    # info with UnicodeEncodeError
    app.status.truncate(0)
    app.status.seek(0)
    logger.info('unicode \u206d...')
    assert app.status.getvalue() == 'unicode ?...\n'


@pytest.mark.sphinx('html', testroot='root')
def test_prefixed_warnings(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    logger.warning('message1')
    with prefixed_warnings('PREFIX:'):
        logger.warning('message2')
        with prefixed_warnings('Another PREFIX:'):
            logger.warning('message3')
        logger.warning('message4')
    logger.warning('message5')

    assert 'WARNING: message1' in app.warning.getvalue()
    assert 'WARNING: PREFIX: message2' in app.warning.getvalue()
    assert 'WARNING: Another PREFIX: message3' in app.warning.getvalue()
    assert 'WARNING: PREFIX: message4' in app.warning.getvalue()
    assert 'WARNING: message5' in app.warning.getvalue()


def test_get_node_location_abspath() -> None:
    # Ensure that node locations are reported as an absolute path,
    # even if the source attribute is a relative path.

    relative_filename = Path('relative', 'path.txt')
    absolute_filename = relative_filename.resolve()

    n = nodes.Element()
    n.source = str(relative_filename)

    location = logging.get_node_location(n)

    assert location == f'{absolute_filename}:'


@pytest.mark.sphinx('html', testroot='root', confoverrides={'show_warning_types': True})
def test_show_warning_types(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)
    logger.warning('message2')
    logger.warning('message3', type='test')
    logger.warning('message4', type='test', subtype='logging')

    warnings = strip_escape_sequences(app.warning.getvalue()).splitlines()

    assert warnings == [
        'WARNING: message2',
        'WARNING: message3 [test]',
        'WARNING: message4 [test.logging]',
    ]
