# -*- coding: utf-8 -*-
import sys

import pytest
from six import StringIO

from util import TestApp


# def pytest_addoption(parser):
#     parser.addoption("-E", action="store", metavar="NAME",
#         help="only run tests matching the environment NAME.")


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers",
        "sphinx(**kw): mark test to run with sphinx.application.Application(**kw)")


def sphinx_app_by_marker(markers):
    if markers is not None:
        pargs = {}
        kwargs = {
            'status': StringIO(),
            'warning': StringIO(),
        }

        for info in reversed(list(markers)):
            for i, a in enumerate(info.args):
                pargs[i] = a
            kwargs.update(info.kwargs)
        args = [pargs[i] for i in sorted(pargs.keys())]
        app_ = TestApp(*args, **kwargs)
        app_.status = kwargs.get('status')
        app_.warning = kwargs.get('warning')
        return app_
    return None


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
@pytest.hookimpl(hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    syspath_marker = pyfuncitem.get_marker("syspath")
    if syspath_marker:
        import pdb;pdb.set_trace()
        sys.path.append(syspath_marker.args[0])

    outcome = yield
    # outcome.excinfo may be None or a (cls, val, tb) tuple

    if syspath_marker:
        sys.path.remove(syspath_marker.args[0])


@pytest.fixture(scope='function')
def app(request):
    # import pdb;pdb.set_trace()
    marker = request.node.get_marker("sphinx")
    app_ = sphinx_app_by_marker(marker)
    yield app_
    app_.cleanup()


# # テスト関数内でアプリケーションを組み立てるfixture
# @pytest.fixture()
# def make_app(request):
#     apps = []
#
#     def make(*args, **kwargs):
#         status, warning = StringIO(), StringIO()
#         kwargs['status'] = status
#         kwargs['warning'] = warning
#         app_ = TestApp(*args, **kwargs)
#         app_.status = kwargs.get('status')
#         app_.warning = kwargs.get('warning')
#         apps.append(app_)
#         return app_
#     yield make
#     for app_ in apps:
#         app_.cleanup()
