# -*- coding: utf-8 -*-
"""
    sphinx.builder
    ~~~~~~~~~~~~~~

    Builder classes for different output formats.

    :copyright: 2007-2008 by Georg Brandl.
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

from sphinx import addnodes
from sphinx.util import (get_matching_docs, ensuredir, relative_uri, SEP, os_path)
from sphinx.htmlhelp import build_hhx
from sphinx.htmlwriter import HTMLWriter, HTMLTranslator, SmartyPantsHTMLTranslator
from sphinx.latexwriter import LaTeXWriter
from sphinx.environment import BuildEnvironment, NoUri
from sphinx.highlighting import PygmentsBridge
from sphinx.util.console import bold, purple, darkgreen

# side effect: registers roles and directives
from sphinx import roles
from sphinx import directives

ENV_PICKLE_FILENAME = 'environment.pickle'
LAST_BUILD_FILENAME = 'last_build'

class Builder(object):
    """
    Builds target formats from the reST sources.
    """

    # builder's name, for the -b command line options
    name = ''

    def __init__(self, app, env=None, freshenv=False):
        self.srcdir = app.srcdir
        self.outdir = app.outdir
        self.doctreedir = app.doctreedir
        if not path.isdir(self.doctreedir):
            os.mkdir(self.doctreedir)

        self.app = app
        self.warn = app.warn
        self.info = app.info
        self.config = app.config

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
        """Call if you need Jinja templates in the builder."""
        # lazily import this, maybe other builders won't need it
        from sphinx._jinja import Environment, SphinxFileSystemLoader

        # load templates
        self.templates = {}
        base_templates_path = path.join(path.dirname(__file__), 'templates')
        ext_templates_path = [path.join(self.srcdir, dir)
                              for dir in self.config.templates_path]
        loader = SphinxFileSystemLoader(base_templates_path, ext_templates_path)
        self.jinja_env = Environment(loader=loader,
                                     # disable traceback, more likely that something
                                     # in the application is broken than in the templates
                                     friendly_traceback=False)

    def get_template(self, name):
        if name in self.templates:
            return self.templates[name]
        template = self.templates[name] = self.jinja_env.get_template(name)
        return template

    def get_target_uri(self, docname, typ=None):
        """
        Return the target URI for a document name (typ can be used to qualify
        the link characteristic for individual builders).
        """
        raise NotImplementedError

    def get_relative_uri(self, from_, to, typ=None):
        """Return a relative URI between two source filenames.
           May raise environment.NoUri if there's no way to return a
           sensible URI."""
        return relative_uri(self.get_target_uri(from_),
                            self.get_target_uri(to, typ))

    def get_outdated_docs(self):
        """Return a list of output files that are outdated."""
        raise NotImplementedError

    def status_iterator(self, iterable, summary, colorfunc):
        l = -1
        for item in iterable:
            if l == -1:
                self.info(bold(summary), nonl=1)
                l = 0
            self.info(colorfunc(item) + ' ', nonl=1)
            yield item
        if l == 0:
            self.info()

    # build methods

    def load_env(self):
        """Set up the build environment."""
        if self.env:
            return
        if not self.freshenv:
            try:
                self.info(bold('trying to load pickled env... '), nonl=True)
                self.env = BuildEnvironment.frompickle(
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
            self.build([], to_build)
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
        iterator = self.env.update(self.config, self.app)
        # the first item in the iterator is a summary message
        self.info(iterator.next())
        for docname in self.status_iterator(iterator, 'reading... ', purple):
            updated_docnames.append(docname)
            # nothing further to do, the environment has already done the reading
        for warning in warnings:
            if warning.strip():
                self.warn(warning)
        self.env.set_warnfunc(self.warn)

        if updated_docnames:
            # save the environment
            self.info(bold('pickling the env... '), nonl=True)
            self.env.topickle(path.join(self.doctreedir, ENV_PICKLE_FILENAME))
            self.info('done')

            # global actions
            self.info(bold('checking consistency...'))
            self.env.check_consistency()
        else:
            if not docnames:
                self.info(bold('no targets are out of date.'))
                return

        # another indirection to support methods which don't build files
        # individually
        self.write(docnames, updated_docnames, method)

        # finish (write static files etc.)
        self.info(bold('finishing... '))
        self.finish()
        if self.app._warncount:
            self.info(bold('build succeeded, %s warning%s.' %
                           (self.app._warncount, self.app._warncount != 1 and 's' or '')))
        else:
            self.info(bold('build succeeded.'))

    def write(self, build_docnames, updated_docnames, method='update'):
        if build_docnames is None:
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

        self.prepare_writing(docnames)

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

    def init(self):
        """Load templates."""
        self.init_templates()
        self.init_translator_class()

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

        self.info(bold('creating index...'))
        self.env.create_index(self)

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

        self.globalcontext = dict(
            project = self.config.project,
            copyright = self.config.copyright,
            release = self.config.release,
            version = self.config.version,
            last_updated = self.last_updated,
            style = self.config.html_style,
            use_modindex = self.config.html_use_modindex,
            builder = self.name,
            parents = [],
            titles = {},
            len = len, # the built-in
        )

    def write_doc(self, docname, doctree):
        destination = StringOutput(encoding='utf-8')
        doctree.settings = self.docsettings

        self.docwriter.write(doctree, destination)
        self.docwriter.assemble_parts()

        prev = next = None
        parents = []
        related = self.env.toctree_relations.get(docname)
        titles = self.env.titles
        if related:
            try:
                prev = {'link': self.get_relative_uri(docname, related[1]),
                        'title': self.render_partial(titles[related[1]])['title']}
            except KeyError:
                # the relation is (somehow) not in the TOC tree, handle that gracefully
                prev = None
            try:
                next = {'link': self.get_relative_uri(docname, related[2]),
                        'title': self.render_partial(titles[related[2]])['title']}
            except KeyError:
                next = None
        while related:
            try:
                parents.append(
                    {'link': self.get_relative_uri(docname, related[0]),
                     'title': self.render_partial(titles[related[0]])['title']})
            except KeyError:
                pass
            related = self.env.toctree_relations.get(related[0])
        if parents:
            parents.pop() # remove link to the master file; we have a generic
                          # "back to index" link already
        parents.reverse()

        title = titles.get(docname)
        if title:
            title = self.render_partial(title)['title']
        else:
            title = ''
        self.globalcontext['titles'][docname] = title
        sourcename = self.config.html_copy_source and docname + '.txt' or ''
        ctx = dict(
            title = title,
            sourcename = sourcename,
            body = self.docwriter.parts['fragment'],
            toc = self.render_partial(self.env.get_toc_for(docname))['fragment'],
            # only display a TOC if there's more than one item to show
            display_toc = (self.env.toc_num_entries[docname] > 1),
            parents = parents,
            prev = prev,
            next = next,
        )

        self.index_page(docname, doctree, title)
        self.handle_page(docname, ctx)

    def finish(self):
        self.info(bold('writing additional files...'), nonl=1)

        # the global general index

        # the total count of lines for each index letter, used to distribute
        # the entries into two columns
        indexcounts = []
        for _, entries in self.env.index:
            indexcounts.append(sum(1 + len(subitems) for _, (_, subitems) in entries))

        genindexcontext = dict(
            genindexentries = self.env.index,
            genindexcounts = indexcounts,
        )
        self.info(' genindex', nonl=1)
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
            pmn = ''
            cg = 0 # collapse group
            fl = '' # first letter
            for mn, (fn, sy, pl, dep) in modules:
                pl = pl and pl.split(', ') or []
                platforms.update(pl)
                if fl != mn[0].lower() and mn[0] != '_':
                    modindexentries.append(['', False, 0, False,
                                            mn[0].upper(), '', [], False])
                tn = mn.split('.')[0]
                if tn != mn:
                    # submodule
                    if pmn == tn:
                        # first submodule - make parent collapsable
                        modindexentries[-1][1] = True
                    elif not pmn.startswith(tn):
                        # submodule without parent in list, add dummy entry
                        cg += 1
                        modindexentries.append([tn, True, cg, False, '', '', [], False])
                else:
                    cg += 1
                modindexentries.append([mn, False, cg, (tn != mn), fn, sy, pl, dep])
                pmn = mn
                fl = mn[0].lower()
            platforms = sorted(platforms)

            modindexcontext = dict(
                modindexentries = modindexentries,
                platforms = platforms,
            )
            self.info(' modindex', nonl=1)
            self.handle_page('modindex', modindexcontext, 'modindex.html')

        # the search page
        self.info(' search', nonl=1)
        self.handle_page('search', {}, 'search.html')

        # additional pages from conf.py
        for pagename, template in self.config.html_additional_pages.items():
            self.info(' '+pagename, nonl=1)
            self.handle_page(pagename, {}, template)

        # the index page
        indextemplate = self.config.html_index
        if indextemplate:
            self.info(' index', nonl=1)
            self.handle_page('index', {'indextemplate': indextemplate}, 'index.html')

        # copy static files
        self.info()
        self.info(bold('copying static files...'))
        ensuredir(path.join(self.outdir, 'static'))
        staticdirnames = [path.join(path.dirname(__file__), 'static')] + \
                         [path.join(self.srcdir, spath)
                          for spath in self.config.html_static_path]
        for staticdirname in staticdirnames:
            for filename in os.listdir(staticdirname):
                if not filename.startswith('.'):
                    shutil.copyfile(path.join(staticdirname, filename),
                                    path.join(self.outdir, 'static', filename))
        # add pygments style file
        f = open(path.join(self.outdir, 'static', 'pygments.css'), 'w')
        f.write(PygmentsBridge('html', self.config.pygments_style).get_stylesheet())
        f.close()

        # dump the search index
        self.handle_finish()

    # --------- these are overwritten by the Pickle builder

    def get_target_uri(self, docname, typ=None):
        return docname + '.html'

    def get_outdated_docs(self):
        for docname in self.env.found_docs:
            targetname = self.env.doc2path(docname, self.outdir, '.html')
            try:
                targetmtime = path.getmtime(targetname)
            except:
                targetmtime = 0
            if docname not in self.env.all_docs:
                yield docname
            elif path.getmtime(self.env.doc2path(docname)) > targetmtime:
                yield docname


    def load_indexer(self, docnames):
        try:
            f = open(path.join(self.outdir, 'searchindex.json'), 'r')
            try:
                self.indexer.load(f, 'json')
            finally:
                f.close()
        except (IOError, OSError):
            pass
        # delete all entries for files that will be rebuilt
        self.indexer.prune(set(self.env.all_docs) - set(docnames))

    def index_page(self, pagename, doctree, title):
        # only index pages with title
        if self.indexer is not None and title:
            self.indexer.feed(pagename, title, doctree)

    def handle_page(self, pagename, addctx, templatename='page.html'):
        ctx = self.globalcontext.copy()
        ctx['current_page_name'] = pagename

        def pathto(otheruri, resource=False,
                   baseuri=self.get_target_uri(pagename)):
            if not resource:
                otheruri = self.get_target_uri(otheruri)
            return relative_uri(baseuri, otheruri)
        ctx['pathto'] = pathto
        ctx['hasdoc'] = lambda name: name in self.env.all_docs
        sidebarfile = self.config.html_sidebars.get(pagename)
        if sidebarfile:
            ctx['customsidebar'] = sidebarfile
        ctx.update(addctx)

        output = self.get_template(templatename).render(ctx)
        outfilename = path.join(self.outdir, os_path(pagename) + '.html')
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
        self.info(bold('dumping search index...'))
        self.indexer.prune(self.env.all_docs)
        f = open(path.join(self.outdir, 'searchindex.json'), 'w')
        try:
            self.indexer.dump(f, 'json')
        finally:
            f.close()


class PickleHTMLBuilder(StandaloneHTMLBuilder):
    """
    Builds HTML docs without rendering templates.
    """
    name = 'pickle'

    def init(self):
        self.init_translator_class()

    def get_outdated_docs(self):
        for docname in self.env.found_docs:
            targetname = self.env.doc2path(docname, self.outdir, '.fpickle')
            try:
                targetmtime = path.getmtime(targetname)
            except:
                targetmtime = 0
            if path.getmtime(self.env.doc2path(docname)) > targetmtime:
                yield docname

    def get_target_uri(self, docname, typ=None):
        if docname == 'index':
            return ''
        if docname.endswith(SEP + 'index'):
            return docname[:-5] # up to sep
        return docname + SEP

    def load_indexer(self, docnames):
        try:
            f = open(path.join(self.outdir, 'searchindex.pickle'), 'r')
            try:
                self.indexer.load(f, 'pickle')
            finally:
                f.close()
        except (IOError, OSError):
            pass
        # delete all entries for files that will be rebuilt
        self.indexer.prune(set(self.env.all_docs) - set(docnames))

    def index_page(self, pagename, doctree, title):
        # only index pages with title
        if self.indexer is not None and title:
            self.indexer.feed(pagename, title, doctree)

    def handle_page(self, pagename, ctx, templatename='page.html'):
        ctx['current_page_name'] = pagename
        sidebarfile = self.config.html_sidebars.get(pagename, '')
        if sidebarfile:
            ctx['customsidebar'] = path.join(self.srcdir, sidebarfile)
        outfilename = path.join(self.outdir, os_path(pagename) + '.fpickle')
        ensuredir(path.dirname(outfilename))
        f = open(outfilename, 'wb')
        try:
            pickle.dump(ctx, f, 2)
        finally:
            f.close()

        # if there is a source file, copy the source file for the
        # "show source" link
        if ctx.get('sourcename'):
            source_name = path.join(self.outdir, 'sources',
                                    os_path(ctx['sourcename']))
            ensuredir(path.dirname(source_name))
            shutil.copyfile(self.env.doc2path(pagename), source_name)

    def handle_finish(self):
        # dump the global context
        outfilename = path.join(self.outdir, 'globalcontext.pickle')
        f = open(outfilename, 'wb')
        try:
            pickle.dump(self.globalcontext, f, 2)
        finally:
            f.close()

        self.info(bold('dumping search index...'))
        self.indexer.prune(self.env.all_docs)
        f = open(path.join(self.outdir, 'searchindex.pickle'), 'wb')
        try:
            self.indexer.dump(f, 'pickle')
        finally:
            f.close()

        # copy the environment file from the doctree dir to the output dir
        # as needed by the web app
        shutil.copyfile(path.join(self.doctreedir, ENV_PICKLE_FILENAME),
                        path.join(self.outdir, ENV_PICKLE_FILENAME))

        # touch 'last build' file, used by the web application to determine
        # when to reload its environment and clear the cache
        open(path.join(self.outdir, LAST_BUILD_FILENAME), 'w').close()
        # copy configuration file if not present
        if not path.isfile(path.join(self.outdir, 'webconf.py')):
            shutil.copyfile(path.join(path.dirname(__file__), 'web', 'webconf.py'),
                            path.join(self.outdir, 'webconf.py'))


class HTMLHelpBuilder(StandaloneHTMLBuilder):
    """
    Builder that also outputs Windows HTML help project, contents and index files.
    Adapted from the original Doc/tools/prechm.py.
    """
    name = 'htmlhelp'

    # don't copy the reST source
    copysource = False

    def handle_finish(self):
        build_hhx(self, self.outdir, self.config.htmlhelp_basename)


class LaTeXBuilder(Builder):
    """
    Builds LaTeX output to create PDF.
    """
    name = 'latex'

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

        for docname, targetname, title, author, docclass in self.document_data:
            destination = FileOutput(
                destination_path=path.join(self.outdir, targetname),
                encoding='utf-8')
            self.info("processing " + targetname + "... ", nonl=1)
            doctree = self.assemble_doctree(
                docname, appendices=(docclass == 'manual') and appendices or [])
            self.info("writing... ", nonl=1)
            doctree.settings = docsettings
            doctree.settings.author = author
            doctree.settings.title = title
            doctree.settings.docname = docname
            doctree.settings.docclass = docclass
            docwriter.write(doctree, destination)
            self.info("done")

    def assemble_doctree(self, indexfile, appendices):
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
                    except:
                        self.warn('%s: toctree contains ref to nonexisting file %r' %
                                  (docname, includefile))
                    else:
                        newnodes.extend(subtree.children)
                toctreenode.parent.replace(toctreenode, newnodes)
            return tree
        largetree = process_tree(indexfile, self.env.get_doctree(indexfile))
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
        self.info(bold('copying TeX support files...'))
        staticdirname = path.join(path.dirname(__file__), 'texinputs')
        for filename in os.listdir(staticdirname):
            if not filename.startswith('.'):
                shutil.copyfile(path.join(staticdirname, filename),
                                path.join(self.outdir, filename))


class ChangesBuilder(Builder):
    """
    Write a summary with all versionadded/changed directives.
    """
    name = 'changes'

    def init(self):
        self.init_templates()
        self.ftemplate = self.get_template('changes/frameset.html')
        self.vtemplate = self.get_template('changes/versionchanges.html')
        self.stemplate = self.get_template('changes/rstsource.html')

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
            'libchanges': sorted(libchanges.iteritems()),
            'apichanges': sorted(apichanges),
            'otherchanges': sorted(otherchanges.iteritems()),
        }
        f = open(path.join(self.outdir, 'index.html'), 'w')
        try:
            f.write(self.ftemplate.render(ctx))
        finally:
            f.close()
        f = open(path.join(self.outdir, 'changes.html'), 'w')
        try:
            f.write(self.vtemplate.render(ctx))
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
                f.write(self.stemplate.render(ctx))
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

# compatibility alias
WebHTMLBuilder = PickleHTMLBuilder


from sphinx.linkcheck import CheckExternalLinksBuilder

builtin_builders = {
    'html': StandaloneHTMLBuilder,
    'pickle': PickleHTMLBuilder,
    'web': PickleHTMLBuilder,
    'htmlhelp': HTMLHelpBuilder,
    'latex': LaTeXBuilder,
    'changes': ChangesBuilder,
    'linkcheck': CheckExternalLinksBuilder,
}
