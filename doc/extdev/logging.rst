.. _logging-api:

Logging API
===========

.. currentmodule:: sphinx.util.logging

.. autofunction:: getLogger(name, *, extension=None)

Identifying an extension
------------------------

The logger name (usually ``__name__``) identifies the source in the underlying
Python log record, but Sphinx does not display that name in its output.
To identify your extension in the output, pass ``extension`` when creating
the logger. The name is then used for every message from that adapter::

    from sphinx.util import logging

    logger = logging.getLogger(__name__, extension='my_extension')
    logger.info('Generating examples')
    logger.warning('Example not found', type='my_extension', subtype='missing')

Sphinx displays these messages as::

    [my_extension] Generating examples
    WARNING: [my_extension] Example not found [my_extension.missing]

The trailing warning category is only displayed when
:confval:`show_warning_types` is enabled.
The extension prefix is independent of that setting and does not affect
:confval:`suppress_warnings`: continue to use ``type`` and ``subtype`` to
categorise warnings for suppression.
With a source location, the output is formatted as
``path:line: WARNING: [my_extension] message``.
If you prefer to display the module name, use ``extension=__name__``.
Omitting ``extension`` from :func:`getLogger`, or passing ``None`` or an empty
string, leaves messages unprefixed.

Individual logging calls can override the default or disable the prefix::

    logger.info('A different label', extension='other_extension')
    logger.info('No extension prefix', extension=None)

These overrides do not change the adapter's default.
Adapters created with the same logger name can have different extension labels
without affecting each other.

.. versionadded:: 9.1.1
   The ``extension`` keyword argument.

Logger methods
--------------

.. autoclass:: SphinxLoggerAdapter(logging.LoggerAdapter)

   .. method:: SphinxLoggerAdapter.error(msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.critical(msg, *args, **kwargs)
   .. method:: SphinxLoggerAdapter.warning(msg, *args, **kwargs)

      Logs a message on this logger with the specified level.
      Basically, the arguments are as with python's logging module.

      In addition, Sphinx logger supports following keyword arguments:

      **extension**
        The extension name to display in square brackets before the message.
        Overrides the default passed to :func:`getLogger`; ``None`` or an empty
        string disables the prefix for this message.
        Supported at all logging levels; see `Identifying an extension`_.

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

      **extension**
        The extension name to display in square brackets before the message.
        For more detail, see `Identifying an extension`_.

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
