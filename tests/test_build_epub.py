# -*- coding: utf-8 -*-
"""
    test_build_html
    ~~~~~~~~~~~~~~~

    Test the HTML builder and check output against XPath.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from subprocess import Popen, PIPE
from xml.etree import ElementTree

import pytest


# check given command is runnable
def runnable(command):
    try:
        p = Popen(command, stdout=PIPE, stderr=PIPE)
    except OSError:
        # command not found
        return False
    else:
        p.communicate()
        return p.returncode == 0


class EPUBElementTree(object):
    """Test helper for content.opf and toc.ncx"""
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


@pytest.mark.sphinx('epub', testroot='basic')
def test_build_epub(app):
    app.build()
    assert (app.outdir / 'mimetype').text() == 'application/epub+zip'
    assert (app.outdir / 'META-INF' / 'container.xml').exists()

    # toc.ncx
    toc = EPUBElementTree.fromstring((app.outdir / 'toc.ncx').text())
    assert toc.find("./ncx:docTitle/ncx:text").text == 'Python  documentation'

    # toc.ncx / head
    meta = list(toc.find("./ncx:head"))
    assert meta[0].attrib == {'name': 'dtb:uid', 'content': 'unknown'}
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
    assert metadata.find("./dc:language").text == 'en'
    assert metadata.find("./dc:title").text == 'Python  documentation'
    assert metadata.find("./dc:description").text == 'unknown'
    assert metadata.find("./dc:creator").text == 'unknown'
    assert metadata.find("./dc:contributor").text == 'unknown'
    assert metadata.find("./dc:publisher").text == 'unknown'
    assert metadata.find("./dc:rights").text is None
    assert metadata.find("./idpf:meta[@property='ibooks:version']").text is None
    assert metadata.find("./idpf:meta[@property='ibooks:specified-fonts']").text == 'true'
    assert metadata.find("./idpf:meta[@property='ibooks:binding']").text == 'true'
    assert metadata.find("./idpf:meta[@property='ibooks:scroll-axis']").text == 'vertical'

    # content.opf / manifest
    manifest = opf.find("./idpf:manifest")
    items = list(manifest)
    assert items[0].attrib == {'id': 'ncx',
                               'href': 'toc.ncx',
                               'media-type': 'application/x-dtbncx+xml'}
    assert items[1].attrib == {'id': 'nav',
                               'href': 'nav.xhtml',
                               'media-type': 'application/xhtml+xml',
                               'properties': 'nav'}
    assert items[2].attrib == {'id': 'epub-0',
                               'href': 'genindex.xhtml',
                               'media-type': 'application/xhtml+xml'}
    assert items[3].attrib == {'id': 'epub-1',
                               'href': 'index.xhtml',
                               'media-type': 'application/xhtml+xml'}

    for i, item in enumerate(items[2:]):
        # items are named as epub-NN
        assert item.get('id') == 'epub-%d' % i

    # content.opf / spine
    spine = opf.find("./idpf:spine")
    itemrefs = list(spine)
    assert spine.get('toc') == 'ncx'
    assert spine.get('page-progression-direction') == 'ltr'
    assert itemrefs[0].get('idref') == 'epub-1'
    assert itemrefs[1].get('idref') == 'epub-0'

    # content.opf / guide
    reference = opf.find("./idpf:guide/idpf:reference")
    assert reference.get('type') == 'toc'
    assert reference.get('title') == 'Table of Contents'
    assert reference.get('href') == 'index.xhtml'

    # nav.xhtml
    nav = EPUBElementTree.fromstring((app.outdir / 'nav.xhtml').text())
    assert nav.attrib == {'lang': 'en',
                          '{http://www.w3.org/XML/1998/namespace}lang': 'en'}
    assert nav.find("./xhtml:head/xhtml:title").text == 'Table of Contents'

    # nav.xhtml / nav
    navlist = nav.find("./xhtml:body/xhtml:nav")
    toc = navlist.findall("./xhtml:ol/xhtml:li")
    assert navlist.find("./xhtml:h1").text == 'Table of Contents'
    assert len(toc) == 1
    assert toc[0].find("./xhtml:a").get("href") == 'index.xhtml'
    assert toc[0].find("./xhtml:a").text == 'The basic Sphinx documentation for testing'


@pytest.mark.sphinx('epub', testroot='footnotes',
                    confoverrides={'epub_cover': ('_images/rimg.png', None)})
def test_epub_cover(app):
    app.build()

    # content.opf / metadata
    opf = EPUBElementTree.fromstring((app.outdir / 'content.opf').text())
    cover_image = opf.find("./idpf:manifest/idpf:item[@href='%s']" % app.config.epub_cover[0])
    cover = opf.find("./idpf:metadata/idpf:meta[@name='cover']")
    assert cover
    assert cover.get('content') == cover_image.get('id')


@pytest.mark.sphinx('epub', testroot='toctree')
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

    # nav.xhtml / nav
    def navinfo(elem):
        anchor = elem.find("./xhtml:a")
        return (anchor.get('href'), anchor.text)

    nav = EPUBElementTree.fromstring((app.outdir / 'nav.xhtml').bytes())
    toc = nav.findall("./xhtml:body/xhtml:nav/xhtml:ol/xhtml:li")
    assert len(toc) == 4
    assert navinfo(toc[0]) == ('index.xhtml',
                               u"Welcome to Sphinx Tests’s documentation!")
    assert toc[0].findall("./xhtml:ol") == []

    # nav.xhtml / nested toc
    assert navinfo(toc[1]) == ('foo.xhtml', 'foo')
    tocchildren = toc[1].findall("./xhtml:ol/xhtml:li")
    assert len(tocchildren) == 3
    assert navinfo(tocchildren[0]) == ('quux.xhtml', 'quux')
    assert navinfo(tocchildren[1]) == ('foo.xhtml#foo-1', 'foo.1')
    assert navinfo(tocchildren[2]) == ('foo.xhtml#foo-2', 'foo.2')

    grandchild = tocchildren[1].findall("./xhtml:ol/xhtml:li")
    assert len(grandchild) == 1
    assert navinfo(grandchild[0]) == ('foo.xhtml#foo-1-1', 'foo.1-1')


@pytest.mark.sphinx('epub', testroot='need-escaped')
def test_escaped_toc(app):
    app.build()

    # toc.ncx
    toc = EPUBElementTree.fromstring((app.outdir / 'toc.ncx').bytes())
    assert toc.find("./ncx:docTitle/ncx:text").text == ('need <b>"escaped"</b> '
                                                        'project  documentation')

    # toc.ncx / navPoint
    def navinfo(elem):
        label = elem.find("./ncx:navLabel/ncx:text")
        content = elem.find("./ncx:content")
        return (elem.get('id'), elem.get('playOrder'),
                content.get('src'), label.text)

    navpoints = toc.findall("./ncx:navMap/ncx:navPoint")
    assert len(navpoints) == 4
    assert navinfo(navpoints[0]) == ('navPoint1', '1', 'index.xhtml',
                                     u"Welcome to Sphinx Tests's documentation!")
    assert navpoints[0].findall("./ncx:navPoint") == []

    # toc.ncx / nested navPoints
    assert navinfo(navpoints[1]) == ('navPoint2', '2', 'foo.xhtml', '<foo>')
    navchildren = navpoints[1].findall("./ncx:navPoint")
    assert len(navchildren) == 4
    assert navinfo(navchildren[0]) == ('navPoint3', '2', 'foo.xhtml', '<foo>')
    assert navinfo(navchildren[1]) == ('navPoint4', '3', 'quux.xhtml', 'quux')
    assert navinfo(navchildren[2]) == ('navPoint5', '4', 'foo.xhtml#foo-1', u'foo “1”')
    assert navinfo(navchildren[3]) == ('navPoint8', '6', 'foo.xhtml#foo-2', 'foo.2')

    # nav.xhtml / nav
    def navinfo(elem):
        anchor = elem.find("./xhtml:a")
        return (anchor.get('href'), anchor.text)

    nav = EPUBElementTree.fromstring((app.outdir / 'nav.xhtml').bytes())
    toc = nav.findall("./xhtml:body/xhtml:nav/xhtml:ol/xhtml:li")
    assert len(toc) == 4
    assert navinfo(toc[0]) == ('index.xhtml',
                               "Welcome to Sphinx Tests's documentation!")
    assert toc[0].findall("./xhtml:ol") == []

    # nav.xhtml / nested toc
    assert navinfo(toc[1]) == ('foo.xhtml', '<foo>')
    tocchildren = toc[1].findall("./xhtml:ol/xhtml:li")
    assert len(tocchildren) == 3
    assert navinfo(tocchildren[0]) == ('quux.xhtml', 'quux')
    assert navinfo(tocchildren[1]) == ('foo.xhtml#foo-1', u'foo “1”')
    assert navinfo(tocchildren[2]) == ('foo.xhtml#foo-2', 'foo.2')

    grandchild = tocchildren[1].findall("./xhtml:ol/xhtml:li")
    assert len(grandchild) == 1
    assert navinfo(grandchild[0]) == ('foo.xhtml#foo-1-1', 'foo.1-1')


@pytest.mark.sphinx('epub', testroot='basic')
def test_epub_writing_mode(app):
    # horizontal (default)
    app.build()

    # horizontal / page-progression-direction
    opf = EPUBElementTree.fromstring((app.outdir / 'content.opf').text())
    assert opf.find("./idpf:spine").get('page-progression-direction') == 'ltr'

    # horizontal / ibooks:scroll-axis
    metadata = opf.find("./idpf:metadata")
    assert metadata.find("./idpf:meta[@property='ibooks:scroll-axis']").text == 'vertical'

    # horizontal / writing-mode (CSS)
    css = (app.outdir / '_static' / 'epub.css').text()
    assert 'writing-mode: horizontal-tb;' in css

    # vertical
    app.config.epub_writing_mode = 'vertical'
    (app.outdir / 'index.xhtml').unlink()  # forcely rebuild
    app.build()

    # vertical / page-progression-direction
    opf = EPUBElementTree.fromstring((app.outdir / 'content.opf').text())
    assert opf.find("./idpf:spine").get('page-progression-direction') == 'rtl'

    # vertical / ibooks:scroll-axis
    metadata = opf.find("./idpf:metadata")
    assert metadata.find("./idpf:meta[@property='ibooks:scroll-axis']").text == 'horizontal'

    # vertical / writing-mode (CSS)
    css = (app.outdir / '_static' / 'epub.css').text()
    assert 'writing-mode: vertical-rl;' in css


@pytest.mark.sphinx('epub', testroot='epub-anchor-id')
def test_epub_anchor_id(app):
    app.build()

    html = (app.outdir / 'index.xhtml').text()
    assert '<p id="std-setting-STATICFILES_FINDERS">blah blah blah</p>' in html
    assert 'see <a class="reference internal" href="#std-setting-STATICFILES_FINDERS">' in html


@pytest.mark.sphinx('epub', testroot='html_assets')
def test_epub_assets(app):
    app.builder.build_all()

    # epub_sytlesheets (same as html_css_files)
    content = (app.outdir / 'index.xhtml').text()
    assert ('<link rel="stylesheet" type="text/css" href="_static/css/style.css" />'
            in content)
    assert ('<link media="print" rel="stylesheet" title="title" type="text/css" '
            'href="https://example.com/custom.css" />' in content)


@pytest.mark.sphinx('epub', testroot='html_assets',
                    confoverrides={'epub_css_files': ['css/epub.css']})
def test_epub_css_files(app):
    app.builder.build_all()

    # epub_css_files
    content = (app.outdir / 'index.xhtml').text()
    assert '<link rel="stylesheet" type="text/css" href="_static/css/epub.css" />' in content

    # files in html_css_files are not outputed
    assert ('<link rel="stylesheet" type="text/css" href="_static/css/style.css" />'
            not in content)
    assert ('<link media="print" rel="stylesheet" title="title" type="text/css" '
            'href="https://example.com/custom.css" />' not in content)


@pytest.mark.sphinx('epub', testroot='roles-download')
def test_html_download_role(app, status, warning):
    app.build()
    assert not (app.outdir / '_downloads' / 'dummy.dat').exists()

    content = (app.outdir / 'index.xhtml').text()
    assert ('<li><p><code class="xref download docutils literal notranslate">'
            '<span class="pre">dummy.dat</span></code></p></li>' in content)
    assert ('<li><p><code class="xref download docutils literal notranslate">'
            '<span class="pre">not_found.dat</span></code></p></li>' in content)
    assert ('<li><p><code class="xref download docutils literal notranslate">'
            '<span class="pre">Sphinx</span> <span class="pre">logo</span></code>'
            '<span class="link-target"> [http://www.sphinx-doc.org/en/master'
            '/_static/sphinxheader.png]</span></p></li>' in content)


@pytest.mark.skipif('DO_EPUBCHECK' not in os.environ,
                    reason='Skipped because DO_EPUBCHECK is not set')
@pytest.mark.sphinx('epub')
def test_run_epubcheck(app):
    app.build()

    epubcheck = os.environ.get('EPUBCHECK_PATH', '/usr/share/java/epubcheck.jar')
    if runnable(['java', '-version']) and os.path.exists(epubcheck):
        p = Popen(['java', '-jar', epubcheck, app.outdir / 'SphinxTests.epub'],
                  stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print(stdout)
            print(stderr)
            assert False, 'epubcheck exited with return code %s' % p.returncode
