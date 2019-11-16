"""
    sphinx.writers.html5
    ~~~~~~~~~~~~~~~~~~~~

    Experimental docutils writers for HTML5 handling Sphinx' custom nodes.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import posixpath
import sys
import warnings
from typing import Any, Iterable, Tuple
from typing import cast

from docutils import nodes
from docutils.nodes import Element, Node, Text
from docutils.writers.html5_polyglot import HTMLTranslator as BaseTranslator

from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.deprecation import RemovedInSphinx30Warning, RemovedInSphinx40Warning
from sphinx.locale import admonitionlabels, _, __
from sphinx.util import logging
from sphinx.util.docutils import SphinxTranslator
from sphinx.util.images import get_image_size

if False:
    # For type annotation
    from sphinx.builders.html import StandaloneHTMLBuilder


logger = logging.getLogger(__name__)

# A good overview of the purpose behind these classes can be found here:
# http://www.arnebrodowski.de/blog/write-your-own-restructuredtext-writer.html


class HTML5Translator(SphinxTranslator, BaseTranslator):
    """
    Our custom HTML translator.
    """

    builder = None  # type: StandaloneHTMLBuilder

    def __init__(self, *args: Any) -> None:
        if isinstance(args[0], nodes.document) and isinstance(args[1], Builder):
            document, builder = args
        else:
            warnings.warn('The order of arguments for HTML5Translator has been changed. '
                          'Please give "document" as 1st and "builder" as 2nd.',
                          RemovedInSphinx40Warning, stacklevel=2)
            builder, document = args
        super().__init__(document, builder)

        self.highlighter = self.builder.highlighter
        self.docnames = [self.builder.current_docname]  # for singlehtml builder
        self.manpages_url = self.config.manpages_url
        self.protect_literal_text = 0
        self.permalink_text = self.config.html_add_permalinks
        # support backwards-compatible setting to a bool
        if not isinstance(self.permalink_text, str):
            self.permalink_text = '¶' if self.permalink_text else ''
        self.permalink_text = self.encode(self.permalink_text)
        self.secnumber_suffix = self.config.html_secnumber_suffix
        self.param_separator = ''
        self.optional_param_level = 0
        self._table_row_index = 0
        self._fieldlist_row_index = 0
        self.required_params_left = 0

    def visit_start_of_file(self, node: Element) -> None:
        # only occurs in the single-file builder
        self.docnames.append(node['docname'])
        self.body.append('<span id="document-%s"></span>' % node['docname'])

    def depart_start_of_file(self, node: Element) -> None:
        self.docnames.pop()

    def visit_desc(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'dl', CLASS=node['objtype']))

    def depart_desc(self, node: Element) -> None:
        self.body.append('</dl>\n\n')

    def visit_desc_signature(self, node: Element) -> None:
        # the id is set automatically
        self.body.append(self.starttag(node, 'dt'))
        # anchor for per-desc interactive data
        if node.parent['objtype'] != 'describe' \
           and node['ids'] and node['first']:
            self.body.append('<!--[%s]-->' % node['ids'][0])

    def depart_desc_signature(self, node: Element) -> None:
        if not node.get('is_multiline'):
            self.add_permalink_ref(node, _('Permalink to this definition'))
        self.body.append('</dt>\n')

    def visit_desc_signature_line(self, node: Element) -> None:
        pass

    def depart_desc_signature_line(self, node: Element) -> None:
        if node.get('add_permalink'):
            # the permalink info is on the parent desc_signature node
            self.add_permalink_ref(node.parent, _('Permalink to this definition'))
        self.body.append('<br />')

    def visit_desc_addname(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'code', '', CLASS='sig-prename descclassname'))

    def depart_desc_addname(self, node: Element) -> None:
        self.body.append('</code>')

    def visit_desc_type(self, node: Element) -> None:
        pass

    def depart_desc_type(self, node: Element) -> None:
        pass

    def visit_desc_returns(self, node: Element) -> None:
        self.body.append(' &#x2192; ')

    def depart_desc_returns(self, node: Element) -> None:
        pass

    def visit_desc_name(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'code', '', CLASS='sig-name descname'))

    def depart_desc_name(self, node: Element) -> None:
        self.body.append('</code>')

    def visit_desc_parameterlist(self, node: Element) -> None:
        self.body.append('<span class="sig-paren">(</span>')
        self.first_param = 1
        self.optional_param_level = 0
        # How many required parameters are left.
        self.required_params_left = sum([isinstance(c, addnodes.desc_parameter)
                                         for c in node.children])
        self.param_separator = node.child_text_separator

    def depart_desc_parameterlist(self, node: Element) -> None:
        self.body.append('<span class="sig-paren">)</span>')

    # If required parameters are still to come, then put the comma after
    # the parameter.  Otherwise, put the comma before.  This ensures that
    # signatures like the following render correctly (see issue #1001):
    #
    #     foo([a, ]b, c[, d])
    #
    def visit_desc_parameter(self, node: Element) -> None:
        if self.first_param:
            self.first_param = 0
        elif not self.required_params_left:
            self.body.append(self.param_separator)
        if self.optional_param_level == 0:
            self.required_params_left -= 1
        if not node.hasattr('noemph'):
            self.body.append('<em class="sig-param">')

    def depart_desc_parameter(self, node: Element) -> None:
        if not node.hasattr('noemph'):
            self.body.append('</em>')
        if self.required_params_left:
            self.body.append(self.param_separator)

    def visit_desc_optional(self, node: Element) -> None:
        self.optional_param_level += 1
        self.body.append('<span class="optional">[</span>')

    def depart_desc_optional(self, node: Element) -> None:
        self.optional_param_level -= 1
        self.body.append('<span class="optional">]</span>')

    def visit_desc_annotation(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'em', '', CLASS='property'))

    def depart_desc_annotation(self, node: Element) -> None:
        self.body.append('</em>')

    def visit_desc_content(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'dd', ''))

    def depart_desc_content(self, node: Element) -> None:
        self.body.append('</dd>')

    def visit_versionmodified(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'div', CLASS=node['type']))

    def depart_versionmodified(self, node: Element) -> None:
        self.body.append('</div>\n')

    # overwritten
    def visit_reference(self, node: Element) -> None:
        atts = {'class': 'reference'}
        if node.get('internal') or 'refuri' not in node:
            atts['class'] += ' internal'
        else:
            atts['class'] += ' external'
        if 'refuri' in node:
            atts['href'] = node['refuri'] or '#'
            if self.settings.cloak_email_addresses and atts['href'].startswith('mailto:'):
                atts['href'] = self.cloak_mailto(atts['href'])
                self.in_mailto = True
        else:
            assert 'refid' in node, \
                   'References must have "refuri" or "refid" attribute.'
            atts['href'] = '#' + node['refid']
        if not isinstance(node.parent, nodes.TextElement):
            assert len(node) == 1 and isinstance(node[0], nodes.image)
            atts['class'] += ' image-reference'
        if 'reftitle' in node:
            atts['title'] = node['reftitle']
        if 'target' in node:
            atts['target'] = node['target']
        self.body.append(self.starttag(node, 'a', '', **atts))

        if node.get('secnumber'):
            self.body.append(('%s' + self.secnumber_suffix) %
                             '.'.join(map(str, node['secnumber'])))

    def visit_number_reference(self, node: Element) -> None:
        self.visit_reference(node)

    def depart_number_reference(self, node: Element) -> None:
        self.depart_reference(node)

    # overwritten -- we don't want source comments to show up in the HTML
    def visit_comment(self, node: Element) -> None:  # type: ignore
        raise nodes.SkipNode

    # overwritten
    def visit_admonition(self, node: Element, name: str = '') -> None:
        self.body.append(self.starttag(
            node, 'div', CLASS=('admonition ' + name)))
        if name:
            node.insert(0, nodes.title(name, admonitionlabels[name]))

    def visit_seealso(self, node: Element) -> None:
        self.visit_admonition(node, 'seealso')

    def depart_seealso(self, node: Element) -> None:
        self.depart_admonition(node)

    def get_secnumber(self, node: Element) -> Tuple[int, ...]:
        if node.get('secnumber'):
            return node['secnumber']

        if isinstance(node.parent, nodes.section):
            if self.builder.name == 'singlehtml':
                docname = self.docnames[-1]
                anchorname = "%s/#%s" % (docname, node.parent['ids'][0])
                if anchorname not in self.builder.secnumbers:
                    anchorname = "%s/" % docname  # try first heading which has no anchor
            else:
                anchorname = '#' + node.parent['ids'][0]
                if anchorname not in self.builder.secnumbers:
                    anchorname = ''  # try first heading which has no anchor

            if self.builder.secnumbers.get(anchorname):
                return self.builder.secnumbers[anchorname]

        return None

    def add_secnumber(self, node: Element) -> None:
        secnumber = self.get_secnumber(node)
        if secnumber:
            self.body.append('<span class="section-number">%s</span>' %
                             ('.'.join(map(str, secnumber)) + self.secnumber_suffix))

    def add_fignumber(self, node: Element) -> None:
        def append_fignumber(figtype: str, figure_id: str) -> None:
            if self.builder.name == 'singlehtml':
                key = "%s/%s" % (self.docnames[-1], figtype)
            else:
                key = figtype

            if figure_id in self.builder.fignumbers.get(key, {}):
                self.body.append('<span class="caption-number">')
                prefix = self.builder.config.numfig_format.get(figtype)
                if prefix is None:
                    msg = __('numfig_format is not defined for %s') % figtype
                    logger.warning(msg)
                else:
                    numbers = self.builder.fignumbers[key][figure_id]
                    self.body.append(prefix % '.'.join(map(str, numbers)) + ' ')
                    self.body.append('</span>')

        figtype = self.builder.env.domains['std'].get_enumerable_node_type(node)
        if figtype:
            if len(node['ids']) == 0:
                msg = __('Any IDs not assigned for %s node') % node.tagname
                logger.warning(msg, location=node)
            else:
                append_fignumber(figtype, node['ids'][0])

    def add_permalink_ref(self, node: Element, title: str) -> None:
        if node['ids'] and self.permalink_text and self.builder.add_permalinks:
            format = '<a class="headerlink" href="#%s" title="%s">%s</a>'
            self.body.append(format % (node['ids'][0], title, self.permalink_text))

    # overwritten
    def visit_bullet_list(self, node: Element) -> None:
        if len(node) == 1 and isinstance(node[0], addnodes.toctree):
            # avoid emitting empty <ul></ul>
            raise nodes.SkipNode
        super().visit_bullet_list(node)

    # overwritten
    def visit_definition(self, node: Element) -> None:
        # don't insert </dt> here.
        self.body.append(self.starttag(node, 'dd', ''))

    # overwritten
    def depart_definition(self, node: Element) -> None:
        self.body.append('</dd>\n')

    # overwritten
    def visit_classifier(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'span', '', CLASS='classifier'))

    # overwritten
    def depart_classifier(self, node: Element) -> None:
        self.body.append('</span>')

        next_node = node.next_node(descend=False, siblings=True)  # type: Node
        if not isinstance(next_node, nodes.classifier):
            # close `<dt>` tag at the tail of classifiers
            self.body.append('</dt>')

    # overwritten
    def visit_term(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'dt', ''))

    # overwritten
    def depart_term(self, node: Element) -> None:
        next_node = node.next_node(descend=False, siblings=True)  # type: Node
        if isinstance(next_node, nodes.classifier):
            # Leave the end tag to `self.depart_classifier()`, in case
            # there's a classifier.
            pass
        else:
            self.body.append('</dt>')

    # overwritten
    def visit_title(self, node: Element) -> None:
        super().visit_title(node)
        self.add_secnumber(node)
        self.add_fignumber(node.parent)

    def depart_title(self, node: Element) -> None:
        close_tag = self.context[-1]
        if (self.permalink_text and self.builder.add_permalinks and
           node.parent.hasattr('ids') and node.parent['ids']):
            # add permalink anchor
            if close_tag.startswith('</h'):
                self.add_permalink_ref(node.parent, _('Permalink to this headline'))
            elif close_tag.startswith('</a></h'):
                self.body.append('</a><a class="headerlink" href="#%s" ' %
                                 node.parent['ids'][0] +
                                 'title="%s">%s' % (
                                     _('Permalink to this headline'),
                                     self.permalink_text))
            elif isinstance(node.parent, nodes.table):
                self.body.append('</span>')
                self.add_permalink_ref(node.parent, _('Permalink to this table'))
        elif isinstance(node.parent, nodes.table):
            self.body.append('</span>')

        super().depart_title(node)

    def visit_table_title(self, node):
        # type: (nodes.Element) -> None
        super().visit_title(node)
        self.add_fignumber(node.parent)
        self.body.append('<span class="caption-text">')

    def depart_table_title(self, node):
        # type: (nodes.Element) -> None
        self.body.append('</span>')
        if self.permalink_text and self.builder.add_permalinks and node.parent.get('ids'):
            # add permalink anchor
            self.add_permalink_ref(node.parent, _('Permalink to this table'))
        super().depart_title(node)

    # overwritten
    def visit_literal_block(self, node: Element) -> None:
        if node.rawsource != node.astext():
            # most probably a parsed-literal block -- don't highlight
            return super().visit_literal_block(node)

        lang = node.get('language', 'default')
        linenos = node.get('linenos', False)
        highlight_args = node.get('highlight_args', {})
        highlight_args['force'] = node.get('force', False)
        if lang is self.builder.config.highlight_language:
            # only pass highlighter options for original language
            opts = self.builder.config.highlight_options
        else:
            opts = {}

        highlighted = self.highlighter.highlight_block(
            node.rawsource, lang, opts=opts, linenos=linenos,
            location=(self.builder.current_docname, node.line), **highlight_args
        )
        starttag = self.starttag(node, 'div', suffix='',
                                 CLASS='highlight-%s notranslate' % lang)
        self.body.append(starttag + highlighted + '</div>\n')
        raise nodes.SkipNode

    def visit_caption(self, node: Element) -> None:
        super().visit_caption(node)
        self.add_fignumber(node.parent)
        self.body.append(self.starttag(node, 'span', '', CLASS='caption-text'))

    def depart_caption(self, node: Element) -> None:
        self.body.append('</span>')

        # append permalink if available
        if node.parent.get('toctree'):
            self.add_permalink_ref(node.parent.parent, _('Permalink to this toctree'))

        super().depart_caption(node)

    def visit_figure_caption(self, node: Element) -> None:
        super().visit_caption(node)

    def depart_figure_caption(self, node: Element) -> None:
        self.body.append('</span>')
        self.add_permalink_ref(node.parent, _('Permalink to this image'))
        super().depart_caption(node)

    def visit_container_caption(self, node: Element) -> None:
        if node.parent.get('literal_block'):
            self.body.append('<div class="code-block-caption">')
        else:
            super().visit_caption(node)

        self.add_fignumber(node.parent)
        self.body.append(self.starttag(node, 'span', '', CLASS='caption-text'))

    def depart_container_caption(self, node: Element) -> None:
        self.body.append('</span>')

        if node.parent.get('literal_block'):
            self.add_permalink_ref(node.parent, _('Permalink to this code'))
            self.body.append('</div>\n')
        else:
            super().depart_caption(node)

    def visit_doctest_block(self, node: Element) -> None:
        self.visit_literal_block(node)

    # overwritten to add the <div> (for XHTML compliance)
    def visit_block_quote(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'blockquote') + '<div>')

    def depart_block_quote(self, node: Element) -> None:
        self.body.append('</div></blockquote>\n')

    # overwritten
    def visit_literal(self, node: Element) -> None:
        if 'kbd' in node['classes']:
            self.body.append(self.starttag(node, 'kbd', '',
                                           CLASS='docutils literal notranslate'))
        else:
            self.body.append(self.starttag(node, 'code', '',
                                           CLASS='docutils literal notranslate'))
            self.protect_literal_text += 1

    def depart_literal(self, node: Element) -> None:
        if 'kbd' in node['classes']:
            self.body.append('</kbd>')
        else:
            self.protect_literal_text -= 1
            self.body.append('</code>')

    def visit_productionlist(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'pre'))
        names = []
        productionlist = cast(Iterable[addnodes.production], node)
        for production in productionlist:
            names.append(production['tokenname'])
        maxlen = max(len(name) for name in names)
        lastname = None
        for production in productionlist:
            if production['tokenname']:
                lastname = production['tokenname'].ljust(maxlen)
                self.body.append(self.starttag(production, 'strong', ''))
                self.body.append(lastname + '</strong> ::= ')
            elif lastname is not None:
                self.body.append('%s     ' % (' ' * len(lastname)))
            production.walkabout(self)
            self.body.append('\n')
        self.body.append('</pre>\n')
        raise nodes.SkipNode

    def depart_productionlist(self, node: Element) -> None:
        pass

    def visit_production(self, node: Element) -> None:
        pass

    def depart_production(self, node: Element) -> None:
        pass

    def visit_centered(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'p', CLASS="centered") +
                         '<strong>')

    def depart_centered(self, node: Element) -> None:
        self.body.append('</strong></p>')

    def visit_compact_paragraph(self, node: Element) -> None:
        pass

    def depart_compact_paragraph(self, node: Element) -> None:
        pass

    def visit_download_reference(self, node: Element) -> None:
        atts = {'class': 'reference download',
                'download': ''}

        if not self.builder.download_support:
            self.context.append('')
        elif 'refuri' in node:
            atts['class'] += ' external'
            atts['href'] = node['refuri']
            self.body.append(self.starttag(node, 'a', '', **atts))
            self.context.append('</a>')
        elif 'filename' in node:
            atts['class'] += ' internal'
            atts['href'] = posixpath.join(self.builder.dlpath, node['filename'])
            self.body.append(self.starttag(node, 'a', '', **atts))
            self.context.append('</a>')
        else:
            self.context.append('')

    def depart_download_reference(self, node: Element) -> None:
        self.body.append(self.context.pop())

    # overwritten
    def visit_image(self, node: Element) -> None:
        olduri = node['uri']
        # rewrite the URI if the environment knows about it
        if olduri in self.builder.images:
            node['uri'] = posixpath.join(self.builder.imgpath,
                                         self.builder.images[olduri])

        if 'scale' in node:
            # Try to figure out image height and width.  Docutils does that too,
            # but it tries the final file name, which does not necessarily exist
            # yet at the time the HTML file is written.
            if not ('width' in node and 'height' in node):
                size = get_image_size(os.path.join(self.builder.srcdir, olduri))
                if size is None:
                    logger.warning(__('Could not obtain image size. :scale: option is ignored.'),  # NOQA
                                   location=node)
                else:
                    if 'width' not in node:
                        node['width'] = str(size[0])
                    if 'height' not in node:
                        node['height'] = str(size[1])

        uri = node['uri']
        if uri.lower().endswith(('svg', 'svgz')):
            atts = {'src': uri}
            if 'width' in node:
                atts['width'] = node['width']
            if 'height' in node:
                atts['height'] = node['height']
            if 'scale' in node:
                scale = node['scale'] / 100.0
                if 'width' in atts:
                    atts['width'] = int(atts['width']) * scale
                if 'height' in atts:
                    atts['height'] = int(atts['height']) * scale
            atts['alt'] = node.get('alt', uri)
            if 'align' in node:
                self.body.append('<div align="%s" class="align-%s">' %
                                 (node['align'], node['align']))
                self.context.append('</div>\n')
            else:
                self.context.append('')
            self.body.append(self.emptytag(node, 'img', '', **atts))
            return

        super().visit_image(node)

    # overwritten
    def depart_image(self, node: Element) -> None:
        if node['uri'].lower().endswith(('svg', 'svgz')):
            self.body.append(self.context.pop())
        else:
            super().depart_image(node)

    def visit_toctree(self, node: Element) -> None:
        # this only happens when formatting a toc from env.tocs -- in this
        # case we don't want to include the subtree
        raise nodes.SkipNode

    def visit_index(self, node: Element) -> None:
        raise nodes.SkipNode

    def visit_tabular_col_spec(self, node: Element) -> None:
        raise nodes.SkipNode

    def visit_glossary(self, node: Element) -> None:
        pass

    def depart_glossary(self, node: Element) -> None:
        pass

    def visit_acks(self, node: Element) -> None:
        pass

    def depart_acks(self, node: Element) -> None:
        pass

    def visit_hlist(self, node: Element) -> None:
        self.body.append('<table class="hlist"><tr>')

    def depart_hlist(self, node: Element) -> None:
        self.body.append('</tr></table>\n')

    def visit_hlistcol(self, node: Element) -> None:
        self.body.append('<td>')

    def depart_hlistcol(self, node: Element) -> None:
        self.body.append('</td>')

    # overwritten
    def visit_Text(self, node: Text) -> None:
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
                    self.body.append('&#160;' * (len(token) - 1) + ' ')
        else:
            if self.in_mailto and self.settings.cloak_email_addresses:
                encoded = self.cloak_email(encoded)
            self.body.append(encoded)

    def visit_note(self, node: Element) -> None:
        self.visit_admonition(node, 'note')

    def depart_note(self, node: Element) -> None:
        self.depart_admonition(node)

    def visit_warning(self, node: Element) -> None:
        self.visit_admonition(node, 'warning')

    def depart_warning(self, node: Element) -> None:
        self.depart_admonition(node)

    def visit_attention(self, node: Element) -> None:
        self.visit_admonition(node, 'attention')

    def depart_attention(self, node: Element) -> None:
        self.depart_admonition(node)

    def visit_caution(self, node: Element) -> None:
        self.visit_admonition(node, 'caution')

    def depart_caution(self, node: Element) -> None:
        self.depart_admonition(node)

    def visit_danger(self, node: Element) -> None:
        self.visit_admonition(node, 'danger')

    def depart_danger(self, node: Element) -> None:
        self.depart_admonition(node)

    def visit_error(self, node: Element) -> None:
        self.visit_admonition(node, 'error')

    def depart_error(self, node: Element) -> None:
        self.depart_admonition(node)

    def visit_hint(self, node: Element) -> None:
        self.visit_admonition(node, 'hint')

    def depart_hint(self, node: Element) -> None:
        self.depart_admonition(node)

    def visit_important(self, node: Element) -> None:
        self.visit_admonition(node, 'important')

    def depart_important(self, node: Element) -> None:
        self.depart_admonition(node)

    def visit_tip(self, node: Element) -> None:
        self.visit_admonition(node, 'tip')

    def depart_tip(self, node: Element) -> None:
        self.depart_admonition(node)

    def visit_literal_emphasis(self, node: Element) -> None:
        return self.visit_emphasis(node)

    def depart_literal_emphasis(self, node: Element) -> None:
        return self.depart_emphasis(node)

    def visit_literal_strong(self, node: Element) -> None:
        return self.visit_strong(node)

    def depart_literal_strong(self, node: Element) -> None:
        return self.depart_strong(node)

    def visit_abbreviation(self, node: Element) -> None:
        attrs = {}
        if node.hasattr('explanation'):
            attrs['title'] = node['explanation']
        self.body.append(self.starttag(node, 'abbr', '', **attrs))

    def depart_abbreviation(self, node: Element) -> None:
        self.body.append('</abbr>')

    def visit_manpage(self, node: Element) -> None:
        self.visit_literal_emphasis(node)
        if self.manpages_url:
            node['refuri'] = self.manpages_url.format(**node.attributes)
            self.visit_reference(node)

    def depart_manpage(self, node: Element) -> None:
        if self.manpages_url:
            self.depart_reference(node)
        self.depart_literal_emphasis(node)

    # overwritten to add even/odd classes

    def generate_targets_for_table(self, node: Element) -> None:
        """Generate hyperlink targets for tables.

        Original visit_table() generates hyperlink targets inside table tags
        (<table>) if multiple IDs are assigned to listings.
        That is invalid DOM structure.  (This is a bug of docutils <= 0.13.1)

        This exports hyperlink targets before tables to make valid DOM structure.
        """
        for id in node['ids'][1:]:
            self.body.append('<span id="%s"></span>' % id)
            node['ids'].remove(id)

    def visit_table(self, node: Element) -> None:
        self.generate_targets_for_table(node)

        self._table_row_index = 0

        classes = [cls.strip(' \t\n') for cls in self.settings.table_style.split(',')]
        classes.insert(0, "docutils")  # compat
        if 'align' in node:
            classes.append('align-%s' % node['align'])
        tag = self.starttag(node, 'table', CLASS=' '.join(classes))
        self.body.append(tag)

    def visit_row(self, node: Element) -> None:
        self._table_row_index += 1
        if self._table_row_index % 2 == 0:
            node['classes'].append('row-even')
        else:
            node['classes'].append('row-odd')
        self.body.append(self.starttag(node, 'tr', ''))
        node.column = 0  # type: ignore

    def visit_field_list(self, node: Element) -> None:
        self._fieldlist_row_index = 0
        return super().visit_field_list(node)

    def visit_field(self, node: Element) -> None:
        self._fieldlist_row_index += 1
        if self._fieldlist_row_index % 2 == 0:
            node['classes'].append('field-even')
        else:
            node['classes'].append('field-odd')

    def visit_math(self, node: Element, math_env: str = '') -> None:
        name = self.builder.math_renderer_name
        visit, _ = self.builder.app.registry.html_inline_math_renderers[name]
        visit(self, node)

    def depart_math(self, node: Element, math_env: str = '') -> None:
        name = self.builder.math_renderer_name
        _, depart = self.builder.app.registry.html_inline_math_renderers[name]
        if depart:
            depart(self, node)

    def visit_math_block(self, node: Element, math_env: str = '') -> None:
        name = self.builder.math_renderer_name
        visit, _ = self.builder.app.registry.html_block_math_renderers[name]
        visit(self, node)

    def depart_math_block(self, node: Element, math_env: str = '') -> None:
        name = self.builder.math_renderer_name
        _, depart = self.builder.app.registry.html_block_math_renderers[name]
        if depart:
            depart(self, node)

    def unknown_visit(self, node: Node) -> None:
        raise NotImplementedError('Unknown node: ' + node.__class__.__name__)

    # --------- METHODS FOR COMPATIBILITY --------------------------------------

    @property
    def highlightlang(self) -> str:
        warnings.warn('HTMLTranslator.highlightlang is deprecated.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return self.builder.config.highlight_language

    @property
    def highlightlang_base(self) -> str:
        warnings.warn('HTMLTranslator.highlightlang_base is deprecated.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return self.builder.config.highlight_language

    @property
    def highlightopts(self) -> str:
        warnings.warn('HTMLTranslator.highlightopts is deprecated.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return self.builder.config.highlight_options

    @property
    def highlightlinenothreshold(self) -> int:
        warnings.warn('HTMLTranslator.highlightlinenothreshold is deprecated.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return sys.maxsize
