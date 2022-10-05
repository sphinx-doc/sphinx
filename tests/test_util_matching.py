"""Tests sphinx.util.matching functions."""
from sphinx.util.matching import Matcher, compile_matchers, get_matching_files


def test_compile_matchers():
    # exact matching
    pat = compile_matchers(['hello.py']).pop()
    assert pat('hello.py')
    assert not pat('hello-py')
    assert not pat('subdir/hello.py')

    # wild card (*)
    pat = compile_matchers(['hello.*']).pop()
    assert pat('hello.py')
    assert pat('hello.rst')

    pat = compile_matchers(['*.py']).pop()
    assert pat('hello.py')
    assert pat('world.py')
    assert not pat('subdir/hello.py')

    # wild card (**)
    pat = compile_matchers(['hello.**']).pop()
    assert pat('hello.py')
    assert pat('hello.rst')
    assert pat('hello.py/world.py')

    pat = compile_matchers(['**.py']).pop()
    assert pat('hello.py')
    assert pat('world.py')
    assert pat('subdir/hello.py')

    pat = compile_matchers(['**/hello.py']).pop()
    assert not pat('hello.py')
    assert pat('subdir/hello.py')
    assert pat('subdir/subdir/hello.py')

    # wild card (?)
    pat = compile_matchers(['hello.?']).pop()
    assert pat('hello.c')
    assert not pat('hello.py')

    # pattern ([...])
    pat = compile_matchers(['hello[12\\].py']).pop()
    assert pat('hello1.py')
    assert pat('hello2.py')
    assert pat('hello\\.py')
    assert not pat('hello3.py')

    pat = compile_matchers(['hello[^12].py']).pop()  # "^" is not negative identifier
    assert pat('hello1.py')
    assert pat('hello2.py')
    assert pat('hello^.py')
    assert not pat('hello3.py')

    # negative pattern ([!...])
    pat = compile_matchers(['hello[!12].py']).pop()
    assert not pat('hello1.py')
    assert not pat('hello2.py')
    assert not pat('hello/.py')  # negative pattern does not match to "/"
    assert pat('hello3.py')

    # non patterns
    pat = compile_matchers(['hello[.py']).pop()
    assert pat('hello[.py')
    assert not pat('hello.py')

    pat = compile_matchers(['hello[].py']).pop()
    assert pat('hello[].py')
    assert not pat('hello.py')

    pat = compile_matchers(['hello[!].py']).pop()
    assert pat('hello[!].py')
    assert not pat('hello.py')


def test_Matcher():
    matcher = Matcher(['hello.py', '**/world.py'])
    assert matcher('hello.py')
    assert not matcher('subdir/hello.py')
    assert matcher('world.py')
    assert matcher('subdir/world.py')


def test_get_matching_files_all(rootdir):
    files = get_matching_files(rootdir / "test-root")
    assert sorted(files) == [
        'Makefile', '_templates/contentssb.html', '_templates/customsb.html',
        '_templates/layout.html', 'autodoc.txt', 'autodoc_target.py', 'bom.txt', 'conf.py',
        'extapi.txt', 'extensions.txt', 'file_with_special_#_chars.xyz', 'footnote.txt',
        'images.txt', 'img.foo.png', 'img.gif', 'img.pdf', 'img.png', 'includes.txt',
        'index.txt', 'lists.txt', 'literal.inc', 'literal_orig.inc', 'markup.txt', 'math.txt',
        'objects.txt', 'otherext.foo', 'parsermod.py', 'quotes.inc', 'rimg.png',
        'special/api.h', 'special/code.py', 'subdir/excluded.txt', 'subdir/images.txt',
        'subdir/img.png', 'subdir/include.inc', 'subdir/includes.txt', 'subdir/simg.png',
        'svgimg.pdf', 'svgimg.svg', 'tabs.inc', 'test.inc', 'wrongenc.inc',
    ]


