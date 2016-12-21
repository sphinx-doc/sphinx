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
from six import string_types
from contextlib import contextmanager
from docutils.utils import get_source_line

from sphinx.errors import SphinxWarning
from sphinx.util.console import darkred  # type: ignore


def getLogger(name):
    """Get logger wrapped by SphinxLoggerAdapter."""
    return SphinxLoggerAdapter(logging.getLogger(name), {})


class SphinxLogRecord(logging.LogRecord):
    """Log record class supporting location"""
    def getMessage(self):
        message = super(SphinxLogRecord, self).getMessage()
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

    def process(self, msg, kwargs):
        extra = kwargs.setdefault('extra', {})
        if 'type' in kwargs:
            extra['type'] = kwargs.pop('type')
        if 'subtype' in kwargs:
            extra['subtype'] = kwargs.pop('subtype')
        if 'location' in kwargs:
            extra['location'] = kwargs.pop('location')

        return msg, kwargs


class MemoryHandler(logging.handlers.BufferingHandler):
    """Handler buffering all logs."""

    def __init__(self):
        super(MemoryHandler, self).__init__(-1)

    def shouldFlush(self, record):
        return False  # never flush

    def flushTo(self, logger):
        self.acquire()
        try:
            for record in self.buffer:
                logger.handle(record)
            self.buffer = []  # type: ignore
        finally:
            self.release()


@contextmanager
def pending_logging():
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


def is_suppressed_warning(type, subtype, suppress_warnings):
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
        self.app = app
        super(WarningSuppressor, self).__init__()

    def filter(self, record):
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
        self.app = app
        super(WarningIsErrorFilter, self).__init__()

    def filter(self, record):
        if self.app.warningiserror:
            raise SphinxWarning(record.msg % record.args)
        else:
            return True


class LogRecordTranslator(logging.Filter):
    """Converts a log record to one Sphinx expects

    * Make a instance of SphinxLogRecord
    * docname to path if location given
    """
    def __init__(self, app):
        self.app = app
        super(LogRecordTranslator, self).__init__()

    def filter(self, record):
        if isinstance(record, logging.LogRecord):
            record.__class__ = SphinxLogRecord  # force subclassing to handle location

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
    """Setup root logger for Sphinx"""
    logger = logging.getLogger()

    # clear all handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    warning_handler = logging.StreamHandler(warning)
    warning_handler.addFilter(WarningSuppressor(app))
    warning_handler.addFilter(WarningIsErrorFilter(app))
    warning_handler.addFilter(LogRecordTranslator(app))
    warning_handler.setLevel(logging.WARNING)
    logger.addHandler(warning_handler)
