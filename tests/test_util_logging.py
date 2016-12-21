# -*- coding: utf-8 -*-
"""
    test_util_logging
    ~~~~~~~~~~~~~~~~~

    Test logging util.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

from docutils import nodes

from sphinx.errors import SphinxWarning
from sphinx.util import logging
from sphinx.util.logging import is_suppressed_warning

from util import with_app, raises, strip_escseq


def test_is_suppressed_warning():
    suppress_warnings = ["ref", "files.*", "rest.duplicated_labels"]

    assert is_suppressed_warning(None, None, suppress_warnings) is False
    assert is_suppressed_warning("ref", None, suppress_warnings) is True
    assert is_suppressed_warning("ref", "numref", suppress_warnings) is True
    assert is_suppressed_warning("ref", "option", suppress_warnings) is True
    assert is_suppressed_warning("files", "image", suppress_warnings) is True
    assert is_suppressed_warning("files", "stylesheet", suppress_warnings) is True
    assert is_suppressed_warning("rest", "syntax", suppress_warnings) is False
    assert is_suppressed_warning("rest", "duplicated_labels", suppress_warnings) is True


@with_app()
def test_suppress_warnings(app, status, warning):
    logging.setup(app, status, warning)
    logger = logging.getLogger(__name__)

    app.config.suppress_warnings = []
    warning.truncate(0)
    logger.warning('message1', type='test', subtype='logging')
    logger.warning('message2', type='test', subtype='crash')
    logger.warning('message3', type='actual', subtype='logging')
    assert 'message1' in warning.getvalue()
    assert 'message2' in warning.getvalue()
    assert 'message3' in warning.getvalue()
    assert app._warncount == 3

    app.config.suppress_warnings = ['test']
    warning.truncate(0)
    logger.warning('message1', type='test', subtype='logging')
    logger.warning('message2', type='test', subtype='crash')
    logger.warning('message3', type='actual', subtype='logging')
    assert 'message1' not in warning.getvalue()
    assert 'message2' not in warning.getvalue()
    assert 'message3' in warning.getvalue()
    assert app._warncount == 4

    app.config.suppress_warnings = ['test.logging']
    warning.truncate(0)
    logger.warning('message1', type='test', subtype='logging')
    logger.warning('message2', type='test', subtype='crash')
    logger.warning('message3', type='actual', subtype='logging')
    assert 'message1' not in warning.getvalue()
    assert 'message2' in warning.getvalue()
    assert 'message3' in warning.getvalue()
    assert app._warncount == 6


@with_app()
def test_warningiserror(app, status, warning):
    logging.setup(app, status, warning)
    logger = logging.getLogger(__name__)

    # if False, warning is not error
    app.warningiserror = False
    logger.warning('message')

    # if True, warning raises SphinxWarning exception
    app.warningiserror = True
    raises(SphinxWarning, logger.warning, 'message')


@with_app()
def test_warning_location(app, status, warning):
    logging.setup(app, status, warning)
    logger = logging.getLogger(__name__)

    logger.warning('message1', location='index')
    assert 'index.txt: WARNING: message1' in warning.getvalue()

    logger.warning('message2', location=('index', 10))
    assert 'index.txt:10: WARNING: message2' in warning.getvalue()

    logger.warning('message3', location=None)
    assert '\x1b[31mWARNING: message3' in warning.getvalue()  # \x1b[31m = darkred


@with_app()
def test_warn_node(app, status, warning):
    logging.setup(app, status, warning)
    logger = logging.getLogger(__name__)

    node = nodes.Node()
    node.source, node.line = ('index.txt', 10)
    logger.warn_node('message1', node)
    assert 'index.txt:10: WARNING: message1' in warning.getvalue()

    node.source, node.line = ('index.txt', None)
    logger.warn_node('message2', node)
    assert 'index.txt:: WARNING: message2' in warning.getvalue()

    node.source, node.line = (None, 10)
    logger.warn_node('message3', node)
    assert '<unknown>:10: WARNING: message3' in warning.getvalue()

    node.source, node.line = (None, None)
    logger.warn_node('message4', node)
    assert '\x1b[31mWARNING: message4' in warning.getvalue()  # \x1b[31m = darkred


@with_app()
def test_pending_logging(app, status, warning):
    logging.setup(app, status, warning)
    logger = logging.getLogger(__name__)

    logger.warning('message1')
    with logging.pending_logging():
        # not logged yet (bufferred) in here
        logger.warning('message2')
        logger.warning('message3')
        assert 'WARNING: message1' in warning.getvalue()
        assert 'WARNING: message2' not in warning.getvalue()
        assert 'WARNING: message3' not in warning.getvalue()

    # actually logged as ordered
    assert 'WARNING: message2\nWARNING: message3' in strip_escseq(warning.getvalue())
