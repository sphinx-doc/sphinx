# -*- coding: utf-8 -*-
"""
    test_build_gettext
    ~~~~~~~~~~~~~~~~~~

    Test the build process with gettext builder with the test root.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import re
import gettext
from subprocess import Popen, PIPE

from nose.tools import assert_true, assert_equal

from util import with_app, gen_with_app, SkipTest, assert_in


@gen_with_app('gettext', srcdir='root-gettext')
def test_all(app, status, warning):
    # Generic build; should fail only when the builder is horribly broken.
    app.builder.build_all()

    # Do messages end up in the correct location?
    # top-level documents end up in a message catalog
    yield assert_true, (app.outdir / 'extapi.pot').isfile()
    # directory items are grouped into sections
    yield assert_true, (app.outdir / 'subdir.pot').isfile()

    # regression test for issue #960
    catalog = (app.outdir / 'markup.pot').text(encoding='utf-8')
    yield assert_in, 'msgid "something, something else, something more"', catalog

    (app.outdir / 'en' / 'LC_MESSAGES').makedirs()
    cwd = os.getcwd()
    os.chdir(app.outdir)
    try:
        try:
            p = Popen(['msginit', '--no-translator', '-i', 'markup.pot',
                       '--locale', 'en_US'],
                      stdout=PIPE, stderr=PIPE)
        except OSError:
            raise SkipTest  # most likely msginit was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print(stdout)
                print(stderr)
                assert False, 'msginit exited with return code %s' % \
                    p.returncode
        yield assert_true, (app.outdir / 'en_US.po').isfile(), 'msginit failed'
        try:
            p = Popen(['msgfmt', 'en_US.po', '-o',
                       os.path.join('en', 'LC_MESSAGES', 'test_root.mo')],
                      stdout=PIPE, stderr=PIPE)
        except OSError:
            raise SkipTest  # most likely msgfmt was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print(stdout)
                print(stderr)
                assert False, 'msgfmt exited with return code %s' % \
                    p.returncode
        yield (assert_true,
               (app.outdir / 'en' / 'LC_MESSAGES' / 'test_root.mo').isfile(),
               'msgfmt failed')
    finally:
        os.chdir(cwd)

    _ = gettext.translation('test_root', app.outdir, languages=['en']).gettext
    yield assert_equal, _("Testing various markup"), u"Testing various markup"


@with_app('gettext', testroot='intl',
          confoverrides={'gettext_compact': False})
def test_gettext_index_entries(app, status, warning):
    # regression test for #976
    app.builder.build(['index_entries'])

    _msgid_getter = re.compile(r'msgid "(.*)"').search

    def msgid_getter(msgid):
        m = _msgid_getter(msgid)
        if m:
            return m.groups()[0]
        return None

    pot = (app.outdir / 'index_entries.pot').text(encoding='utf-8')
    msgids = [_f for _f in map(msgid_getter, pot.splitlines()) if _f]

    expected_msgids = [
        "i18n with index entries",
        "index target section",
        "this is :index:`Newsletter` target paragraph.",
        "various index entries",
        "That's all.",
        "Mailing List",
        "Newsletter",
        "Recipients List",
        "First",
        "Second",
        "Third",
        "Entry",
        "See",
        "Module",
        "Keyword",
        "Operator",
        "Object",
        "Exception",
        "Statement",
        "Builtin",
    ]
    for expect in expected_msgids:
        assert expect in msgids
        msgids.remove(expect)

    # unexpected msgid existent
    assert msgids == []


@with_app('gettext', testroot='intl',
          confoverrides={'gettext_compact': False, 'gettext_additional_targets': []})
def test_gettext_disable_index_entries(app, status, warning):
    # regression test for #976
    app.builder.build(['index_entries'])

    _msgid_getter = re.compile(r'msgid "(.*)"').search

    def msgid_getter(msgid):
        m = _msgid_getter(msgid)
        if m:
            return m.groups()[0]
        return None

    pot = (app.outdir / 'index_entries.pot').text(encoding='utf-8')
    msgids = [_f for _f in map(msgid_getter, pot.splitlines()) if _f]

    expected_msgids = [
        "i18n with index entries",
        "index target section",
        "this is :index:`Newsletter` target paragraph.",
        "various index entries",
        "That's all.",
    ]
    for expect in expected_msgids:
        assert expect in msgids
        msgids.remove(expect)

    # unexpected msgid existent
    assert msgids == []


@with_app(buildername='gettext', testroot='intl')
def test_gettext_template(app, status, warning):
    app.builder.build_all()
    assert (app.outdir / 'sphinx.pot').isfile()

    result = (app.outdir / 'sphinx.pot').text(encoding='utf-8')
    assert "Welcome" in result
    assert "Sphinx %(version)s" in result
