# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from sphinx.util.urepr import urepr


def assert_round_trips(obj):
    """ Check the repr is valid """
    assert eval(urepr(obj)) == obj

def test_text():
    assert urepr('test') == "u'test'"
    assert urepr(r'日本語\PATH') == r"u'日本語\\PATH'"
    assert urepr(r'αβ\PATH')     == r"u'αβ\\PATH'"
    assert urepr(r'АБГ\PATH')    == r"u'АБГ\\PATH'"
    assert urepr('\0\x01\x02\x03\n') == r"u'\0\x01\x02\x03\n'"

def test_bytes():
    # the encoding shouldn't be guessed for bytes
    assert urepr(r'日本語\PATH'.encode('utf8')) == r"b'\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e\\PATH'"

def test_sequences():
    assert_round_trips([r'日本語\PATH', r'АБГ\PATH'])
    assert_round_trips({r'日本語\PATH': r'АБГ\PATH'})
