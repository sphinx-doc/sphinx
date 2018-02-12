# -*- coding: utf-8 -*-
"""
    py3/test_util_inspect
    ~~~~~~~~~~~~~~~~~~~~~

    Tests util.inspect functions.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.util import inspect


def test_Signature_keyword_only_arguments():
    def func1(arg1, arg2, *, arg3=None, arg4=None):
        pass

    def func2(*, arg3, arg4):
        pass

    sig = inspect.Signature(func1).format_args()
    assert sig == '(arg1, arg2, *, arg3=None, arg4=None)'

    sig = inspect.Signature(func2).format_args()
    assert sig == '(*, arg3, arg4)'
