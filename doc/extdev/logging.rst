.. _logging-api:

Logging API
===========

.. currentmodule:: sphinx.util.logging

.. autofunction:: getLogger(name)

.. autoclass:: SphinxLoggerAdapter(logging.LoggerAdapter)

   .. method:: SphinxLoggerAdapter.error(msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.critical(msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.warning(msg, *args, **kwargs)

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
        The color of logs.  By default, error level logs are colored as
        ``"darkred"``, critical level ones is not colored, and warning level
        ones are colored as ``"red"``.

   .. method:: SphinxLoggerAdapter.log(level, msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.info(msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.verbose(msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.debug(msg, *args, **kwargs)

      Logs a message to this logger with the specified level.
      Basically, the arguments are as with python's logging module.

      In addition, Sphinx logger supports following keyword arguments:

      **nonl**
        If true, the logger does not fold lines at the end of the log message.
        The default is ``False``.

      **location**
        Where the message emitted.  For more detail, see
        :meth:`SphinxLoggerAdapter.warning`.

      **color**
        The color of logs.  By default, info and verbose level logs are not
        colored, and debug level ones are colored as ``"darkgray"``.

.. autofunction:: pending_logging()

.. autofunction:: pending_warnings()

.. autofunction:: prefixed_warnings()
