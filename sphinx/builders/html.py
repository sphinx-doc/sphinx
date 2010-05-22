# -*- coding: utf-8 -*-
"""
    sphinx.builders.html
    ~~~~~~~~~~~~~~~~~~~~

    Several HTML builders.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import sys
import codecs
import posixpath
import cPickle as pickle
from os import path
try:
    from hashlib import md5
except ImportError:
    # 2.4 compatibility
    from md5 import md5

from docutils import nodes
from docutils.io import DocTreeInput, StringOutput
from docutils.core import publish_parts
from docutils.utils import new_document
from docutils.frontend import OptionParser
from docutils.readers.doctree import Reader as DoctreeReader

from sphinx import package_dir, __version__
from sphinx.util import SEP, os_path, relative_uri, ensuredir, \
    movefile, ustrftime, copy_static_entry, copyfile
from sphinx.errors import SphinxError
from sphinx.search import js_index
from sphinx.theming import Theme
from sphinx.builders import Builder, ENV_PICKLE_FILENAME
from sphinx.highlighting import PygmentsBridge
from sphinx.util.console import bold
from sphinx.writers.html import HTMLWriter, HTMLTranslator, \
     SmartyPantsHTMLTranslator

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        json = None

#: the filename for the inventory of objects
INVENTORY_FILENAME = 'objects.inv'
#: the filename for the "last build" file (for serializing builders)
LAST_BUILD_FILENAME = 'last_build'


class StandaloneHTMLBuilder(Builder):
    """
    Builds standalone HTML docs.
    """
    name = 'html'
    format = 'html'
    copysource = True
    out_suffix = '.html'
    link_suffix = '.html'  # defaults to matching out_suffix
    indexer_format = js_index
    supported_image_types = ['image/svg+xml', 'image/png',
                             'image/gif', 'image/jpeg']
    searchindex_filename = 'searchindex.js'
    add_permalinks = True
    embedded = False  # for things like HTML help or Qt help: suppresses sidebar

    # This is a class attribute because it is mutated by Sphinx.add_javascript.
    script_files = ['_static/jquery.js', '_static/doctools.js']

    def init(self):
        # a hash of all config values that, if changed, cause a full rebuild
        self.config_hash = ''
        self.tags_hash = ''
        # section numbers for headings in the currently visited document
        self.secnumbers = {}

        self.init_templates()
        self.init_highlighter()
        self.init_translator_class()
        if self.config.html_file_suffix:
            self.out_suffix = self.config.html_file_suffix

        if self.config.html_link_suffix is not None:
            self.link_suffix = self.config.html_link_suffix
        else:
            self.link_suffix = self.out_suffix

        if self.config.language is not None:
            jsfile_list = [path.join(package_dir, 'locale',
                self.config.language, 'LC_MESSAGES', 'sphinx.js'),
                path.join(sys.prefix, 'share/sphinx/locale',
                    self.config.language, 'sphinx.js')]

            for jsfile in jsfile_list:
                if path.isfile(jsfile):
                    self.script_files.append('_static/translations.js')
                    break

    def init_templates(self):
        Theme.init_themes(self)
        self.theme = Theme(self.config.html_theme)
        self.create_template_bridge()
        self.templates.init(self, self.theme)

    def init_highlighter(self):
        # determine Pygments style and create the highlighter
        if self.config.pygments_style is not None:
            style = self.config.pygments_style
        elif self.theme:
            style = self.theme.get_confstr('theme', 'pygments_style', 'none')
        else:
            style = 'sphinx'
        self.highlighter = PygmentsBridge('html', style)

    def init_translator_class(self):
        if self.config.html_translator_class:
            self.translator_class = self.app.import_object(
                self.config.html_translator_class,
                'html_translator_class setting')
        elif self.config.html_use_smartypants:
            self.translator_class = SmartyPantsHTMLTranslator
        else:
            self.translator_class = HTMLTranslator

    def get_outdated_docs(self):
        cfgdict = dict((name, self.config[name])
                       for (name, desc) in self.config.values.iteritems()
                       if desc[1] == 'html')
        self.config_hash = md5(str(cfgdict)).hexdigest()
        self.tags_hash = md5(str(sorted(self.tags))).hexdigest()
        old_config_hash = old_tags_hash = ''
        try:
            fp = open(path.join(self.outdir, '.buildinfo'))
            version = fp.readline()
            if version.rstrip() != '# Sphinx build info version 1':
                raise ValueError
            fp.readline()  # skip commentary
            cfg, old_config_hash = fp.readline().strip().split(': ')
            if cfg != 'config':
                raise ValueError
            tag, old_tags_hash = fp.readline().strip().split(': ')
            if tag != 'tags':
                raise ValueError
            fp.close()
        except ValueError:
            self.warn('unsupported build info format in %r, building all' %
                      path.join(self.outdir, '.buildinfo'))
        except Exception:
            pass
        if old_config_hash != self.config_hash or \
               old_tags_hash != self.tags_hash:
            for docname in self.env.found_docs:
                yield docname
            return

        if self.templates:
            template_mtime = self.templates.newest_template_mtime()
        else:
            template_mtime = 0
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = self.get_outfilename(docname)
            try:
                targetmtime = path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = max(path.getmtime(self.env.doc2path(docname)),
                               template_mtime)
                if srcmtime > targetmtime:
                    yield docname
            except EnvironmentError:
                # source doesn't exist anymore
                pass

    def render_partial(self, node):
        """Utility: Render a lone doctree node."""
        if node is None:
            return {'fragment': ''}
        doc = new_document('<partial node>')
        doc.append(node)
        return publish_parts(
            doc,
            source_class=DocTreeInput,
            reader=DoctreeReader(),
            writer=HTMLWriter(self),
            settings_overrides={'output_encoding': 'unicode'}
        )

    def prepare_writing(self, docnames):
        from sphinx.search import IndexBuilder

        self.indexer = IndexBuilder(self.env)
        self.load_indexer(docnames)
        self.docwriter = HTMLWriter(self)
        self.docsettings = OptionParser(
            defaults=self.env.settings,
            components=(self.docwriter,)).get_default_values()

        # format the "last updated on" string, only once is enough since it
        # typically doesn't include the time of day
        lufmt = self.config.html_last_updated_fmt
        if lufmt is not None:
            self.last_updated = ustrftime(lufmt or _('%b %d, %Y'))
        else:
            self.last_updated = None

        logo = self.config.html_logo and \
               path.basename(self.config.html_logo) or ''

        favicon = self.config.html_favicon and \
                  path.basename(self.config.html_favicon) or ''
        if favicon and os.path.splitext(favicon)[1] != '.ico':
            self.warn('html_favicon is not an .ico file')

        if not isinstance(self.config.html_use_opensearch, basestring):
            self.warn('html_use_opensearch config value must now be a string')

        self.relations = self.env.collect_relations()

        rellinks = []
        if self.config.html_use_index:
            rellinks.append(('genindex', _('General Index'), 'I', _('index')))
        if self.config.html_use_modindex and self.env.modules:
            rellinks.append(('modindex', _('Global Module Index'),
                             'M', _('modules')))

        if self.config.html_style is not None:
            stylename = self.config.html_style
        elif self.theme:
            stylename = self.theme.get_confstr('theme', 'stylesheet')
        else:
            stylename = 'default.css'

        self.globalcontext = dict(
            embedded = self.embedded,
            project = self.config.project,
            release = self.config.release,
            version = self.config.version,
            last_updated = self.last_updated,
            copyright = self.config.copyright,
            master_doc = self.config.master_doc,
            use_opensearch = self.config.html_use_opensearch,
            docstitle = self.config.html_title,
            shorttitle = self.config.html_short_title,
            show_sphinx = self.config.html_show_sphinx,
            has_source = self.config.html_copy_source,
            show_source = self.config.html_show_sourcelink,
            file_suffix = self.out_suffix,
            script_files = self.script_files,
            sphinx_version = __version__,
            style = stylename,
            rellinks = rellinks,
            builder = self.name,
            parents = [],
            logo = logo,
            favicon = favicon,
        )
        if self.theme:
            self.globalcontext.update(
                ('theme_' + key, val) for (key, val) in
                self.theme.get_options(
                self.config.html_theme_options).iteritems())
        self.globalcontext.update(self.config.html_context)

    def get_doc_context(self, docname, body, metatags):
        """Collect items for the template context of a page."""
        # find out relations
        prev = next = None
        parents = []
        rellinks = self.globalcontext['rellinks'][:]
        related = self.relations.get(docname)
        titles = self.env.titles
        if related and related[2]:
            try:
                next = {
                    'link': self.get_relative_uri(docname, related[2]),
                    'title': self.render_partial(titles[related[2]])['title']
                }
                rellinks.append((related[2], next['title'], 'N', _('next')))
            except KeyError:
                next = None
        if related and related[1]:
            try:
                prev = {
                    'link': self.get_relative_uri(docname, related[1]),
                    'title': self.render_partial(titles[related[1]])['title']
                }
                rellinks.append((related[1], prev['title'], 'P', _('previous')))
            except KeyError:
                # the relation is (somehow) not in the TOC tree, handle
                # that gracefully
                prev = None
        while related and related[0]:
            try:
                parents.append(
                    {'link': self.get_relative_uri(docname, related[0]),
                     'title': self.render_partial(titles[related[0]])['title']})
            except KeyError:
                pass
            related = self.relations.get(related[0])
        if parents:
            parents.pop() # remove link to the master file; we have a generic
                          # "back to index" link already
        parents.reverse()

        # title rendered as HTML
        title = self.env.longtitles.get(docname)
        title = title and self.render_partial(title)['title'] or ''
        # the name for the copied source
        sourcename = self.config.html_copy_source and docname + '.txt' or ''

        # metadata for the document
        meta = self.env.metadata.get(docname)

        # local TOC and global TOC tree
        toc = self.render_partial(self.env.get_toc_for(docname))['fragment']

        return dict(
            parents = parents,
            prev = prev,
            next = next,
            title = title,
            meta = meta,
            body = body,
            metatags = metatags,
            rellinks = rellinks,
            sourcename = sourcename,
            toc = toc,
            # only display a TOC if there's more than one item to show
            display_toc = (self.env.toc_num_entries[docname] > 1),
        )

    def write_doc(self, docname, doctree):
        destination = StringOutput(encoding='utf-8')
        doctree.settings = self.docsettings

        self.secnumbers = self.env.toc_secnumbers.get(docname, {})
        self.imgpath = relative_uri(self.get_target_uri(docname), '_images')
        self.post_process_images(doctree)
        self.dlpath = relative_uri(self.get_target_uri(docname), '_downloads')
        self.docwriter.write(doctree, destination)
        self.docwriter.assemble_parts()
        body = self.docwriter.parts['fragment']
        metatags = self.docwriter.clean_meta

        ctx = self.get_doc_context(docname, body, metatags)
        self.index_page(docname, doctree, ctx.get('title', ''))
        self.handle_page(docname, ctx, event_arg=doctree)

    def finish(self):
        self.info(bold('writing additional files...'), nonl=1)

        # the global general index

        if self.config.html_use_index:
            # the total count of lines for each index letter, used to distribute
            # the entries into two columns
            genindex = self.env.create_index(self)
            indexcounts = []
            for _, entries in genindex:
                indexcounts.append(sum(1 + len(subitems)
                                       for _, (_, subitems) in entries))

            genindexcontext = dict(
                genindexentries = genindex,
                genindexcounts = indexcounts,
                split_index = self.config.html_split_index,
            )
            self.info(' genindex', nonl=1)

            if self.config.html_split_index:
                self.handle_page('genindex', genindexcontext,
                                 'genindex-split.html')
                self.handle_page('genindex-all', genindexcontext,
                                 'genindex.html')
                for (key, entries), count in zip(genindex, indexcounts):
                    ctx = {'key': key, 'entries': entries, 'count': count,
                           'genindexentries': genindex}
                    self.handle_page('genindex-' + key, ctx,
                                     'genindex-single.html')
            else:
                self.handle_page('genindex', genindexcontext, 'genindex.html')

        # the global module index

        if self.config.html_use_modindex and self.env.modules:
            # the sorted list of all modules, for the global module index
            modules = sorted(((mn, (self.get_relative_uri('modindex', fn) +
                                    '#module-' + mn, sy, pl, dep))
                              for (mn, (fn, sy, pl, dep)) in
                              self.env.modules.iteritems()),
                             key=lambda x: x[0].lower())
            # collect all platforms
            platforms = set()
            # sort out collapsable modules
            modindexentries = []
            letters = []
            pmn = ''
            num_toplevels = 0
            num_collapsables = 0
            cg = 0 # collapse group
            fl = '' # first letter
            for mn, (fn, sy, pl, dep) in modules:
                pl = pl and pl.split(', ') or []
                platforms.update(pl)

                ignore = self.env.config['modindex_common_prefix']
                ignore = sorted(ignore, key=len, reverse=True)
                for i in ignore:
                    if mn.startswith(i):
                        mn = mn[len(i):]
                        stripped = i
                        break
                else:
                    stripped = ''

                # we stripped the whole module name
                if not mn:
                    continue

                if fl != mn[0].lower() and mn[0] != '_':
                    # heading
                    letter = mn[0].upper()
                    if letter not in letters:
                        modindexentries.append(['', False, 0, False,
                                                letter, '', [], False, ''])
                        letters.append(letter)
                tn = mn.split('.')[0]
                if tn != mn:
                    # submodule
                    if pmn == tn:
                        # first submodule - make parent collapsable
                        modindexentries[-1][1] = True
                        num_collapsables += 1
                    elif not pmn.startswith(tn):
                        # submodule without parent in list, add dummy entry
                        cg += 1
                        modindexentries.append([tn, True, cg, False, '', '',
                                                [], False, stripped])
                else:
                    num_toplevels += 1
                    cg += 1
                modindexentries.append([mn, False, cg, (tn != mn), fn, sy, pl,
                                        dep, stripped])
                pmn = mn
                fl = mn[0].lower()
            platforms = sorted(platforms)

            # apply heuristics when to collapse modindex at page load:
            # only collapse if number of toplevel modules is larger than
            # number of submodules
            collapse = len(modules) - num_toplevels < num_toplevels

            # As some parts of the module names may have been stripped, those
            # names have changed, thus it is necessary to sort the entries.
            if ignore:
                def sorthelper(entry):
                    name = entry[0]
                    if name == '':
                        # heading
                        name = entry[4]
                    return name.lower()

                modindexentries.sort(key=sorthelper)
                letters.sort()

            modindexcontext = dict(
                modindexentries = modindexentries,
                platforms = platforms,
                letters = letters,
                collapse_modindex = collapse,
            )
            self.info(' modindex', nonl=1)
            self.handle_page('modindex', modindexcontext, 'modindex.html')

        # the search page
        if self.name != 'htmlhelp':
            self.info(' search', nonl=1)
            self.handle_page('search', {}, 'search.html')

        # additional pages from conf.py
        for pagename, template in self.config.html_additional_pages.items():
            self.info(' '+pagename, nonl=1)
            self.handle_page(pagename, {}, template)

        if self.config.html_use_opensearch and self.name != 'htmlhelp':
            self.info(' opensearch', nonl=1)
            fn = path.join(self.outdir, '_static', 'opensearch.xml')
            self.handle_page('opensearch', {}, 'opensearch.xml', outfilename=fn)

        self.info()

        # copy image files
        if self.images:
            self.info(bold('copying images...'), nonl=True)
            ensuredir(path.join(self.outdir, '_images'))
            for src, dest in self.images.iteritems():
                self.info(' '+src, nonl=1)
                try:
                    copyfile(path.join(self.srcdir, src),
                             path.join(self.outdir, '_images', dest))
                except Exception, err:
                    self.warn('cannot copy image file %r: %s' %
                              (path.join(self.srcdir, src), err))
            self.info()

        # copy downloadable files
        if self.env.dlfiles:
            self.info(bold('copying downloadable files...'), nonl=True)
            ensuredir(path.join(self.outdir, '_downloads'))
            for src, (_, dest) in self.env.dlfiles.iteritems():
                self.info(' '+src, nonl=1)
                try:
                    copyfile(path.join(self.srcdir, src),
                             path.join(self.outdir, '_downloads', dest))
                except Exception, err:
                    self.warn('cannot copy downloadable file %r: %s' %
                              (path.join(self.srcdir, src), err))
            self.info()

        # copy static files
        self.info(bold('copying static files... '), nonl=True)
        ensuredir(path.join(self.outdir, '_static'))
        # first, create pygments style file
        f = open(path.join(self.outdir, '_static', 'pygments.css'), 'w')
        f.write(self.highlighter.get_stylesheet())
        f.close()
        # then, copy translations JavaScript file
        if self.config.language is not None:
            jsfile_list = [path.join(package_dir, 'locale',
                self.config.language, 'LC_MESSAGES', 'sphinx.js'),
                path.join(sys.prefix, 'share/sphinx/locale',
                    self.config.language, 'sphinx.js')]
            for jsfile in jsfile_list:
                if path.isfile(jsfile):
                    copyfile(jsfile, path.join(self.outdir, '_static',
                                               'translations.js'))
                    break
        # then, copy over all user-supplied static files
        if self.theme:
            staticdirnames = [path.join(themepath, 'static')
                              for themepath in self.theme.get_dirchain()[::-1]]
        else:
            staticdirnames = []
        staticdirnames += [path.join(self.confdir, spath)
                           for spath in self.config.html_static_path]
        for staticdirname in staticdirnames:
            if not path.isdir(staticdirname):
                self.warn('static directory %r does not exist' % staticdirname)
                continue
            for filename in os.listdir(staticdirname):
                if filename.startswith('.'):
                    continue
                fullname = path.join(staticdirname, filename)
                targetname = path.join(self.outdir, '_static', filename)
                copy_static_entry(fullname, targetname, self,
                                  self.globalcontext)
        # last, copy logo file (handled differently)
        if self.config.html_logo:
            logobase = path.basename(self.config.html_logo)
            copyfile(path.join(self.confdir, self.config.html_logo),
                     path.join(self.outdir, '_static', logobase))

        # write build info file
        fp = open(path.join(self.outdir, '.buildinfo'), 'w')
        try:
            fp.write('# Sphinx build info version 1\n'
                     '# This file hashes the configuration used when building'
                     ' these files. When it is not found, a full rebuild will'
                     ' be done.\nconfig: %s\ntags: %s\n' %
                     (self.config_hash, self.tags_hash))
        finally:
            fp.close()

        self.info('done')

        # dump the search index
        self.handle_finish()

    def cleanup(self):
        # clean up theme stuff
        if self.theme:
            self.theme.cleanup()

    def post_process_images(self, doctree):
        """
        Pick the best candidate for an image and link down-scaled images to
        their high res version.
        """
        Builder.post_process_images(self, doctree)
        for node in doctree.traverse(nodes.image):
            if not node.has_key('scale') or \
               isinstance(node.parent, nodes.reference):
                # docutils does unfortunately not preserve the
                # ``target`` attribute on images, so we need to check
                # the parent node here.
                continue
            uri = node['uri']
            reference = nodes.reference()
            if uri in self.images:
                reference['refuri'] = posixpath.join(self.imgpath,
                                                     self.images[uri])
            else:
                reference['refuri'] = uri
            node.replace_self(reference)
            reference.append(node)

    def load_indexer(self, docnames):
        keep = set(self.env.all_docs) - set(docnames)
        try:
            f = open(path.join(self.outdir, self.searchindex_filename), 'rb')
            try:
                self.indexer.load(f, self.indexer_format)
            finally:
                f.close()
        except (IOError, OSError, ValueError):
            if keep:
                self.warn('search index couldn\'t be loaded, but not all '
                          'documents will be built: the index will be '
                          'incomplete.')
        # delete all entries for files that will be rebuilt
        self.indexer.prune(keep)

    def index_page(self, pagename, doctree, title):
        # only index pages with title
        if self.indexer is not None and title:
            self.indexer.feed(pagename, title, doctree)

    def _get_local_toctree(self, docname, collapse=True):
        return self.render_partial(self.env.get_toctree_for(
            docname, self, collapse))['fragment']

    def get_outfilename(self, pagename):
        return path.join(self.outdir, os_path(pagename) + self.out_suffix)

    # --------- these are overwritten by the serialization builder

    def get_target_uri(self, docname, typ=None):
        return docname + self.link_suffix

    def handle_page(self, pagename, addctx, templatename='page.html',
                    outfilename=None, event_arg=None):
        ctx = self.globalcontext.copy()
        # current_page_name is backwards compatibility
        ctx['pagename'] = ctx['current_page_name'] = pagename

        def pathto(otheruri, resource=False,
                   baseuri=self.get_target_uri(pagename)):
            if not resource:
                otheruri = self.get_target_uri(otheruri)
            uri = relative_uri(baseuri, otheruri) or '#'
            return uri
        ctx['pathto'] = pathto
        ctx['hasdoc'] = lambda name: name in self.env.all_docs
        ctx['customsidebar'] = self.config.html_sidebars.get(pagename)
        ctx['toctree'] = lambda **kw: self._get_local_toctree(pagename, **kw)
        ctx.update(addctx)

        self.app.emit('html-page-context', pagename, templatename,
                      ctx, event_arg)

        try:
            output = self.templates.render(templatename, ctx)
        except UnicodeError:
            self.warn("a Unicode error occurred when rendering the page %s. "
                      "Please make sure all config values that contain "
                      "non-ASCII content are Unicode strings." % pagename)
            return

        if not outfilename:
            outfilename = self.get_outfilename(pagename)
        # outfilename's path is in general different from self.outdir
        ensuredir(path.dirname(outfilename))
        try:
            f = codecs.open(outfilename, 'w', 'utf-8')
            try:
                f.write(output)
            finally:
                f.close()
        except (IOError, OSError), err:
            self.warn("error writing file %s: %s" % (outfilename, err))
        if self.copysource and ctx.get('sourcename'):
            # copy the source file for the "show source" link
            source_name = path.join(self.outdir, '_sources',
                                    os_path(ctx['sourcename']))
            ensuredir(path.dirname(source_name))
            copyfile(self.env.doc2path(pagename), source_name)

    def handle_finish(self):
        self.info(bold('dumping search index... '), nonl=True)
        self.indexer.prune(self.env.all_docs)
        searchindexfn = path.join(self.outdir, self.searchindex_filename)
        # first write to a temporary file, so that if dumping fails,
        # the existing index won't be overwritten
        f = open(searchindexfn + '.tmp', 'wb')
        try:
            self.indexer.dump(f, self.indexer_format)
        finally:
            f.close()
        movefile(searchindexfn + '.tmp', searchindexfn)
        self.info('done')

        self.info(bold('dumping object inventory... '), nonl=True)
        f = open(path.join(self.outdir, INVENTORY_FILENAME), 'w')
        try:
            f.write('# Sphinx inventory version 1\n')
            f.write('# Project: %s\n' % self.config.project.encode('utf-8'))
            f.write('# Version: %s\n' % self.config.version)
            for modname, info in self.env.modules.iteritems():
                f.write('%s mod %s\n' % (modname, self.get_target_uri(info[0])))
            for refname, (docname, desctype) in self.env.descrefs.iteritems():
                f.write('%s %s %s\n' % (refname, desctype,
                                        self.get_target_uri(docname)))
        finally:
            f.close()
        self.info('done')


class DirectoryHTMLBuilder(StandaloneHTMLBuilder):
    """
    A StandaloneHTMLBuilder that creates all HTML pages as "index.html" in
    a directory given by their pagename, so that generated URLs don't have
    ``.html`` in them.
    """
    name = 'dirhtml'

    def get_target_uri(self, docname, typ=None):
        if docname == 'index':
            return ''
        if docname.endswith(SEP + 'index'):
            return docname[:-5] # up to sep
        return docname + SEP

    def get_outfilename(self, pagename):
        if pagename == 'index' or pagename.endswith(SEP + 'index'):
            outfilename = path.join(self.outdir, os_path(pagename)
                                    + self.out_suffix)
        else:
            outfilename = path.join(self.outdir, os_path(pagename),
                                    'index' + self.out_suffix)

        return outfilename


class SerializingHTMLBuilder(StandaloneHTMLBuilder):
    """
    An abstract builder that serializes the generated HTML.
    """
    #: the serializing implementation to use.  Set this to a module that
    #: implements a `dump`, `load`, `dumps` and `loads` functions
    #: (pickle, simplejson etc.)
    implementation = None

    #: the filename for the global context file
    globalcontext_filename = None

    supported_image_types = ['image/svg+xml', 'image/png',
                             'image/gif', 'image/jpeg']

    def init(self):
        self.config_hash = ''
        self.tags_hash = ''
        self.theme = None       # no theme necessary
        self.templates = None   # no template bridge necessary
        self.init_translator_class()
        self.init_highlighter()

    def get_target_uri(self, docname, typ=None):
        if docname == 'index':
            return ''
        if docname.endswith(SEP + 'index'):
            return docname[:-5] # up to sep
        return docname + SEP

    def handle_page(self, pagename, ctx, templatename='page.html',
                    outfilename=None, event_arg=None):
        ctx['current_page_name'] = pagename
        sidebarfile = self.config.html_sidebars.get(pagename)
        if sidebarfile:
            ctx['customsidebar'] = sidebarfile

        if not outfilename:
            outfilename = path.join(self.outdir,
                                    os_path(pagename) + self.out_suffix)

        self.app.emit('html-page-context', pagename, templatename,
                      ctx, event_arg)

        ensuredir(path.dirname(outfilename))
        f = open(outfilename, 'wb')
        try:
            self.implementation.dump(ctx, f, 2)
        finally:
            f.close()

        # if there is a source file, copy the source file for the
        # "show source" link
        if ctx.get('sourcename'):
            source_name = path.join(self.outdir, '_sources',
                                    os_path(ctx['sourcename']))
            ensuredir(path.dirname(source_name))
            copyfile(self.env.doc2path(pagename), source_name)

    def handle_finish(self):
        # dump the global context
        outfilename = path.join(self.outdir, self.globalcontext_filename)
        f = open(outfilename, 'wb')
        try:
            self.implementation.dump(self.globalcontext, f, 2)
        finally:
            f.close()

        # super here to dump the search index
        StandaloneHTMLBuilder.handle_finish(self)

        # copy the environment file from the doctree dir to the output dir
        # as needed by the web app
        copyfile(path.join(self.doctreedir, ENV_PICKLE_FILENAME),
                 path.join(self.outdir, ENV_PICKLE_FILENAME))

        # touch 'last build' file, used by the web application to determine
        # when to reload its environment and clear the cache
        open(path.join(self.outdir, LAST_BUILD_FILENAME), 'w').close()


class PickleHTMLBuilder(SerializingHTMLBuilder):
    """
    A Builder that dumps the generated HTML into pickle files.
    """
    implementation = pickle
    indexer_format = pickle
    name = 'pickle'
    out_suffix = '.fpickle'
    globalcontext_filename = 'globalcontext.pickle'
    searchindex_filename = 'searchindex.pickle'

# compatibility alias
WebHTMLBuilder = PickleHTMLBuilder


class JSONHTMLBuilder(SerializingHTMLBuilder):
    """
    A builder that dumps the generated HTML into JSON files.
    """
    implementation = json
    indexer_format = json
    name = 'json'
    out_suffix = '.fjson'
    globalcontext_filename = 'globalcontext.json'
    searchindex_filename = 'searchindex.json'

    def init(self):
        if json is None:
            raise SphinxError(
                'The module simplejson (or json in Python >= 2.6) '
                'is not available. The JSONHTMLBuilder builder will not work.')
        SerializingHTMLBuilder.init(self)
