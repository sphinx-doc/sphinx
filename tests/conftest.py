# -*- coding: utf-8 -*-
import sys
import subprocess

import pytest
from six import StringIO, string_types

from util import SphinxTestApp


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


@pytest.fixture
def test_params(request):
    """
    test parameters that is specified by 'pytest.mark.testenv'

    :param bool build:
       If True, 'app' fixture will be build before test function is called.
       Default is False.
    :param Union[str, bool, None] specific_srcdir:
       If True, testroot directory will be copied into
       '<TMPDIR>/<TEST FUNCTION NAME>'.
       If string is specified, it copied into '<TMPDIR>/<THE STRING>'.
       You can used this feature for providing special crafted source
       directory. Also you can used for sharing source directory for
       parametrized testing and/or inter test functions. Default is None.
    :param Union[str, bool, None] shared_result:
       If True, app._status and app._warning objects will be shared in the
       parametrized test functions. If string is specified, the objects will
       be shred in the test functions that have same 'shared_result' value.
       If you don't specify specific_srcdir, this option override
       specific_srcdir param by 'shared_result' value. Default is None.
    """
    env = request.node.get_marker('testenv')
    kwargs = env.kwargs if env else {}
    result = {
       'build': False,  # pre build in fixture
        'specific_srcdir': None,
        'shared_result': None,
    }
    result.update(kwargs)

    if (result['shared_result'] and
            not isinstance(result['shared_result'], string_types)):
        r = result['shared_result'] = request.node.originalname or request.node.name

    if result['shared_result'] and not result['specific_srcdir']:
        result['specific_srcdir'] = result['shared_result']

    if (result['specific_srcdir'] and
        not isinstance(result['specific_srcdir'], string_types)):
        result['specific_srcdir'] = request.node.originalname or request.node.name

    return result


@pytest.fixture(scope='function')
def app(test_params, app_params, make_app, shared_result):
    """
    provides sphinx.application.Sphinx object
    """
    args, kwargs = app_params
    if test_params['specific_srcdir'] and 'srcdir' not in kwargs:
        kwargs['srcdir'] = test_params['specific_srcdir']

    if test_params['shared_result']:
        restore = shared_result.restore(test_params['shared_result'])
        kwargs.update(restore)

    app_ = make_app(*args, **kwargs)

    if test_params['build']:
        # if listdir is not empty, we can use built cache
        if not app_.outdir.listdir():
            app_.build()
    yield app_

    if test_params['shared_result']:
        shared_result.store(test_params['shared_result'], app_)


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


class SharedResult(object):
    cache = {}

    def store(self, key, app_):
        if key in self.cache:
            return
        data = {
            'status': app_._status.getvalue(),
            'warning': app_._warning.getvalue(),
        }
        self.cache[key] = data

    def restore(self, key):
        if key not in self.cache:
            return {}
        data = self.cache[key]
        return {
            'status': StringIO(data['status']),
            'warning': StringIO(data['warning']),
        }


@pytest.fixture
def shared_result():
    return SharedResult()


@pytest.fixture(scope='module', autouse=True)
def _shared_result_cache():
    SharedResult.cache.clear()


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


def pytest_addoption(parser):
    """
    the test that have pytest.mark.env('foobar') will be skipped when
    '-S foobar' command-line option is provided.
    """
    parser.addoption("-S", action="store", metavar="NAME",
                     help="skip tests matching the environment NAME.")


def pytest_configure(config):
    """
    the test that have pytest.mark.env('foobar') will be skipped when
    '-S foobar' command-line option is provided.
    """
    # register an additional marker
    config.addinivalue_line("markers",
        "env(name): mark test to run only on named environment")


def pytest_runtest_setup(item):
    """
    the test that have pytest.mark.env('foobar') will be skipped when
    '-S foobar' command-line option is provided.
    """
    envmarker = item.get_marker("env")
    if envmarker is not None:
        envname = envmarker.args[0]
        if envname == item.config.getoption("-S"):
            pytest.skip("skip test %r" % envname)
