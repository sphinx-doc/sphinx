# -*- coding: utf-8 -*-
"""
    test_build_gettext
    ~~~~~~~~~~~~~~~~~~

    Test the build process with gettext builder with the test root.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import gettext
import os
import re
from subprocess import Popen, PIPE

from util import test_root, test_roots, with_app, SkipTest


def teardown_module():
    (test_root / '_build').rmtree(True)
    (test_roots / 'test-intl' / '_build').rmtree(True),


@with_app(buildername='gettext')
def test_all(app):
    # Generic build; should fail only when the builder is horribly broken.
    app.builder.build_all()


@with_app(buildername='gettext')
def test_build(app):
    # Do messages end up in the correct location?
    app.builder.build(['extapi', 'subdir/includes'])
    # top-level documents end up in a message catalog
    assert (app.outdir / 'extapi.pot').isfile()
    # directory items are grouped into sections
    assert (app.outdir / 'subdir.pot').isfile()


@with_app(buildername='gettext')
def test_seealso(app):
    # regression test for issue #960
    app.builder.build(['markup'])
    catalog = (app.outdir / 'markup.pot').text(encoding='utf-8')
    assert 'msgid "something, something else, something more"' in catalog


@with_app(buildername='gettext')
def test_gettext(app):
    app.builder.build(['markup'])

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
                print stdout
                print stderr
                assert False, 'msginit exited with return code %s' % \
                        p.returncode
        assert (app.outdir / 'en_US.po').isfile(), 'msginit failed'
        try:
            p = Popen(['msgfmt', 'en_US.po', '-o',
                os.path.join('en', 'LC_MESSAGES', 'test_root.mo')],
                stdout=PIPE, stderr=PIPE)
        except OSError:
            raise SkipTest  # most likely msgfmt was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print stdout
                print stderr
                assert False, 'msgfmt exited with return code %s' % \
                        p.returncode
        assert (app.outdir / 'en' / 'LC_MESSAGES' / 'test_root.mo').isfile(), \
                'msgfmt failed'
    finally:
        os.chdir(cwd)

    _ = gettext.translation('test_root', app.outdir, languages=['en']).gettext
    assert _("Testing various markup") == u"Testing various markup"


@with_app(buildername='gettext',
          srcdir=(test_roots / 'test-intl'),
          doctreedir=(test_roots / 'test-intl' / '_build' / 'doctree'),
          confoverrides={'gettext_compact': False})
def test_gettext_index_entries(app):
    # regression test for #976
    app.builder.build(['index_entries'])

    _msgid_getter = re.compile(r'msgid "(.*)"').search
    def msgid_getter(msgid):
        m = _msgid_getter(msgid)
        if m:
            return m.groups()[0]
        return None

    pot = (app.outdir / 'index_entries.pot').text(encoding='utf-8')
    msgids = filter(None, map(msgid_getter, pot.splitlines()))

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


@with_app(buildername='gettext',
          srcdir=(test_roots / 'test-intl'),
          doctreedir=(test_roots / 'test-intl' / '_build' / 'doctree'))
def test_gettext_template(app):
    app.builder.build_all()
    assert (app.outdir / 'sphinx.pot').isfile()

    result = (app.outdir / 'sphinx.pot').text(encoding='utf-8')
    assert "Welcome" in result
    assert "Sphinx %(version)s" in result
