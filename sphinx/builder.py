# -*- coding: utf-8 -*-
"""
    sphinx.builder
    ~~~~~~~~~~~~~~

    Builder classes for different output formats.

    :copyright: 2007-2008 by Georg Brandl, Sebastian Wiesner.
    :license: BSD.
"""

import os
import time
import codecs
import shutil
import cPickle as pickle
from os import path
from cgi import escape

from docutils import nodes
from docutils.io import StringOutput, FileOutput, DocTreeInput
from docutils.core import publish_parts
from docutils.utils import new_document
from docutils.frontend import OptionParser
from docutils.readers.doctree import Reader as DoctreeReader

from sphinx import addnodes, __version__
from sphinx.util import ensuredir, relative_uri, SEP, os_path, json
from sphinx.htmlhelp import build_hhx
from sphinx.htmlwriter import HTMLWriter, HTMLTranslator, SmartyPantsHTMLTranslator
from sphinx.textwriter import TextWriter
from sphinx.latexwriter import LaTeXWriter
from sphinx.environment import BuildEnvironment, NoUri
from sphinx.highlighting import PygmentsBridge
from sphinx.util.console import bold, purple, darkgreen

# side effect: registers roles and directives
from sphinx import roles
from sphinx import directives

ENV_PICKLE_FILENAME = 'environment.pickle'
LAST_BUILD_FILENAME = 'last_build'
INVENTORY_FILENAME = 'inventory.txt'


