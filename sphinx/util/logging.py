# -*- coding: utf-8 -*-
"""
    sphinx.util.logging
    ~~~~~~~~~~~~~~~~~~~

    Logging utility functions for Sphinx.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import absolute_import

import logging
import logging.handlers
from contextlib import contextmanager
from collections import defaultdict

from six import PY2, StringIO, string_types
from docutils.utils import get_source_line

from sphinx.errors import SphinxWarning
from sphinx.util.console import darkred  # type: ignore

if False:
    # For type annotation
    from typing import Any, Generator, IO, Tuple  # NOQA
    from docutils import nodes  # NOQA
    from sphinx.application import Sphinx  # NOQA


VERBOSE = 15
DEBUG2 = 5
VERBOSITY_MAP = defaultdict(lambda: 0)  # type: Dict[int, int]
VERBOSITY_MAP.update({
    0: logging.INFO,
    1: VERBOSE,
    2: logging.DEBUG,
    3: DEBUG2,
})


def getLogger(name):
    # type: (str) -> SphinxLoggerAdapter
    """Get logger wrapped by SphinxLoggerAdapter."""
    return SphinxLoggerAdapter(logging.getLogger(name), {})


class SphinxWarningLogRecord(logging.LogRecord):
    """Log record class supporting location"""
    location = None  # type: Any

    def getMessage(self):
        # type: () -> str
        message = super(SphinxWarningLogRecord, self).getMessage()
        if isinstance(message, string_types):
            location = getattr(self, 'location', None)
            if location:
                message = '%s: WARNING: %s' % (location, message)
            elif 'WARNING:' not in message:
                message = 'WARNING: %s' % message

            return darkred(message)
        else:
            return message


class SphinxLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter allowing ``type`` and ``subtype`` keywords."""

    def warn_node(self, message, node, **kwargs):
        # type: (unicode, nodes.Node, Any) -> None
        """Emit a warning for specific node.

        :param message: a message of warning
        :param node: a node related with the warning
        """
        (source, line) = get_source_line(node)
        if source and line:
            kwargs['location'] = "%s:%s" % (source, line)
        elif source:
            kwargs['location'] = "%s:" % source
        elif line:
            kwargs['location'] = "<unknown>:%s" % line

        self.warning(message, **kwargs)

    def verbose(self, msg, *args, **kwargs):
        # type: (unicode, Any, Any) -> None
        self.log(VERBOSE, msg, *args, **kwargs)

    def debug2(self, msg, *args, **kwargs):
        # type: (unicode, Any, Any) -> None
        self.log(DEBUG2, msg, *args, **kwargs)

    def process(self, msg, kwargs):  # type: ignore
        # type: (unicode, Dict) -> Tuple[unicode, Dict]
        extra = kwargs.setdefault('extra', {})
        if 'type' in kwargs:
            extra['type'] = kwargs.pop('type')
        if 'subtype' in kwargs:
            extra['subtype'] = kwargs.pop('subtype')
        if 'location' in kwargs:
            extra['location'] = kwargs.pop('location')
        if 'nonl' in kwargs:
            extra['nonl'] = kwargs.pop('nonl')

        return msg, kwargs


class NewLineStreamHandlerPY2(logging.StreamHandler):
    """StreamHandler which switches line terminator by record.nonl flag."""

    def emit(self, record):
        # type: (logging.LogRecord) -> None
        try:
            self.acquire()
            stream = self.stream  # type: ignore
            if getattr(record, 'nonl', False):
                # remove return code forcely when nonl=True
                self.stream = StringIO()
                super(NewLineStreamHandlerPY2, self).emit(record)
                stream.write(self.stream.getvalue()[:-1])
                stream.flush()
            else:
                super(NewLineStreamHandlerPY2, self).emit(record)
        finally:
            self.stream = stream
            self.release()


class NewLineStreamHandlerPY3(logging.StreamHandler):
    """StreamHandler which switches line terminator by record.nonl flag."""

    def emit(self, record):
        # type: (logging.LogRecord) -> None
        try:
            self.acquire()
            if getattr(record, 'nonl', False):
                # skip appending terminator when nonl=True
                self.terminator = ''
            super(NewLineStreamHandlerPY3, self).emit(record)
        finally:
            self.terminator = '\n'
            self.release()


if PY2:
    NewLineStreamHandler = NewLineStreamHandlerPY2
