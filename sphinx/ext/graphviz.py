# -*- coding: utf-8 -*-
"""
    sphinx.ext.graphviz
    ~~~~~~~~~~~~~~~~~~~

    Allow graphviz-formatted graphs to be included in Sphinx-generated
    documents inline.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import codecs
import posixpath
from os import path
from math import ceil
from subprocess import Popen, PIPE
try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx.errors import SphinxError
from sphinx.locale import _
from sphinx.util.osutil import ensuredir, ENOENT, EPIPE, EINVAL
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
    optional_arguments = 1
    final_argument_whitespace = False
    option_spec = {
        'alt': directives.unchanged,
        'inline': directives.flag,
        'caption': directives.unchanged,
    }

    def run(self):
        if self.arguments:
            document = self.state.document
            if self.content:
                return [document.reporter.warning(
                    'Graphviz directive cannot have both content and '
                    'a filename argument', line=self.lineno)]
            env = self.state.document.settings.env
            rel_filename, filename = env.relfn2path(self.arguments[0])
            env.note_dependency(rel_filename)
            try:
                fp = codecs.open(filename, 'r', 'utf-8')
                try:
                    dotcode = fp.read()
                finally:
                    fp.close()
            except (IOError, OSError):
                return [document.reporter.warning(
                    'External Graphviz file %r not found or reading '
                    'it failed' % filename, line=self.lineno)]
        else:
            dotcode = '\n'.join(self.content)
            if not dotcode.strip():
                return [self.state_machine.reporter.warning(
                    'Ignoring "graphviz" directive without content.',
                    line=self.lineno)]
        node = graphviz()
        node['code'] = dotcode
        node['options'] = []
        if 'alt' in self.options:
            node['alt'] = self.options['alt']
        if 'caption' in self.options:
            node['caption'] = self.options['caption']
        node['inline'] = 'inline' in self.options
        return [node]


class GraphvizSimple(Directive):
    """
    Directive to insert arbitrary dot markup.
    """
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'alt': directives.unchanged,
        'inline': directives.flag,
        'caption': directives.unchanged,
    }

    def run(self):
        node = graphviz()
        node['code'] = '%s %s {\n%s\n}\n' % \
                       (self.name, self.arguments[0], '\n'.join(self.content))
        node['options'] = []
        if 'alt' in self.options:
            node['alt'] = self.options['alt']
        if 'caption' in self.options:
            node['caption'] = self.options['caption']
        node['inline'] = 'inline' in self.options
        return [node]


def render_dot(self, code, options, format, prefix='graphviz'):
    """Render graphviz code into a PNG or PDF output file."""
    hashkey = code.encode('utf-8') + str(options) + \
              str(self.builder.config.graphviz_dot) + \
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
    wentWrong = False
    try:
        # Graphviz may close standard input when an error occurs,
        # resulting in a broken pipe on communicate()
        stdout, stderr = p.communicate(code)
    except (OSError, IOError), err:
        if err.errno != EPIPE:
            raise
        wentWrong = True
    except IOError, err:
        if err.errno != EINVAL:
            raise
        wentWrong = True
    if wentWrong:
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
    format = self.builder.config.graphviz_output_format
    try:
        if format not in ('png', 'svg'):
            raise GraphvizError("graphviz_output_format must be one of 'png', "
                                "'svg', but is %r" % format)
        fname, outfn = render_dot(self, code, options, format, prefix)
    except GraphvizError, exc:
        self.builder.warn('dot code %r: ' % code + str(exc))
        raise nodes.SkipNode

    inline = node.get('inline', False)
    if inline:
        wrapper = 'span'
    else:
        wrapper = 'p'

    self.body.append(self.starttag(node, wrapper, CLASS='graphviz'))
    if fname is None:
        self.body.append(self.encode(code))
    else:
        if alt is None:
            alt = node.get('alt', self.encode(code).strip())
        imgcss = imgcls and 'class="%s"' % imgcls or ''
        if format == 'svg':
            svgtag = '<img src="%s" alt="%s" %s/>\n' % (fname, alt, imgcss)
            self.body.append(svgtag)
        else:
            mapfile = open(outfn + '.map', 'rb')
            try:
                imgmap = mapfile.readlines()
            finally:
                mapfile.close()
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
        if node.get('caption') and not inline:
            self.body.append('</p>\n<p class="caption">')
            self.body.append(self.encode(node['caption']))

    self.body.append('</%s>\n' % wrapper)
    raise nodes.SkipNode


def html_visit_graphviz(self, node):
    render_dot_html(self, node, node['code'], node['options'])


def render_dot_latex(self, node, code, options, prefix='graphviz'):
    try:
        fname, outfn = render_dot(self, code, options, 'pdf', prefix)
    except GraphvizError, exc:
        self.builder.warn('dot code %r: ' % code + str(exc))
        raise nodes.SkipNode

    inline = node.get('inline', False)
    if inline:
        para_separator = ''
    else:
        para_separator = '\n'

    if fname is not None:
        caption = node.get('caption')
        # XXX add ids from previous target node
        if caption and not inline:
            self.body.append('\n\\begin{figure}[h!]')
            self.body.append('\n\\begin{center}')
            self.body.append('\n\\caption{%s}' % self.encode(caption))
            self.body.append('\n\\includegraphics{%s}' % fname)
            self.body.append('\n\\end{center}')
            self.body.append('\n\\end{figure}\n')
        else:
            self.body.append('%s\\includegraphics{%s}%s' %
                             (para_separator, fname, para_separator))
    raise nodes.SkipNode


def latex_visit_graphviz(self, node):
    render_dot_latex(self, node, node['code'], node['options'])


def render_dot_texinfo(self, node, code, options, prefix='graphviz'):
    try:
        fname, outfn = render_dot(self, code, options, 'png', prefix)
    except GraphvizError, exc:
        self.builder.warn('dot code %r: ' % code + str(exc))
        raise nodes.SkipNode
    if fname is not None:
        self.body.append('\n\n@float\n')
        caption = node.get('caption')
        if caption:
            self.body.append('@caption{%s}\n' % self.escape_arg(caption))
        self.body.append('@image{%s,,,[graphviz],png}\n'
                         '@end float\n\n' % fname[:-4])
    raise nodes.SkipNode

def texinfo_visit_graphviz(self, node):
    render_dot_texinfo(self, node, node['code'], node['options'])


def text_visit_graphviz(self, node):
    if 'alt' in node.attributes:
        self.add_text(_('[graph: %s]') % node['alt'])
    self.add_text(_('[graph]'))


def man_visit_graphviz(self, node):
    if 'alt' in node.attributes:
        self.body.append(_('[graph: %s]') % node['alt'] + '\n')
    self.body.append(_('[graph]'))
    raise nodes.SkipNode


def setup(app):
    app.add_node(graphviz,
                 html=(html_visit_graphviz, None),
                 latex=(latex_visit_graphviz, None),
                 texinfo=(texinfo_visit_graphviz, None),
                 text=(text_visit_graphviz, None),
                 man=(man_visit_graphviz, None))
    app.add_directive('graphviz', Graphviz)
    app.add_directive('graph', GraphvizSimple)
    app.add_directive('digraph', GraphvizSimple)
    app.add_config_value('graphviz_dot', 'dot', 'html')
    app.add_config_value('graphviz_dot_args', [], 'html')
    app.add_config_value('graphviz_output_format', 'png', 'html')
