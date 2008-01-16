# -*- coding: utf-8 -*-
"""
    sphinx.web.oldurls
    ~~~~~~~~~~~~~~~~~~

    Handle old URLs gracefully.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import re

from sphinx.web.wsgiutil import RedirectResponse, NotFound


_module_re = re.compile(r'module-(.*)\.html')
_modobj_re = re.compile(r'(.*)-objects\.html')
_modsub_re = re.compile(r'(.*?)-(.*)\.html')


special_module_names = {
    'main': '__main__',
    'builtin': '__builtin__',
    'future': '__future__',
    'pycompile': 'py_compile',
}

tutorial_nodes = [
    '', '', '',
    'appetite',
    'interpreter',
    'introduction',
    'controlflow',
    'datastructures',
    'modules',
    'inputoutput',
    'errors',
    'classes',
    'stdlib',
    'stdlib2',
    'whatnow',
    'interactive',
    'floatingpoint',
    '',
    'glossary',
]


def handle_html_url(req, url):
    def inner():
        # global special pages
        if url.endswith('/contents.html'):
            return 'contents/'
        if url.endswith('/genindex.html'):
            return 'genindex/'
        if url.endswith('/about.html'):
            return 'about/'
        if url.endswith('/reporting-bugs.html'):
            return 'bugs/'
        if url == 'modindex.html' or url.endswith('/modindex.html'):
            return 'modindex/'
        if url == 'mac/using.html':
            return 'howto/pythonmac/'
        # library
        if url[:4] in ('lib/', 'mac/'):
            p = 'library/'
            m = _module_re.match(url[4:])
            if m:
                mn = m.group(1)
                return p + special_module_names.get(mn, mn)
            # module sub-pages
            m = _modsub_re.match(url[4:])
            if m and not _modobj_re.match(url[4:]):
                mn = m.group(1)
                return p + special_module_names.get(mn, mn)
        # XXX: handle all others
        # tutorial
        elif url[:4] == 'tut/':
            try:
                node = int(url[8:].split('.html')[0])
            except ValueError:
                pass
            else:
                if tutorial_nodes[node]:
                    return 'tutorial/' + tutorial_nodes[node]
        # installing: all in one (ATM)
        elif url[:5] == 'inst/':
            return 'install/'
        # no mapping for "documenting Python..."
        # nothing found
        raise NotFound()
    return RedirectResponse('%s?oldurl=1' % inner())