class Builder(object):
    """
    Builds target formats from the reST sources.
    """

    # builder's name, for the -b command line options
    name = ''

    def __init__(self, app, env=None, freshenv=False):
        self.srcdir = app.srcdir
        self.confdir = app.confdir
        self.outdir = app.outdir
        self.doctreedir = app.doctreedir
        if not path.isdir(self.doctreedir):
            os.mkdir(self.doctreedir)

        self.app = app
        self.warn = app.warn
        self.info = app.info
        self.config = app.config

        # images that need to be copied over (source -> dest)
        self.images = {}

        # if None, this is set in load_env()
        self.env = env
        self.freshenv = freshenv

        self.init()
        self.load_env()

    # helper methods

    def init(self):
        """Load necessary templates and perform initialization."""
        raise NotImplementedError

    def init_templates(self):
        # Call this from init() if you need templates.
        if self.config.template_bridge:
            self.templates = self.app.import_object(
                self.config.template_bridge, 'template_bridge setting')()
        else:
            from sphinx._jinja import BuiltinTemplates
            self.templates = BuiltinTemplates()
        self.templates.init(self)

    def get_target_uri(self, docname, typ=None):
        """
        Return the target URI for a document name (typ can be used to qualify
        the link characteristic for individual builders).
        """
        raise NotImplementedError

    def get_relative_uri(self, from_, to, typ=None):
        """
        Return a relative URI between two source filenames. May raise environment.NoUri
        if there's no way to return a sensible URI.
        """
        return relative_uri(self.get_target_uri(from_),
                            self.get_target_uri(to, typ))

    def get_outdated_docs(self):
        """
        Return an iterable of output files that are outdated, or a string describing
        what an update build will build.
        """
        raise NotImplementedError

    def status_iterator(self, iterable, summary, colorfunc=darkgreen):
        l = -1
        for item in iterable:
            if l == -1:
                self.info(bold(summary), nonl=1)
                l = 0
            self.info(colorfunc(item) + ' ', nonl=1)
            yield item
        if l == 0:
            self.info()

    supported_image_types = []

    def post_process_images(self, doctree):
        """
        Pick the best candidate for all image URIs.
        """
        for node in doctree.traverse(nodes.image):
            if '?' in node['candidates']:
                # don't rewrite nonlocal image URIs
                continue
            if '*' not in node['candidates']:
                for imgtype in self.supported_image_types:
                    candidate = node['candidates'].get(imgtype, None)
                    if candidate:
                        break
                else:
                    self.warn('%s:%s: no matching candidate for image URI %r' %
                              (node.source, getattr(node, 'lineno', ''), node['uri']))
                    continue
                node['uri'] = candidate
            else:
                candidate = node['uri']
            if candidate not in self.env.images:
                # non-existing URI; let it alone
                continue
            self.images[candidate] = self.env.images[candidate][1]

    # build methods

    def load_env(self):
        """Set up the build environment."""
        if self.env:
            return
        if not self.freshenv:
            try:
                self.info(bold('loading pickled environment... '), nonl=True)
                self.env = BuildEnvironment.frompickle(self.config,
                    path.join(self.doctreedir, ENV_PICKLE_FILENAME))
                self.info('done')
            except Exception, err:
                if type(err) is IOError and err.errno == 2:
                    self.info('not found')
                else:
                    self.info('failed: %s' % err)
                self.env = BuildEnvironment(self.srcdir, self.doctreedir, self.config)
                self.env.find_files(self.config)
        else:
            self.env = BuildEnvironment(self.srcdir, self.doctreedir, self.config)
            self.env.find_files(self.config)
        self.env.set_warnfunc(self.warn)

    def build_all(self):
        """Build all source files."""
        self.build(None, summary='all source files', method='all')

    def build_specific(self, filenames):
        """Only rebuild as much as needed for changes in the source_filenames."""
        # bring the filenames to the canonical format, that is,
        # relative to the source directory and without source_suffix.
        dirlen = len(self.srcdir) + 1
        to_write = []
        suffix = self.config.source_suffix
        for filename in filenames:
            filename = path.abspath(filename)[dirlen:]
            if filename.endswith(suffix):
                filename = filename[:-len(suffix)]
            filename = filename.replace(os.path.sep, SEP)
            to_write.append(filename)
        self.build(to_write, method='specific',
                   summary='%d source files given on command '
                   'line' % len(to_write))

    def build_update(self):
        """Only rebuild files changed or added since last build."""
        to_build = self.get_outdated_docs()
        if isinstance(to_build, str):
            self.build(['__all__'], to_build)
        else:
            to_build = list(to_build)
            self.build(to_build,
                       summary='targets for %d source files that are '
                       'out of date' % len(to_build))

    def build(self, docnames, summary=None, method='update'):
        if summary:
            self.info(bold('building [%s]: ' % self.name), nonl=1)
            self.info(summary)

        updated_docnames = []
        # while reading, collect all warnings from docutils
        warnings = []
        self.env.set_warnfunc(warnings.append)
        self.info(bold('updating environment: '), nonl=1)
        iterator = self.env.update(self.config, self.srcdir, self.doctreedir, self.app)
        # the first item in the iterator is a summary message
        self.info(iterator.next())
        for docname in self.status_iterator(iterator, 'reading sources... ', purple):
            updated_docnames.append(docname)
            # nothing further to do, the environment has already done the reading
        for warning in warnings:
            if warning.strip():
                self.warn(warning)
        self.env.set_warnfunc(self.warn)

        if updated_docnames:
            # save the environment
            self.info(bold('pickling environment... '), nonl=True)
            self.env.topickle(path.join(self.doctreedir, ENV_PICKLE_FILENAME))
            self.info('done')

            # global actions
            self.info(bold('checking consistency... '), nonl=True)
            self.env.check_consistency()
            self.info('done')
        else:
            if method == 'update' and not docnames:
                self.info(bold('no targets are out of date.'))
                return

        # another indirection to support methods which don't build files
        # individually
        self.write(docnames, updated_docnames, method)

        # finish (write static files etc.)
        self.finish()
        if self.app._warncount:
            self.info(bold('build succeeded, %s warning%s.' %
                           (self.app._warncount,
                            self.app._warncount != 1 and 's' or '')))
        else:
            self.info(bold('build succeeded.'))

    def write(self, build_docnames, updated_docnames, method='update'):
        if build_docnames is None or build_docnames == ['__all__']:
            # build_all
            build_docnames = self.env.found_docs
        if method == 'update':
            # build updated ones as well
            docnames = set(build_docnames) | set(updated_docnames)
        else:
            docnames = set(build_docnames)

        # add all toctree-containing files that may have changed
        for docname in list(docnames):
            for tocdocname in self.env.files_to_rebuild.get(docname, []):
                docnames.add(tocdocname)
        docnames.add(self.config.master_doc)

        self.info(bold('preparing documents... '), nonl=True)
        self.prepare_writing(docnames)
        self.info('done')

        # write target files
        warnings = []
        self.env.set_warnfunc(warnings.append)
        for docname in self.status_iterator(sorted(docnames),
                                            'writing output... ', darkgreen):
            doctree = self.env.get_and_resolve_doctree(docname, self)
            self.write_doc(docname, doctree)
        for warning in warnings:
            if warning.strip():
                self.warn(warning)
        self.env.set_warnfunc(self.warn)

    def prepare_writing(self, docnames):
        raise NotImplementedError

    def write_doc(self, docname, doctree):
        raise NotImplementedError

    def finish(self):
        raise NotImplementedError


