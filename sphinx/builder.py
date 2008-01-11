# -*- coding: utf-8 -*-
"""
    sphinx.builder
    ~~~~~~~~~~~~~~

    Builder classes for different output formats.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""
from __future__ import with_statement

import os
import sys
import time
import types
import codecs
import shutil
import cPickle as pickle
import cStringIO as StringIO
from os import path
from cgi import escape

from docutils.io import StringOutput, FileOutput, DocTreeInput
from docutils.core import publish_parts
from docutils.utils import new_document
from docutils.readers import doctree
from docutils.frontend import OptionParser

from .util import (get_matching_files, attrdict, status_iterator, ensuredir,
                   get_category, relative_uri, os_path, SEP)
from .htmlhelp import build_hhx
from .patchlevel import get_version_info, get_sys_version_info
from .htmlwriter import HTMLWriter
from .latexwriter import LaTeXWriter
from .environment import BuildEnvironment, NoUri
from .highlighting import pygments, highlight_block, get_stylesheet
from .util.console import bold, purple, green

from . import addnodes
# side effect: registers roles and directives
from . import roles
from . import directives

ENV_PICKLE_FILENAME = 'environment.pickle'
LAST_BUILD_FILENAME = 'last_build'

# Helper objects

class relpath_to(object):
    def __init__(self, builder, filename):
        self.baseuri = builder.get_target_uri(filename)
        self.builder = builder
    def __call__(self, otheruri, resource=False):
        if not resource:
            otheruri = self.builder.get_target_uri(otheruri)
        return relative_uri(self.baseuri, otheruri)


class collect_env_warnings(object):
    def __init__(self, builder):
        self.builder = builder
        self.warnings = []
    def __enter__(self):
        self.builder.env.set_warnfunc(self.warnings.append)
    def __exit__(self, *args):
        self.builder.env.set_warnfunc(self.builder.warn)
        for warning in self.warnings:
            self.builder.warn(warning)


class Builder(object):
    """
    Builds target formats from the reST sources.
    """

    option_spec = {}

    def __init__(self, srcdirname, outdirname, doctreedirname,
                 options, confoverrides=None, env=None,
                 status_stream=None, warning_stream=None,
                 freshenv=False):
        self.srcdir = srcdirname
        self.outdir = outdirname
        self.doctreedir = doctreedirname
        if not path.isdir(doctreedirname):
            os.mkdir(doctreedirname)
        self.freshenv = freshenv

        self.options = attrdict(options)
        self.validate_options()

        self.status_stream = status_stream or sys.stdout
        self.warning_stream = warning_stream or sys.stderr

        # probably set in load_env()
        self.env = env

        self.config = {}
        execfile(path.join(srcdirname, 'conf.py'), self.config)
        # remove potentially pickling-problematic values
        del self.config['__builtins__']
        for key, val in self.config.items():
            if isinstance(val, types.ModuleType):
                del self.config[key]
        if confoverrides:
            self.config.update(confoverrides)
        # replace version info if 'auto'
        if self.config['version'] == 'auto' or self.config['release'] == 'auto':
            try:
                version, release = get_version_info(srcdirname)
            except (IOError, OSError):
                version, release = get_sys_version_info()
                self.warn('Can\'t get version info from Include/patchlevel.h, '
                          'using version of this interpreter (%s).' % release)
            if self.config['version'] == 'auto':
                self.config['version'] = version
            if self.config['release'] == 'auto':
                self.config['release'] = release

        self.init()

    # helper methods

    def validate_options(self):
        for option in self.options:
            if option not in self.option_spec:
                raise ValueError('Got unexpected option %s' % option)
        for option in self.option_spec:
            if option not in self.options:
                self.options[option] = False

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

    def get_target_uri(self, source_filename, typ=None):
        """Return the target URI for a source filename."""
        raise NotImplementedError

    def get_relative_uri(self, from_, to, typ=None):
        """Return a relative URI between two source filenames."""
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
        with collect_env_warnings(self):
            self.msg('reading, updating environment:', nonl=1)
            iterator = self.env.update(self.config)
            self.msg(iterator.next(), nonl=1, nobold=1)
            for filename in iterator:
                if not updated_filenames:
                    self.msg('')
                updated_filenames.append(filename)
                self.msg(purple(filename), nonl=1, nobold=1)
            self.msg()

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
        with collect_env_warnings(self):
            self.msg('writing output...')
            for filename in status_iterator(sorted(filenames), green,
                                            stream=self.status_stream):
                doctree = self.env.get_and_resolve_doctree(filename, self)
                self.write_file(filename, doctree)

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
        # lazily import this, maybe other builders won't need it
        from ._jinja import Environment, FileSystemLoader

        # load templates
        self.templates = {}
        templates_path = path.join(path.dirname(__file__), 'templates')
        jinja_env = Environment(loader=FileSystemLoader(templates_path),
                                # disable traceback, more likely that something in the
                                # application is broken than in the templates
                                friendly_traceback=False)
        for fname in os.listdir(templates_path):
            if fname.endswith('.html'):
                self.templates[fname[:-5]] = jinja_env.get_template(fname)

    def render_partial(self, node):
        """Utility: Render a lone doctree node."""
        doc = new_document('foo')
        doc.append(node)
        return publish_parts(
            doc,
            source_class=DocTreeInput,
            reader=doctree.Reader(),
            writer=HTMLWriter(self),
            settings_overrides={'output_encoding': 'unicode'}
        )

    def prepare_writing(self, filenames):
        from .search import IndexBuilder
        self.indexer = IndexBuilder()
        self.load_indexer(filenames)
        self.docwriter = HTMLWriter(self)
        self.docsettings = OptionParser(
            defaults=self.env.settings,
            components=(self.docwriter,)).get_default_values()

        # format the "last updated on" string, only once is enough since it
        # typically doesn't include the time of day
        lufmt = self.config.get('html_last_updated_fmt')
        if lufmt:
            self.last_updated = time.strftime(lufmt)
        else:
            self.last_updated = None

        self.globalcontext = dict(
            last_updated = self.last_updated,
            builder = self.name,
            release = self.config['release'],
            version = self.config['version'],
            parents = [],
            len = len,
            titles = {},
        )

    def write_file(self, filename, doctree):
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
        sourcename = filename[:-4] + '.txt'
        context = dict(
            title = title,
            sourcename = sourcename,
            pathto = relpath_to(self, self.get_target_uri(filename)),
            body = self.docwriter.parts['fragment'],
            toc = self.render_partial(self.env.get_toc_for(filename))['fragment'],
            # only display a TOC if there's more than one item to show
            display_toc = (self.env.toc_num_entries[filename] > 1),
            parents = parents,
            prev = prev,
            next = next,
        )

        self.index_file(filename, doctree, title)
        self.handle_file(filename, context)

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
            current_page_name = 'genindex',
            pathto = relpath_to(self, self.get_target_uri('genindex.rst')),
        )
        self.handle_file('genindex.rst', genindexcontext, 'genindex')

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
            pl = pl.split(', ') if pl else []
            platforms.update(pl)
            if fl != mn[0].lower() and mn[0] != '_':
                modindexentries.append(['', False, 0, False,
                                        mn[0].upper(), '', [], False])
            tn = mn.partition('.')[0]
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
            current_page_name = 'modindex',
            pathto = relpath_to(self, self.get_target_uri('modindex.rst')),
        )
        self.handle_file('modindex.rst', modindexcontext, 'modindex')

        # the download page
        downloadcontext = dict(
            pathto = relpath_to(self, self.get_target_uri('download.rst')),
            current_page_name = 'download',
            download_base_url = self.config['html_download_base_url'],
        )
        self.handle_file('download.rst', downloadcontext, 'download')

        # the index page
        indexcontext = dict(
            pathto = relpath_to(self, self.get_target_uri('index.rst')),
            current_page_name = 'index',
        )
        self.handle_file('index.rst', indexcontext, 'index')

        # the search page
        searchcontext = dict(
            pathto = relpath_to(self, self.get_target_uri('search.rst')),
            current_page_name = 'search',
        )
        self.handle_file('search.rst', searchcontext, 'search')

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
            self.srcdir, '*.rst', exclude=set(self.config.get('unused_files', ()))):
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
            with open(path.join(self.outdir, 'searchindex.json'), 'r') as f:
                self.indexer.load(f, 'json')
        except (IOError, OSError):
            pass
        # delete all entries for files that will be rebuilt
        self.indexer.prune([fn[:-4] for fn in set(self.env.all_files) - set(filenames)])

    def index_file(self, filename, doctree, title):
        # only index pages with title
        if self.indexer is not None and title:
            category = get_category(filename)
            if category is not None:
                self.indexer.feed(self.get_target_uri(filename)[:-5], # strip '.html'
                                  category, title, doctree)

    def handle_file(self, filename, context, templatename='page'):
        ctx = self.globalcontext.copy()
        ctx.update(context)
        output = self.templates[templatename].render(ctx)
        outfilename = path.join(self.outdir, os_path(filename)[:-4] + '.html')
        ensuredir(path.dirname(outfilename)) # normally different from self.outdir
        try:
            with codecs.open(outfilename, 'w', 'utf-8') as fp:
                fp.write(output)
        except (IOError, OSError), err:
            self.warn("Error writing file %s: %s" % (outfilename, err))
        if self.copysource and context.get('sourcename'):
            # copy the source file for the "show source" link
            shutil.copyfile(path.join(self.srcdir, os_path(filename)),
                            path.join(self.outdir, os_path(context['sourcename'])))

    def handle_finish(self):
        self.msg('dumping search index...')
        self.indexer.prune([self.get_target_uri(fn)[:-5] for fn in self.env.all_files])
        with open(path.join(self.outdir, 'searchindex.json'), 'w') as f:
            self.indexer.dump(f, 'json')


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
            self.srcdir, '*.rst', exclude=set(self.config.get('unused_files', ()))):
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
            with open(path.join(self.outdir, 'searchindex.pickle'), 'r') as f:
                self.indexer.load(f, 'pickle')
        except (IOError, OSError):
            pass
        # delete all entries for files that will be rebuilt
        self.indexer.prune(set(self.env.all_files) - set(filenames))

    def index_file(self, filename, doctree, title):
        # only index pages with title and category
        if self.indexer is not None and title:
            category = get_category(filename)
            if category is not None:
                self.indexer.feed(filename, category, title, doctree)

    def handle_file(self, filename, context, templatename='page'):
        outfilename = path.join(self.outdir, os_path(filename)[:-4] + '.fpickle')
        ensuredir(path.dirname(outfilename))
        context.pop('pathto', None) # can't be pickled
        with file(outfilename, 'wb') as fp:
            pickle.dump(context, fp, 2)

        # if there is a source file, copy the source file for the "show source" link
        if context.get('sourcename'):
            source_name = path.join(self.outdir, 'sources',
                                    os_path(context['sourcename']))
            ensuredir(path.dirname(source_name))
            shutil.copyfile(path.join(self.srcdir, os_path(filename)), source_name)

    def handle_finish(self):
        # dump the global context
        outfilename = path.join(self.outdir, 'globalcontext.pickle')
        with file(outfilename, 'wb') as fp:
            pickle.dump(self.globalcontext, fp, 2)

        self.msg('dumping search index...')
        self.indexer.prune(self.env.all_files)
        with open(path.join(self.outdir, 'searchindex.pickle'), 'wb') as f:
            self.indexer.dump(f, 'pickle')

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

    option_spec = {
        'outname': 'Output file base name (default "pydoc")'
    }

    # don't copy the reST source
    copysource = False

    def handle_finish(self):
        build_hhx(self, self.outdir, self.options.get('outname') or 'pydoc')


class LaTeXBuilder(Builder):
    """
    Builds LaTeX output to create PDF.
    """
    name = 'latex'

    def init(self):
        self.filenames = []

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

    def get_document_data(self):
        # Python specific...
        for toplevel in ["c-api", "distutils", "documenting", "extending",
                         "install", "reference", "tutorial", "using", "library"]:
            yield (toplevel + SEP + 'index.rst', toplevel+'.tex', 'manual')
        yield ('whatsnew' + SEP + self.config['version'] + '.rst',
               'whatsnew.tex', 'howto')
        for howto in [fn for fn in self.env.all_files
                      if fn.startswith('howto'+SEP)
                         and not fn.endswith('index.rst')]:
            yield (howto, 'howto-'+howto[6:-4]+'.tex', 'howto')

    def write(self, *ignored):
        # first, assemble the "special" docs that are in every PDF
        specials = []
        for fname in ["glossary", "about", "license", "copyright"]:
            specials.append(self.env.get_doctree(fname+".rst"))

        docwriter = LaTeXWriter(self)
        docsettings = OptionParser(
            defaults=self.env.settings,
            components=(docwriter,)).get_default_values()

        for sourcename, targetname, docclass in self.get_document_data():
            destination = FileOutput(
                destination_path=path.join(self.outdir, targetname),
                encoding='utf-8')
            print "processing", targetname + "...",
            doctree = self.assemble_doctree(
                sourcename, specials=(docclass == 'manual') and specials or [])
            print "writing...",
            doctree.settings = docsettings
            doctree.settings.filename = sourcename
            doctree.settings.docclass = docclass
            output = docwriter.write(doctree, destination)
            print "done"

    def assemble_doctree(self, indexfile, specials):
        self.filenames = set([indexfile, 'glossary.rst', 'about.rst',
                              'license.rst', 'copyright.rst'])
        print green(indexfile),
        def process_tree(filename, tree):
            #tree = tree.deepcopy() XXX
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
        largetree.extend(specials)
        print
        print "resolving references..."
        # XXX problem here: :ref:s to distant tex files
        self.env.resolve_references(largetree, indexfile, self)
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
        from ._jinja import Environment, FileSystemLoader
        templates_path = path.join(path.dirname(__file__), 'templates')
        jinja_env = Environment(loader=FileSystemLoader(templates_path),
                                # disable traceback, more likely that something in the
                                # application is broken than in the templates
                                friendly_traceback=False)
        self.ftemplate = jinja_env.get_template('versionchanges_frameset.html')
        self.vtemplate = jinja_env.get_template('versionchanges.html')
        self.stemplate = jinja_env.get_template('rstsource.html')

    def get_outdated_files(self):
        return self.outdir

    typemap = {
        'versionadded': 'added',
        'versionchanged': 'changed',
        'deprecated': 'deprecated',
    }

    def write(self, *ignored):
        ver = self.config['version']
        libchanges = {}
        apichanges = []
        otherchanges = {}
        self.msg('writing summary file...')
        for type, filename, lineno, module, descname, content in \
                self.env.versionchanges[ver]:
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
            'version': ver,
            'libchanges': sorted(libchanges.iteritems()),
            'apichanges': sorted(apichanges),
            'otherchanges': sorted(otherchanges.iteritems()),
        }
        with open(path.join(self.outdir, 'index.html'), 'w') as f:
            f.write(self.ftemplate.render(ctx))
        with open(path.join(self.outdir, 'changes.html'), 'w') as f:
            f.write(self.vtemplate.render(ctx))

        hltext = ['.. versionadded:: %s' % ver,
                  '.. versionchanged:: %s' % ver,
                  '.. deprecated:: %s' % ver]

        def hl(no, line):
            line = '<a name="L%s"> </a>' % no + escape(line)
            for x in hltext:
                if x in line:
                    line = '<span class="hl">%s</span>' % line
                    break
            return line

        self.msg('copying source files...')
        for filename in self.env.all_files:
            with open(path.join(self.srcdir, os_path(filename))) as f:
                lines = f.readlines()
            targetfn = path.join(self.outdir, 'rst', os_path(filename)) + '.html'
            ensuredir(path.dirname(targetfn))
            with codecs.open(targetfn, 'w', 'utf8') as f:
                text = ''.join(hl(i+1, line) for (i, line) in enumerate(lines))
                ctx = {'filename': filename, 'text': text}
                f.write(self.stemplate.render(ctx))
        shutil.copyfile(path.join(path.dirname(__file__), 'style', 'default.css'),
                        path.join(self.outdir, 'default.css'))

    def hl(self, text, ver):
        text = escape(text)
        for directive in ['versionchanged', 'versionadded', 'deprecated']:
            text = text.replace('.. %s:: %s' % (directive, ver),
                                '<b>.. %s:: %s</b>' % (directive, ver))
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
