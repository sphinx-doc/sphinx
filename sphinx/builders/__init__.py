# -*- coding: utf-8 -*-
"""
    sphinx.builders
    ~~~~~~~~~~~~~~~

    Builder superclass for all builders.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import gettext
from os import path

from docutils import nodes

from sphinx import package_dir, locale
from sphinx.util import SEP, ENOENT, relative_uri
from sphinx.environment import BuildEnvironment
from sphinx.util.console import bold, purple, darkgreen, term_width_line

# side effect: registers roles and directives
from sphinx import roles
from sphinx import directives


ENV_PICKLE_FILENAME = 'environment.pickle'


class Builder(object):
    """
    Builds target formats from the reST sources.
    """

    # builder's name, for the -b command line options
    name = ''
    # builder's output format, or '' if no document output is produced
    format = ''

    def __init__(self, app, env=None, freshenv=False):
        self.srcdir = app.srcdir
        self.confdir = app.confdir
        self.outdir = app.outdir
        self.doctreedir = app.doctreedir
        if not path.isdir(self.doctreedir):
            os.makedirs(self.doctreedir)

        self.app = app
        self.warn = app.warn
        self.info = app.info
        self.config = app.config

        self.load_i18n()

        # images that need to be copied over (source -> dest)
        self.images = {}

        # if None, this is set in load_env()
        self.env = env
        self.freshenv = freshenv

        self.init()
        self.load_env()

    # helper methods

    def init(self):
        """
        Load necessary templates and perform initialization.  The default
        implementation does nothing.
        """
        pass

    def create_template_bridge(self):
        """
        Return the template bridge configured.
        """
        if self.config.template_bridge:
            self.templates = self.app.import_object(
                self.config.template_bridge, 'template_bridge setting')()
        else:
            from sphinx.jinja2glue import BuiltinTemplateLoader
            self.templates = BuiltinTemplateLoader()

    def get_target_uri(self, docname, typ=None):
        """
        Return the target URI for a document name (*typ* can be used to qualify
        the link characteristic for individual builders).
        """
        raise NotImplementedError

    def get_relative_uri(self, from_, to, typ=None):
        """
        Return a relative URI between two source filenames. May raise
        environment.NoUri if there's no way to return a sensible URI.
        """
        return relative_uri(self.get_target_uri(from_),
                            self.get_target_uri(to, typ))

    def get_outdated_docs(self):
        """
        Return an iterable of output files that are outdated, or a string
        describing what an update build will build.

        If the builder does not output individual files corresponding to
        source files, return a string here.  If it does, return an iterable
        of those files that need to be written.
        """
        raise NotImplementedError

    def old_status_iterator(self, iterable, summary, colorfunc=darkgreen):
        l = 0
        for item in iterable:
            if l == 0:
                self.info(bold(summary), nonl=1)
                l = 1
            self.info(colorfunc(item) + ' ', nonl=1)
            yield item
        if l == 1:
            self.info()

    # new version with progress info
    def status_iterator(self, iterable, summary, colorfunc=darkgreen, length=0):
        if length == 0:
            for item in self.old_status_iterator(iterable, summary, colorfunc):
                yield item
            return
        l = 0
        summary = bold(summary)
        for item in iterable:
            l += 1
            self.info(term_width_line('%s[%3d%%] %s' %
                                      (summary, 100*l/length,
                                       colorfunc(item))), nonl=1)
            yield item
        if l > 0:
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
                    self.warn(
                        'no matching candidate for image URI %r' % node['uri'],
                        '%s:%s' % (node.source, getattr(node, 'line', '')))
                    continue
                node['uri'] = candidate
            else:
                candidate = node['uri']
            if candidate not in self.env.images:
                # non-existing URI; let it alone
                continue
            self.images[candidate] = self.env.images[candidate][1]

    # build methods

    def load_i18n(self):
        """
        Load translated strings from the configured localedirs if
        enabled in the configuration.
        """
        self.translator = None
        if self.config.language is not None:
            self.info(bold('loading translations [%s]... ' %
                           self.config.language), nonl=True)
            # the None entry is the system's default locale path
            locale_dirs = [None, path.join(package_dir, 'locale')] + \
                [path.join(self.srcdir, x) for x in self.config.locale_dirs]
            for dir_ in locale_dirs:
                try:
                    trans = gettext.translation('sphinx', localedir=dir_,
                            languages=[self.config.language])
                    if self.translator is None:
                        self.translator = trans
                    else:
                        self.translator._catalog.update(trans._catalog)
                except Exception:
                    # Language couldn't be found in the specified path
                    pass
            if self.translator is not None:
                self.info('done')
            else:
                self.info('locale not available')
        if self.translator is None:
            self.translator = gettext.NullTranslations()
        self.translator.install(unicode=True)
        locale.init()  # translate common labels

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
                if type(err) is IOError and err.errno == ENOENT:
                    self.info('not found')
                else:
                    self.info('failed: %s' % err)
                self.env = BuildEnvironment(self.srcdir, self.doctreedir,
                                            self.config)
                self.env.find_files(self.config)
        else:
            self.env = BuildEnvironment(self.srcdir, self.doctreedir,
                                        self.config)
            self.env.find_files(self.config)
        self.env.set_warnfunc(self.warn)

    def build_all(self):
        """Build all source files."""
        self.build(None, summary='all source files', method='all')

    def build_specific(self, filenames):
        """Only rebuild as much as needed for changes in the *filenames*."""
        # bring the filenames to the canonical format, that is,
        # relative to the source directory and without source_suffix.
        dirlen = len(self.srcdir) + 1
        to_write = []
        suffix = self.config.source_suffix
        for filename in filenames:
            filename = path.normpath(path.abspath(filename))
            if not filename.startswith(self.srcdir):
                self.warn('file %r given on command line is not under the '
                          'source directory, ignoring' % filename)
                continue
            if not (path.isfile(filename) or path.isfile(filename + suffix)):
                self.warn('file %r given on command line does not exist, '
                          'ignoring' % filename)
                continue
            filename = filename[dirlen:]
            if filename.endswith(suffix):
                filename = filename[:-len(suffix)]
            filename = filename.replace(path.sep, SEP)
            to_write.append(filename)
        self.build(to_write, method='specific',
                   summary='%d source files given on command '
                   'line' % len(to_write))

    def build_update(self):
        """Only rebuild what was changed or added since last build."""
        to_build = self.get_outdated_docs()
        if isinstance(to_build, str):
            self.build(['__all__'], to_build)
        else:
            to_build = list(to_build)
            self.build(to_build,
                       summary='targets for %d source files that are '
                       'out of date' % len(to_build))

    def build(self, docnames, summary=None, method='update'):
        """
        Main build method.  First updates the environment, and then
        calls :meth:`write`.
        """
        if summary:
            self.info(bold('building [%s]: ' % self.name), nonl=1)
            self.info(summary)

        updated_docnames = set()
        # while reading, collect all warnings from docutils
        warnings = []
        self.env.set_warnfunc(lambda *args: warnings.append(args))
        self.info(bold('updating environment: '), nonl=1)
        msg, length, iterator = self.env.update(self.config, self.srcdir,
                                                self.doctreedir, self.app)
        self.info(msg)
        for docname in self.status_iterator(iterator, 'reading sources... ',
                                            purple, length):
            updated_docnames.add(docname)
            # nothing further to do, the environment has already
            # done the reading
        for warning in warnings:
            self.warn(*warning)
        self.env.set_warnfunc(self.warn)

        doccount = len(updated_docnames)
        self.info(bold('looking for now-outdated files... '), nonl=1)
        for docname in self.env.check_dependents(updated_docnames):
            updated_docnames.add(docname)
        outdated = len(updated_docnames) - doccount
        if outdated:
            self.info('%d found' % outdated)
        else:
            self.info('none found')

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

        # another indirection to support builders that don't build
        # files individually
        self.write(docnames, list(updated_docnames), method)

        # finish (write static files etc.)
        self.finish()
        status = (self.app.statuscode == 0 and 'succeeded'
                                           or 'finished with problems')
        if self.app._warncount:
            self.info(bold('build %s, %s warning%s.' %
                           (status, self.app._warncount,
                            self.app._warncount != 1 and 's' or '')))
        else:
            self.info(bold('build %s.' % status))

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
        self.env.set_warnfunc(lambda *args: warnings.append(args))
        for docname in self.status_iterator(
            sorted(docnames), 'writing output... ', darkgreen, len(docnames)):
            doctree = self.env.get_and_resolve_doctree(docname, self)
            self.write_doc(docname, doctree)
        for warning in warnings:
            self.warn(*warning)
        self.env.set_warnfunc(self.warn)

    def prepare_writing(self, docnames):
        raise NotImplementedError

    def write_doc(self, docname, doctree):
        raise NotImplementedError

    def finish(self):
        """
        Finish the building process.  The default implementation does nothing.
        """
        pass

    def cleanup(self):
        """
        Cleanup any resources.  The default implementation does nothing.
        """


BUILTIN_BUILDERS = {
    'html':      ('html', 'StandaloneHTMLBuilder'),
    'dirhtml':   ('html', 'DirectoryHTMLBuilder'),
    'pickle':    ('html', 'PickleHTMLBuilder'),
    'json':      ('html', 'JSONHTMLBuilder'),
    'web':       ('html', 'PickleHTMLBuilder'),
    'htmlhelp':  ('htmlhelp', 'HTMLHelpBuilder'),
    'qthelp':    ('qthelp', 'QtHelpBuilder'),
    'latex':     ('latex', 'LaTeXBuilder'),
    'text':      ('text', 'TextBuilder'),
    'changes':   ('changes', 'ChangesBuilder'),
    'linkcheck': ('linkcheck', 'CheckExternalLinksBuilder'),
}