class StandaloneHTMLBuilder(Builder):
    """
    Builds standalone HTML docs.
    """
    name = 'html'
    copysource = True
    out_suffix = '.html'
    indexer_format = json
    supported_image_types = ['image/svg+xml', 'image/png', 'image/gif',
                             'image/jpeg']
    searchindex_filename = 'searchindex.json'
    add_header_links = True
    add_definition_links = True

    def init(self):
        """Load templates."""
        self.init_templates()
        self.init_translator_class()
        if self.config.html_file_suffix:
            self.out_suffix = self.config.html_file_suffix

    def init_translator_class(self):
        if self.config.html_translator_class:
            self.translator_class = self.app.import_object(
                self.config.html_translator_class, 'html_translator_class setting')
        elif self.config.html_use_smartypants:
            self.translator_class = SmartyPantsHTMLTranslator
        else:
            self.translator_class = HTMLTranslator

    def render_partial(self, node):
        """Utility: Render a lone doctree node."""
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

        self.indexer = IndexBuilder()
        self.load_indexer(docnames)
        self.docwriter = HTMLWriter(self)
        self.docsettings = OptionParser(
            defaults=self.env.settings,
            components=(self.docwriter,)).get_default_values()

        # format the "last updated on" string, only once is enough since it
        # typically doesn't include the time of day
        lufmt = self.config.html_last_updated_fmt
        if lufmt:
            self.last_updated = time.strftime(lufmt)
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
            rellinks.append(('genindex', 'General Index', 'I', 'index'))
        if self.config.html_use_modindex:
            rellinks.append(('modindex', 'Global Module Index', 'M', 'modules'))

        self.globalcontext = dict(
            project = self.config.project,
            release = self.config.release,
            version = self.config.version,
            last_updated = self.last_updated,
            copyright = self.config.copyright,
            style = self.config.html_style,
            use_opensearch = self.config.html_use_opensearch,
            docstitle = self.config.html_title,
            shorttitle = self.config.html_short_title,
            show_sphinx = self.config.html_show_sphinx,
            file_suffix = self.out_suffix,
            sphinx_version = __version__,
            rellinks = rellinks,
            builder = self.name,
            parents = [],
            logo = logo,
            favicon = favicon,
        )

    def get_doc_context(self, docname, body):
        """Collect items for the template context of a page."""
        # find out relations
        prev = next = None
        parents = []
        rellinks = self.globalcontext['rellinks'][:]
        related = self.relations.get(docname)
        titles = self.env.titles
        if related and related[2]:
            try:
                next = {'link': self.get_relative_uri(docname, related[2]),
                        'title': self.render_partial(titles[related[2]])['title']}
                rellinks.append((related[2], next['title'], 'N', 'next'))
            except KeyError:
                next = None
        if related and related[1]:
            try:
                prev = {'link': self.get_relative_uri(docname, related[1]),
                        'title': self.render_partial(titles[related[1]])['title']}
                rellinks.append((related[1], prev['title'], 'P', 'previous'))
            except KeyError:
                # the relation is (somehow) not in the TOC tree, handle that gracefully
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
        title = titles.get(docname)
        title = title and self.render_partial(title)['title'] or ''
        # the name for the copied source
        sourcename = self.config.html_copy_source and docname + '.txt' or ''

        # metadata for the document
        meta = self.env.metadata.get(docname)

        return dict(
            parents = parents,
            prev = prev,
            next = next,
            title = title,
            meta = meta,
            body = body,
            rellinks = rellinks,
            sourcename = sourcename,
            toc = self.render_partial(self.env.get_toc_for(docname))['fragment'],
            # only display a TOC if there's more than one item to show
            display_toc = (self.env.toc_num_entries[docname] > 1),
        )

    def write_doc(self, docname, doctree):
        self.post_process_images(doctree)
        destination = StringOutput(encoding='utf-8')
        doctree.settings = self.docsettings

        self.imgpath = relative_uri(self.get_target_uri(docname), '_images')
        self.docwriter.write(doctree, destination)
        self.docwriter.assemble_parts()
        body = self.docwriter.parts['fragment']

        ctx = self.get_doc_context(docname, body)
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
                self.handle_page('genindex', genindexcontext, 'genindex-split.html')
                self.handle_page('genindex-all', genindexcontext, 'genindex.html')
                for (key, entries), count in zip(genindex, indexcounts):
                    ctx = {'key': key, 'entries': entries, 'count': count,
                           'genindexentries': genindex}
                    self.handle_page('genindex-' + key, ctx, 'genindex-single.html')
            else:
                self.handle_page('genindex', genindexcontext, 'genindex.html')

        # the global module index

        if self.config.html_use_modindex:
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
                if fl != mn[0].lower() and mn[0] != '_':
                    # heading
                    modindexentries.append(['', False, 0, False,
                                            mn[0].upper(), '', [], False])
                    letters.append(mn[0].upper())
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
                        modindexentries.append([tn, True, cg, False, '', '', [], False])
                else:
                    num_toplevels += 1
                    cg += 1
                modindexentries.append([mn, False, cg, (tn != mn), fn, sy, pl, dep])
                pmn = mn
                fl = mn[0].lower()
            platforms = sorted(platforms)

            # apply heuristics when to collapse modindex at page load:
            # only collapse if number of toplevel modules is larger than
            # number of submodules
            collapse = len(modules) - num_toplevels < num_toplevels

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
                shutil.copyfile(path.join(self.srcdir, src),
                                path.join(self.outdir, '_images', dest))
            self.info()

        # copy static files
        self.info(bold('copying static files... '), nonl=True)
        ensuredir(path.join(self.outdir, '_static'))
        staticdirnames = [path.join(path.dirname(__file__), 'static')] + \
                         [path.join(self.confdir, spath)
                          for spath in self.config.html_static_path]
        for staticdirname in staticdirnames:
            for filename in os.listdir(staticdirname):
                if filename.startswith('.'):
                    continue
                fullname = path.join(staticdirname, filename)
                targetname = path.join(self.outdir, '_static', filename)
                if path.isfile(fullname):
                    shutil.copyfile(fullname, targetname)
                elif path.isdir(fullname):
                    shutil.rmtree(targetname)
                    shutil.copytree(fullname, targetname)
        # copy logo file (handled differently)
        if self.config.html_logo:
            logobase = path.basename(self.config.html_logo)
            shutil.copyfile(path.join(self.confdir, self.config.html_logo),
                            path.join(self.outdir, '_static', logobase))
        # add pygments style file
        f = open(path.join(self.outdir, '_static', 'pygments.css'), 'w')
        f.write(PygmentsBridge('html', self.config.pygments_style).get_stylesheet())
        f.close()
        self.info('done')

        # dump the search index
        self.handle_finish()

    def get_outdated_docs(self):
        if self.templates:
            template_mtime = self.templates.newest_template_mtime()
        else:
            template_mtime = 0
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = self.env.doc2path(docname, self.outdir, self.out_suffix)
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

    def load_indexer(self, docnames):
        try:
            f = open(path.join(self.outdir, self.searchindex_filename), 'rb')
            try:
                self.indexer.load(f, self.indexer_format)
            finally:
                f.close()
        except (IOError, OSError, NotImplementedError):
            # we catch NotImplementedError here because if no simplejson
            # is installed the searchindex can't be loaded
            pass
        # delete all entries for files that will be rebuilt
        self.indexer.prune(set(self.env.all_docs) - set(docnames))

    def index_page(self, pagename, doctree, title):
        # only index pages with title
        if self.indexer is not None and title:
            self.indexer.feed(pagename, title, doctree)

    # --------- these are overwritten by the serialization builder

    def get_target_uri(self, docname, typ=None):
        return docname + self.out_suffix

    def handle_page(self, pagename, addctx, templatename='page.html',
                    outfilename=None, event_arg=None):
        ctx = self.globalcontext.copy()
        # current_page_name is backwards compatibility
        ctx['pagename'] = ctx['current_page_name'] = pagename

        def pathto(otheruri, resource=False,
                   baseuri=self.get_target_uri(pagename)):
            if not resource:
                otheruri = self.get_target_uri(otheruri)
            return relative_uri(baseuri, otheruri)
        ctx['pathto'] = pathto
        ctx['hasdoc'] = lambda name: name in self.env.all_docs
        ctx['customsidebar'] = self.config.html_sidebars.get(pagename)
        ctx.update(addctx)

        self.app.emit('html-page-context', pagename, templatename, ctx, event_arg)

        output = self.templates.render(templatename, ctx)
        if not outfilename:
            outfilename = path.join(self.outdir, os_path(pagename) + self.out_suffix)
        ensuredir(path.dirname(outfilename)) # normally different from self.outdir
        try:
            f = codecs.open(outfilename, 'w', 'utf-8')
            try:
                f.write(output)
            finally:
                f.close()
        except (IOError, OSError), err:
            self.warn("Error writing file %s: %s" % (outfilename, err))
        if self.copysource and ctx.get('sourcename'):
            # copy the source file for the "show source" link
            source_name = path.join(self.outdir, '_sources', os_path(ctx['sourcename']))
            ensuredir(path.dirname(source_name))
            shutil.copyfile(self.env.doc2path(pagename), source_name)

    def handle_finish(self):
        self.info(bold('dumping search index... '), nonl=True)
        self.indexer.prune(self.env.all_docs)
        f = open(path.join(self.outdir, self.searchindex_filename), 'wb')
        try:
            self.indexer.dump(f, self.indexer_format)
        finally:
            f.close()
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
                f.write('%s %s %s\n' % (refname, desctype, self.get_target_uri(docname)))
        finally:
            f.close()
        self.info('done')


