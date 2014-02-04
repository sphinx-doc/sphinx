# -*- coding: utf-8 -*-
"""
    test_autosummary
    ~~~~~~~~~~~~~~~~

    Test the autosummary extension.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import sys

from sphinx.ext.autosummary import mangle_signature

from util import with_app, test_roots

def test_mangle_signature():
    TEST = """
    () :: ()
    (a, b, c, d, e) :: (a, b, c, d, e)
    (a, b, c=1, d=2, e=3) :: (a, b[, c, d, e])
    (a, b, aaa=1, bbb=1, ccc=1, eee=1, fff=1, ggg=1, hhh=1, iii=1, jjj=1)\
    :: (a, b[, aaa, bbb, ccc, ...])
    (a, b, c=(), d=<foo>) :: (a, b[, c, d])
    (a, b, c='foobar()', d=123) :: (a, b[, c, d])
    (a, b[, c]) :: (a, b[, c])
    (a, b[, cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx]) :: (a, b[, ...)
    (a, b='c=d, e=f, g=h', c=3) :: (a[, b, c])
    (a, b='c=d, \\'e=f,\\' g=h', c=3) :: (a[, b, c])
    (a, b='c=d, ', e='\\\\' g=h, c=3) :: (a[, b, e, c])
    (a, b={'c=d, ': 3, '\\\\': 3}) :: (a[, b])
    (a=1, b=2, c=3) :: ([a, b, c])
    (a=1, b=<SomeClass: a, b, c>, c=3) :: ([a, b, c])
    """

    TEST = [map(lambda x: x.strip(), x.split("::")) for x in TEST.split("\n")
            if '::' in x]
    for inp, outp in TEST:
        res = mangle_signature(inp).strip().replace(u"\u00a0", " ")
        assert res == outp, (u"'%s' -> '%s' != '%s'" % (inp, res, outp))


# I can't just run this directly, because I need to monkey-patch Autosummary and
# modify the python path BEFORE creating the app... so I use
# _do_test_get_items_summary func just as a handy way to build the app, and
# test_get_items_summary will do the "setup", and is what is actually discovered
# / run by nose...

@with_app(confoverrides={'extensions': ['sphinx.ext.autosummary'],
                         'autosummary_generate': True,
                         'source_suffix': '.rst'},
          buildername='html', srcdir=(test_roots / 'test-autosummary'))
def _do_test_get_items_summary(app):
    (app.srcdir / 'contents.rst').write_text(
            '\n.. autosummary::'
            '\n   :nosignatures:'
            '\n   :toctree:'
            '\n   '
            '\n   dummy_module'
            '\n')

    app.builder.build_all()

def test_get_items_summary():
    # monkey-patch Autosummary.get_items so we can easily get access to it's
    # results..
    import sphinx.ext.autosummary
    orig_get_items = sphinx.ext.autosummary.Autosummary.get_items

    autosummary_items = {}

    def new_get_items(self, names, *args, **kwargs):
        results = orig_get_items(self, names, *args, **kwargs)
        for name, result in zip(names, results):
            autosummary_items[name] = result
        return results

    sphinx.ext.autosummary.Autosummary.get_items = new_get_items
    try:
        # Now, modify the python path...
        srcdir = test_roots / 'test-autosummary'
        sys.path.insert(0, srcdir)
        try:
            _do_test_get_items_summary()
        finally:
            if srcdir in sys.path:
                sys.path.remove(srcdir)
            # remove the auto-generated dummy_module.rst
            dummy_rst = srcdir / 'dummy_module.rst'
            if dummy_rst.isfile():
                dummy_rst.unlink()
    finally:
        sphinx.ext.autosummary.Autosummary.get_items = orig_get_items

    expected_values = {
        'withSentence': 'I have a sentence which spans multiple lines.',
        'noSentence': "this doesn't start with a",
        'emptyLine': "This is the real summary",
    }
    for key, expected in expected_values.iteritems():
        assert autosummary_items[key][2] == expected, 'Summary for %s was %r -'\
            ' expected %r' % (key, autosummary_items[key], expected)
