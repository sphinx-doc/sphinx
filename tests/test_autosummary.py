# -*- coding: utf-8 -*-
"""
    test_autosummary
    ~~~~~~~~~~~~~~~~

    Test the autosummary extension.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import sys
from functools import wraps
from StringIO import StringIO

from sphinx.ext.autosummary import mangle_signature

from util import test_roots, TestApp

html_warnfile = StringIO()


def with_autosummary_app(*args, **kw):
    default_kw = {
        'srcdir': (test_roots / 'test-autosummary'),
        'confoverrides': {
            'extensions': ['sphinx.ext.autosummary'],
            'autosummary_generate': True,
            'source_suffix': '.rst'
        }
    }
    default_kw.update(kw)
    def generator(func):
        @wraps(func)
        def deco(*args2, **kwargs2):
            # Now, modify the python path...
            srcdir = default_kw['srcdir']
            sys.path.insert(0, srcdir)
            try:
                app = TestApp(*args, **default_kw)
                func(app, *args2, **kwargs2)
            finally:
                if srcdir in sys.path:
                    sys.path.remove(srcdir)
                # remove the auto-generated dummy_module.rst
                dummy_rst = srcdir / 'dummy_module.rst'
                if dummy_rst.isfile():
                    dummy_rst.unlink()

            # don't execute cleanup if test failed
            app.cleanup()
        return deco
    return generator


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


@with_autosummary_app(buildername='html', warning=html_warnfile)
def test_get_items_summary(app):
    app.builddir.rmtree(True)

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
        app.builder.build_all()
    finally:
        sphinx.ext.autosummary.Autosummary.get_items = orig_get_items

    html_warnings = html_warnfile.getvalue()
    assert html_warnings == ''

    expected_values = {
        'withSentence': 'I have a sentence which spans multiple lines.',
        'noSentence': "this doesn't start with a",
        'emptyLine': "This is the real summary",
        'module_attr': 'This is a module attribute',
        'C.class_attr': 'This is a class attribute',
        'C.prop_attr1': 'This is a function docstring',
        'C.prop_attr2': 'This is a attribute docstring',
        'C.C2': 'This is a nested inner class docstring',
    }
    for key, expected in expected_values.iteritems():
        assert autosummary_items[key][2] == expected, 'Summary for %s was %r -'\
            ' expected %r' % (key, autosummary_items[key], expected)


@with_autosummary_app(buildername='html')
def test_process_doc_event(app):
    app.builddir.rmtree(True)

    def handler(app, what, name, obj, options, lines):
        assert isinstance(lines, list)
    app.connect('autodoc-process-docstring', handler)
    app.builder.build_all()
