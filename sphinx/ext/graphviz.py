# -*- coding: utf-8 -*-
"""
    sphinx.ext.graphviz
    ~~~~~~~~~~~~~~~~~~~

    Allow graphviz-formatted graphs to be included in Sphinx-generated
    documents inline.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import posixpath
from os import path
from subprocess import Popen, PIPE
try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha

from docutils import nodes

from sphinx.errors import SphinxError
from sphinx.util import ensuredir, ENOENT, EPIPE
from sphinx.util.compat import Directive


mapname_re = re.compile(r'<map id="(.*?)"')


class GraphvizError(SphinxError):
    category = 'Graphviz error'


class graphviz(nodes.General, nodes.Element):
    pass


class Graphviz(Directive):
    """
    Directive to insert arbitrary dot markup.
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        dotcode = '\n'.join(self.content)
        if not dotcode.strip():
            return [self.state_machine.reporter.warning(
                'Ignoring "graphviz" directive without content.',
                line=self.lineno)]
        node = graphviz()
        node['code'] = dotcode
        node['options'] = []
        return [node]


class GraphvizSimple(Directive):
    """
    Directive to insert arbitrary dot markup.
    """
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        node = graphviz()
        node['code'] = '%s %s {\n%s\n}\n' % \
                       (self.name, self.arguments[0], '\n'.join(self.content))
        node['options'] = []
        return [node]


def render_dot(self, code, options, format, prefix='graphviz'):
    """
    Render graphviz code into a PNG or PDF output file.
    """
    hashkey = code.encode('utf-8') + str(options) + \
              str(self.builder.config.graphviz_dot_args)
    fname = '%s-%s.%s' % (prefix, sha(hashkey).hexdigest(), format)
    if hasattr(self.builder, 'imgpath'):
        # HTML
        relfn = posixpath.join(self.builder.imgpath, fname)
        outfn = path.join(self.builder.outdir, '_images', fname)
    else:
        # LaTeX
        relfn = fname
        outfn = path.join(self.builder.outdir, fname)

    if path.isfile(outfn):
        return relfn, outfn

    if hasattr(self.builder, '_graphviz_warned_dot') or \
       hasattr(self.builder, '_graphviz_warned_ps2pdf'):
        return None, None

    ensuredir(path.dirname(outfn))

    # graphviz expects UTF-8 by default
    if isinstance(code, unicode):
        code = code.encode('utf-8')

    dot_args = [self.builder.config.graphviz_dot]
    dot_args.extend(self.builder.config.graphviz_dot_args)
    dot_args.extend(options)
    dot_args.extend(['-T' + format, '-o' + outfn])
    if format == 'png':
        dot_args.extend(['-Tcmapx', '-o%s.map' % outfn])
    try:
        p = Popen(dot_args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    except OSError, err:
        if err.errno != ENOENT:   # No such file or directory
            raise
        self.builder.warn('dot command %r cannot be run (needed for graphviz '
                          'output), check the graphviz_dot setting' %
                          self.builder.config.graphviz_dot)
        self.builder._graphviz_warned_dot = True
        return None, None
    try:
        # Graphviz may close standard input when an error occurs,
        # resulting in a broken pipe on communicate()
        stdout, stderr = p.communicate(code)
    except OSError, err:
        if err.errno != EPIPE:
            raise
        # in this case, read the standard output and standard error streams
        # directly, to get the error message(s)
        stdout, stderr = p.stdout.read(), p.stderr.read()
        p.wait()
    if p.returncode != 0:
        raise GraphvizError('dot exited with error:\n[stderr]\n%s\n'
                            '[stdout]\n%s' % (stderr, stdout))
    return relfn, outfn


def render_dot_html(self, node, code, options, prefix='graphviz',
                    imgcls=None, alt=None):
    try:
        fname, outfn = render_dot(self, code, options, 'png', prefix)
    except GraphvizError, exc:
        self.builder.warn('dot code %r: ' % code + str(exc))
        raise nodes.SkipNode

    self.body.append(self.starttag(node, 'p', CLASS='graphviz'))
    if fname is None:
        self.body.append(self.encode(code))
    else:
        mapfile = open(outfn + '.map', 'rb')
        try:
            imgmap = mapfile.readlines()
        finally:
            mapfile.close()
        imgcss = imgcls and 'class="%s"' % imgcls or ''
        if alt is None:
            alt = self.encode(code).strip()
        if len(imgmap) == 2:
            # nothing in image map (the lines are <map> and </map>)
            self.body.append('<img src="%s" alt="%s" %s/>\n' %
                             (fname, alt, imgcss))
        else:
            # has a map: get the name of the map and connect the parts
            mapname = mapname_re.match(imgmap[0]).group(1)
            self.body.append('<img src="%s" alt="%s" usemap="#%s" %s/>\n' %
                             (fname, alt, mapname, imgcss))
            self.body.extend(imgmap)
    self.body.append('</p>\n')
    raise nodes.SkipNode


def html_visit_graphviz(self, node):
    render_dot_html(self, node, node['code'], node['options'])


def render_dot_latex(self, node, code, options, prefix='graphviz'):
    try:
        fname, outfn = render_dot(self, code, options, 'pdf', prefix)
    except GraphvizError, exc:
        self.builder.warn('dot code %r: ' % code + str(exc))
        raise nodes.SkipNode

    if fname is not None:
        self.body.append('\\includegraphics{%s}' % fname)
    raise nodes.SkipNode


def latex_visit_graphviz(self, node):
    render_dot_latex(self, node, node['code'], node['options'])

def setup(app):
    app.add_node(graphviz,
                 html=(html_visit_graphviz, None),
                 latex=(latex_visit_graphviz, None))
    app.add_directive('graphviz', Graphviz)
    app.add_directive('graph', GraphvizSimple)
    app.add_directive('digraph', GraphvizSimple)
    app.add_config_value('graphviz_dot', 'dot', 'html')
    app.add_config_value('graphviz_dot_args', [], 'html')
