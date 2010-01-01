# -*- coding: utf-8 -*-
"""
    sphinx.writers.html
    ~~~~~~~~~~~~~~~~~~~

    docutils writers handling Sphinx' custom nodes.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import posixpath
import os

from docutils import nodes
from docutils.writers.html4css1 import Writer, HTMLTranslator as BaseTranslator

from sphinx.locale import admonitionlabels, versionlabels
from sphinx.util.smartypants import sphinx_smarty_pants

try:
    import Image                        # check for the Python Imaging Library
except ImportError:
    Image = None


class HTMLWriter(Writer):
    def __init__(self, builder):
        Writer.__init__(self)
        self.builder = builder

    def translate(self):
        # sadly, this is mostly copied from parent class
        self.visitor = visitor = self.builder.translator_class(self.builder,
                                                               self.document)
        self.document.walkabout(visitor)
        self.output = visitor.astext()
        for attr in ('head_prefix', 'stylesheet', 'head', 'body_prefix',
                     'body_pre_docinfo', 'docinfo', 'body', 'fragment',
                     'body_suffix', 'meta', 'title', 'subtitle', 'header',
                     'footer', 'html_prolog', 'html_head', 'html_title',
                     'html_subtitle', 'html_body', ):
            setattr(self, attr, getattr(visitor, attr, None))
        self.clean_meta = ''.join(visitor.meta[2:])


class HTMLTranslator(BaseTranslator):
    """
    Our custom HTML translator.
    """

    def __init__(self, builder, *args, **kwds):
        BaseTranslator.__init__(self, *args, **kwds)
        self.highlighter = builder.highlighter
        self.no_smarty = 0
        self.builder = builder
        self.highlightlang = builder.config.highlight_language
        self.highlightlinenothreshold = sys.maxint
        self.protect_literal_text = 0
        self.add_permalinks = builder.config.html_add_permalinks

    def visit_desc(self, node):
        self.body.append(self.starttag(node, 'dl', CLASS=node['desctype']))
    def depart_desc(self, node):
        self.body.append('</dl>\n\n')

    def visit_desc_signature(self, node):
        # the id is set automatically
        self.body.append(self.starttag(node, 'dt'))
        # anchor for per-desc interactive data
        if node.parent['desctype'] != 'describe' \
               and node['ids'] and node['first']:
            self.body.append('<!--[%s]-->' % node['ids'][0])
    def depart_desc_signature(self, node):
        if node['ids'] and self.add_permalinks and self.builder.add_permalinks:
            self.body.append(u'<a class="headerlink" href="#%s" '
                             % node['ids'][0] +
                             u'title="%s">\u00B6</a>' %
                             _('Permalink to this definition'))
        self.body.append('</dt>\n')

    def visit_desc_addname(self, node):
        self.body.append(self.starttag(node, 'tt', '', CLASS='descclassname'))
    def depart_desc_addname(self, node):
        self.body.append('</tt>')

    def visit_desc_type(self, node):
        pass
    def depart_desc_type(self, node):
        pass

    def visit_desc_returns(self, node):
        self.body.append(' &rarr; ')
    def depart_desc_returns(self, node):
        pass

    def visit_desc_name(self, node):
        self.body.append(self.starttag(node, 'tt', '', CLASS='descname'))
    def depart_desc_name(self, node):
        self.body.append('</tt>')

    def visit_desc_parameterlist(self, node):
        self.body.append('<big>(</big>')
        self.first_param = 1
    def depart_desc_parameterlist(self, node):
        self.body.append('<big>)</big>')

    def visit_desc_parameter(self, node):
        if not self.first_param:
            self.body.append(', ')
        else:
            self.first_param = 0
        if not node.hasattr('noemph'):
            self.body.append('<em>')
    def depart_desc_parameter(self, node):
        if not node.hasattr('noemph'):
            self.body.append('</em>')

    def visit_desc_optional(self, node):
        self.body.append('<span class="optional">[</span>')
    def depart_desc_optional(self, node):
        self.body.append('<span class="optional">]</span>')

    def visit_desc_annotation(self, node):
        self.body.append(self.starttag(node, 'em', '', CLASS='property'))
    def depart_desc_annotation(self, node):
        self.body.append('</em>')

    def visit_desc_content(self, node):
        self.body.append(self.starttag(node, 'dd', ''))
    def depart_desc_content(self, node):
        self.body.append('</dd>')

    def visit_refcount(self, node):
        self.body.append(self.starttag(node, 'em', '', CLASS='refcount'))
    def depart_refcount(self, node):
        self.body.append('</em>')

    def visit_versionmodified(self, node):
        self.body.append(self.starttag(node, 'p'))
        text = versionlabels[node['type']] % node['version']
        if len(node):
            text += ': '
        else:
            text += '.'
        self.body.append('<span class="versionmodified">%s</span>' % text)
    def depart_versionmodified(self, node):
        self.body.append('</p>\n')

    # overwritten
    def visit_reference(self, node):
        BaseTranslator.visit_reference(self, node)
        if node.hasattr('reftitle'):
            # ugly hack to add a title attribute
            starttag = self.body[-1]
            if not starttag.startswith('<a '):
                return
            self.body[-1] = '<a title="%s"' % self.attval(node['reftitle']) + \
                            starttag[2:]
        if node.hasattr('secnumber'):
            self.body.append('%s. ' % '.'.join(map(str, node['secnumber'])))

    # overwritten -- we don't want source comments to show up in the HTML
    def visit_comment(self, node):
        raise nodes.SkipNode

    # overwritten
    def visit_admonition(self, node, name=''):
        self.body.append(self.starttag(
            node, 'div', CLASS=('admonition ' + name)))
        if name and name != 'seealso':
            node.insert(0, nodes.title(name, admonitionlabels[name]))
        self.set_first_last(node)

    def visit_seealso(self, node):
        self.visit_admonition(node, 'seealso')
    def depart_seealso(self, node):
        self.depart_admonition(node)

    def add_secnumber(self, node):
        if node.hasattr('secnumber'):
            self.body.append('.'.join(map(str, node['secnumber'])) + '. ')
        elif isinstance(node.parent, nodes.section):
            anchorname = '#' + node.parent['ids'][0]
            if anchorname not in self.builder.secnumbers:
                anchorname = ''  # try first heading which has no anchor
            if anchorname in self.builder.secnumbers:
                numbers = self.builder.secnumbers[anchorname]
                self.body.append('.'.join(map(str, numbers)) + '. ')

    # overwritten for docutils 0.4
    if hasattr(BaseTranslator, 'start_tag_with_title'):
        def visit_section(self, node):
            # the 0.5 version, to get the id attribute in the <div> tag
            self.section_level += 1
            self.body.append(self.starttag(node, 'div', CLASS='section'))

        def visit_title(self, node):
            # don't move the id attribute inside the <h> tag
            BaseTranslator.visit_title(self, node, move_ids=0)
            self.add_secnumber(node)
    else:
        def visit_title(self, node):
            BaseTranslator.visit_title(self, node)
            self.add_secnumber(node)

    # overwritten
    def visit_literal_block(self, node):
        if node.rawsource != node.astext():
            # most probably a parsed-literal block -- don't highlight
            return BaseTranslator.visit_literal_block(self, node)
        lang = self.highlightlang
        linenos = node.rawsource.count('\n') >= \
                  self.highlightlinenothreshold - 1
        if node.has_key('language'):
            # code-block directives
            lang = node['language']
        if node.has_key('linenos'):
            linenos = node['linenos']
        highlighted = self.highlighter.highlight_block(node.rawsource,
                                                       lang, linenos)
        starttag = self.starttag(node, 'div', suffix='',
                                 CLASS='highlight-%s' % lang)
        self.body.append(starttag + highlighted + '</div>\n')
        raise nodes.SkipNode

    def visit_doctest_block(self, node):
        self.visit_literal_block(node)

    # overwritten
    def visit_literal(self, node):
        if len(node.children) == 1 and \
               node.children[0] in ('None', 'True', 'False'):
            node['classes'].append('xref')
        self.body.append(self.starttag(node, 'tt', '',
                                       CLASS='docutils literal'))
        self.protect_literal_text += 1
    def depart_literal(self, node):
        self.protect_literal_text -= 1
        self.body.append('</tt>')

    def visit_productionlist(self, node):
        self.body.append(self.starttag(node, 'pre'))
        names = []
        for production in node:
            names.append(production['tokenname'])
        maxlen = max(len(name) for name in names)
        for production in node:
            if production['tokenname']:
                lastname = production['tokenname'].ljust(maxlen)
                self.body.append(self.starttag(production, 'strong', ''))
                self.body.append(lastname + '</strong> ::= ')
            else:
                self.body.append('%s     ' % (' '*len(lastname)))
            production.walkabout(self)
            self.body.append('\n')
        self.body.append('</pre>\n')
        raise nodes.SkipNode
    def depart_productionlist(self, node):
        pass

    def visit_production(self, node):
        pass
    def depart_production(self, node):
        pass

    def visit_centered(self, node):
        self.body.append(self.starttag(node, 'p', CLASS="centered")
                         + '<strong>')
    def depart_centered(self, node):
        self.body.append('</strong></p>')

    def visit_compact_paragraph(self, node):
        pass
    def depart_compact_paragraph(self, node):
        pass

    def visit_highlightlang(self, node):
        self.highlightlang = node['lang']
        self.highlightlinenothreshold = node['linenothreshold']
    def depart_highlightlang(self, node):
        pass

    def visit_download_reference(self, node):
        if node.hasattr('filename'):
            self.body.append('<a href="%s">' % posixpath.join(
                self.builder.dlpath, node['filename']))
            self.context.append('</a>')
        else:
            self.context.append('')
    def depart_download_reference(self, node):
        self.body.append(self.context.pop())

    # overwritten
    def visit_image(self, node):
        olduri = node['uri']
        # rewrite the URI if the environment knows about it
        if olduri in self.builder.images:
            node['uri'] = posixpath.join(self.builder.imgpath,
                                         self.builder.images[olduri])

        if node['uri'].lower().endswith('svg') or \
           node['uri'].lower().endswith('svgz'):
            atts = {'data': node['uri'], 'type': 'image/svg+xml'}
            if node.has_key('width'):
                atts['width'] = node['width']
            if node.has_key('height'):
                atts['height'] = node['height']
            if node.has_key('align'):
                self.body.append('<div align="%s" class="align-%s">' %
                                 (node['align'], node['align']))
                self.context.append('</div>\n')
            else:
                self.context.append('')
            embatts = atts.copy()
            embatts['src'] = embatts.pop('data')
            self.body.append(self.starttag(node, 'object', '', **atts))
            self.body.append(self.emptytag(node, 'embed', '', **embatts))
            self.body.append('</object>\n')
            return

        if node.has_key('scale'):
            if Image and not (node.has_key('width')
                              and node.has_key('height')):
                try:
                    im = Image.open(os.path.join(self.builder.srcdir, olduri))
                except (IOError, # Source image can't be found or opened
                        UnicodeError):  # PIL doesn't like Unicode paths.
                    pass
                else:
                    if not node.has_key('width'):
                        node['width'] = str(im.size[0])
                    if not node.has_key('height'):
                        node['height'] = str(im.size[1])
                    del im
        BaseTranslator.visit_image(self, node)

    def visit_toctree(self, node):
        # this only happens when formatting a toc from env.tocs -- in this
        # case we don't want to include the subtree
        raise nodes.SkipNode

    def visit_index(self, node):
        raise nodes.SkipNode

    def visit_tabular_col_spec(self, node):
        raise nodes.SkipNode

    def visit_glossary(self, node):
        pass
    def depart_glossary(self, node):
        pass

    def visit_acks(self, node):
        pass
    def depart_acks(self, node):
        pass

    def visit_module(self, node):
        pass
    def depart_module(self, node):
        pass

    def visit_hlist(self, node):
        self.body.append('<table class="hlist"><tr>')
    def depart_hlist(self, node):
        self.body.append('</tr></table>\n')

    def visit_hlistcol(self, node):
        self.body.append('<td>')
    def depart_hlistcol(self, node):
        self.body.append('</td>')

    def bulk_text_processor(self, text):
        return text

    # overwritten
    def visit_Text(self, node):
        text = node.astext()
        encoded = self.encode(text)
        if self.protect_literal_text:
            # moved here from base class's visit_literal to support
            # more formatting in literal nodes
            for token in self.words_and_spaces.findall(encoded):
                if token.strip():
                    # protect literal text from line wrapping
                    self.body.append('<span class="pre">%s</span>' % token)
                elif token in ' \n':
                    # allow breaks at whitespace
                    self.body.append(token)
                else:
                    # protect runs of multiple spaces; the last one can wrap
                    self.body.append('&nbsp;' * (len(token)-1) + ' ')
        else:
            if self.in_mailto and self.settings.cloak_email_addresses:
                encoded = self.cloak_email(encoded)
            else:
                encoded = self.bulk_text_processor(encoded)
            self.body.append(encoded)

    # these are all for docutils 0.5 compatibility

    def visit_note(self, node):
        self.visit_admonition(node, 'note')
    def depart_note(self, node):
        self.depart_admonition(node)

    def visit_warning(self, node):
        self.visit_admonition(node, 'warning')
    def depart_warning(self, node):
        self.depart_admonition(node)

    def visit_attention(self, node):
        self.visit_admonition(node, 'attention')

    def depart_attention(self, node):
        self.depart_admonition()

    def visit_caution(self, node):
        self.visit_admonition(node, 'caution')
    def depart_caution(self, node):
        self.depart_admonition()

    def visit_danger(self, node):
        self.visit_admonition(node, 'danger')
    def depart_danger(self, node):
        self.depart_admonition()

    def visit_error(self, node):
        self.visit_admonition(node, 'error')
    def depart_error(self, node):
        self.depart_admonition()

    def visit_hint(self, node):
        self.visit_admonition(node, 'hint')
    def depart_hint(self, node):
        self.depart_admonition()

    def visit_important(self, node):
        self.visit_admonition(node, 'important')
    def depart_important(self, node):
        self.depart_admonition()

    def visit_tip(self, node):
        self.visit_admonition(node, 'tip')
    def depart_tip(self, node):
        self.depart_admonition()

    # these are only handled specially in the SmartyPantsHTMLTranslator
    def visit_literal_emphasis(self, node):
        return self.visit_emphasis(node)
    def depart_literal_emphasis(self, node):
        return self.depart_emphasis(node)

    def visit_abbreviation(self, node):
        attrs = {}
        if node.hasattr('explanation'):
            attrs['title'] = node['explanation']
        self.body.append(self.starttag(node, 'abbr', '', **attrs))
    def depart_abbreviation(self, node):
        self.body.append('</abbr>')

    def depart_title(self, node):
        close_tag = self.context[-1]
        if (self.add_permalinks and self.builder.add_permalinks and
            node.parent.hasattr('ids') and node.parent['ids']):
            aname = node.parent['ids'][0]
            # add permalink anchor
            if close_tag.startswith('</h'):
                self.body.append(u'<a class="headerlink" href="#%s" ' % aname +
                                 u'title="%s">\u00B6</a>' %
                                 _('Permalink to this headline'))
            elif close_tag.startswith('</a></h'):
                self.body.append(u'</a><a class="headerlink" href="#%s" ' %
                                 aname +
                                 u'title="%s">\u00B6' %
                                 _('Permalink to this headline'))

        BaseTranslator.depart_title(self, node)

    def unknown_visit(self, node):
        raise NotImplementedError('Unknown node: ' + node.__class__.__name__)


class SmartyPantsHTMLTranslator(HTMLTranslator):
    """
    Handle ordinary text via smartypants, converting quotes and dashes
    to the correct entities.
    """

    def __init__(self, *args, **kwds):
        self.no_smarty = 0
        HTMLTranslator.__init__(self, *args, **kwds)

    def visit_literal(self, node):
        self.no_smarty += 1
        try:
            # this raises SkipNode
            HTMLTranslator.visit_literal(self, node)
        finally:
            self.no_smarty -= 1

    def visit_literal_block(self, node):
        self.no_smarty += 1
        try:
            HTMLTranslator.visit_literal_block(self, node)
        finally:
            self.no_smarty -= 1

    def visit_literal_emphasis(self, node):
        self.no_smarty += 1
        self.visit_emphasis(node)

    def depart_literal_emphasis(self, node):
        self.depart_emphasis(node)
        self.no_smarty -= 1

    def visit_desc_signature(self, node):
        self.no_smarty += 1
        HTMLTranslator.visit_desc_signature(self, node)

    def depart_desc_signature(self, node):
        self.no_smarty -= 1
        HTMLTranslator.depart_desc_signature(self, node)

    def visit_productionlist(self, node):
        self.no_smarty += 1
        try:
            HTMLTranslator.visit_productionlist(self, node)
        finally:
            self.no_smarty -= 1

    def visit_option(self, node):
        self.no_smarty += 1
        HTMLTranslator.visit_option(self, node)
    def depart_option(self, node):
        self.no_smarty -= 1
        HTMLTranslator.depart_option(self, node)

    def bulk_text_processor(self, text):
        if self.no_smarty <= 0:
            return sphinx_smarty_pants(text)
        return text
