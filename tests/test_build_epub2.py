# -*- coding: utf-8 -*-
"""
    test_build_epub2
    ~~~~~~~~~~~~~~~~

    Test the epub2 builder and check output against XPath.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from xml.etree import ElementTree

import pytest

if False:
    from sphinx.testing.util import SphinxTestApp


class EPUBElementTree(object):
    """Test helper for content.opf and tox.ncx"""
    namespaces = {
        'idpf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'ibooks': 'http://vocabulary.itunes.apple.com/rdf/ibooks/vocabulary-extensions-1.0/',
        'ncx': 'http://www.daisy.org/z3986/2005/ncx/',
        'xhtml': 'http://www.w3.org/1999/xhtml',
        'epub': 'http://www.idpf.org/2007/ops'
    }

    def __init__(self, tree):
        self.tree = tree

    @classmethod
    def fromstring(cls, string):
        return cls(ElementTree.fromstring(string))

    def find(self, match):
        ret = self.tree.find(match, namespaces=self.namespaces)
        if ret is not None:
            return self.__class__(ret)
        else:
            return ret

    def findall(self, match):
        ret = self.tree.findall(match, namespaces=self.namespaces)
        return [self.__class__(e) for e in ret]

    def __getattr__(self, name):
        return getattr(self.tree, name)

    def __iter__(self):
        for child in self.tree:
            yield self.__class__(child)


@pytest.mark.sphinx('epub2', testroot='basic',
                    confoverrides={
                        'version': '1.0',
                        'epub_basename': "fakeepub2",
                        'epub_theme': 'epub',
                        'epub_theme_options': {
                            'relbar1': False,
                            'footer': False
                        },
                        'epub_title': "fake_epub2_title",
                        'epub_author': "fake_epub2_author",
                        'epub_language': 'fr',
                        'epub_publisher': "fake_epub2_publisher",
                        'epub_copyright': 'fake_epub2_copyright',
                        'epub_identifier': "9781449325299",
                        'epub_scheme': 'ISBN',
                        'epub_uid': "BookID"}
                    )
def test_build_epub(app):
    # type: (SphinxTestApp) -> None
    app.build()
    assert (app.outdir / 'mimetype').text() == 'application/epub+zip'
    assert (app.outdir / 'META-INF' / 'container.xml').exists()

    # toc.ncx
    toc = EPUBElementTree.fromstring((app.outdir / 'toc.ncx').text())
    assert toc.find("./ncx:docTitle/ncx:text").text == app.config.epub_title

    # toc.ncx / head
    meta = list(toc.find("./ncx:head"))
    assert meta[0].attrib == {'name': 'dtb:uid', 'content': app.config.epub_identifier}
    assert meta[1].attrib == {'name': 'dtb:depth', 'content': '1'}
    assert meta[2].attrib == {'name': 'dtb:totalPageCount', 'content': '0'}
    assert meta[3].attrib == {'name': 'dtb:maxPageNumber', 'content': '0'}

    # toc.ncx / navMap
    navpoints = toc.findall("./ncx:navMap/ncx:navPoint")
    assert len(navpoints) == 1
    assert navpoints[0].attrib == {'id': 'navPoint1', 'playOrder': '1'}
    assert navpoints[0].find("./ncx:content").attrib == {'src': 'index.xhtml'}

    navlabel = navpoints[0].find("./ncx:navLabel/ncx:text")
    assert navlabel.text == 'The basic Sphinx documentation for testing'

    # content.opf
    opf = EPUBElementTree.fromstring((app.outdir / 'content.opf').text())

    # content.opf / metadata
    metadata = opf.find("./idpf:metadata")
    identifier = metadata.find("./dc:identifier")
    assert identifier.text == app.config.epub_identifier
    assert identifier.attrib == {'id': app.config.epub_uid,
                                 '{http://www.idpf.org/2007/opf}scheme': app.config.epub_scheme}
    assert metadata.find("./dc:language").text == app.config.epub_language
    assert metadata.find("./dc:title").text == app.config.epub_title
    assert metadata.find("./dc:creator").text == app.config.epub_author
    assert metadata.find("./dc:publisher").text == app.config.epub_publisher
    assert metadata.find("./dc:rights").text == app.config.epub_copyright

    # content.opf / manifest
    manifest = opf.find("./idpf:manifest")
    items = list(manifest)
    assert items[0].attrib == {'id': 'ncx',
                               'href': 'toc.ncx',
                               'media-type': 'application/x-dtbncx+xml'}
    assert items[1].attrib == {'id': 'epub-0',
                               'href': 'genindex.xhtml',
                               'media-type': 'application/xhtml+xml'}
    assert items[2].attrib == {'id': 'epub-1',
                               'href': 'index.xhtml',
                               'media-type': 'application/xhtml+xml'}

    for i, item in enumerate(items[1:]):
        # items are named as epub-NN
        assert item.get('id') == 'epub-%d' % i

    # content.opf / spine
    spine = opf.find("./idpf:spine")
    itemrefs = list(spine)
    assert spine.get('toc') == 'ncx'
    assert itemrefs[0].get('idref') == 'epub-1'
    assert itemrefs[1].get('idref') == 'epub-0'

    # content.opf / guide
    reference = opf.find("./idpf:guide/idpf:reference")
    assert reference.get('type') == 'toc'
    assert reference.get('title') == 'Table of Contents'
    assert reference.get('href') == 'index.xhtml'


@pytest.mark.sphinx('epub2', testroot='footnotes',
                    confoverrides={'epub_cover': ('_images/rimg.png', None)})
def test_epub_cover(app):
    app.build()

    # content.opf / metadata
    opf = EPUBElementTree.fromstring((app.outdir / 'content.opf').text())
    cover_image = opf.find("./idpf:manifest/idpf:item[@href='%s']" % app.config.epub_cover[0])
    cover = opf.find("./idpf:metadata/idpf:meta[@name='cover']")
    assert cover
    assert cover.get('content') == cover_image.get('id')


@pytest.mark.sphinx('epub2', testroot='toctree')
def test_nested_toc(app):
    app.build()

    # toc.ncx
    toc = EPUBElementTree.fromstring((app.outdir / 'toc.ncx').bytes())
    assert toc.find("./ncx:docTitle/ncx:text").text == 'Python  documentation'

    # toc.ncx / navPoint
    def navinfo(elem):
        label = elem.find("./ncx:navLabel/ncx:text")
        content = elem.find("./ncx:content")
        return (elem.get('id'), elem.get('playOrder'),
                content.get('src'), label.text)

    navpoints = toc.findall("./ncx:navMap/ncx:navPoint")
    assert len(navpoints) == 4
    assert navinfo(navpoints[0]) == ('navPoint1', '1', 'index.xhtml',
                                     u"Welcome to Sphinx Tests’s documentation!")
    assert navpoints[0].findall("./ncx:navPoint") == []

    # toc.ncx / nested navPoints
    assert navinfo(navpoints[1]) == ('navPoint2', '2', 'foo.xhtml', 'foo')
    navchildren = navpoints[1].findall("./ncx:navPoint")
    assert len(navchildren) == 4
    assert navinfo(navchildren[0]) == ('navPoint3', '2', 'foo.xhtml', 'foo')
    assert navinfo(navchildren[1]) == ('navPoint4', '3', 'quux.xhtml', 'quux')
    assert navinfo(navchildren[2]) == ('navPoint5', '4', 'foo.xhtml#foo-1', 'foo.1')
    assert navinfo(navchildren[3]) == ('navPoint8', '6', 'foo.xhtml#foo-2', 'foo.2')