class SerializingHTMLBuilder(StandaloneHTMLBuilder):
    """
    An abstract builder that serializes the HTML generated.
    """
    #: the serializing implementation to use.  Set this to a module that
    #: implements a `dump`, `load`, `dumps` and `loads` functions
    #: (pickle, simplejson etc.)
    implementation = None

    #: the filename for the global context file
    globalcontext_filename = None

    supported_image_types = ('image/svg+xml', 'image/png', 'image/gif',
                             'image/jpeg')

    def init(self):
        self.init_translator_class()
        self.templates = None   # no template bridge necessary

    indexer_format = property(lambda x: x.implementation, doc='''
        Alias the indexer format to the serilization implementation''')

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
            outfilename = path.join(self.outdir, os_path(pagename) + self.out_suffix)

        self.app.emit('html-page-context', pagename, templatename, ctx, event_arg)

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
            shutil.copyfile(self.env.doc2path(pagename), source_name)

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
        shutil.copyfile(path.join(self.doctreedir, ENV_PICKLE_FILENAME),
                        path.join(self.outdir, ENV_PICKLE_FILENAME))

        # touch 'last build' file, used by the web application to determine
        # when to reload its environment and clear the cache
        open(path.join(self.outdir, LAST_BUILD_FILENAME), 'w').close()


