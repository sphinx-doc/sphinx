.. _logging-api:

Logging API
===========

.. function:: sphinx.util.logging.getLogger(name)

   Returns a logger wrapped by :class:`SphinxLoggerAdapter` with the specified *name*.

   Example usage::

     from sphinx.util import logging  # Load on top of python's logging module

     logger = logging.getLogger(__name__)
     logger.info('Hello, this is an extension!')

.. class:: SphinxLoggerAdapter(logging.LoggerAdapter)

   .. method:: SphinxLoggerAdapter.error(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.critical(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.warning(level, msg, *args, **kwargs)

      Logs a message on this logger with the specified level.
      Basically, the arguments are as with python's logging module.

      In addition, Sphinx logger supports following keyword arguments:

      **type**, ***subtype***
        Categories of warning logs.  It is used to suppress
        warnings by :confval:`suppress_warnings` setting.

      **location**
        Where the warning happened.  It is used to include
        the path and line number in each log.  It allows docname,
        tuple of docname and line number and nodes::

          logger = sphinx.util.logging.getLogger(__name__)
          logger.warning('Warning happened!', location='index')
          logger.warning('Warning happened!', location=('chapter1/index', 10))
          logger.warning('Warning happened!', location=some_node)

      **color**
        The color of logs.  By default, warning level logs are
        colored as ``"darkred"``.  The others are not colored.

   .. method:: SphinxLoggerAdapter.log(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.info(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.verbose(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.debug(level, msg, *args, **kwargs)

      Logs a message to this logger with the specified level.
      Basically, the arguments are as with python's logging module.

      In addition, Sphinx logger supports following keyword arguments:

      **nonl**
        If true, the logger does not fold lines at the end of the log message.
        The default is ``False``.

      **color**
        The color of logs.  By default, debug level logs are
        colored as ``"darkgray"``, and debug2 level ones are ``"lightgray"``.
        The others are not colored.

.. function:: pending_logging()

   Marks all logs as pending::

     with pending_logging():
       logger.warning('Warning message!')  # not flushed yet
       some_long_process()

     # the warning is flushed here

.. function:: pending_warnings()

   Marks warning logs as pending.  Similar to :func:`pending_logging`.
