# -*- coding: utf-8 -*-
import sys
import subprocess

import pytest
from six import StringIO

from util import SphinxTestApp, path


@pytest.fixture
def app_params(request):
    """
    parameters that is specified by 'pytest.mark.sphinx' for
    sphinx.application.Sphinx initialization
    """
    markers = request.node.get_marker("sphinx")
    pargs = {}
    kwargs = {}

    if markers is not None:
        # to avoid stacking positional args
        for info in reversed(list(markers)):
            for i, a in enumerate(info.args):
                pargs[i] = a
            kwargs.update(info.kwargs)

    args = [pargs[i] for i in sorted(pargs.keys())]
    return args, kwargs


@pytest.fixture(scope='function')
def app(app_params, make_app):
    """
    provides sphinx.application.Sphinx object
    """
    args, kwargs = app_params
    app_ = make_app(*args, **kwargs)
    yield app_


@pytest.fixture(scope='function')
def status(app):
    """
    compat for testing with previous @with_app decorator
    """
    return app._status


@pytest.fixture(scope='function')
def warning(app):
    """
    compat for testing with previous @with_app decorator
    """
    return app._warning


@pytest.fixture()
def make_app():
    """
    provides make_app function to initialize SphinxTestApp instance.
    if you want to initialize 'app' in your test function. please use this
    instead of using SphinxTestApp class directory.
    """
    apps = []
    syspath = sys.path[:]

    def make(*args, **kwargs):
        status, warning = StringIO(), StringIO()
        kwargs.setdefault('status', status)
        kwargs.setdefault('warning', warning)
        app_ = SphinxTestApp(*args, **kwargs)
        apps.append(app_)
        return app_
    yield make

    sys.path[:] = syspath
    for app_ in apps:
        app_.cleanup()


@pytest.fixture
def if_graphviz_found(app):
    """
    The test will be skipped when using 'if_graphviz_found' fixture and graphviz
    dot command is not found.
    """
    graphviz_dot = getattr(app.config, 'graphviz_dot', '')
    try:
        if graphviz_dot:
            dot = subprocess.Popen([graphviz_dot, '-V'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)  # show version
            dot.communicate()
            return
    except OSError:  # No such file or directory
        pass

    pytest.skip('graphviz "dot" is not available')


@pytest.fixture
def tempdir(tmpdir):
    """
    temporary directory that wrapped with `path` class.
    this fixture is for compat with old test implementation.
    """
    return path(tmpdir)
