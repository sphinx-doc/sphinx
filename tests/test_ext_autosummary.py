"""
    test_autosummary
    ~~~~~~~~~~~~~~~~

    Test the autosummary extension.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from io import StringIO
import os
from unittest.mock import Mock

import pytest

from sphinx.ext.autosummary import mangle_signature, import_by_name, extract_summary
from sphinx.testing.util import etree_parse
from sphinx.util.docutils import new_document

html_warnfile = StringIO()


default_kw = {
    'testroot': 'autosummary',
    'confoverrides': {
        'extensions': ['sphinx.ext.autosummary'],
        'autosummary_generate': True,
        'source_suffix': '.rst'
    }
}


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
    (a: int, b: int) -> str :: (a, b)
    """

    TEST = [[y.strip() for y in x.split("::")] for x in TEST.split("\n")
            if '::' in x]
    for inp, outp in TEST:
        res = mangle_signature(inp).strip().replace("\u00a0", " ")
        assert res == outp, ("'%s' -> '%s' != '%s'" % (inp, res, outp))


def test_extract_summary(capsys):
    settings = Mock(language_code='',
                    id_prefix='',
                    auto_id_prefix='',
                    pep_reference=False,
                    rfc_reference=False)
    document = new_document('', settings)

    # normal case
    doc = ['',
           'This is a first sentence. And second one.',
           '',
           'Second block is here']
    assert extract_summary(doc, document) == 'This is a first sentence.'

    # inliner case
    doc = ['This sentence contains *emphasis text having dots.*,',
           'it does not break sentence.']
    assert extract_summary(doc, document) == ' '.join(doc)

    # abbreviations
    doc = ['Blabla, i.e. bla.']
    assert extract_summary(doc, document) == 'Blabla, i.e.'

    # literal
    doc = ['blah blah::']
    assert extract_summary(doc, document) == 'blah blah.'

    # heading
    doc = ['blah blah',
           '=========']
    assert extract_summary(doc, document) == 'blah blah'

    _, err = capsys.readouterr()
    assert err == ''


@pytest.mark.sphinx('dummy', **default_kw)
def test_get_items_summary(make_app, app_params):
    import sphinx.ext.autosummary
    import sphinx.ext.autosummary.generate
    args, kwargs = app_params
    app = make_app(*args, **kwargs)

    sphinx.ext.autosummary.generate.setup_documenters(app)
    # monkey-patch Autosummary.get_items so we can easily get access to it's
    # results..
    orig_get_items = sphinx.ext.autosummary.Autosummary.get_items

    autosummary_items = {}

    def new_get_items(self, names, *args, **kwargs):
        results = orig_get_items(self, names, *args, **kwargs)
        for name, result in zip(names, results):
            autosummary_items[name] = result
        return results

    def handler(app, what, name, obj, options, lines):
        assert isinstance(lines, list)

        # ensure no docstring is processed twice:
        assert 'THIS HAS BEEN HANDLED' not in lines
        lines.append('THIS HAS BEEN HANDLED')
    app.connect('autodoc-process-docstring', handler)

    sphinx.ext.autosummary.Autosummary.get_items = new_get_items
    try:
        app.builder.build_all()
    finally:
        sphinx.ext.autosummary.Autosummary.get_items = orig_get_items

    html_warnings = app._warning.getvalue()
    assert html_warnings == ''

    expected_values = {
        'withSentence': 'I have a sentence which spans multiple lines.',
        'noSentence': "this doesn't start with a capital.",
        'emptyLine': "This is the real summary",
        'module_attr': 'This is a module attribute',
        'C.class_attr': 'This is a class attribute',
        'C.prop_attr1': 'This is a function docstring',
        'C.prop_attr2': 'This is a attribute docstring',
        'C.C2': 'This is a nested inner class docstring',
    }
    for key, expected in expected_values.items():
        assert autosummary_items[key][2] == expected, 'Summary for %s was %r -'\
            ' expected %r' % (key, autosummary_items[key], expected)

    # check an item in detail
    assert 'func' in autosummary_items
    func_attrs = ('func',
                  '(arg_, *args, **kwargs)',
                  'Test function take an argument ended with underscore.',
                  'dummy_module.func')
    assert autosummary_items['func'] == func_attrs


