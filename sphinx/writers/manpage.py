# -*- coding: utf-8 -*-
"""
    sphinx.writers.manpage
    ~~~~~~~~~~~~~~~~~~~~~~

    Manual page writer, extended for Sphinx custom nodes.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
try:
    from docutils.writers.manpage import MACRO_DEF, Writer, \
         Translator as BaseTranslator
    has_manpage_writer = True
except ImportError:
    # define the classes in any case, sphinx.application needs it
    Writer = BaseTranslator = object
    has_manpage_writer = False

from sphinx import addnodes
from sphinx.locale import admonitionlabels, versionlabels, _
from sphinx.util.osutil import ustrftime


class ManualPageWriter(Writer):
    def __init__(self, builder):
        Writer.__init__(self)
        self.builder = builder

    def translate(self):
        visitor = ManualPageTranslator(self.builder, self.document)
        self.visitor = visitor
        self.document.walkabout(visitor)
        self.output = visitor.astext()


class ManualPageTranslator(BaseTranslator):
    """
    Custom translator.
    """

    def __init__(self, builder, *args, **kwds):
        BaseTranslator.__init__(self, *args, **kwds)
        self.builder = builder

        self.in_productionlist = 0

        # first title is the manpage title
        self.section_level = -1

        # docinfo set by man_pages config value
        self._docinfo['title'] = self.document.settings.title
        self._docinfo['subtitle'] = self.document.settings.subtitle
        if self.document.settings.authors:
            # don't set it if no author given
            self._docinfo['author'] = self.document.settings.authors
        self._docinfo['manual_section'] = self.document.settings.section

        # docinfo set by other config values
        self._docinfo['title_upper'] = self._docinfo['title'].upper()
        if builder.config.today:
            self._docinfo['date'] = builder.config.today
        else:
            self._docinfo['date'] = ustrftime(builder.config.today_fmt
                                              or _('%B %d, %Y'))
        self._docinfo['copyright'] = builder.config.copyright
        self._docinfo['version'] = builder.config.version
        self._docinfo['manual_group'] = builder.config.project

        # since self.append_header() is never called, need to do this here
        self.body.append(MACRO_DEF)

    # overwritten -- added quotes around all .TH arguments
    def header(self):
        tmpl = (".TH \"%(title_upper)s\" \"%(manual_section)s\""
                " \"%(date)s\" \"%(version)s\" \"%(manual_group)s\"\n"
                ".SH NAME\n"
                "%(title)s \- %(subtitle)s\n")
        return tmpl % self._docinfo

    def visit_start_of_file(self, node):
        pass
    def depart_start_of_file(self, node):
        pass

    def visit_desc(self, node):
        self.visit_definition_list(node)
    def depart_desc(self, node):
        self.depart_definition_list(node)

    def visit_desc_signature(self, node):
        self.visit_definition_list_item(node)
        self.visit_term(node)
    def depart_desc_signature(self, node):
        self.depart_term(node)

    def visit_desc_addname(self, node):
        pass
    def depart_desc_addname(self, node):
        pass

    def visit_desc_type(self, node):
        pass
    def depart_desc_type(self, node):
        pass

    def visit_desc_returns(self, node):
        self.body.append(' -> ')
    def depart_desc_returns(self, node):
        pass

    def visit_desc_name(self, node):
        pass
    def depart_desc_name(self, node):
        pass

    def visit_desc_parameterlist(self, node):
        self.body.append('(')
        self.first_param = 1
    def depart_desc_parameterlist(self, node):
        self.body.append(')')

    def visit_desc_parameter(self, node):
        if not self.first_param:
            self.body.append(', ')
        else:
            self.first_param = 0
    def depart_desc_parameter(self, node):
        pass

    def visit_desc_optional(self, node):
        self.body.append('[')
    def depart_desc_optional(self, node):
        self.body.append(']')

    def visit_desc_annotation(self, node):
        pass
    def depart_desc_annotation(self, node):
        pass

    def visit_desc_content(self, node):
        self.visit_definition(node)
    def depart_desc_content(self, node):
        self.depart_definition(node)

    def visit_refcount(self, node):
        self.body.append(self.defs['emphasis'][0])
    def depart_refcount(self, node):
        self.body.append(self.defs['emphasis'][1])

    def visit_versionmodified(self, node):
        self.visit_paragraph(node)
        text = versionlabels[node['type']] % node['version']
        if len(node):
            text += ': '
        else:
            text += '.'
        self.body.append(text)
    def depart_versionmodified(self, node):
        self.depart_paragraph(node)

    def visit_termsep(self, node):
        self.body.append(', ')
        raise nodes.SkipNode

    # overwritten -- we don't want source comments to show up
    def visit_comment(self, node):
        raise nodes.SkipNode

    # overwritten -- added ensure_eol()
    def visit_footnote(self, node):
        self.ensure_eol()
        BaseTranslator.visit_footnote(self, node)

    # overwritten -- handle footnotes rubric
    def visit_rubric(self, node):
        self.ensure_eol()
        if len(node.children) == 1:
            rubtitle = node.children[0].astext()
            if rubtitle in ('Footnotes', _('Footnotes')):
                self.body.append('.SH ' + self.deunicode(rubtitle).upper() +
                                 '\n')
                raise nodes.SkipNode
        else:
            self.body.append('.sp\n')
    def depart_rubric(self, node):
        pass

    def visit_seealso(self, node):
        self.visit_admonition(node)
    def depart_seealso(self, node):
        self.depart_admonition(node)

    # overwritten -- use our own label translations
    def visit_admonition(self, node, name=None):
        if name:
            self.body.append('.IP %s\n' %
                             self.deunicode(admonitionlabels.get(name, name)))

    def visit_productionlist(self, node):
        self.ensure_eol()
        names = []
        self.in_productionlist += 1
        self.body.append('.sp\n.nf\n')
        for production in node:
            names.append(production['tokenname'])
        maxlen = max(len(name) for name in names)
        for production in node:
            if production['tokenname']:
                lastname = production['tokenname'].ljust(maxlen)
                self.body.append(self.defs['strong'][0])
                self.body.append(self.deunicode(lastname))
                self.body.append(self.defs['strong'][1])
                self.body.append(' ::= ')
            else:
                self.body.append('%s     ' % (' '*len(lastname)))
            production.walkabout(self)
            self.body.append('\n')
        self.body.append('\n.fi\n')
        self.in_productionlist -= 1
        raise nodes.SkipNode

    def visit_production(self, node):
        pass
    def depart_production(self, node):
        pass

    # overwritten -- don't emit a warning for images
    def visit_image(self, node):
        if 'alt' in node.attributes:
            self.body.append(_('[image: %s]') % node['alt'] + '\n')
        self.body.append(_('[image]') + '\n')
        raise nodes.SkipNode

    # overwritten -- don't visit inner marked up nodes
    def visit_reference(self, node):
        self.body.append(self.defs['reference'][0])
        self.body.append(node.astext())
        self.body.append(self.defs['reference'][1])

        uri = node.get('refuri', '')
        if uri.startswith('mailto:') or uri.startswith('http:') or \
                 uri.startswith('https:') or uri.startswith('ftp:'):
            # if configured, put the URL after the link
            if self.builder.config.man_show_urls and \
                   node.astext() != uri:
                if uri.startswith('mailto:'):
                    uri = uri[7:]
                self.body.extend([
                    ' <',
                    self.defs['strong'][0], uri, self.defs['strong'][1],
                    '>'])
        raise nodes.SkipNode

    def visit_centered(self, node):
        self.ensure_eol()
        self.body.append('.sp\n.ce\n')
    def depart_centered(self, node):
        self.body.append('\n.ce 0\n')

    def visit_compact_paragraph(self, node):
        pass
    def depart_compact_paragraph(self, node):
        pass

    def visit_highlightlang(self, node):
        pass
    def depart_highlightlang(self, node):
        pass

    def visit_download_reference(self, node):
        pass
    def depart_download_reference(self, node):
        pass

    def visit_toctree(self, node):
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
        self.ensure_eol()
        self.body.append(', '.join(n.astext()
                                   for n in node.children[0].children) + '.')
        self.body.append('\n')
        raise nodes.SkipNode

    def visit_hlist(self, node):
        self.visit_bullet_list(node)
    def depart_hlist(self, node):
        self.depart_bullet_list(node)

    def visit_hlistcol(self, node):
        pass
    def depart_hlistcol(self, node):
        pass

    def visit_literal_emphasis(self, node):
        return self.visit_emphasis(node)
    def depart_literal_emphasis(self, node):
        return self.depart_emphasis(node)

    def visit_abbreviation(self, node):
        pass
    def depart_abbreviation(self, node):
        pass

    # overwritten: handle section titles better than in 0.6 release
    def visit_title(self, node):
        if isinstance(node.parent, addnodes.seealso):
            self.body.append('.IP "')
            return
        elif isinstance(node.parent, nodes.section):
            if self.section_level == 0:
                # skip the document title
                raise nodes.SkipNode
            elif self.section_level == 1:
                self.body.append('.SH %s\n' %
                                 self.deunicode(node.astext().upper()))
                raise nodes.SkipNode
        return BaseTranslator.visit_title(self, node)
    def depart_title(self, node):
        if isinstance(node.parent, addnodes.seealso):
            self.body.append('"\n')
            return
        return BaseTranslator.depart_title(self, node)

    def visit_raw(self, node):
        if 'manpage' in node.get('format', '').split():
            self.body.append(node.astext())
        raise nodes.SkipNode

    def unknown_visit(self, node):
        raise NotImplementedError('Unknown node: ' + node.__class__.__name__)