def test_get_matching_files_all_exclude_single(rootdir):
    files = get_matching_files(rootdir / "test-root", exclude_patterns=["**.html"])
    assert sorted(files) == [
        'Makefile', 'autodoc.txt', 'autodoc_target.py', 'bom.txt', 'conf.py',
        'extapi.txt', 'extensions.txt', 'file_with_special_#_chars.xyz', 'footnote.txt',
        'images.txt', 'img.foo.png', 'img.gif', 'img.pdf', 'img.png', 'includes.txt',
        'index.txt', 'lists.txt', 'literal.inc', 'literal_orig.inc', 'markup.txt', 'math.txt',
        'objects.txt', 'otherext.foo', 'parsermod.py', 'quotes.inc', 'rimg.png',
        'special/api.h', 'special/code.py', 'subdir/excluded.txt', 'subdir/images.txt',
        'subdir/img.png', 'subdir/include.inc', 'subdir/includes.txt', 'subdir/simg.png',
        'svgimg.pdf', 'svgimg.svg', 'tabs.inc', 'test.inc', 'wrongenc.inc',
    ]


def test_get_matching_files_all_exclude_multiple(rootdir):
    files = get_matching_files(rootdir / "test-root", exclude_patterns=["**.html", "**.inc"])
    assert sorted(files) == [
        'Makefile', 'autodoc.txt', 'autodoc_target.py', 'bom.txt', 'conf.py',
        'extapi.txt', 'extensions.txt', 'file_with_special_#_chars.xyz', 'footnote.txt',
        'images.txt', 'img.foo.png', 'img.gif', 'img.pdf', 'img.png', 'includes.txt',
        'index.txt', 'lists.txt', 'markup.txt', 'math.txt', 'objects.txt', 'otherext.foo',
        'parsermod.py', 'rimg.png', 'special/api.h', 'special/code.py', 'subdir/excluded.txt',
        'subdir/images.txt', 'subdir/img.png', 'subdir/includes.txt', 'subdir/simg.png',
        'svgimg.pdf', 'svgimg.svg',
    ]


def test_get_matching_files_all_exclude_nonexistent(rootdir):
    files = get_matching_files(rootdir / "test-root", exclude_patterns=["halibut/**"])
    assert sorted(files) == [
        'Makefile', '_templates/contentssb.html', '_templates/customsb.html',
        '_templates/layout.html', 'autodoc.txt', 'autodoc_target.py', 'bom.txt', 'conf.py',
        'extapi.txt', 'extensions.txt', 'file_with_special_#_chars.xyz', 'footnote.txt',
        'images.txt', 'img.foo.png', 'img.gif', 'img.pdf', 'img.png', 'includes.txt',
        'index.txt', 'lists.txt', 'literal.inc', 'literal_orig.inc', 'markup.txt', 'math.txt',
        'objects.txt', 'otherext.foo', 'parsermod.py', 'quotes.inc', 'rimg.png',
        'special/api.h', 'special/code.py', 'subdir/excluded.txt', 'subdir/images.txt',
        'subdir/img.png', 'subdir/include.inc', 'subdir/includes.txt', 'subdir/simg.png',
        'svgimg.pdf', 'svgimg.svg', 'tabs.inc', 'test.inc', 'wrongenc.inc',
    ]


def test_get_matching_files_all_include_single(rootdir):
    files = get_matching_files(rootdir / "test-root", include_patterns=["subdir/**"])
    assert sorted(files) == [
        'subdir/excluded.txt', 'subdir/images.txt', 'subdir/img.png', 'subdir/include.inc',
        'subdir/includes.txt', 'subdir/simg.png',
    ]


def test_get_matching_files_all_include_multiple(rootdir):
    files = get_matching_files(rootdir / "test-root", include_patterns=["special/**", "subdir/**"])
    assert sorted(files) == [
        'special/api.h', 'special/code.py', 'subdir/excluded.txt', 'subdir/images.txt',
        'subdir/img.png', 'subdir/include.inc', 'subdir/includes.txt', 'subdir/simg.png',
    ]


def test_get_matching_files_all_include_nonexistent(rootdir):
    files = get_matching_files(rootdir / "test-root", include_patterns=["halibut/**"])
    assert sorted(files) == []


def test_get_matching_files_all_include_prefix(rootdir):
    files = get_matching_files(rootdir / "test-root", include_patterns=["autodoc*"])
    assert sorted(files) == [
        'autodoc.txt', 'autodoc_target.py',
    ]


def test_get_matching_files_all_include_question_mark(rootdir):
    files = get_matching_files(rootdir / "test-root", include_patterns=["img.???"])
    assert sorted(files) == [
        'img.gif', 'img.pdf', 'img.png',
    ]
