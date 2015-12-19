# -*- coding: utf-8 -*-
"""
    test_util
    ~~~~~~~~~~~~~~~

    Tests util functions.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from sphinx.util import encode_uri


def test_encode_uri():
    expected = (u'https://ru.wikipedia.org/wiki/%D0%A1%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D0%B0_'
                u'%D1%83%D0%BF%D1%80%D0%B0%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D1%8F_'
                u'%D0%B1%D0%B0%D0%B7%D0%B0%D0%BC%D0%B8_%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D1%85')
    uri = 'https://ru.wikipedia.org/wiki/Система_управления_базами_данных'
    assert expected, encode_uri(uri)
