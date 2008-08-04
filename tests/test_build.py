# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test the entire build process with the test root.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

import os
import htmlentitydefs
from StringIO import StringIO
from etree13 import ElementTree as ET

from util import *

from sphinx.builder import StandaloneHTMLBuilder, LaTeXBuilder


html_warnfile = StringIO()
latex_warnfile = StringIO()

ENV_WARNINGS = """\
WARNING: %(root)s/images.txt:9: Image file not readable: foo.png
WARNING: %(root)s/images.txt:20: Nonlocal image URI found: http://www.python.org/logo.png
WARNING: %(root)s/includes.txt:: (WARNING/2) Encoding 'utf-8' used for reading included file u'wrongenc.inc' seems to be wrong, try giving an :encoding: option
"""

HTML_WARNINGS = ENV_WARNINGS + """\
WARNING: %(root)s/images.txt:: no matching candidate for image URI u'foo.*'
"""

LATEX_WARNINGS = ENV_WARNINGS + """\
WARNING: None:: no matching candidate for image URI u'foo.*'
"""

HTML_XPATH = {
    'images.html': {
        ".//img[@src='_images/img.png']": '',
        ".//img[@src='_images/img1.png']": '',
    },
    'includes.html': {
        ".//pre/span[@class='s']": u'üöä',
        ".//pre": u'Max Strauß',
    },
}

class NslessParser(ET.XMLParser):
    """XMLParser that throws away namespaces in tag names."""

    def _fixname(self, key):
        try:
            return self._names[key]
        except KeyError:
            name = key
            br = name.find('}')
            if br > 0:
                name = name[br+1:]
            self._names[key] = name = self._fixtext(name)
            return name


@with_testapp(buildername='html', warning=html_warnfile)
def test_html(app):
    app.builder.build_all()
    html_warnings = html_warnfile.getvalue().replace(os.sep, '/')
    assert html_warnings == HTML_WARNINGS % {'root': app.srcdir}

    if not ET:
        return
    for fname, paths in HTML_XPATH.iteritems():
        parser = NslessParser()
        parser.entity.update(htmlentitydefs.entitydefs)
        etree = ET.parse(app.outdir / fname, parser)
        for path, text in paths.iteritems():
            nodes = list(etree.findall(path))
            assert nodes != []
            if not text:
                # only check for node presence
                continue
            for node in nodes:
                if node.text and text in node.text:
                    break
            else:
                assert False, ('%r not found in any node matching '
                               'path %s in %s' % (text, path, fname))


@with_testapp(buildername='latex', warning=latex_warnfile)
def test_latex(app):
    app.builder.build_all()
    latex_warnings = latex_warnfile.getvalue().replace(os.sep, '/')
    assert latex_warnings == LATEX_WARNINGS % {'root': app.srcdir}
