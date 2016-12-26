# -*- coding: utf-8 -*-
import sys
import contextlib

import pytest
from six import StringIO

from util import TestApp


@pytest.fixture
def app_params(request):
    markers = request.node.get_marker("sphinx")
    pargs = {}
    kwargs = {
        'status': StringIO(),
        'warning': StringIO(),
    }

    if markers is not None:
        # to avoid stacking positional args
        for info in reversed(list(markers)):
            for i, a in enumerate(info.args):
                pargs[i] = a
            kwargs.update(info.kwargs)

    args = [pargs[i] for i in sorted(pargs.keys())]
    return args, kwargs


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
def app(app_params, make_app):
    args, kwargs = app_params
    coderoot = kwargs.pop('coderoot', None)
    if coderoot:
        sys.path.append(coderoot)
    app_ = make_app(*args, **kwargs)
    yield app_
    if coderoot:
        sys.path.remove(coderoot)


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
        app_ = TestApp(*args, **kwargs)
        app_.status = kwargs.get('status')
        app_.warning = kwargs.get('warning')
        apps.append(app_)
        return app_
    yield make
    for app_ in apps:
        app_.cleanup()


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
