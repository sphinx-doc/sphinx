.. _logging-api:

Logging API
===========

.. function:: sphinx.util.logging.getLogger(name)

   Return a logger wrapped by :class:`SphinxLoggerAdapter` with the specified *name*.

   Example usage::

     from sphinx.util import logging  # Load instead python's logging module

     logger = logging.getLogger(__name__)
     logger.info('Hello, this is an extension!')

.. class:: SphinxLoggerAdapter(logging.LoggerAdapter)

   .. method:: SphinxLoggerAdapter.error(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.critical(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.warning(level, msg, *args, **kwargs)

      Logs a message with specified level on this logger.
      Basically, the arguments are same as python's logging module.

      In addition, Sphinx logger supports following keyword arguments:

      **type**, ***subtype***
        Indicate categories of warning logs.  It is used to suppress
        warnings by :confval:`suppress_warnings` setting.

      **location**
        Indicate where the warning is happened.  It is used to show
        the path and line number to each log.  It allows docname,
        tuple of docname and line number and nodes::

          logger = sphinx.util.logging.getLogger(__name__)
          logger.warning('Warning happened!', location='index')
          logger.warning('Warning happened!', location=('chapter1/index', 10))
          logger.warning('Warning happened!', location=some_node)

      **color**
        Indicate the color of logs.  By default, warning level logs are
        colored as ``"darkred"``.  The others are not colored.

   .. method:: SphinxLoggerAdapter.log(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.info(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.verbose(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.debug(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.debug2(level, msg, *args, **kwargs)

      Logs a message with specified level on this logger.
      Basically, the arguments are same as python's logging module.

      In addition, Sphinx logger supports following keyword arguments:

      **nonl**
        If true, the logger does not fold lines at end of the log message.
        The default is ``False``.

      **color**
        Indicate the color of logs.  By default, debug level logs are
        colored as ``"darkgray"``, and debug2 ones are ``"lightgray"``.
        The others are not colored.

.. function:: pending_logging()

   Make all logs as pending while the context::

     with pending_logging():
       logger.warning('Warning message!')  # not flushed yet
       some_long_process()

     # the warning is flushed here

.. function:: pending_warnings()

   Make warning logs as pending while the context.  Similar to :func:`pending_logging`.