def str_content(elem):
    if elem.text is not None:
        return elem.text
    else:
        return ''.join(str_content(e) for e in elem)


@pytest.mark.sphinx('xml', **default_kw)
def test_escaping(app, status, warning):
    app.builder.build_all()

    outdir = app.builder.outdir

    docpage = outdir / 'underscore_module_.xml'
    assert docpage.exists()

    title = etree_parse(docpage).find('section/title')

    assert str_content(title) == 'underscore_module_'


@pytest.mark.sphinx('dummy', testroot='ext-autosummary')
def test_autosummary_generate(app, status, warning):
    app.builder.build_all()
    module = (app.srcdir / 'generated' / 'autosummary_dummy_module.rst').text()
    assert ('   .. autosummary::\n'
            '   \n'
            '      Foo\n'
            '   \n' in module)

    Foo = (app.srcdir / 'generated' / 'autosummary_dummy_module.Foo.rst').text()
    assert '.. automethod:: __init__' in Foo
    assert ('   .. autosummary::\n'
            '   \n'
            '      ~Foo.__init__\n'
            '      ~Foo.bar\n'
            '   \n' in Foo)
    assert ('   .. autosummary::\n'
            '   \n'
            '      ~Foo.baz\n'
            '   \n' in Foo)


def _assert_autosummary_generate_package(app):
    app.builder.build_all()

    # Prepare package exploration
    max_depth = 3
    depth_limit = app.config.autosummary_depth_limit
    assert depth_limit <= max_depth
    
    unlimited = depth_limit < 0

    # All packages, modules and classes have the same name
    package_name = 'package'
    module_name = 'module'
    class_name = 'Foo'
    extension = 'rst'
    nsuffix = len(extension)+1

    # Expected module.rst template formatting
    package_rubic_name = 'packages'
    module_rubic_name = 'modules'
    package_rubic = '.. rubric:: ' + package_rubic_name
    module_rubic = '.. rubric:: ' + module_rubic_name
    package_summary = '.. autosummary::\n'\
                      '   :toctree: {}\n'\
                      '\n'\
                      '   {{}}.{}\n'.format(package_rubic_name, package_name)
    module_summary = '.. autosummary::\n'\
                     '   :toctree: {}\n'\
                     '\n'\
                     '   {{}}.{}\n'.format(module_rubic_name, module_name)
    class_summary = '   .. autosummary::\n'\
                    '   \n'\
                    '      {}\n'\
                    '   \n'.format(class_name)

    def assert_package_content(file):
        pkgroot = file.basename()[:-nsuffix]
        content = file.text()
        expected = ['.. automodule:: ' + pkgroot]
        unexpected = []
        if has_modules:
            lst = expected
        else:
            lst = unexpected
        lst.append(module_rubic)
        lst.append(module_summary.format(pkgroot))
        if has_packages:
            lst = expected
        else:
            lst = unexpected
        lst.append(package_rubic)
        lst.append(package_summary.format(pkgroot))
        for text in expected:
            assert text in content
        for text in unexpected:
            assert text not in content

    def assert_module_content(file):
        modname = file.basename()[:-nsuffix]
        content = file.text()
        assert '.. automodule:: '+modname in content
        assert '   .. rubric:: Classes' in content
        assert class_summary in content

    root = app.srcdir / 'generated'
    depth = 0
    pkgroot = ''
    packages = []
    modules = []
    directories = []
    while True:
        limit_reached = (depth == depth_limit) and not unlimited
        last_package = depth == max_depth
        has_packages = not limit_reached and not last_package
        has_modules = not limit_reached

        if pkgroot:
            pkgroot = '.'.join((pkgroot, package_name))
        else:
            pkgroot = package_name
        package = root / '.'.join((pkgroot, extension))
        packages.append(package)
        assert_package_content(package)

        if limit_reached:
            break

        directories.append(root / module_rubic_name)
        module = root / module_rubic_name / \
            '.'.join((pkgroot, module_name, extension))
        modules.append(module)
        assert_module_content(module)

        if last_package:
            # The last package contains a module but no subpackage
            break

        directories.append(root / package_rubic_name)
        root /= package_rubic_name
        depth += 1

    # Check generated files and directories
    generated = []
    root = app.srcdir / 'generated'
    for dir, subdirs, files in os.walk(str(root)):
        root = root / dir
        for name in files:
            generated.append(root / name)
        for name in subdirs:
            generated.append(root / name)
    expected = directories + packages + modules
    assert set(generated) == set(expected)


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-package')
def test_autosummary_generate_package(make_app, app_params):
    import sphinx.ext.autosummary
    import sphinx.ext.autosummary.generate
    logger = sphinx.ext.autosummary.logger
    args, kwargs = app_params
    confoverrides = {'autosummary_depth_limit': 0}
    kwargs['confoverrides'] = confoverrides
    # Try different depth limits
    # TODO: going from higher to lower limit
    # currently fails because generated files
    # are not deleted
    for limit in 0, 1, 2, 3, -1:
        logger.info('autosummary_depth_limit = {}'.format(limit))
        confoverrides['autosummary_depth_limit'] = limit
        app = make_app(*args, **kwargs)
        _assert_autosummary_generate_package(app)
        # Cleanup
        # root = app.srcdir / 'generated'
        # root.rmtree()


