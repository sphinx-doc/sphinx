"""Test inventory util functions."""

import posixpath
import zlib
from io import BytesIO

from sphinx.ext.intersphinx import InventoryFile
from sphinx.testing.util import SphinxTestApp

inventory_v1 = b'''\
# Sphinx inventory version 1
# Project: foo
# Version: 1.0
module mod foo.html
module.cls class foo.html
'''

inventory_v2 = b'''\
# Sphinx inventory version 2
# Project: foo
# Version: 2.0
# The remainder of this file is compressed with zlib.
''' + zlib.compress(b'''\
module1 py:module 0 foo.html#module-module1 Long Module desc
module2 py:module 0 foo.html#module-$ -
module1.func py:function 1 sub/foo.html#$ -
module1.Foo.bar py:method 1 index.html#foo.Bar.baz -
CFunc c:function 2 cfunc.html#CFunc -
std cpp:type 1 index.html#std -
std::uint8_t cpp:type 1 index.html#std_uint8_t -
foo::Bar cpp:class 1 index.html#cpp_foo_bar -
foo::Bar::baz cpp:function 1 index.html#cpp_foo_bar_baz -
foons cpp:type 1 index.html#foons -
foons::bartype cpp:type 1 index.html#foons_bartype -
a term std:term -1 glossary.html#term-a-term -
ls.-l std:cmdoption 1 index.html#cmdoption-ls-l -
docname std:doc -1 docname.html -
foo js:module 1 index.html#foo -
foo.bar js:class 1 index.html#foo.bar -
foo.bar.baz js:method 1 index.html#foo.bar.baz -
foo.bar.qux js:data 1 index.html#foo.bar.qux -
a term including:colon std:term -1 glossary.html#term-a-term-including-colon -
''')

inventory_v2_not_having_version = b'''\
# Sphinx inventory version 2
# Project: foo
# Version:
# The remainder of this file is compressed with zlib.
''' + zlib.compress(b'''\
module1 py:module 0 foo.html#module-module1 Long Module desc
''')


def test_read_inventory_v1():
    f = BytesIO(inventory_v1)
    invdata = InventoryFile.load(f, '/util', posixpath.join)
    assert invdata['py:module']['module'] == \
        ('foo', '1.0', '/util/foo.html#module-module', '-')
    assert invdata['py:class']['module.cls'] == \
        ('foo', '1.0', '/util/foo.html#module.cls', '-')


def test_read_inventory_v2():
    f = BytesIO(inventory_v2)
    invdata = InventoryFile.load(f, '/util', posixpath.join)

    assert len(invdata['py:module']) == 2
    assert invdata['py:module']['module1'] == \
        ('foo', '2.0', '/util/foo.html#module-module1', 'Long Module desc')
    assert invdata['py:module']['module2'] == \
        ('foo', '2.0', '/util/foo.html#module-module2', '-')
    assert invdata['py:function']['module1.func'][2] == \
        '/util/sub/foo.html#module1.func'
    assert invdata['c:function']['CFunc'][2] == '/util/cfunc.html#CFunc'
    assert invdata['std:term']['a term'][2] == \
        '/util/glossary.html#term-a-term'
    assert invdata['std:term']['a term including:colon'][2] == \
        '/util/glossary.html#term-a-term-including-colon'


def test_read_inventory_v2_not_having_version():
    f = BytesIO(inventory_v2_not_having_version)
    invdata = InventoryFile.load(f, '/util', posixpath.join)
    assert invdata['py:module']['module1'] == \
        ('foo', '', '/util/foo.html#module-module1', 'Long Module desc')


def _app_language(tempdir, language):
    (tempdir / language).makedirs()
    (tempdir / language / 'conf.py').write_text(f'language = "{language}"', encoding='utf8')
    (tempdir / language / 'index.rst').write_text('index.rst', encoding='utf8')
    assert (tempdir / language).listdir() == ['conf.py', 'index.rst']
    assert (tempdir / language / 'index.rst').exists()
    return SphinxTestApp(srcdir=(tempdir / language))


def test_inventory_localization(tempdir):
    # Build an app using Estonian (EE) locale
    app_et = _app_language(tempdir, "et")
    app_et.build()
    inventory_et = (app_et.outdir / 'objects.inv').read_bytes()
    app_et.cleanup()

    # Build the same app using English (US) locale
    app_en = _app_language(tempdir, "en")
    app_en.build()
    inventory_en = (app_en.outdir / 'objects.inv').read_bytes()
    app_en.cleanup()

    # Ensure that the inventory contents differ
    assert inventory_et != inventory_en


def test_inventory_reproducible(tempdir, monkeypatch):
    # Configure reproducible builds
    # See: https://reproducible-builds.org/docs/source-date-epoch/
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")

    # Build an app using Estonian (EE) locale
    app_et = _app_language(tempdir, "et")
    app_et.build()
    inventory_et = (app_et.outdir / 'objects.inv').read_bytes()
    app_et.cleanup()

    # Build the same app using English (US) locale
    app_en = _app_language(tempdir, "en")
    app_en.build()
    inventory_en = (app_en.outdir / 'objects.inv').read_bytes()
    app_en.cleanup()

    # Ensure that the inventory contents are identical
    assert inventory_et == inventory_en
