# -*- coding: utf-8 -*-
"""
    sphinx.ext.viewcode
    ~~~~~~~~~~~~~~~~~~~

    Add links to module code in Python object descriptions.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

from sphinx import addnodes
from sphinx.util import make_refnode
from sphinx.pycode import ModuleAnalyzer


def doctree_read(app, doctree):
    env = app.builder.env
    if not hasattr(env, '_viewcode_modules'):
        env._viewcode_modules = {}

    def has_tag(modname, fullname, docname):
        entry = env._viewcode_modules.get(modname, None)
        if entry is None:
            try:
                analyzer = ModuleAnalyzer.for_module(modname)
            except Exception:
                env._viewcode_modules[modname] = False
                return
            analyzer.find_tags()
            entry = analyzer.code, analyzer.tags, {}
            env._viewcode_modules[modname] = entry
        elif entry is False:
            return
        code, tags, used = entry
        if fullname in tags:
            used[fullname] = docname
            return True

    for objnode in doctree.traverse(addnodes.desc):
        if objnode['domain'] != 'py':
            continue
        names = set()
        for signode in objnode:
            if not isinstance(signode, addnodes.desc_signature):
                continue
            modname = signode['module']
            if not modname:
                continue
            fullname = signode['fullname']
            if not has_tag(modname, fullname, env.docname):
                continue
            if fullname in names:
                # only one link per name, please
                continue
            names.add(fullname)
            pagename = '_modules/' + modname.replace('.', '/')
            onlynode = addnodes.only(expr='html')
            onlynode += addnodes.pending_xref(
                '', reftype='viewcode', refdomain='std', refexplicit=False,
                reftarget=pagename, refid=fullname,
                refdoc=env.docname)
            onlynode[0] += nodes.inline('', _('[source]'),
                                        classes=['viewcode-link'])
            signode += onlynode


def missing_reference(app, env, node, contnode):
    # resolve our "viewcode" reference nodes -- they need special treatment
    if node['reftype'] == 'viewcode':
        return make_refnode(app.builder, node['refdoc'], node['reftarget'],
                            node['refid'], contnode)


def collect_pages(app):
    env = app.builder.env
    if not hasattr(env, '_viewcode_modules'):
        return
    highlighter = app.builder.highlighter
    urito = app.builder.get_relative_uri

    modnames = set(env._viewcode_modules)

    for modname, (code, tags, used) in env._viewcode_modules.iteritems():
        # construct a page name for the highlighted source
        pagename = '_modules/' + modname.replace('.', '/')
        # highlight the source using the builder's highlighter
        highlighted = highlighter.highlight_block(code, 'python', False)
        # split the code into lines
        lines = highlighted.splitlines()
        # split off wrap markup from the first line of the actual code
        before, after = lines[0].split('<pre>')
        lines[0:1] = [before + '<pre>', after]
        # nothing to do for the last line; it always starts with </pre> anyway
        # now that we have code lines (starting at index 1), insert anchors for
        # the collected tags (HACK: this only works if the tag boundaries are
        # properly nested!)
        for name, docname in used.iteritems():
            type, start, end = tags[name]
            backlink = urito(pagename, docname) + '#' + modname + '.' + name
            lines[start] = (
                '<div class="viewcode-block" id="%s"><a class="viewcode-back" '
                'href="%s">%s</a>' % (name, backlink, _('[docs]'))
                + lines[start])
            lines[end - 1] += '</div>'
        # try to find parents (for submodules)
        parents = []
        parent = modname
        while '.' in parent:
            parent = parent.rsplit('.', 1)[0]
            if parent in modnames:
                parents.append({
                    'link': urito(pagename, '_modules/' +
                                  parent.replace('.', '/')),
                    'title': parent})
        parents.append({'link': urito(pagename, '_modules/index'),
                        'title': _('Module code')})
        parents.reverse()
        # putting it all together
        context = {
            'parents': parents,
            'title': modname,
            'body': _('<h2>Source code for %s</h2>') % modname + \
                    '\n'.join(lines)
        }
        app.builder.info(' '+pagename, nonl=1)
        yield (pagename, context, 'page.html')

    if not modnames:
        return

    app.builder.info(' _modules/index')
    html = ['\n']
    # the stack logic is needed for using nested lists for submodules
    stack = ['']
    for modname in sorted(modnames):
        if modname.startswith(stack[-1]):
            stack.append(modname + '.')
            html.append('<ul>')
        else:
            stack.pop()
            while not modname.startswith(stack[-1]):
                stack.pop()
                html.append('</ul>')
            stack.append(modname + '.')
        html.append('<li><a href="%s">%s</a></li>\n' % (
            urito('_modules/index', '_modules/' + modname.replace('.', '/')),
            modname))
    html.append('</ul>' * (len(stack) - 1))
    context = {
        'title': _('Overview: module code'),
        'body': _('<h2>All modules for which code is available</h2>') + \
            ''.join(html),
    }

    yield ('_modules/index', context, 'page.html')


def setup(app):
    app.connect('doctree-read', doctree_read)
    app.connect('html-collect-pages', collect_pages)
    app.connect('missing-reference', missing_reference)
    #app.add_config_value('viewcode_include_modules', [], 'env')
    #app.add_config_value('viewcode_exclude_modules', [], 'env')