@pytest.mark.sphinx('latex', **default_kw)
def test_autosummary_latex_table_colspec(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'python.tex').text(encoding='utf8')
    print(status.getvalue())
    print(warning.getvalue())
    assert r'\begin{longtable}[c]{\X{1}{2}\X{1}{2}}' in result
    assert r'p{0.5\linewidth}' not in result


def test_import_by_name():
    import sphinx
    import sphinx.ext.autosummary

    prefixed_name, obj, parent, modname = import_by_name('sphinx')
    assert prefixed_name == 'sphinx'
    assert obj is sphinx
    assert parent is None
    assert modname == 'sphinx'

    prefixed_name, obj, parent, modname = import_by_name('sphinx.ext.autosummary.__name__')
    assert prefixed_name == 'sphinx.ext.autosummary.__name__'
    assert obj is sphinx.ext.autosummary.__name__
    assert parent is sphinx.ext.autosummary
    assert modname == 'sphinx.ext.autosummary'

    prefixed_name, obj, parent, modname = \
        import_by_name('sphinx.ext.autosummary.Autosummary.get_items')
    assert prefixed_name == 'sphinx.ext.autosummary.Autosummary.get_items'
    assert obj == sphinx.ext.autosummary.Autosummary.get_items
    assert parent is sphinx.ext.autosummary.Autosummary
    assert modname == 'sphinx.ext.autosummary'


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-mock_imports')
def test_autosummary_mock_imports(app, status, warning):
    try:
        app.build()
        assert warning.getvalue() == ''

        # generated/foo is generated successfully
        assert app.env.get_doctree('generated/foo')
    finally:
        sys.modules.pop('foo', None)  # unload foo module


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-imported_members')
def test_autosummary_imported_members(app, status, warning):
    try:
        app.build()
        # generated/foo is generated successfully
        assert app.env.get_doctree('generated/autosummary_dummy_package')

        module = (app.srcdir / 'generated' / 'autosummary_dummy_package.rst').text()
        assert ('   .. autosummary::\n'
                '   \n'
                '      Bar\n'
                '   \n' in module)
        assert ('   .. autosummary::\n'
                '   \n'
                '      foo\n'
                '   \n' in module)
    finally:
        sys.modules.pop('autosummary_dummy_package', None)