else:
    NewLineStreamHandler = NewLineStreamHandlerPY3


class MemoryHandler(logging.handlers.BufferingHandler):
    """Handler buffering all logs."""

    def __init__(self):
        super(MemoryHandler, self).__init__(-1)

    def shouldFlush(self, record):
        # type: (logging.LogRecord) -> bool
        return False  # never flush

    def flushTo(self, logger):
        # type: (logging.Logger) -> None
        self.acquire()
        try:
            for record in self.buffer:
                logger.handle(record)
            self.buffer = []  # type: List[logging.LogRecord]
        finally:
            self.release()


@contextmanager
def pending_logging():
    # type: () -> Generator
    """contextmanager to pend logging temporary."""
    logger = logging.getLogger()
    memhandler = MemoryHandler()

    try:
        handlers = []
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handlers.append(handler)

        logger.addHandler(memhandler)
        yield
    finally:
        logger.removeHandler(memhandler)

        for handler in handlers:
            logger.addHandler(handler)

        memhandler.flushTo(logger)


class InfoFilter(logging.Filter):
    """Filter error and warning messages."""

    def filter(self, record):
        # type: (logging.LogRecord) -> bool
        if record.levelno < logging.WARNING:
            return True
        else:
            return False


def is_suppressed_warning(type, subtype, suppress_warnings):
    # type: (unicode, unicode, List[unicode]) -> bool
    """Check the warning is suppressed or not."""
    if type is None:
        return False

    for warning_type in suppress_warnings:
        if '.' in warning_type:
            target, subtarget = warning_type.split('.', 1)
        else:
            target, subtarget = warning_type, None

        if target == type:
            if (subtype is None or subtarget is None or
               subtarget == subtype or subtarget == '*'):
                return True

    return False


class WarningSuppressor(logging.Filter):
    """Filter logs by `suppress_warnings`."""

    def __init__(self, app):
        # type: (Sphinx) -> None
        self.app = app
        super(WarningSuppressor, self).__init__()

    def filter(self, record):
        # type: (logging.LogRecord) -> bool
        type = getattr(record, 'type', None)
        subtype = getattr(record, 'subtype', None)

        if is_suppressed_warning(type, subtype, self.app.config.suppress_warnings):
            return False
        else:
            self.app._warncount += 1
            return True


class WarningIsErrorFilter(logging.Filter):
    """Raise exception if warning emitted."""

    def __init__(self, app):
        # type: (Sphinx) -> None
        self.app = app
        super(WarningIsErrorFilter, self).__init__()

    def filter(self, record):
        # type: (logging.LogRecord) -> bool
        if self.app.warningiserror:
            raise SphinxWarning(record.msg % record.args)
        else:
            return True


class WarningLogRecordTranslator(logging.Filter):
    """Converts a log record to one Sphinx expects

    * Make a instance of SphinxWarningLogRecord
    * docname to path if location given
    """
    def __init__(self, app):
        # type: (Sphinx) -> None
        self.app = app
        super(WarningLogRecordTranslator, self).__init__()

    def filter(self, record):  # type: ignore
        # type: (SphinxWarningLogRecord) -> bool
        if isinstance(record, logging.LogRecord):
            record.__class__ = SphinxWarningLogRecord  # force subclassing to handle location

        location = getattr(record, 'location', None)
        if isinstance(location, tuple):
            docname, lineno = location
            if docname and lineno:
                record.location = '%s:%s' % (self.app.env.doc2path(docname), lineno)
            elif docname:
                record.location = '%s' % self.app.env.doc2path(docname)
            else:
                record.location = None
        elif location and ':' not in location:
            record.location = '%s' % self.app.env.doc2path(location)

        return True


def setup(app, status, warning):
    # type: (Sphinx, IO, IO) -> None
    """Setup root logger for Sphinx"""
    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    # clear all handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    info_handler = NewLineStreamHandler(status)
    info_handler.addFilter(InfoFilter())
    info_handler.setLevel(VERBOSITY_MAP.get(app.verbosity))

    warning_handler = logging.StreamHandler(warning)
    warning_handler.addFilter(WarningSuppressor(app))
    warning_handler.addFilter(WarningIsErrorFilter(app))
    warning_handler.addFilter(WarningLogRecordTranslator(app))
    warning_handler.setLevel(logging.WARNING)
    logger.addHandler(info_handler)
    logger.addHandler(warning_handler)
