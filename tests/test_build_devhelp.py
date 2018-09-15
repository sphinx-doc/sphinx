import xml.etree.cElementTree as ElementTree

import pytest


@pytest.mark.sphinx('devhelp', testroot='basic')
def test_devhelp_basic(app):
    app.builder.build_all()
    result = (app.outdir / 'Python.devhelp2').text(encoding='utf-8')

    assert '<?xml version="1.0" encoding="utf-8" standalone="no"?>' in result
    assert '<book' in result
    assert '<chapters' in result
    assert '<functions' in result

@pytest.mark.sphinx('devhelp', testroot='root')
def test_devhelp_check_info(app):
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.devhelp2').text(encoding='utf-8')

    index = ElementTree.fromstring(result)

    assert index.tag == '{http://www.devhelp.net/book}book'

    # Attributes required book root tag
    assert 'title' in index.keys()
    assert 'link' in index.keys()
    assert 'name' in index.keys()
    assert 'version' in index.keys()
    assert 'language' in index.keys()
    assert 'online' in index.keys()
    assert 'author' in index.keys()

    # Chapters-sub Attributes
    sub_element = index.findall('./')[0].findall('./')[0]
    assert sub_element.tag == '{http://www.devhelp.net/book}sub'
    assert 'name' in sub_element.keys()
    assert 'link' in sub_element.keys()

    # Functions-keyword Attributes
    keyword_element = index.findall('./')[1].find('./')
    assert keyword_element.tag == '{http://www.devhelp.net/book}keyword'
    assert 'name' in keyword_element.keys()
    assert 'link' in keyword_element.keys()
    assert 'type' in keyword_element.keys()