class PickleHTMLBuilder(SerializingHTMLBuilder):
    """
    A Builder that dumps the generated HTML into pickle files.
    """
    implementation = pickle
    name = 'pickle'
    out_suffix = '.fpickle'
    globalcontext_filename = 'globalcontext.pickle'
    searchindex_filename = 'searchindex.pickle'


class JSONHTMLBuilder(SerializingHTMLBuilder):
    """
    A builder that dumps the generated HTML into JSON files.
    """
    implementation = json
    name = 'json'
    out_suffix = '.fjson'
    globalcontext_filename = 'globalcontext.json'
    searchindex_filename = 'searchindex.json'


class HTMLHelpBuilder(StandaloneHTMLBuilder):
    """
    Builder that also outputs Windows HTML help project, contents and index files.
    Adapted from the original Doc/tools/prechm.py.
    """
    name = 'htmlhelp'

    # don't copy the reST source
    copysource = False
    supported_image_types = ['image/png', 'image/gif', 'image/jpeg']

    # don't add links
    add_header_links = False
    add_definition_links = False

    def init(self):
        StandaloneHTMLBuilder.init(self)
        # the output files for HTML help must be .html only
        self.out_suffix = '.html'

    def handle_finish(self):
        build_hhx(self, self.outdir, self.config.htmlhelp_basename)


