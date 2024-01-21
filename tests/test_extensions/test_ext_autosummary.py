"""Test the autosummary extension."""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.ext.autosummary import (
    autosummary_table,
    autosummary_toc,
    extract_summary,
    import_by_name,
    mangle_signature,
)
from sphinx.ext.autosummary.generate import (
    AutosummaryEntry,
    generate_autosummary_content,
    generate_autosummary_docs,
)
from sphinx.ext.autosummary.generate import main as autogen_main
from sphinx.testing.util import assert_node, etree_parse
from sphinx.util.docutils import new_document

try:
    from contextlib import chdir
except ImportError:
    from sphinx.util.osutil import _chdir as chdir

html_warnfile = StringIO()


default_kw = {
    'testroot': 'autosummary',
    'confoverrides': {
        'extensions': ['sphinx.ext.autosummary'],
        'autosummary_generate': True,
        'autosummary_generate_overwrite': False,
        'source_suffix': '.rst',
    },
}


@pytest.fixture(autouse=True)
def _unload_target_module():
    sys.modules.pop('target', None)


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
    (a, b="c=d, e=f, g=h", c=3) :: (a[, b, c])
    (a, b='c=d, \\'e=f,\\' g=h', c=3) :: (a[, b, c])
    (a, b='c=d, ', e='\\\\' g=h, c=3) :: (a[, b, e, c])
    (a, b={'c=d, ': 3, '\\\\': 3}) :: (a[, b])
    (a=1, b=2, c=3) :: ([a, b, c])
    (a=1, b=<SomeClass: a, b, c>, c=3) :: ([a, b, c])
    (a=1, b=T(a=1, b=2), c=3) :: ([a, b, c])
    (a: Tuple[int, str], b: int) -> str :: (a, b)
    """

    TEST = [[y.strip() for y in x.split("::")] for x in TEST.split("\n")
            if '::' in x]
    for inp, outp in TEST:
        res = mangle_signature(inp).strip().replace("\u00a0", " ")
        assert res == outp, (f"'{inp}' -> '{res}' != '{outp}'")


def test_extract_summary(capsys):
    settings = Mock(language_code='en',
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
    assert extract_summary(doc, document) == ' '.join(doc)

    doc = ['Blabla, (i.e. bla).']
    assert extract_summary(doc, document) == ' '.join(doc)

    doc = ['Blabla, e.g. bla.']
    assert extract_summary(doc, document) == ' '.join(doc)

    doc = ['Blabla, (e.g. bla).']
    assert extract_summary(doc, document) == ' '.join(doc)

    doc = ['Blabla, et al. bla.']
    assert extract_summary(doc, document) == ' '.join(doc)

    # literal
    doc = ['blah blah::']
    assert extract_summary(doc, document) == 'blah blah.'

    # heading
    doc = ['blah blah',
           '=========']
    assert extract_summary(doc, document) == 'blah blah'

    doc = ['=========',
           'blah blah',
           '=========']
    assert extract_summary(doc, document) == 'blah blah'

    # hyperlink target
    doc = ['Do `this <https://www.sphinx-doc.org/>`_ and that. '
           'blah blah blah.']
    assert (extract_summary(doc, document) ==
            'Do `this <https://www.sphinx-doc.org/>`_ and that.')

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
            autosummary_items[name] = result  # NoQA: PERF403
        return results

    def handler(app, what, name, obj, options, lines):
        assert isinstance(lines, list)

        # ensure no docstring is processed twice:
        assert 'THIS HAS BEEN HANDLED' not in lines
        lines.append('THIS HAS BEEN HANDLED')
    app.connect('autodoc-process-docstring', handler)

    sphinx.ext.autosummary.Autosummary.get_items = new_get_items
    try:
        app.build(force_all=True)
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
        'C.instance_attr': 'This is an instance attribute',
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
    app.build(force_all=True)

    outdir = Path(app.builder.outdir)

    docpage = outdir / 'underscore_module_.xml'
    assert docpage.exists()

    title = etree_parse(docpage).find('section/title')

    assert str_content(title) == 'underscore_module_'


@pytest.mark.sphinx(testroot='ext-autosummary')
def test_autosummary_generate_content_for_module(app):
    import autosummary_dummy_module
    template = Mock()

    generate_autosummary_content('autosummary_dummy_module', autosummary_dummy_module, None,
                                 template, None, False, app, False, {})
    assert template.render.call_args[0][0] == 'module'

    context = template.render.call_args[0][1]
    assert context['members'] == ['CONSTANT1', 'CONSTANT2', 'Exc', 'Foo', '_Baz', '_Exc',
                                  '__all__', '__builtins__', '__cached__', '__doc__',
                                  '__file__', '__name__', '__package__', '_quux', 'bar',
                                  'non_imported_member', 'quuz', 'qux']
    assert context['functions'] == ['bar']
    assert context['all_functions'] == ['_quux', 'bar']
    assert context['classes'] == ['Foo']
    assert context['all_classes'] == ['Foo', '_Baz']
    assert context['exceptions'] == ['Exc']
    assert context['all_exceptions'] == ['Exc', '_Exc']
    assert context['attributes'] == ['CONSTANT1', 'qux', 'quuz', 'non_imported_member']
    assert context['all_attributes'] == ['CONSTANT1', 'qux', 'quuz', 'non_imported_member']
    assert context['fullname'] == 'autosummary_dummy_module'
    assert context['module'] == 'autosummary_dummy_module'
    assert context['objname'] == ''
    assert context['name'] == ''
    assert context['objtype'] == 'module'


@pytest.mark.sphinx(testroot='ext-autosummary')
def test_autosummary_generate_content_for_module___all__(app):
    import autosummary_dummy_module
    template = Mock()
    app.config.autosummary_ignore_module_all = False

    generate_autosummary_content('autosummary_dummy_module', autosummary_dummy_module, None,
                                 template, None, False, app, False, {})
    assert template.render.call_args[0][0] == 'module'

    context = template.render.call_args[0][1]
    assert context['members'] == ['CONSTANT1', 'Exc', 'Foo', '_Baz', 'bar', 'qux', 'path']
    assert context['functions'] == ['bar']
    assert context['all_functions'] == ['bar']
    assert context['classes'] == ['Foo']
    assert context['all_classes'] == ['Foo', '_Baz']
    assert context['exceptions'] == ['Exc']
    assert context['all_exceptions'] == ['Exc']
    assert context['attributes'] == ['CONSTANT1', 'qux']
    assert context['all_attributes'] == ['CONSTANT1', 'qux']
    assert context['fullname'] == 'autosummary_dummy_module'
    assert context['module'] == 'autosummary_dummy_module'
    assert context['objname'] == ''
    assert context['name'] == ''
    assert context['objtype'] == 'module'


@pytest.mark.sphinx(testroot='ext-autosummary')
def test_autosummary_generate_content_for_module_skipped(app):
    import autosummary_dummy_module
    template = Mock()

    def skip_member(app, what, name, obj, skip, options):
        if name in ('Foo', 'bar', 'Exc'):
            return True
        return None

    app.connect('autodoc-skip-member', skip_member)
    generate_autosummary_content('autosummary_dummy_module', autosummary_dummy_module, None,
                                 template, None, False, app, False, {})
    context = template.render.call_args[0][1]
    assert context['members'] == ['CONSTANT1', 'CONSTANT2', '_Baz', '_Exc', '__all__',
                                  '__builtins__', '__cached__', '__doc__', '__file__',
                                  '__name__', '__package__', '_quux', 'non_imported_member',
                                  'quuz', 'qux']
    assert context['functions'] == []
    assert context['classes'] == []
    assert context['exceptions'] == []


@pytest.mark.sphinx(testroot='ext-autosummary')
def test_autosummary_generate_content_for_module_imported_members(app):
    import autosummary_dummy_module
    template = Mock()

    generate_autosummary_content('autosummary_dummy_module', autosummary_dummy_module, None,
                                 template, None, True, app, False, {})
    assert template.render.call_args[0][0] == 'module'

    context = template.render.call_args[0][1]
    assert context['members'] == ['CONSTANT1', 'CONSTANT2', 'Class', 'Exc', 'Foo', 'Union',
                                  '_Baz', '_Exc', '__all__', '__builtins__', '__cached__',
                                  '__doc__', '__file__', '__loader__', '__name__',
                                  '__package__', '__spec__', '_quux', 'bar',
                                  'considered_as_imported', 'non_imported_member', 'path',
                                  'quuz', 'qux']
    assert context['functions'] == ['bar']
    assert context['all_functions'] == ['_quux', 'bar']
    assert context['classes'] == ['Class', 'Foo']
    assert context['all_classes'] == ['Class', 'Foo', '_Baz']
    assert context['exceptions'] == ['Exc']
    assert context['all_exceptions'] == ['Exc', '_Exc']
    assert context['attributes'] == ['CONSTANT1', 'qux', 'quuz', 'non_imported_member']
    assert context['all_attributes'] == ['CONSTANT1', 'qux', 'quuz', 'non_imported_member']
    assert context['fullname'] == 'autosummary_dummy_module'
    assert context['module'] == 'autosummary_dummy_module'
    assert context['objname'] == ''
    assert context['name'] == ''
    assert context['objtype'] == 'module'


@pytest.mark.sphinx(testroot='ext-autosummary')
def test_autosummary_generate_content_for_module_imported_members_inherited_module(app):
    import autosummary_dummy_inherited_module
    template = Mock()

    generate_autosummary_content('autosummary_dummy_inherited_module',
                                 autosummary_dummy_inherited_module, None,
                                 template, None, True, app, False, {})
    assert template.render.call_args[0][0] == 'module'

    context = template.render.call_args[0][1]
    assert context['members'] == ['Foo', 'InheritedAttrClass', '__all__', '__builtins__', '__cached__',
                                  '__doc__', '__file__', '__loader__', '__name__',
                                  '__package__', '__spec__']
    assert context['functions'] == []
    assert context['classes'] == ['Foo', 'InheritedAttrClass']
    assert context['exceptions'] == []
    assert context['all_exceptions'] == []
    assert context['attributes'] == []
    assert context['all_attributes'] == []
    assert context['fullname'] == 'autosummary_dummy_inherited_module'
    assert context['module'] == 'autosummary_dummy_inherited_module'
    assert context['objname'] == ''
    assert context['name'] == ''
    assert context['objtype'] == 'module'


@pytest.mark.sphinx('dummy', testroot='ext-autosummary')
def test_autosummary_generate(app, status, warning):
    app.build(force_all=True)

    doctree = app.env.get_doctree('index')
    assert_node(doctree, (nodes.paragraph,
                          nodes.paragraph,
                          addnodes.tabular_col_spec,
                          autosummary_table,
                          [autosummary_toc, addnodes.toctree]))
    assert_node(doctree[3],
                [autosummary_table, nodes.table, nodes.tgroup, (nodes.colspec,
                                                                nodes.colspec,
                                                                [nodes.tbody, (nodes.row,
                                                                               nodes.row,
                                                                               nodes.row,
                                                                               nodes.row,
                                                                               nodes.row,
                                                                               nodes.row,
                                                                               nodes.row,
                                                                               nodes.row)])])
    assert_node(doctree[4][0], addnodes.toctree, caption="An autosummary")

    assert len(doctree[3][0][0][2]) == 8
    assert doctree[3][0][0][2][0].astext() == 'autosummary_dummy_module\n\n'
    assert doctree[3][0][0][2][1].astext() == 'autosummary_dummy_module.Foo()\n\n'
    assert doctree[3][0][0][2][2].astext() == 'autosummary_dummy_module.Foo.Bar()\n\n'
    assert doctree[3][0][0][2][3].astext() == 'autosummary_dummy_module.Foo.value\n\ndocstring'
    assert doctree[3][0][0][2][4].astext() == 'autosummary_dummy_module.bar(x[, y])\n\n'
    assert doctree[3][0][0][2][5].astext() == 'autosummary_dummy_module.qux\n\na module-level attribute'
    assert doctree[3][0][0][2][6].astext() == 'autosummary_dummy_inherited_module.InheritedAttrClass()\n\n'
    assert doctree[3][0][0][2][7].astext() == 'autosummary_dummy_inherited_module.InheritedAttrClass.subclassattr\n\nother docstring'

    module = (app.srcdir / 'generated' / 'autosummary_dummy_module.rst').read_text(encoding='utf8')

    assert ('   .. autosummary::\n'
            '   \n'
            '      Foo\n'
            '   \n' in module)
    assert ('   .. autosummary::\n'
            '   \n'
            '      CONSTANT1\n'
            '      qux\n'
            '      quuz\n'
            '      non_imported_member\n'
            '   \n' in module)

    Foo = (app.srcdir / 'generated' / 'autosummary_dummy_module.Foo.rst').read_text(encoding='utf8')
    assert '.. automethod:: __init__' in Foo
    assert ('   .. autosummary::\n'
            '   \n'
            '      ~Foo.__init__\n'
            '      ~Foo.bar\n'
            '   \n' in Foo)
    assert ('   .. autosummary::\n'
            '   \n'
            '      ~Foo.CONSTANT3\n'
            '      ~Foo.CONSTANT4\n'
            '      ~Foo.baz\n'
            '      ~Foo.value\n'
            '   \n' in Foo)

    FooBar = (app.srcdir / 'generated' / 'autosummary_dummy_module.Foo.Bar.rst').read_text(encoding='utf8')
    assert ('.. currentmodule:: autosummary_dummy_module\n'
            '\n'
            '.. autoclass:: Foo.Bar\n' in FooBar)

    Foo_value = (app.srcdir / 'generated' / 'autosummary_dummy_module.Foo.value.rst').read_text(encoding='utf8')
    assert ('.. currentmodule:: autosummary_dummy_module\n'
            '\n'
            '.. autoattribute:: Foo.value' in Foo_value)

    qux = (app.srcdir / 'generated' / 'autosummary_dummy_module.qux.rst').read_text(encoding='utf8')
    assert ('.. currentmodule:: autosummary_dummy_module\n'
            '\n'
            '.. autodata:: qux' in qux)

    InheritedAttrClass = (app.srcdir / 'generated' / 'autosummary_dummy_inherited_module.InheritedAttrClass.rst').read_text(encoding='utf8')
    print(InheritedAttrClass)
    assert '.. automethod:: __init__' in Foo
    assert ('   .. autosummary::\n'
            '   \n'
            '      ~InheritedAttrClass.__init__\n'
            '      ~InheritedAttrClass.bar\n'
            '   \n' in InheritedAttrClass)
    assert ('   .. autosummary::\n'
            '   \n'
            '      ~InheritedAttrClass.CONSTANT3\n'
            '      ~InheritedAttrClass.CONSTANT4\n'
            '      ~InheritedAttrClass.baz\n'
            '      ~InheritedAttrClass.subclassattr\n'
            '      ~InheritedAttrClass.value\n'
            '   \n' in InheritedAttrClass)

    InheritedAttrClass_subclassattr = (app.srcdir / 'generated' / 'autosummary_dummy_inherited_module.InheritedAttrClass.subclassattr.rst').read_text(encoding='utf8')
    assert ('.. currentmodule:: autosummary_dummy_inherited_module\n'
            '\n'
            '.. autoattribute:: InheritedAttrClass.subclassattr' in InheritedAttrClass_subclassattr)


@pytest.mark.sphinx('dummy', testroot='ext-autosummary',
                    confoverrides={'autosummary_generate_overwrite': False})
def test_autosummary_generate_overwrite1(app_params, make_app):
    args, kwargs = app_params
    srcdir = kwargs.get('srcdir')

    (srcdir / 'generated').mkdir(parents=True, exist_ok=True)
    (srcdir / 'generated' / 'autosummary_dummy_module.rst').write_text('', encoding='utf8')

    app = make_app(*args, **kwargs)
    content = (srcdir / 'generated' / 'autosummary_dummy_module.rst').read_text(encoding='utf8')
    assert content == ''
    assert 'autosummary_dummy_module.rst' not in app._warning.getvalue()


@pytest.mark.sphinx('dummy', testroot='ext-autosummary',
                    confoverrides={'autosummary_generate_overwrite': True})
def test_autosummary_generate_overwrite2(app_params, make_app):
    args, kwargs = app_params
    srcdir = kwargs.get('srcdir')

    (srcdir / 'generated').mkdir(parents=True, exist_ok=True)
    (srcdir / 'generated' / 'autosummary_dummy_module.rst').write_text('', encoding='utf8')

    app = make_app(*args, **kwargs)
    content = (srcdir / 'generated' / 'autosummary_dummy_module.rst').read_text(encoding='utf8')
    assert content != ''
    assert 'autosummary_dummy_module.rst' not in app._warning.getvalue()


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-recursive')
@pytest.mark.usefixtures("rollback_sysmodules")
def test_autosummary_recursive(app, status, warning):
    sys.modules.pop('package', None)  # unload target module to clear the module cache

    app.build()

    # autosummary having :recursive: option
    assert (app.srcdir / 'generated' / 'package.rst').exists()
    assert (app.srcdir / 'generated' / 'package.module.rst').exists()
    assert (app.srcdir / 'generated' / 'package.module_importfail.rst').exists() is False
    assert (app.srcdir / 'generated' / 'package.package.rst').exists()
    assert (app.srcdir / 'generated' / 'package.package.module.rst').exists()

    # autosummary not having :recursive: option
    assert (app.srcdir / 'generated' / 'package2.rst').exists()
    assert (app.srcdir / 'generated' / 'package2.module.rst').exists() is False

    # Check content of recursively generated stub-files
    content = (app.srcdir / 'generated' / 'package.rst').read_text(encoding='utf8')
    assert 'package.module' in content
    assert 'package.package' in content
    assert 'package.module_importfail' in content

    content = (app.srcdir / 'generated' / 'package.package.rst').read_text(encoding='utf8')
    assert 'package.package.module' in content


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-recursive',
                    srcdir='test_autosummary_recursive_skips_mocked_modules',
                    confoverrides={'autosummary_mock_imports': ['package.package']})
@pytest.mark.usefixtures("rollback_sysmodules")
def test_autosummary_recursive_skips_mocked_modules(app, status, warning):
    sys.modules.pop('package', None)  # unload target module to clear the module cache
    app.build()

    assert (app.srcdir / 'generated' / 'package.rst').exists()
    assert (app.srcdir / 'generated' / 'package.module.rst').exists()
    assert (app.srcdir / 'generated' / 'package.package.rst').exists() is False
    assert (app.srcdir / 'generated' / 'package.package.module.rst').exists() is False


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-filename-map')
def test_autosummary_filename_map(app, status, warning):
    app.build()

    assert (app.srcdir / 'generated' / 'module_mangled.rst').exists()
    assert not (app.srcdir / 'generated' / 'autosummary_dummy_module.rst').exists()
    assert (app.srcdir / 'generated' / 'bar.rst').exists()
    assert not (app.srcdir / 'generated' / 'autosummary_dummy_module.bar.rst').exists()
    assert (app.srcdir / 'generated' / 'autosummary_dummy_module.Foo.rst').exists()

    html_warnings = app._warning.getvalue()
    assert html_warnings == ''


@pytest.mark.sphinx('latex', **default_kw)
def test_autosummary_latex_table_colspec(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(status.getvalue())
    print(warning.getvalue())
    assert r'\begin{longtable}{\X{1}{2}\X{1}{2}}' in result
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

        module = (app.srcdir / 'generated' / 'autosummary_dummy_package.rst').read_text(encoding='utf8')
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


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-module_all')
def test_autosummary_module_all(app, status, warning):
    try:
        app.build()
        # generated/foo is generated successfully
        assert app.env.get_doctree('generated/autosummary_dummy_package_all')
        module = (app.srcdir / 'generated' / 'autosummary_dummy_package_all.rst').read_text(encoding='utf8')
        assert ('   .. autosummary::\n'
                '   \n'
                '      PublicBar\n'
                '   \n' in module)
        assert ('   .. autosummary::\n'
                '   \n'
                '      public_foo\n'
                '      public_baz\n'
                '   \n' in module)
        assert ('.. autosummary::\n'
                '   :toctree:\n'
                '   :recursive:\n\n'
                '   autosummary_dummy_package_all.extra_dummy_module\n\n' in module)
    finally:
        sys.modules.pop('autosummary_dummy_package_all', None)


@pytest.mark.sphinx(testroot='ext-autodoc',
                    confoverrides={'extensions': ['sphinx.ext.autosummary']})
def test_generate_autosummary_docs_property(app):
    with patch('sphinx.ext.autosummary.generate.find_autosummary_in_files') as mock:
        mock.return_value = [AutosummaryEntry('target.methods.Base.prop', 'prop', None, False)]
        generate_autosummary_docs([], output_dir=app.srcdir, app=app)

    content = (app.srcdir / 'target.methods.Base.prop.rst').read_text(encoding='utf8')
    assert content == ("target.methods.Base.prop\n"
                       "========================\n"
                       "\n"
                       ".. currentmodule:: target.methods\n"
                       "\n"
                       ".. autoproperty:: Base.prop")


@pytest.mark.sphinx(testroot='ext-autosummary-skip-member')
def test_autosummary_skip_member(app):
    app.build()

    content = (app.srcdir / 'generate' / 'target.Foo.rst').read_text(encoding='utf8')
    assert 'Foo.skipmeth' not in content
    assert 'Foo._privatemeth' in content


@pytest.mark.sphinx(testroot='ext-autosummary-template')
def test_autosummary_template(app):
    app.build()

    content = (app.srcdir / 'generate' / 'target.Foo.rst').read_text(encoding='utf8')
    assert 'EMPTY' in content


@pytest.mark.sphinx('dummy', testroot='ext-autosummary',
                    confoverrides={'autosummary_generate': []})
def test_empty_autosummary_generate(app, status, warning):
    app.build()
    assert ("WARNING: autosummary: failed to import autosummary_importfail"
            in warning.getvalue())


@pytest.mark.sphinx('dummy', testroot='ext-autosummary',
                    confoverrides={'autosummary_generate': ['unknown']})
def test_invalid_autosummary_generate(app, status, warning):
    assert 'WARNING: autosummary_generate: file not found: unknown.rst' in warning.getvalue()


def test_autogen(rootdir, tmp_path):
    with chdir(rootdir / 'test-templating'):
        args = ['-o', str(tmp_path), '-t', '.', 'autosummary_templating.txt']
        autogen_main(args)
        assert (tmp_path / 'sphinx.application.TemplateBridge.rst').exists()
