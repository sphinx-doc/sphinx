# -*- coding: utf-8 -*-
"""
    test_intl
    ~~~~~~~~~

    Test message patching for internationalization purposes.  Runs the text
    builder in the test root.

    :copyright: Copyright 2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from subprocess import Popen, PIPE

from util import *
from util import SkipTest


def setup_module():
    (test_root / 'xx' / 'LC_MESSAGES').makedirs()
    # Compile all required catalogs into binary format (*.mo).
    for catalog in 'bom', 'subdir':
        try:
            p = Popen(['msgfmt', test_root / '%s.po' % catalog, '-o',
                test_root / 'xx' / 'LC_MESSAGES' / '%s.mo' % catalog],
                stdout=PIPE, stderr=PIPE)
        except OSError:
            # The test will fail the second time it's run if we don't
            # tear down here. Not sure if there's a more idiomatic way
            # of ensuring that teardown gets run in the event of an
            # exception from the setup function.
            teardown_module()
            raise SkipTest  # most likely msgfmt was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print stdout
                print stderr
                assert False, 'msgfmt exited with return code %s' % p.returncode
            assert (test_root / 'xx' / 'LC_MESSAGES' / ('%s.mo' % catalog)
                   ).isfile(), 'msgfmt failed'


def teardown_module():
    (test_root / '_build').rmtree(True)
    (test_root / 'xx').rmtree(True)


@with_app(buildername='text',
          confoverrides={'language': 'xx', 'locale_dirs': ['.']})
def test_simple(app):
    app.builder.build(['bom'])
    result = (app.outdir / 'bom.txt').text(encoding='utf-8')
    expect = (u"\nDatei mit UTF-8"
              u"\n***************\n" # underline matches new translation
              u"\nThis file has umlauts: äöü.\n")
    assert result == expect


@with_app(buildername='text',
          confoverrides={'language': 'xx', 'locale_dirs': ['.']})
def test_subdir(app):
    app.builder.build(['subdir/includes'])
    result = (app.outdir / 'subdir' / 'includes.txt').text(encoding='utf-8')
    assert result.startswith(u"\ntranslation\n***********\n\n")