class LaTeXBuilder(Builder):
    """
    Builds LaTeX output to create PDF.
    """
    name = 'latex'
    supported_image_types = ['application/pdf', 'image/png', 'image/gif',
                             'image/jpeg']

    def init(self):
        self.docnames = []
        self.document_data = []

    def get_outdated_docs(self):
        return 'all documents' # for now

    def get_target_uri(self, docname, typ=None):
        if typ == 'token':
            # token references are always inside production lists and must be
            # replaced by \token{} in LaTeX
            return '@token'
        if docname not in self.docnames:
            raise NoUri
        else:
            return ''

    def init_document_data(self):
        preliminary_document_data = map(list, self.config.latex_documents)
        if not preliminary_document_data:
            self.warn('No "latex_documents" config value found; no documents '
                      'will be written.')
            return
        # assign subdirs to titles
        self.titles = []
        for entry in preliminary_document_data:
            docname = entry[0]
            if docname not in self.env.all_docs:
                self.warn('"latex_documents" config value references unknown '
                          'document %s' % docname)
                continue
            self.document_data.append(entry)
            if docname.endswith(SEP+'index'):
                docname = docname[:-5]
            self.titles.append((docname, entry[2]))

    def write(self, *ignored):
        # first, assemble the "appendix" docs that are in every PDF
        appendices = []
        for fname in self.config.latex_appendices:
            appendices.append(self.env.get_doctree(fname))

        docwriter = LaTeXWriter(self)
        docsettings = OptionParser(
            defaults=self.env.settings,
            components=(docwriter,)).get_default_values()

        self.init_document_data()

        for entry in self.document_data:
            docname, targetname, title, author, docclass = entry[:5]
            toctree_only = False
            if len(entry) > 5:
                toctree_only = entry[5]
            destination = FileOutput(
                destination_path=path.join(self.outdir, targetname),
                encoding='utf-8')
            self.info("processing " + targetname + "... ", nonl=1)
            doctree = self.assemble_doctree(docname, toctree_only,
                appendices=(docclass == 'manual') and appendices or [])
            self.post_process_images(doctree)
            self.info("writing... ", nonl=1)
            doctree.settings = docsettings
            doctree.settings.author = author
            doctree.settings.title = title
            doctree.settings.docname = docname
            doctree.settings.docclass = docclass
            docwriter.write(doctree, destination)
            self.info("done")

    def assemble_doctree(self, indexfile, toctree_only, appendices):
        self.docnames = set([indexfile] + appendices)
        self.info(darkgreen(indexfile) + " ", nonl=1)
        def process_tree(docname, tree):
            tree = tree.deepcopy()
            for toctreenode in tree.traverse(addnodes.toctree):
                newnodes = []
                includefiles = map(str, toctreenode['includefiles'])
                for includefile in includefiles:
                    try:
                        self.info(darkgreen(includefile) + " ", nonl=1)
                        subtree = process_tree(includefile,
                                               self.env.get_doctree(includefile))
                        self.docnames.add(includefile)
                    except Exception:
                        self.warn('%s: toctree contains ref to nonexisting file %r' %
                                  (docname, includefile))
                    else:
                        newnodes.append(addnodes.start_of_file())
                        newnodes.extend(subtree.children)
                toctreenode.parent.replace(toctreenode, newnodes)
            return tree
        tree = self.env.get_doctree(indexfile)
        if toctree_only:
            # extract toctree nodes from the tree and put them in a fresh document
            new_tree = new_document('<latex output>')
            new_sect = nodes.section()
            new_sect += nodes.title('<temp>', '<temp>')
            new_tree += new_sect
            for node in tree.traverse(addnodes.toctree):
                new_sect += node
            tree = new_tree
        largetree = process_tree(indexfile, tree)
        largetree.extend(appendices)
        self.info()
        self.info("resolving references...")
        self.env.resolve_references(largetree, indexfile, self)
        # resolve :ref:s to distant tex files -- we can't add a cross-reference,
        # but append the document name
        for pendingnode in largetree.traverse(addnodes.pending_xref):
            docname = pendingnode['refdocname']
            sectname = pendingnode['refsectname']
            newnodes = [nodes.emphasis(sectname, sectname)]
            for subdir, title in self.titles:
                if docname.startswith(subdir):
                    newnodes.append(nodes.Text(' (in ', ' (in '))
                    newnodes.append(nodes.emphasis(title, title))
                    newnodes.append(nodes.Text(')', ')'))
                    break
            else:
                pass
            pendingnode.replace_self(newnodes)
        return largetree

    def finish(self):
        # copy image files
        if self.images:
            self.info(bold('copying images...'), nonl=1)
            for src, dest in self.images.iteritems():
                self.info(' '+src, nonl=1)
                shutil.copyfile(path.join(self.srcdir, src),
                                path.join(self.outdir, dest))
            self.info()

        # the logo is handled differently
        if self.config.latex_logo:
            logobase = path.basename(self.config.latex_logo)
            shutil.copyfile(path.join(self.confdir, self.config.latex_logo),
                            path.join(self.outdir, logobase))

        self.info(bold('copying TeX support files... '), nonl=True)
        staticdirname = path.join(path.dirname(__file__), 'texinputs')
        for filename in os.listdir(staticdirname):
            if not filename.startswith('.'):
                shutil.copyfile(path.join(staticdirname, filename),
                                path.join(self.outdir, filename))
        self.info('done')


