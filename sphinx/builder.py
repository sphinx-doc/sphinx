# -*- coding: utf-8 -*-
"""
    sphinx.builder
    ~~~~~~~~~~~~~~

    Builder classes for different output formats.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import os
import sys
import time
import codecs
import shutil
import cPickle as pickle
import cStringIO as StringIO
from os import path
from cgi import escape

from docutils import nodes
from docutils.io import StringOutput, FileOutput, DocTreeInput
from docutils.core import publish_parts
from docutils.utils import new_document
from docutils.readers import doctree
from docutils.frontend import OptionParser

from sphinx import addnodes
from sphinx.util import (get_matching_files, attrdict, status_iterator,
                         ensuredir, relative_uri, os_path, SEP)
from sphinx.htmlhelp import build_hhx
from sphinx.extension import DummyEventManager, import_object
from sphinx.patchlevel import get_version_info, get_sys_version_info
from sphinx.htmlwriter import HTMLWriter, HTMLTranslator, SmartyPantsHTMLTranslator
from sphinx.latexwriter import LaTeXWriter
from sphinx.environment import BuildEnvironment, NoUri
from sphinx.highlighting import pygments, highlight_block, get_stylesheet
from sphinx.util.console import bold, purple, green

# side effect: registers roles and directives
from sphinx import roles
from sphinx import directives

ENV_PICKLE_FILENAME = 'environment.pickle'
LAST_BUILD_FILENAME = 'last_build'

class Builder(object):
    """
    Builds target formats from the reST sources.
    """

    def __init__(self, srcdirname, outdirname, doctreedirname,
                 config, env=None, freshenv=False, events=None,
                 status_stream=None, warning_stream=None):
        self.srcdir = srcdirname
        self.outdir = outdirname
        self.doctreedir = doctreedirname
        if not path.isdir(doctreedirname):
            os.mkdir(doctreedirname)
        self.freshenv = freshenv

        self.status_stream = status_stream or sys.stdout
        self.warning_stream = warning_stream or sys.stderr

        self.config = config
        # if None, this is set in load_env()
        self.env = env

        self.events = events or DummyEventManager()

        self.init()

    # helper methods

    def msg(self, message='', nonl=False, nobold=False):
        if not nobold: message = bold(message)
        if nonl:
            print >>self.status_stream, message,
        else:
            print >>self.status_stream, message
        self.status_stream.flush()

    def warn(self, message):
        print >>self.warning_stream, 'WARNING:', message

    def init(self):
        """Load necessary templates and perform initialization."""
        raise NotImplementedError

    def init_templates(self):
        """Call if you need Jinja templates in the builder."""
        # lazily import this, maybe other builders won't need it
        from sphinx._jinja import Environment, SphinxFileSystemLoader

        # load templates
        self.templates = {}
        templates_path = [path.join(path.dirname(__file__), 'templates')]
        templates_path.extend(self.config.templates_path)
        self.jinja_env = Environment(loader=SphinxFileSystemLoader(templates_path),
                                     # disable traceback, more likely that something
                                     # in the application is broken than in the templates
                                     friendly_traceback=False)

    def get_template(self, name):
        if name in self.templates:
            return self.templates[name]
        template = self.templates[name] = self.jinja_env.get_template(name)
        return template

    def get_target_uri(self, source_filename, typ=None):
        """Return the target URI for a source filename."""
        raise NotImplementedError

    def get_relative_uri(self, from_, to, typ=None):
        """Return a relative URI between two source filenames.
           May raise environment.NoUri if there's no way to return a
           sensible URI."""
        return relative_uri(self.get_target_uri(from_),
                            self.get_target_uri(to, typ))

    def get_outdated_files(self):
        """Return a list of output files that are outdated."""
        raise NotImplementedError

    # build methods

    def load_env(self):
        """Set up the build environment. Return True if a pickled file could be
           successfully loaded, False if a new environment had to be created."""
        if self.env:
            return
        if not self.freshenv:
            try:
                self.msg('trying to load pickled env...', nonl=True)
                self.env = BuildEnvironment.frompickle(
                    path.join(self.doctreedir, ENV_PICKLE_FILENAME))
                self.msg('done', nobold=True)
            except Exception, err:
                self.msg('failed: %s' % err, nobold=True)
                self.env = BuildEnvironment(self.srcdir, self.doctreedir)
        else:
            self.env = BuildEnvironment(self.srcdir, self.doctreedir)

    def build_all(self):
        """Build all source files."""
        self.load_env()
        self.build(None, summary='all source files')

    def build_specific(self, source_filenames):
        """Only rebuild as much as needed for changes in the source_filenames."""
        # bring the filenames to the canonical format, that is,
        # relative to the source directory.
        dirlen = len(self.srcdir) + 1
        to_write = [path.abspath(filename)[dirlen:] for filename in source_filenames]
        self.load_env()
        self.build(to_write,
                   summary='%d source files given on command line' % len(to_write))

    def build_update(self):
        """Only rebuild files changed or added since last build."""
        self.load_env()
        to_build = self.get_outdated_files()
        if not to_build:
            self.msg('no target files are out of date, exiting.')
            return
        if isinstance(to_build, str):
            self.build([], to_build)
        else:
            to_build = list(to_build)
            self.build(to_build,
                       summary='targets for %d source files that are '
                       'out of date' % len(to_build))

    def build(self, filenames, summary=None):
        if summary:
            self.msg('building [%s]:' % self.name, nonl=1)
            self.msg(summary, nobold=1)

        updated_filenames = []
        # while reading, collect all warnings from docutils
        warnings = []
        self.env.set_warnfunc(warnings.append)
        self.msg('reading, updating environment:', nonl=1)
        iterator = self.env.update(
            self.config,
            hook=lambda doctree: self.events.emit('doctree-read', doctree))
        self.msg(iterator.next(), nonl=1, nobold=1)
        for filename in iterator:
            if not updated_filenames:
                self.msg('')
            updated_filenames.append(filename)
            self.msg(purple(filename), nonl=1, nobold=1)
        self.msg()
        for warning in warnings:
            self.warn(warning)
        self.env.set_warnfunc(self.warn)

        if updated_filenames:
            # save the environment
            self.msg('pickling the env...', nonl=True)
            self.env.topickle(path.join(self.doctreedir, ENV_PICKLE_FILENAME))
            self.msg('done', nobold=True)

            # global actions
            self.msg('checking consistency...')
            self.env.check_consistency()

        # another indirection to support methods which don't build files
        # individually
        self.write(filenames, updated_filenames)

        # finish (write style files etc.)
        self.msg('finishing...')
        self.finish()
        self.msg('done!')

    def write(self, build_filenames, updated_filenames):
        if build_filenames is None: # build_all
            build_filenames = self.env.all_files
        filenames = set(build_filenames) | set(updated_filenames)

        # add all toctree-containing files that may have changed
        for filename in list(filenames):
            for tocfilename in self.env.files_to_rebuild.get(filename, []):
                filenames.add(tocfilename)
        filenames.add('contents.rst')

        self.msg('creating index...')
        self.env.create_index(self)
        self.prepare_writing(filenames)

        # write target files
        warnings = []
        self.env.set_warnfunc(warnings.append)
        self.msg('writing output...')
        for filename in status_iterator(sorted(filenames), green,
                                        stream=self.status_stream):
            doctree = self.env.get_and_resolve_doctree(filename, self)
            self.write_file(filename, doctree)
        for warning in warnings:
            self.warn(warning)
        self.env.set_warnfunc(self.warn)

    def prepare_writing(self, filenames):
        raise NotImplementedError

    def write_file(self, filename, doctree):
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
        if self.config.html_translator_class:
            self.translator_class = import_object(self.config.html_translator_class,
                                                  'html_translator_class setting')
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
            reader=doctree.Reader(),
            writer=HTMLWriter(self),
            settings_overrides={'output_encoding': 'unicode'}
        )

    def prepare_writing(self, filenames):
        from sphinx.search import IndexBuilder
        self.indexer = IndexBuilder()
        self.load_indexer(filenames)
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
            builder = self.name,
            parents = [],
            titles = {},
            len = len, # the built-in
        )

    def write_file(self, filename, doctree):
        pagename = filename[:-4]
        destination = StringOutput(encoding='utf-8')
        doctree.settings = self.docsettings

        output = self.docwriter.write(doctree, destination)
        self.docwriter.assemble_parts()

        prev = next = None
        parents = []
        related = self.env.toctree_relations.get(filename)
        if related:
            prev = {'link': self.get_relative_uri(filename, related[1]),
                    'title': self.render_partial(self.env.titles[related[1]])['title']}
            next = {'link': self.get_relative_uri(filename, related[2]),
                    'title': self.render_partial(self.env.titles[related[2]])['title']}
        while related:
            parents.append(
                {'link': self.get_relative_uri(filename, related[0]),
                 'title': self.render_partial(self.env.titles[related[0]])['title']})
            related = self.env.toctree_relations.get(related[0])
        if parents:
            parents.pop() # remove link to "contents.rst"; we have a generic
                          # "back to index" link already
        parents.reverse()

        title = self.env.titles.get(filename)
        if title:
            title = self.render_partial(title)['title']
        else:
            title = ''
        self.globalcontext['titles'][filename] = title
        sourcename = pagename + '.txt'
        context = dict(
            title = title,
            sourcename = sourcename,
            body = self.docwriter.parts['fragment'],
            toc = self.render_partial(self.env.get_toc_for(filename))['fragment'],
            # only display a TOC if there's more than one item to show
            display_toc = (self.env.toc_num_entries[filename] > 1),
            parents = parents,
            prev = prev,
            next = next,
        )

        self.index_page(pagename, doctree, title)
        self.handle_page(pagename, context)

    def finish(self):
        self.msg('writing additional files...')

        # the global general index

        # the total count of lines for each index letter, used to distribute
        # the entries into two columns
        indexcounts = []
        for key, entries in self.env.index:
            indexcounts.append(sum(1 + len(subitems) for _, (_, subitems) in entries))

        genindexcontext = dict(
            genindexentries = self.env.index,
            genindexcounts = indexcounts,
        )
        self.handle_page('genindex', genindexcontext, 'genindex.html')

        # the global module index

        # the sorted list of all modules, for the global module index
        modules = sorted(((mn, (self.get_relative_uri('modindex.rst', fn) +
                                '#module-' + mn, sy, pl, dep))
                          for (mn, (fn, sy, pl, dep)) in self.env.modules.iteritems()),
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
        self.handle_page('modindex', modindexcontext, 'modindex.html')

        # the search page
        self.handle_page('search', {}, 'search.html')

        # additional pages from conf.py
        for pagename, template in self.config.html_additional_pages.items():
            template = path.join(self.srcdir, template)
            self.handle_page(pagename, {}, template)

        # the index page
        indextemplate = self.config.html_index
        if indextemplate:
            indextemplate = path.join(self.srcdir, indextemplate)
        self.handle_page('index', {'indextemplate': indextemplate}, 'index.html')

        # copy style files
        self.msg('copying style files...')
        styledirname = path.join(path.dirname(__file__), 'style')
        ensuredir(path.join(self.outdir, 'style'))
        for filename in os.listdir(styledirname):
            if not filename.startswith('.'):
                shutil.copyfile(path.join(styledirname, filename),
                                path.join(self.outdir, 'style', filename))
        # add pygments style file
        f = open(path.join(self.outdir, 'style', 'pygments.css'), 'w')
        if pygments:
            f.write(get_stylesheet())
        f.close()

        # dump the search index
        self.handle_finish()

    # --------- these are overwritten by the Web builder

    def get_target_uri(self, source_filename, typ=None):
        return source_filename[:-4] + '.html'

    def get_outdated_files(self):
        for filename in get_matching_files(
            self.srcdir, '*.rst', exclude=set(self.config.unused_files)):
            try:
                rstname = path.join(self.outdir, os_path(filename))
                targetmtime = path.getmtime(rstname[:-4] + '.html')
            except:
                targetmtime = 0
            if filename not in self.env.all_files:
                yield filename
            elif path.getmtime(path.join(self.srcdir, os_path(filename))) > targetmtime:
                yield filename


    def load_indexer(self, filenames):
        try:
            f = open(path.join(self.outdir, 'searchindex.json'), 'r')
            try:
                self.indexer.load(f, 'json')
            finally:
                f.close()
        except (IOError, OSError):
            pass
        # delete all entries for files that will be rebuilt
        self.indexer.prune([fn[:-4] for fn in set(self.env.all_files) - set(filenames)])

    def index_page(self, pagename, doctree, title):
        # only index pages with title
        if self.indexer is not None and title:
            self.indexer.feed(pagename, title, doctree)

    def handle_page(self, pagename, addctx, templatename='page.html'):
        ctx = self.globalcontext.copy()
        ctx['current_page_name'] = pagename

        def pathto(otheruri, resource=False,
                   baseuri=self.get_target_uri(pagename+'.rst')):
            if not resource:
                otheruri = self.get_target_uri(otheruri+'.rst')
            return relative_uri(baseuri, otheruri)
        ctx['pathto'] = pathto
        ctx['hasdoc'] = lambda name: name+'.rst' in self.env.all_files
        sidebarfile = self.config.html_sidebars.get(pagename)
        if sidebarfile:
            ctx['customsidebar'] = path.join(self.srcdir, sidebarfile)
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
            shutil.copyfile(path.join(self.srcdir, os_path(pagename+'.rst')),
                            path.join(self.outdir, os_path(ctx['sourcename'])))

    def handle_finish(self):
        self.msg('dumping search index...')
        self.indexer.prune([fn[:-4] for fn in self.env.all_files])
        f = open(path.join(self.outdir, 'searchindex.json'), 'w')
        try:
            self.indexer.dump(f, 'json')
        finally:
            f.close()


class WebHTMLBuilder(StandaloneHTMLBuilder):
    """
    Builds HTML docs usable with the web-based doc server.
    """
    name = 'web'

    def init(self):
        # Nothing to do here.
        pass

    def get_outdated_files(self):
        for filename in get_matching_files(
            self.srcdir, '*.rst', exclude=set(self.config.unused_files)):
            try:
                targetmtime = path.getmtime(
                    path.join(self.outdir, os_path(filename)[:-4] + '.fpickle'))
            except:
                targetmtime = 0
            if path.getmtime(path.join(self.srcdir,
                                       os_path(filename))) > targetmtime:
                yield filename

    def get_target_uri(self, source_filename, typ=None):
        if source_filename == 'index.rst':
            return ''
        if source_filename.endswith(SEP+'index.rst'):
            return source_filename[:-9] # up to sep
        return source_filename[:-4] + SEP

    def load_indexer(self, filenames):
        try:
            f = open(path.join(self.outdir, 'searchindex.pickle'), 'r')
            try:
                self.indexer.load(f, 'pickle')
            finally:
                f.close()
        except (IOError, OSError):
            pass
        # delete all entries for files that will be rebuilt
        self.indexer.prune(set(self.env.all_files) - set(filenames))

    def index_page(self, pagename, doctree, title):
        # only index pages with title
        if self.indexer is not None and title:
            self.indexer.feed(pagename+'.rst', title, doctree)

    def handle_page(self, pagename, context, templatename='page.html'):
        context['current_page_name'] = pagename
        sidebarfile = self.confightml_sidebars.get(pagename, '')
        if sidebarfile:
            context['customsidebar'] = path.join(self.srcdir, sidebarfile)
        outfilename = path.join(self.outdir, os_path(pagename) + '.fpickle')
        ensuredir(path.dirname(outfilename))
        f = open(outfilename, 'wb')
        try:
            pickle.dump(context, f, 2)
        finally:
            f.close()

        # if there is a source file, copy the source file for the "show source" link
        if context.get('sourcename'):
            source_name = path.join(self.outdir, 'sources',
                                    os_path(context['sourcename']))
            ensuredir(path.dirname(source_name))
            shutil.copyfile(path.join(self.srcdir, os_path(pagename)+'.rst'), source_name)

    def handle_finish(self):
        # dump the global context
        outfilename = path.join(self.outdir, 'globalcontext.pickle')
        f = open(outfilename, 'wb')
        try:
            pickle.dump(self.globalcontext, f, 2)
        finally:
            f.close()

        self.msg('dumping search index...')
        self.indexer.prune(self.env.all_files)
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
        self.filenames = []
        self.document_data = map(list, self.config.latex_documents)

        # assign subdirs to titles
        self.titles = []
        for entry in self.document_data:
            # replace version with real version
            sourcename = entry[0]
            if sourcename.endswith('/index.rst'):
                sourcename = sourcename[:-9]
            self.titles.append((sourcename, entry[2]))

    def get_outdated_files(self):
        return 'all documents' # for now

    def get_target_uri(self, source_filename, typ=None):
        if typ == 'token':
            # token references are always inside production lists and must be
            # replaced by \token{} in LaTeX
            return '@token'
        if source_filename not in self.filenames:
            raise NoUri
        else:
            return ''

    def write(self, *ignored):
        # first, assemble the "appendix" docs that are in every PDF
        appendices = []
        for fname in self.config.latex_appendices:
            appendices.append(self.env.get_doctree(fname))

        docwriter = LaTeXWriter(self)
        docsettings = OptionParser(
            defaults=self.env.settings,
            components=(docwriter,)).get_default_values()

        if not self.document_data:
            self.warn('No "latex_documents" config setting found; no documents '
                      'will be written.')

        for sourcename, targetname, title, author, docclass in self.document_data:
            destination = FileOutput(
                destination_path=path.join(self.outdir, targetname),
                encoding='utf-8')
            print "processing", targetname + "...",
            doctree = self.assemble_doctree(
                sourcename, appendices=(docclass == 'manual') and appendices or [])
            print "writing...",
            doctree.settings = docsettings
            doctree.settings.author = author
            doctree.settings.filename = sourcename
            doctree.settings.docclass = docclass
            output = docwriter.write(doctree, destination)
            print "done"

    def assemble_doctree(self, indexfile, appendices):
        self.filenames = set([indexfile, 'glossary.rst', 'about.rst',
                              'license.rst', 'copyright.rst'])
        print green(indexfile),
        def process_tree(filename, tree):
            tree = tree.deepcopy()
            for toctreenode in tree.traverse(addnodes.toctree):
                newnodes = []
                includefiles = map(str, toctreenode['includefiles'])
                for includefile in includefiles:
                    try:
                        print green(includefile),
                        subtree = process_tree(includefile,
                                               self.env.get_doctree(includefile))
                        self.filenames.add(includefile)
                    except:
                        self.warn('%s: toctree contains ref to nonexisting file %r' %
                                  (filename, includefile))
                    else:
                        newnodes.extend(subtree.children)
                toctreenode.parent.replace(toctreenode, newnodes)
            return tree
        largetree = process_tree(indexfile, self.env.get_doctree(indexfile))
        largetree.extend(appendices)
        print
        print "resolving references..."
        self.env.resolve_references(largetree, indexfile, self)
        # resolve :ref:s to distant tex files -- we can't add a cross-reference,
        # but append the document name
        for pendingnode in largetree.traverse(addnodes.pending_xref):
            filename = pendingnode['reffilename']
            sectname = pendingnode['refsectname']
            newnodes = [nodes.emphasis(sectname, sectname)]
            for subdir, title in self.titles:
                if filename.startswith(subdir):
                    newnodes.append(nodes.Text(' (in ', ' (in '))
                    newnodes.append(nodes.emphasis(title, title))
                    newnodes.append(nodes.Text(')', ')'))
                    break
            else:
                pass
            pendingnode.replace_self(newnodes)
        return largetree

    def finish(self):
        self.msg('copying TeX support files...')
        styledirname = path.join(path.dirname(__file__), 'texinputs')
        for filename in os.listdir(styledirname):
            if not filename.startswith('.'):
                shutil.copyfile(path.join(styledirname, filename),
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

    def get_outdated_files(self):
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
        self.msg('writing summary file...')
        for type, filename, lineno, module, descname, content in \
                self.env.versionchanges[version]:
            ttext = self.typemap[type]
            context = content.replace('\n', ' ')
            if descname and filename.startswith('c-api'):
                if not descname:
                    continue
                if context:
                    entry = '<b>%s</b>: <i>%s:</i> %s' % (descname, ttext, context)
                else:
                    entry = '<b>%s</b>: <i>%s</i>.' % (descname, ttext)
                apichanges.append((entry, filename, lineno))
            elif descname or module:
                if not module:
                    module = 'Builtins'
                if not descname:
                    descname = 'Module level'
                if context:
                    entry = '<b>%s</b>: <i>%s:</i> %s' % (descname, ttext, context)
                else:
                    entry = '<b>%s</b>: <i>%s</i>.' % (descname, ttext)
                libchanges.setdefault(module, []).append((entry, filename, lineno))
            else:
                if not context:
                    continue
                entry = '<i>%s:</i> %s' % (ttext.capitalize(), context)
                title = self.env.titles[filename].astext()
                otherchanges.setdefault((filename, title), []).append(
                    (entry, filename, lineno))

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

        self.msg('copying source files...')
        for filename in self.env.all_files:
            f = open(path.join(self.srcdir, os_path(filename)))
            lines = f.readlines()
            targetfn = path.join(self.outdir, 'rst', os_path(filename)) + '.html'
            ensuredir(path.dirname(targetfn))
            f = codecs.open(targetfn, 'w', 'utf8')
            try:
                text = ''.join(hl(i+1, line) for (i, line) in enumerate(lines))
                ctx = {'filename': filename, 'text': text}
                f.write(self.stemplate.render(ctx))
            finally:
                f.close()
        shutil.copyfile(path.join(path.dirname(__file__), 'style', 'default.css'),
                        path.join(self.outdir, 'default.css'))

    def hl(self, text, version):
        text = escape(text)
        for directive in ['versionchanged', 'versionadded', 'deprecated']:
            text = text.replace('.. %s:: %s' % (directive, version),
                                '<b>.. %s:: %s</b>' % (directive, version))
        return text

    def finish(self):
        pass


builders = {
    'html': StandaloneHTMLBuilder,
    'web': WebHTMLBuilder,
    'htmlhelp': HTMLHelpBuilder,
    'latex': LaTeXBuilder,
    'changes': ChangesBuilder,
}
