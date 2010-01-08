# -*- coding: utf-8 -*-
"""
    test_build_html
    ~~~~~~~~~~~~~~~

    Test the HTML builder and check output against XPath.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import difflib
import htmlentitydefs
from StringIO import StringIO

try:
    import pygments
except ImportError:
    pygments = None

from sphinx import __version__
from util import *
from test_build import ENV_WARNINGS
from etree13 import ElementTree as ET


def teardown_module():
    (test_root / '_build').rmtree(True)


html_warnfile = StringIO()

HTML_WARNINGS = ENV_WARNINGS + """\
%(root)s/images.txt:20: WARNING: no matching candidate for image URI u'foo.*'
%(root)s/markup.txt:: WARNING: invalid index entry u''
%(root)s/markup.txt:: WARNING: invalid pair index entry u''
%(root)s/markup.txt:: WARNING: invalid pair index entry u'keyword; '
"""

HTML_XPATH = {
    'images.html': {
        ".//img[@src='_images/img.png']": '',
        ".//img[@src='_images/img1.png']": '',
        ".//img[@src='_images/simg.png']": '',
        ".//object[@data='_images/svgimg.svg']": '',
        ".//embed[@src='_images/svgimg.svg']": '',
    },
    'subdir/images.html': {
        ".//img[@src='../_images/img1.png']": '',
        ".//img[@src='../_images/rimg.png']": '',
    },
    'subdir/includes.html': {
        ".//a[@href='../_downloads/img.png']": '',
    },
    'includes.html': {
        ".//pre": u'Max Strauß',
        ".//a[@href='_downloads/img.png']": '',
        ".//a[@href='_downloads/img1.png']": '',
        ".//pre": u'"quotes"',
        ".//pre": u"'included'",
    },
    'autodoc.html': {
        ".//dt[@id='test_autodoc.Class']": '',
        ".//dt[@id='test_autodoc.function']/em": r'\*\*kwds',
        ".//dd": r'Return spam\.',
    },
    'markup.html': {
        ".//meta[@name='author'][@content='Me']": '',
        ".//meta[@name='keywords'][@content='docs, sphinx']": '',
        ".//a[@href='contents.html#ref1']": '',
        ".//div[@id='label']": '',
        ".//span[@class='option']": '--help',
        ".//p": 'A global substitution.',
        ".//p": 'In HTML.',
        ".//p": 'In both.',
        ".//p": 'Always present',
        ".//title": 'set by title directive',
        ".//span[@class='pre']": 'CFunction()',
    },
    'desc.html': {
        ".//dt[@id='mod.Cls.meth1']": '',
        ".//dt[@id='errmod.Error']": '',
        ".//a[@href='#mod.Cls']": '',
        ".//dl[@class='userdesc']": '',
        ".//dt[@id='userdescrole-myobj']": '',
        ".//a[@href='#userdescrole-myobj']": '',
        # custom sidebar
        ".//h4": 'Custom sidebar',
    },
    'contents.html': {
        ".//meta[@name='hc'][@content='hcval']": '',
        ".//meta[@name='hc_co'][@content='hcval_co']": '',
        ".//meta[@name='testopt'][@content='testoverride']": '',
        #".//td[@class='label']": r'\[Ref1\]',   # docutils 0.5 only
        ".//td[@class='label']": '',
        ".//li[@class='toctree-l1']/a": 'Testing various markup',
        ".//li[@class='toctree-l2']/a": 'Admonitions',
        ".//title": 'Sphinx <Tests>',
        ".//div[@class='footer']": 'Georg Brandl & Team',
        ".//a[@href='http://python.org/']": '',
        # custom sidebar only for contents
        ".//h4": 'Contents sidebar',
    },
    'bom.html': {
        ".//title": " File with UTF-8 BOM",
    },
    'extensions.html': {
        ".//a[@href='http://python.org/dev/']": "http://python.org/dev/",
        ".//a[@href='http://bugs.python.org/issue1000']": "issue 1000",
        ".//a[@href='http://bugs.python.org/issue1042']": "explicit caption",
    },
    '_static/statictmpl.html': {
        ".//project": 'Sphinx <Tests>',
    },
}

if pygments:
    HTML_XPATH['includes.html'].update({
        ".//pre/span[@class='s']": u'üöä',
        ".//div[@class='inc-pyobj1 highlight-text']//pre":
            r'^class Foo:\n    pass\n\s*$',
        ".//div[@class='inc-pyobj2 highlight-text']//pre":
            r'^    def baz\(\):\n        pass\n\s*$',
        ".//div[@class='inc-lines highlight-text']//pre":
            r'^class Foo:\n    pass\nclass Bar:\n$',
        ".//div[@class='inc-startend highlight-text']//pre":
            ur'^foo = u"Including Unicode characters: üöä"\n$',
        ".//div[@class='inc-preappend highlight-text']//pre":
            r'(?m)^START CODE$',
        ".//div[@class='inc-pyobj-dedent highlight-python']//span":
            r'def',
        ".//div[@class='inc-tab3 highlight-text']//pre":
            r'-| |-',
        ".//div[@class='inc-tab8 highlight-python']//pre":
            r'-|      |-',
    })
    HTML_XPATH['subdir/includes.html'].update({
        ".//pre/span": 'line 1',
        ".//pre/span": 'line 2',
    })

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


def check_xpath(etree, fname, path, check):
    nodes = list(etree.findall(path))
    assert nodes != [], ('did not find any node matching xpath '
                         '%r in file %s' % (path, fname))
    if hasattr(check, '__call__'):
        check(nodes)
    elif not check:
        # only check for node presence
        pass
    else:
        rex = re.compile(check)
        for node in nodes:
            if node.text and rex.search(node.text):
                break
        else:
            assert False, ('%r not found in any node matching '
                           'path %s in %s: %r' % (check, path, fname,
                           [node.text for node in nodes]))

def check_static_entries(outdir):
    staticdir = outdir / '_static'
    assert staticdir.isdir()
    # a file from a directory entry in html_static_path
    assert (staticdir / 'README').isfile()
    # a directory from a directory entry in html_static_path
    assert (staticdir / 'subdir' / 'foo.css').isfile()
    # a file from a file entry in html_static_path
    assert (staticdir / 'templated.css').isfile()
    assert (staticdir / 'templated.css').text().splitlines()[1] == __version__
    # a file from _static, but matches exclude_patterns
    assert not (staticdir / 'excluded.css').exists()

@gen_with_app(buildername='html', warning=html_warnfile, cleanenv=True,
              confoverrides={'html_context.hckey_co': 'hcval_co'},
              tags=['testtag'])
def test_html(app):
    app.builder.build_all()
    html_warnings = html_warnfile.getvalue().replace(os.sep, '/')
    html_warnings_exp = HTML_WARNINGS % {'root': app.srcdir}
    assert html_warnings == html_warnings_exp, 'Warnings don\'t match:\n' + \
           '\n'.join(difflib.ndiff(html_warnings_exp.splitlines(),
                                   html_warnings.splitlines()))

    for fname, paths in HTML_XPATH.iteritems():
        parser = NslessParser()
        parser.entity.update(htmlentitydefs.entitydefs)
        etree = ET.parse(os.path.join(app.outdir, fname), parser)
        for path, check in paths.iteritems():
            yield check_xpath, etree, fname, path, check

    check_static_entries(app.builder.outdir)