class ChangesBuilder(Builder):
    """
    Write a summary with all versionadded/changed directives.
    """
    name = 'changes'

    def init(self):
        self.init_templates()

    def get_outdated_docs(self):
        return self.outdir

    typemap = {
        'versionadded': 'added',
        'versionchanged': 'changed',
        'deprecated': 'deprecated',
    }

    def write(self, *ignored):
        version = self.config.version
        libchanges = {}
        apichanges = []
        otherchanges = {}
        self.info(bold('writing summary file...'))
        for type, docname, lineno, module, descname, content in \
                self.env.versionchanges[version]:
            ttext = self.typemap[type]
            context = content.replace('\n', ' ')
            if descname and docname.startswith('c-api'):
                if not descname:
                    continue
                if context:
                    entry = '<b>%s</b>: <i>%s:</i> %s' % (descname, ttext, context)
                else:
                    entry = '<b>%s</b>: <i>%s</i>.' % (descname, ttext)
                apichanges.append((entry, docname, lineno))
            elif descname or module:
                if not module:
                    module = 'Builtins'
                if not descname:
                    descname = 'Module level'
                if context:
                    entry = '<b>%s</b>: <i>%s:</i> %s' % (descname, ttext, context)
                else:
                    entry = '<b>%s</b>: <i>%s</i>.' % (descname, ttext)
                libchanges.setdefault(module, []).append((entry, docname, lineno))
            else:
                if not context:
                    continue
                entry = '<i>%s:</i> %s' % (ttext.capitalize(), context)
                title = self.env.titles[docname].astext()
                otherchanges.setdefault((docname, title), []).append(
                    (entry, docname, lineno))

        ctx = {
            'project': self.config.project,
            'version': version,
            'docstitle': self.config.html_title,
            'shorttitle': self.config.html_short_title,
            'libchanges': sorted(libchanges.iteritems()),
            'apichanges': sorted(apichanges),
            'otherchanges': sorted(otherchanges.iteritems()),
            'show_sphinx': self.config.html_show_sphinx,
        }
        f = open(path.join(self.outdir, 'index.html'), 'w')
        try:
            f.write(self.templates.render('changes/frameset.html', ctx))
        finally:
            f.close()
        f = open(path.join(self.outdir, 'changes.html'), 'w')
        try:
            f.write(self.templates.render('changes/versionchanges.html', ctx))
        finally:
            f.close()

        hltext = ['.. versionadded:: %s' % version,
                  '.. versionchanged:: %s' % version,
                  '.. deprecated:: %s' % version]

        def hl(no, line):
            line = '<a name="L%s"> </a>' % no + escape(line)
            for x in hltext:
                if x in line:
                    line = '<span class="hl">%s</span>' % line
                    break
            return line

        self.info(bold('copying source files...'))
        for docname in self.env.all_docs:
            f = open(self.env.doc2path(docname))
            lines = f.readlines()
            targetfn = path.join(self.outdir, 'rst', os_path(docname)) + '.html'
            ensuredir(path.dirname(targetfn))
            f = codecs.open(targetfn, 'w', 'utf8')
            try:
                text = ''.join(hl(i+1, line) for (i, line) in enumerate(lines))
                ctx = {'filename': self.env.doc2path(docname, None), 'text': text}
                f.write(self.templates.render('changes/rstsource.html', ctx))
            finally:
                f.close()
        shutil.copyfile(path.join(path.dirname(__file__), 'static', 'default.css'),
                        path.join(self.outdir, 'default.css'))

    def hl(self, text, version):
        text = escape(text)
        for directive in ['versionchanged', 'versionadded', 'deprecated']:
            text = text.replace('.. %s:: %s' % (directive, version),
                                '<b>.. %s:: %s</b>' % (directive, version))
        return text

    def finish(self):
        pass


