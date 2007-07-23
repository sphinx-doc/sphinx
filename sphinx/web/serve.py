# -*- coding: utf-8 -*-
"""
    sphinx.web.serve
    ~~~~~~~~~~~~~~~~

    This module optionally wraps the `wsgiref` module so that it reloads code
    automatically. Works with any WSGI application but it won't help in non
    `wsgiref` environments. Use it only for development.

    :copyright: 2007 by Armin Ronacher, Georg Brandl.
    :license: Python license.
"""
import os
import sys
import time
import thread


def reloader_loop(extra_files):
    """When this function is run from the main thread, it will force other
    threads to exit when any modules currently loaded change.

    :param extra_files: a list of additional files it should watch.
    """
    mtimes = {}
    while True:
        for filename in filter(None, [getattr(module, '__file__', None)
                                      for module in sys.modules.values()] +
                               extra_files):
            while not os.path.isfile(filename):
                filename = os.path.dirname(filename)
                if not filename:
                    break
            if not filename:
                continue

            if filename[-4:] in ('.pyc', '.pyo'):
                filename = filename[:-1]

            mtime = os.stat(filename).st_mtime
            if filename not in mtimes:
                mtimes[filename] = mtime
                continue
            if mtime > mtimes[filename]:
                sys.exit(3)
        time.sleep(1)


def restart_with_reloader():
    """Spawn a new Python interpreter with the same arguments as this one,
    but running the reloader thread."""
    while True:
        print '* Restarting with reloader...'
        args = [sys.executable] + sys.argv
        if sys.platform == 'win32':
            args = ['"%s"' % arg for arg in args]
        new_environ = os.environ.copy()
        new_environ['RUN_MAIN'] = 'true'
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
        if exit_code != 3:
            return exit_code


def run_with_reloader(main_func, extra_watch):
    """
    Run the given function in an independent python interpreter.
    """
    if os.environ.get('RUN_MAIN') == 'true':
        thread.start_new_thread(main_func, ())
        try:
            reloader_loop(extra_watch)
        except KeyboardInterrupt:
            return
    try:
        sys.exit(restart_with_reloader())
    except KeyboardInterrupt:
        pass


def run_simple(hostname, port, make_app, use_reloader=False,
               extra_files=None):
    """
    Start an application using wsgiref and with an optional reloader.
    """
    from wsgiref.simple_server import make_server
    def inner():
        application = make_app()
        print '* Startup complete.'
        srv = make_server(hostname, port, application)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
    if os.environ.get('RUN_MAIN') != 'true':
        print '* Running on http://%s:%d/' % (hostname, port)
    if use_reloader:
        run_with_reloader(inner, extra_files or [])
    else:
        inner()
