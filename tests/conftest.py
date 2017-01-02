# -*- coding: utf-8 -*-
import sys
import contextlib

import pytest
from six import StringIO, string_types

from util import SphinxTestApp


@pytest.fixture
def app_params(request):
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
    env = request.node.get_marker('testenv')
    kwargs = env.kwargs if env else {}
    result = {
       'build': False,  # pre build in fixture
        'specific_srcdir': None,  # use specific src dir. if True, use test function name
        'shared_result': None,  # if True, app object is shared in each parametrized test
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


## 各テストのセットアップ時に呼ばれる
# def pytest_runtest_setup(item):
#     marker = item.get_marker("sphinx")
#     # import pdb;pdb.set_trace()
#     app = sphinx_app_by_marker(marker)
#     # FIXME: how to call app.cleanup()?
#     # def fin(*a, **k):
#     #     import pdb;pdb.set_trace()
#     #     app.cleanup()
#     # item.addfinalizer(fin)


# 各テストの実行時に呼ばれる
# @pytest.hookimpl(hookwrapper=True)
# def pytest_pyfunc_call(pyfuncitem):
#     syspath_marker = pyfuncitem.get_marker("syspath")
#     if syspath_marker:
#         import pdb;pdb.set_trace()
#         sys.path.append(syspath_marker.args[0])
#
#     outcome = yield
#     # outcome.excinfo may be None or a (cls, val, tb) tuple
#
#     if syspath_marker:
#         sys.path.remove(syspath_marker.args[0])


@pytest.fixture(scope='function')
def app(test_params, app_params, make_app, shared_result):
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
    return app.status


@pytest.fixture(scope='function')
def warning(app):
    return app.warning


# # テスト関数内でアプリケーションを組み立てるfixture
@pytest.fixture()
def make_app():
    apps = []

    def make(*args, **kwargs):
        status, warning = StringIO(), StringIO()
        kwargs.setdefault('status', status)
        kwargs.setdefault('warning', warning)
        app_ = SphinxTestApp(*args, **kwargs)
        app_.status = kwargs.get('status')
        app_.warning = kwargs.get('warning')
        apps.append(app_)
        return app_
    yield make
    for app_ in apps:
        app_.cleanup()


class SharedResult(object):
    cache = {}

    def store(self, key, app_):
        if key in self.cache:
            return
        data = {
            'status': app_.status.getvalue(),
            'warning': app_.warning.getvalue(),
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


@pytest.fixture()
def syspath():
    @contextlib.contextmanager
    def syspath_context(path):
        sys.path.append(path)
        yield syspath
        sys.path.remove(path)
    yield syspath_context


def pytest_addoption(parser):
    parser.addoption("-S", action="store", metavar="NAME",
        help="skip tests matching the environment NAME.")


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line("markers",
        "env(name): mark test to run only on named environment")


def pytest_runtest_setup(item):
    envmarker = item.get_marker("env")
    if envmarker is not None:
        envname = envmarker.args[0]
        if envname == item.config.getoption("-S"):
            pytest.skip("skip test %r" % envname)