class TextBuilder(Builder):
    name = 'text'
    out_suffix = '.txt'

    def init(self):
        pass

    def get_outdated_docs(self):
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = self.env.doc2path(docname, self.outdir, self.out_suffix)
            try:
                targetmtime = path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = path.getmtime(self.env.doc2path(docname))
                if srcmtime > targetmtime:
                    yield docname
            except EnvironmentError:
                # source doesn't exist anymore
                pass

    def get_target_uri(self, docname, typ=None):
        return ''

    def prepare_writing(self, docnames):
        self.writer = TextWriter(self)

    def write_doc(self, docname, doctree):
        destination = StringOutput(encoding='utf-8')
        self.writer.write(doctree, destination)
        outfilename = path.join(self.outdir, os_path(docname) + self.out_suffix)
        ensuredir(path.dirname(outfilename)) # normally different from self.outdir
        try:
            f = codecs.open(outfilename, 'w', 'utf-8')
            try:
                f.write(self.writer.output)
            finally:
                f.close()
        except (IOError, OSError), err:
            self.warn("Error writing file %s: %s" % (outfilename, err))

    def finish(self):
        pass


# compatibility alias
WebHTMLBuilder = PickleHTMLBuilder


from sphinx.linkcheck import CheckExternalLinksBuilder

builtin_builders = {
    'html': StandaloneHTMLBuilder,
    'pickle': PickleHTMLBuilder,
    'json': JSONHTMLBuilder,
    'web': PickleHTMLBuilder,
    'htmlhelp': HTMLHelpBuilder,
    'latex': LaTeXBuilder,
    'text': TextBuilder,
    'changes': ChangesBuilder,
    'linkcheck': CheckExternalLinksBuilder,
}
