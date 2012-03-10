# -*- coding: utf-8 -*-
"""
    sphinx.environment
    ~~~~~~~~~~~~~~~~~~

    Global creation environment.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import os
import sys
import time
import types
import codecs
import imghdr
import string
import unicodedata
import cPickle as pickle
from os import path
from glob import glob
from itertools import izip, groupby

from docutils import nodes
from docutils.io import FileInput, NullOutput
from docutils.core import Publisher
from docutils.utils import Reporter, relative_path, new_document, \
     get_source_line
from docutils.readers import standalone
from docutils.parsers.rst import roles, directives, Parser as RSTParser
from docutils.parsers.rst.languages import en as english
from docutils.parsers.rst.directives.html import MetaBody
from docutils.writers import UnfilteredWriter
from docutils.transforms import Transform
from docutils.transforms.parts import ContentsFilter

from sphinx import addnodes
from sphinx.util import url_re, get_matching_docs, docname_join, split_into, \
     FilenameUniqDict
from sphinx.util.nodes import clean_astext, make_refnode, extract_messages, \
     WarningStream
from sphinx.util.osutil import movefile, SEP, ustrftime, find_catalog
from sphinx.util.matching import compile_matchers
from sphinx.util.pycompat import all, class_types
from sphinx.util.websupport import is_commentable
from sphinx.errors import SphinxError, ExtensionError
from sphinx.locale import _, init as init_locale
from sphinx.versioning import add_uids, merge_doctrees

fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()

orig_role_function = roles.role
orig_directive_function = directives.directive

class ElementLookupError(Exception): pass


default_settings = {
    'embed_stylesheet': False,
    'cloak_email_addresses': True,
    'pep_base_url': 'http://www.python.org/dev/peps/',
    'rfc_base_url': 'http://tools.ietf.org/html/',
    'input_encoding': 'utf-8-sig',
    'doctitle_xform': False,
    'sectsubtitle_xform': False,
    'halt_level': 5,
}

# This is increased every time an environment attribute is added
# or changed to properly invalidate pickle files.
ENV_VERSION = 41


default_substitutions = set([
    'version',
    'release',
    'today',
])

dummy_reporter = Reporter('', 4, 4)

versioning_conditions = {
    'none': False,
    'text': nodes.TextElement,
    'commentable': is_commentable,
}


class NoUri(Exception):
    """Raised by get_relative_uri if there is no URI available."""
    pass


class DefaultSubstitutions(Transform):
    """
    Replace some substitutions if they aren't defined in the document.
    """
    # run before the default Substitutions
    default_priority = 210

    def apply(self):
        config = self.document.settings.env.config
        # only handle those not otherwise defined in the document
        to_handle = default_substitutions - set(self.document.substitution_defs)
        for ref in self.document.traverse(nodes.substitution_reference):
            refname = ref['refname']
            if refname in to_handle:
                text = config[refname]
                if refname == 'today' and not text:
                    # special handling: can also specify a strftime format
                    text = ustrftime(config.today_fmt or _('%B %d, %Y'))
                ref.replace_self(nodes.Text(text, text))


class MoveModuleTargets(Transform):
    """
    Move module targets that are the first thing in a section to the section
    title.

    XXX Python specific
    """
    default_priority = 210

    def apply(self):
        for node in self.document.traverse(nodes.target):
            if not node['ids']:
                continue
            if (node.has_key('ismod') and
                node.parent.__class__ is nodes.section and
                # index 0 is the section title node
                node.parent.index(node) == 1):
                node.parent['ids'][0:0] = node['ids']
                node.parent.remove(node)


class HandleCodeBlocks(Transform):
    """
    Several code block related transformations.
    """
    default_priority = 210

    def apply(self):
        # move doctest blocks out of blockquotes
        for node in self.document.traverse(nodes.block_quote):
            if all(isinstance(child, nodes.doctest_block) for child
                     in node.children):
                node.replace_self(node.children)
        # combine successive doctest blocks
        #for node in self.document.traverse(nodes.doctest_block):
        #    if node not in node.parent.children:
        #        continue
        #    parindex = node.parent.index(node)
        #    while len(node.parent) > parindex+1 and \
        #            isinstance(node.parent[parindex+1], nodes.doctest_block):
        #        node[0] = nodes.Text(node[0] + '\n\n' +
        #                             node.parent[parindex+1][0])
        #        del node.parent[parindex+1]


class SortIds(Transform):
    """
    Sort secion IDs so that the "id[0-9]+" one comes last.
    """
    default_priority = 261

    def apply(self):
        for node in self.document.traverse(nodes.section):
            if len(node['ids']) > 1 and node['ids'][0].startswith('id'):
                node['ids'] = node['ids'][1:] + [node['ids'][0]]


class CitationReferences(Transform):
    """
    Replace citation references by pending_xref nodes before the default
    docutils transform tries to resolve them.
    """
    default_priority = 619

    def apply(self):
        for citnode in self.document.traverse(nodes.citation_reference):
            cittext = citnode.astext()
            refnode = addnodes.pending_xref(cittext, reftype='citation',
                                            reftarget=cittext, refwarn=True)
            refnode.line = citnode.line or citnode.parent.line
            refnode += nodes.Text('[' + cittext + ']')
            citnode.parent.replace(citnode, refnode)


class Locale(Transform):
    """
    Replace translatable nodes with their translated doctree.
    """
    default_priority = 0
    def apply(self):
        env = self.document.settings.env
        settings, source = self.document.settings, self.document['source']
        # XXX check if this is reliable
        assert source.startswith(env.srcdir)
        docname = path.splitext(relative_path(env.srcdir, source))[0]
        textdomain = find_catalog(docname,
                                  self.document.settings.gettext_compact)

        # fetch translations
        dirs = [path.join(env.srcdir, directory)
                for directory in env.config.locale_dirs]
        catalog, has_catalog = init_locale(dirs, env.config.language,
                                           textdomain)
        if not has_catalog:
            return

        parser = RSTParser()

        for node, msg in extract_messages(self.document):
            patch = new_document(source, settings)
            msgstr = catalog.gettext(msg)
            # XXX add marker to untranslated parts
            if not msgstr or msgstr == msg: # as-of-yet untranslated
                continue
            parser.parse(msgstr, patch)
            patch = patch[0]
            # XXX doctest and other block markup
            if not isinstance(patch, nodes.paragraph):
                continue # skip for now
            for child in patch.children: # update leaves
                child.parent = node
            node.children = patch.children


class SphinxStandaloneReader(standalone.Reader):
    """
    Add our own transforms.
    """
    transforms = [Locale, CitationReferences, DefaultSubstitutions,
                  MoveModuleTargets, HandleCodeBlocks, SortIds]

    def get_transforms(self):
        return standalone.Reader.get_transforms(self) + self.transforms


class SphinxDummyWriter(UnfilteredWriter):
    supported = ('html',)  # needed to keep "meta" nodes

    def translate(self):
        pass


class SphinxContentsFilter(ContentsFilter):
    """
    Used with BuildEnvironment.add_toc_from() to discard cross-file links
    within table-of-contents link nodes.
    """
    def visit_pending_xref(self, node):
        text = node.astext()
        self.parent.append(nodes.literal(text, text))
        raise nodes.SkipNode

    def visit_image(self, node):
        raise nodes.SkipNode


class BuildEnvironment:
    """
    The environment in which the ReST files are translated.
    Stores an inventory of cross-file targets and provides doctree
    transformations to resolve links to them.
    """

    # --------- ENVIRONMENT PERSISTENCE ----------------------------------------

    @staticmethod
    def frompickle(config, filename):
        picklefile = open(filename, 'rb')
        try:
            env = pickle.load(picklefile)
        finally:
            picklefile.close()
        if env.version != ENV_VERSION:
            raise IOError('env version not current')
        env.config.values = config.values
        return env

    def topickle(self, filename):
        # remove unpicklable attributes
        warnfunc = self._warnfunc
        self.set_warnfunc(None)
        values = self.config.values
        del self.config.values
        domains = self.domains
        del self.domains
        # first write to a temporary file, so that if dumping fails,
        # the existing environment won't be overwritten
        picklefile = open(filename + '.tmp', 'wb')
        # remove potentially pickling-problematic values from config
        for key, val in vars(self.config).items():
            if key.startswith('_') or \
                   isinstance(val, types.ModuleType) or \
                   isinstance(val, types.FunctionType) or \
                   isinstance(val, class_types):
                del self.config[key]
        try:
            pickle.dump(self, picklefile, pickle.HIGHEST_PROTOCOL)
        finally:
            picklefile.close()
        movefile(filename + '.tmp', filename)
        # reset attributes
        self.domains = domains
        self.config.values = values
        self.set_warnfunc(warnfunc)

    # --------- ENVIRONMENT INITIALIZATION -------------------------------------

    def __init__(self, srcdir, doctreedir, config):
        self.doctreedir = doctreedir
        self.srcdir = srcdir
        self.config = config

        # the method of doctree versioning; see set_versioning_method
        self.versioning_condition = None

        # the application object; only set while update() runs
        self.app = None

        # all the registered domains, set by the application
        self.domains = {}

        # the docutils settings for building
        self.settings = default_settings.copy()
        self.settings['env'] = self

        # the function to write warning messages with
        self._warnfunc = None

        # this is to invalidate old pickles
        self.version = ENV_VERSION

        # make this a set for faster testing
        self._nitpick_ignore = set(self.config.nitpick_ignore)

        # All "docnames" here are /-separated and relative and exclude
        # the source suffix.

        self.found_docs = set()     # contains all existing docnames
        self.all_docs = {}          # docname -> mtime at the time of build
                                    # contains all built docnames
        self.dependencies = {}      # docname -> set of dependent file
                                    # names, relative to documentation root
        self.reread_always = set()  # docnames to re-read unconditionally on
                                    # next build

        # File metadata
        self.metadata = {}          # docname -> dict of metadata items

        # TOC inventory
        self.titles = {}            # docname -> title node
        self.longtitles = {}        # docname -> title node; only different if
                                    # set differently with title directive
        self.tocs = {}              # docname -> table of contents nodetree
        self.toc_num_entries = {}   # docname -> number of real entries
        # used to determine when to show the TOC
        # in a sidebar (don't show if it's only one item)
        self.toc_secnumbers = {}    # docname -> dict of sectionid -> number

        self.toctree_includes = {}  # docname -> list of toctree includefiles
        self.files_to_rebuild = {}  # docname -> set of files
                                    # (containing its TOCs) to rebuild too
        self.glob_toctrees = set()  # docnames that have :glob: toctrees
        self.numbered_toctrees = set() # docnames that have :numbered: toctrees

        # domain-specific inventories, here to be pickled
        self.domaindata = {}        # domainname -> domain-specific dict

        # Other inventories
        self.citations = {}         # citation name -> docname, labelid
        self.indexentries = {}      # docname -> list of
                                    # (type, string, target, aliasname)
        self.versionchanges = {}    # version -> list of (type, docname,
                                    # lineno, module, descname, content)

        # these map absolute path -> (docnames, unique filename)
        self.images = FilenameUniqDict()
        self.dlfiles = FilenameUniqDict()

        # temporary data storage while reading a document
        self.temp_data = {}

    def set_warnfunc(self, func):
        self._warnfunc = func
        self.settings['warning_stream'] = WarningStream(func)

    def set_versioning_method(self, method):
        """This sets the doctree versioning method for this environment.

        Versioning methods are a builder property; only builders with the same
        versioning method can share the same doctree directory.  Therefore, we
        raise an exception if the user tries to use an environment with an
        incompatible versioning method.
        """
        if method not in versioning_conditions:
            raise ValueError('invalid versioning method: %r' % method)
        condition = versioning_conditions[method]
        if self.versioning_condition not in (None, condition):
            raise SphinxError('This environment is incompatible with the '
                              'selected builder, please choose another '
                              'doctree directory.')
        self.versioning_condition = condition

    def warn(self, docname, msg, lineno=None):
        # strange argument order is due to backwards compatibility
        self._warnfunc(msg, (docname, lineno))

    def warn_node(self, msg, node):
        self._warnfunc(msg, '%s:%s' % get_source_line(node))

    def clear_doc(self, docname):
        """Remove all traces of a source file in the inventory."""
        if docname in self.all_docs:
            self.all_docs.pop(docname, None)
            self.reread_always.discard(docname)
            self.metadata.pop(docname, None)
            self.dependencies.pop(docname, None)
            self.titles.pop(docname, None)
            self.longtitles.pop(docname, None)
            self.tocs.pop(docname, None)
            self.toc_secnumbers.pop(docname, None)
            self.toc_num_entries.pop(docname, None)
            self.toctree_includes.pop(docname, None)
            self.indexentries.pop(docname, None)
            self.glob_toctrees.discard(docname)
            self.numbered_toctrees.discard(docname)
            self.images.purge_doc(docname)
            self.dlfiles.purge_doc(docname)

            for subfn, fnset in self.files_to_rebuild.items():
                fnset.discard(docname)
                if not fnset:
                    del self.files_to_rebuild[subfn]
            for key, (fn, _) in self.citations.items():
                if fn == docname:
                    del self.citations[key]
            for version, changes in self.versionchanges.items():
                new = [change for change in changes if change[1] != docname]
                changes[:] = new

        for domain in self.domains.values():
            domain.clear_doc(docname)

    def doc2path(self, docname, base=True, suffix=None):
        """Return the filename for the document name.

        If *base* is True, return absolute path under self.srcdir.
        If *base* is None, return relative path to self.srcdir.
        If *base* is a path string, return absolute path under that.
        If *suffix* is not None, add it instead of config.source_suffix.
        """
        docname = docname.replace(SEP, path.sep)
        suffix = suffix or self.config.source_suffix
        if base is True:
            return path.join(self.srcdir, docname) + suffix
        elif base is None:
            return docname + suffix
        else:
            return path.join(base, docname) + suffix

    def relfn2path(self, filename, docname=None):
        """Return paths to a file referenced from a document, relative to
        documentation root and absolute.

        Absolute filenames are relative to the source dir, while relative
        filenames are relative to the dir of the containing document.
        """
        if filename.startswith('/') or filename.startswith(os.sep):
            rel_fn = filename[1:]
        else:
            docdir = path.dirname(self.doc2path(docname or self.docname,
                                                base=None))
            rel_fn = path.join(docdir, filename)
        try:
            return rel_fn, path.join(self.srcdir, rel_fn)
        except UnicodeDecodeError:
            # the source directory is a bytestring with non-ASCII characters;
            # let's try to encode the rel_fn in the file system encoding
            enc_rel_fn = rel_fn.encode(sys.getfilesystemencoding())
            return rel_fn, path.join(self.srcdir, enc_rel_fn)

    def find_files(self, config):
        """Find all source files in the source dir and put them in
        self.found_docs.
        """
        matchers = compile_matchers(
            config.exclude_patterns[:] +
            config.exclude_trees +
            [d + config.source_suffix for d in config.unused_docs] +
            ['**/' + d for d in config.exclude_dirnames] +
            ['**/_sources', '.#*']
        )
        self.found_docs = set(get_matching_docs(
            self.srcdir, config.source_suffix, exclude_matchers=matchers))

    def get_outdated_files(self, config_changed):
        """Return (added, changed, removed) sets."""
        # clear all files no longer present
        removed = set(self.all_docs) - self.found_docs

        added = set()
        changed = set()

        if config_changed:
            # config values affect e.g. substitutions
            added = self.found_docs
        else:
            for docname in self.found_docs:
                if docname not in self.all_docs:
                    added.add(docname)
                    continue
                # if the doctree file is not there, rebuild
                if not path.isfile(self.doc2path(docname, self.doctreedir,
                                                 '.doctree')):
                    changed.add(docname)
                    continue
                # check the "reread always" list
                if docname in self.reread_always:
                    changed.add(docname)
                    continue
                # check the mtime of the document
                mtime = self.all_docs[docname]
                newmtime = path.getmtime(self.doc2path(docname))
                if newmtime > mtime:
                    changed.add(docname)
                    continue
                # finally, check the mtime of dependencies
                for dep in self.dependencies.get(docname, ()):
                    try:
                        # this will do the right thing when dep is absolute too
                        deppath = path.join(self.srcdir, dep)
                        if not path.isfile(deppath):
                            changed.add(docname)
                            break
                        depmtime = path.getmtime(deppath)
                        if depmtime > mtime:
                            changed.add(docname)
                            break
                    except EnvironmentError:
                        # give it another chance
                        changed.add(docname)
                        break

        return added, changed, removed

    def update(self, config, srcdir, doctreedir, app=None):
        """(Re-)read all files new or changed since last update.

        Returns a summary, the total count of documents to reread and an
        iterator that yields docnames as it processes them.  Store all
        environment docnames in the canonical format (ie using SEP as a
        separator in place of os.path.sep).
        """
        config_changed = False
        if self.config is None:
            msg = '[new config] '
            config_changed = True
        else:
            # check if a config value was changed that affects how
            # doctrees are read
            for key, descr in config.values.iteritems():
                if descr[1] != 'env':
                    continue
                if self.config[key] != config[key]:
                    msg = '[config changed] '
                    config_changed = True
                    break
            else:
                msg = ''
            # this value is not covered by the above loop because it is handled
            # specially by the config class
            if self.config.extensions != config.extensions:
                msg = '[extensions changed] '
                config_changed = True
        # the source and doctree directories may have been relocated
        self.srcdir = srcdir
        self.doctreedir = doctreedir
        self.find_files(config)
        self.config = config

        added, changed, removed = self.get_outdated_files(config_changed)

        # allow user intervention as well
        for docs in app.emit('env-get-outdated', self, added, changed, removed):
            changed.update(set(docs) & self.found_docs)

        # if files were added or removed, all documents with globbed toctrees
        # must be reread
        if added or removed:
            # ... but not those that already were removed
            changed.update(self.glob_toctrees & self.found_docs)

        msg += '%s added, %s changed, %s removed' % (len(added), len(changed),
                                                     len(removed))

        def update_generator():
            self.app = app

            # clear all files no longer present
            for docname in removed:
                if app:
                    app.emit('env-purge-doc', self, docname)
                self.clear_doc(docname)

            # read all new and changed files
            for docname in sorted(added | changed):
                yield docname
                self.read_doc(docname, app=app)

            if config.master_doc not in self.all_docs:
                self.warn(None, 'master file %s not found' %
                          self.doc2path(config.master_doc))

            self.app = None
            if app:
                app.emit('env-updated', self)

        return msg, len(added | changed), update_generator()

    def check_dependents(self, already):
        to_rewrite = self.assign_section_numbers()
        for docname in to_rewrite:
            if docname not in already:
                yield docname

    # --------- SINGLE FILE READING --------------------------------------------

    def warn_and_replace(self, error):
        """Custom decoding error handler that warns and replaces."""
        linestart = error.object.rfind('\n', 0, error.start)
        lineend = error.object.find('\n', error.start)
        if lineend == -1: lineend = len(error.object)
        lineno = error.object.count('\n', 0, error.start) + 1
        self.warn(self.docname, 'undecodable source characters, '
                  'replacing with "?": %r' %
                  (error.object[linestart+1:error.start] + '>>>' +
                   error.object[error.start:error.end] + '<<<' +
                   error.object[error.end:lineend]), lineno)
        return (u'?', error.end)

    def lookup_domain_element(self, type, name):
        """Lookup a markup element (directive or role), given its name which can
        be a full name (with domain).
        """
        name = name.lower()
        # explicit domain given?
        if ':' in name:
            domain_name, name = name.split(':', 1)
            if domain_name in self.domains:
                domain = self.domains[domain_name]
                element = getattr(domain, type)(name)
                if element is not None:
                    return element, []
        # else look in the default domain
        else:
            def_domain = self.temp_data.get('default_domain')
            if def_domain is not None:
                element = getattr(def_domain, type)(name)
                if element is not None:
                    return element, []
        # always look in the std domain
        element = getattr(self.domains['std'], type)(name)
        if element is not None:
            return element, []
        raise ElementLookupError

    def patch_lookup_functions(self):
        """Monkey-patch directive and role dispatch, so that domain-specific
        markup takes precedence.
        """
        def directive(name, lang_module, document):
            try:
                return self.lookup_domain_element('directive', name)
            except ElementLookupError:
                return orig_directive_function(name, lang_module, document)

        def role(name, lang_module, lineno, reporter):
            try:
                return self.lookup_domain_element('role', name)
            except ElementLookupError:
                return orig_role_function(name, lang_module, lineno, reporter)

        directives.directive = directive
        roles.role = role

    def read_doc(self, docname, src_path=None, save_parsed=True, app=None):
        """Parse a file and add/update inventory entries for the doctree.

        If srcpath is given, read from a different source file.
        """
        # remove all inventory entries for that file
        if app:
            app.emit('env-purge-doc', self, docname)

        self.clear_doc(docname)

        if src_path is None:
            src_path = self.doc2path(docname)

        self.temp_data['docname'] = docname
        # defaults to the global default, but can be re-set in a document
        self.temp_data['default_domain'] = \
            self.domains.get(self.config.primary_domain)

        self.settings['input_encoding'] = self.config.source_encoding
        self.settings['trim_footnote_reference_space'] = \
            self.config.trim_footnote_reference_space
        self.settings['gettext_compact'] = self.config.gettext_compact

        self.patch_lookup_functions()

        if self.config.default_role:
            role_fn, messages = roles.role(self.config.default_role, english,
                                           0, dummy_reporter)
            if role_fn:
                roles._roles[''] = role_fn
            else:
                self.warn(docname, 'default role %s not found' %
                          self.config.default_role)

        codecs.register_error('sphinx', self.warn_and_replace)

        class SphinxSourceClass(FileInput):
            def __init__(self_, *args, **kwds):
                # don't call sys.exit() on IOErrors
                kwds['handle_io_errors'] = False
                FileInput.__init__(self_, *args, **kwds)

            def decode(self_, data):
                if isinstance(data, unicode):
                    return data
                return data.decode(self_.encoding, 'sphinx')

            def read(self_):
                data = FileInput.read(self_)
                if app:
                    arg = [data]
                    app.emit('source-read', docname, arg)
                    data = arg[0]
                if self.config.rst_epilog:
                    data = data + '\n' + self.config.rst_epilog + '\n'
                if self.config.rst_prolog:
                    data = self.config.rst_prolog + '\n' + data
                return data

        # publish manually
        pub = Publisher(reader=SphinxStandaloneReader(),
                        writer=SphinxDummyWriter(),
                        source_class=SphinxSourceClass,
                        destination_class=NullOutput)
        pub.set_components(None, 'restructuredtext', None)
        pub.process_programmatic_settings(None, self.settings, None)
        pub.set_source(None, src_path.encode(fs_encoding))
        pub.set_destination(None, None)
        try:
            pub.publish()
            doctree = pub.document
        except UnicodeError, err:
            raise SphinxError(str(err))

        # post-processing
        self.filter_messages(doctree)
        self.process_dependencies(docname, doctree)
        self.process_images(docname, doctree)
        self.process_downloads(docname, doctree)
        self.process_metadata(docname, doctree)
        self.process_refonly_bullet_lists(docname, doctree)
        self.create_title_from(docname, doctree)
        self.note_indexentries_from(docname, doctree)
        self.note_citations_from(docname, doctree)
        self.build_toc_from(docname, doctree)
        for domain in self.domains.itervalues():
            domain.process_doc(self, docname, doctree)

        # allow extension-specific post-processing
        if app:
            app.emit('doctree-read', doctree)

        # store time of build, for outdated files detection
        self.all_docs[docname] = time.time()

        if self.versioning_condition:
            # get old doctree
            try:
                f = open(self.doc2path(docname,
                                       self.doctreedir, '.doctree'), 'rb')
                try:
                    old_doctree = pickle.load(f)
                finally:
                    f.close()
            except EnvironmentError:
                old_doctree = None

            # add uids for versioning
            if old_doctree is None:
                list(add_uids(doctree, self.versioning_condition))
            else:
                list(merge_doctrees(
                    old_doctree, doctree, self.versioning_condition))

        # make it picklable
        doctree.reporter = None
        doctree.transformer = None
        doctree.settings.warning_stream = None
        doctree.settings.env = None
        doctree.settings.record_dependencies = None
        for metanode in doctree.traverse(MetaBody.meta):
            # docutils' meta nodes aren't picklable because the class is nested
            metanode.__class__ = addnodes.meta

        # cleanup
        self.temp_data.clear()

        if save_parsed:
            # save the parsed doctree
            doctree_filename = self.doc2path(docname, self.doctreedir,
                                             '.doctree')
            dirname = path.dirname(doctree_filename)
            if not path.isdir(dirname):
                os.makedirs(dirname)
            f = open(doctree_filename, 'wb')
            try:
                pickle.dump(doctree, f, pickle.HIGHEST_PROTOCOL)
            finally:
                f.close()
        else:
            return doctree

    # utilities to use while reading a document

    @property
    def docname(self):
        """Backwards compatible alias."""
        return self.temp_data['docname']

    @property
    def currmodule(self):
        """Backwards compatible alias."""
        return self.temp_data.get('py:module')

    @property
    def currclass(self):
        """Backwards compatible alias."""
        return self.temp_data.get('py:class')

    def new_serialno(self, category=''):
        """Return a serial number, e.g. for index entry targets."""
        key = category + 'serialno'
        cur = self.temp_data.get(key, 0)
        self.temp_data[key] = cur + 1
        return cur

    def note_dependency(self, filename):
        self.dependencies.setdefault(self.docname, set()).add(filename)

    def note_reread(self):
        self.reread_always.add(self.docname)

    def note_versionchange(self, type, version, node, lineno):
        self.versionchanges.setdefault(version, []).append(
            (type, self.temp_data['docname'], lineno,
             self.temp_data.get('py:module'),
             self.temp_data.get('object'), node.astext()))

    # post-processing of read doctrees

    def filter_messages(self, doctree):
        """Filter system messages from a doctree."""
        filterlevel = self.config.keep_warnings and 2 or 5
        for node in doctree.traverse(nodes.system_message):
            if node['level'] < filterlevel:
                node.parent.remove(node)


    def process_dependencies(self, docname, doctree):
        """Process docutils-generated dependency info."""
        cwd = os.getcwd()
        frompath = path.join(path.normpath(self.srcdir), 'dummy')
        deps = doctree.settings.record_dependencies
        if not deps:
            return
        for dep in deps.list:
            # the dependency path is relative to the working dir, so get
            # one relative to the srcdir
            relpath = relative_path(frompath,
                                    path.normpath(path.join(cwd, dep)))
            self.dependencies.setdefault(docname, set()).add(relpath)

    def process_downloads(self, docname, doctree):
        """Process downloadable file paths. """
        for node in doctree.traverse(addnodes.download_reference):
            targetname = node['reftarget']
            rel_filename, filename = self.relfn2path(targetname, docname)
            self.dependencies.setdefault(docname, set()).add(rel_filename)
            if not os.access(filename, os.R_OK):
                self.warn_node('download file not readable: %s' % filename,
                               node)
                continue
            uniquename = self.dlfiles.add_file(docname, filename)
            node['filename'] = uniquename

    def process_images(self, docname, doctree):
        """Process and rewrite image URIs."""
        for node in doctree.traverse(nodes.image):
            # Map the mimetype to the corresponding image.  The writer may
            # choose the best image from these candidates.  The special key * is
            # set if there is only single candidate to be used by a writer.
            # The special key ? is set for nonlocal URIs.
            node['candidates'] = candidates = {}
            imguri = node['uri']
            if imguri.find('://') != -1:
                self.warn_node('nonlocal image URI found: %s' % imguri, node)
                candidates['?'] = imguri
                continue
            rel_imgpath, full_imgpath = self.relfn2path(imguri, docname)
            # set imgpath as default URI
            node['uri'] = rel_imgpath
            if rel_imgpath.endswith(os.extsep + '*'):
                for filename in glob(full_imgpath):
                    new_imgpath = relative_path(self.srcdir, filename)
                    if filename.lower().endswith('.pdf'):
                        candidates['application/pdf'] = new_imgpath
                    elif filename.lower().endswith('.svg'):
                        candidates['image/svg+xml'] = new_imgpath
                    else:
                        try:
                            f = open(filename, 'rb')
                            try:
                                imgtype = imghdr.what(f)
                            finally:
                                f.close()
                        except (OSError, IOError), err:
                            self.warn_node('image file %s not readable: %s' %
                                           (filename, err), node)
                        if imgtype:
                            candidates['image/' + imgtype] = new_imgpath
            else:
                candidates['*'] = rel_imgpath
            # map image paths to unique image names (so that they can be put
            # into a single directory)
            for imgpath in candidates.itervalues():
                self.dependencies.setdefault(docname, set()).add(imgpath)
                if not os.access(path.join(self.srcdir, imgpath), os.R_OK):
                    self.warn_node('image file not readable: %s' % imgpath,
                                   node)
                    continue
                self.images.add_file(docname, imgpath)

    def process_metadata(self, docname, doctree):
        """Process the docinfo part of the doctree as metadata.

        Keep processing minimal -- just return what docutils says.
        """
        self.metadata[docname] = md = {}
        try:
            docinfo = doctree[0]
        except IndexError:
            # probably an empty document
            return
        if docinfo.__class__ is not nodes.docinfo:
            # nothing to see here
            return
        for node in docinfo:
            # nodes are multiply inherited...
            if isinstance(node, nodes.authors):
                md['authors'] = [author.astext() for author in node]
            elif isinstance(node, nodes.TextElement): # e.g. author
                md[node.__class__.__name__] = node.astext()
            else:
                name, body = node
                md[name.astext()] = body.astext()
        del doctree[0]

    def process_refonly_bullet_lists(self, docname, doctree):
        """Change refonly bullet lists to use compact_paragraphs.

        Specifically implemented for 'Indices and Tables' section, which looks
        odd when html_compact_lists is false.
        """
        if self.config.html_compact_lists:
            return

        class RefOnlyListChecker(nodes.GenericNodeVisitor):
            """Raise `nodes.NodeFound` if non-simple list item is encountered.

            Here 'simple' means a list item containing only a paragraph with a
            single reference in it.
            """

            def default_visit(self, node):
                raise nodes.NodeFound

            def visit_bullet_list(self, node):
                pass

            def visit_list_item(self, node):
                children = []
                for child in node.children:
                    if not isinstance(child, nodes.Invisible):
                        children.append(child)
                if len(children) != 1:
                    raise nodes.NodeFound
                if not isinstance(children[0], nodes.paragraph):
                    raise nodes.NodeFound
                para = children[0]
                if len(para) != 1:
                    raise nodes.NodeFound
                if not isinstance(para[0], addnodes.pending_xref):
                    raise nodes.NodeFound
                raise nodes.SkipChildren

            def invisible_visit(self, node):
                """Invisible nodes should be ignored."""
                pass

        def check_refonly_list(node):
            """Check for list with only references in it."""
            visitor = RefOnlyListChecker(doctree)
            try:
                node.walk(visitor)
            except nodes.NodeFound:
                return False
            else:
                return True

        for node in doctree.traverse(nodes.bullet_list):
            if check_refonly_list(node):
                for item in node.traverse(nodes.list_item):
                    para = item[0]
                    ref = para[0]
                    compact_para = addnodes.compact_paragraph()
                    compact_para += ref
                    item.replace(para, compact_para)

    def create_title_from(self, docname, document):
        """Add a title node to the document (just copy the first section title),
        and store that title in the environment.
        """
        titlenode = nodes.title()
        longtitlenode = titlenode
        # explicit title set with title directive; use this only for
        # the <title> tag in HTML output
        if document.has_key('title'):
            longtitlenode = nodes.title()
            longtitlenode += nodes.Text(document['title'])
        # look for first section title and use that as the title
        for node in document.traverse(nodes.section):
            visitor = SphinxContentsFilter(document)
            node[0].walkabout(visitor)
            titlenode += visitor.get_entry_text()
            break
        else:
            # document has no title
            titlenode += nodes.Text('<no title>')
        self.titles[docname] = titlenode
        self.longtitles[docname] = longtitlenode

    def note_indexentries_from(self, docname, document):
        entries = self.indexentries[docname] = []
        for node in document.traverse(addnodes.index):
            entries.extend(node['entries'])

    def note_citations_from(self, docname, document):
        for node in document.traverse(nodes.citation):
            label = node[0].astext()
            if label in self.citations:
                self.warn_node('duplicate citation %s, ' % label +
                               'other instance in %s' % self.doc2path(
                                   self.citations[label][0]), node)
            self.citations[label] = (docname, node['ids'][0])

    def note_toctree(self, docname, toctreenode):
        """Note a TOC tree directive in a document and gather information about
        file relations from it.
        """
        if toctreenode['glob']:
            self.glob_toctrees.add(docname)
        if toctreenode.get('numbered'):
            self.numbered_toctrees.add(docname)
        includefiles = toctreenode['includefiles']
        for includefile in includefiles:
            # note that if the included file is rebuilt, this one must be
            # too (since the TOC of the included file could have changed)
            self.files_to_rebuild.setdefault(includefile, set()).add(docname)
        self.toctree_includes.setdefault(docname, []).extend(includefiles)

    def build_toc_from(self, docname, document):
        """Build a TOC from the doctree and store it in the inventory."""
        numentries = [0] # nonlocal again...

        try:
            maxdepth = int(self.metadata[docname].get('tocdepth', 0))
        except ValueError:
            maxdepth = 0

        def traverse_in_section(node, cls):
            """Like traverse(), but stay within the same section."""
            result = []
            if isinstance(node, cls):
                result.append(node)
            for child in node.children:
                if isinstance(child, nodes.section):
                    continue
                result.extend(traverse_in_section(child, cls))
            return result

        def build_toc(node, depth=1):
            entries = []
            for sectionnode in node:
                # find all toctree nodes in this section and add them
                # to the toc (just copying the toctree node which is then
                # resolved in self.get_and_resolve_doctree)
                if isinstance(sectionnode, addnodes.only):
                    onlynode = addnodes.only(expr=sectionnode['expr'])
                    blist = build_toc(sectionnode, depth)
                    if blist:
                        onlynode += blist.children
                        entries.append(onlynode)
                if not isinstance(sectionnode, nodes.section):
                    for toctreenode in traverse_in_section(sectionnode,
                                                           addnodes.toctree):
                        item = toctreenode.copy()
                        entries.append(item)
                        # important: do the inventory stuff
                        self.note_toctree(docname, toctreenode)
                    continue
                title = sectionnode[0]
                # copy the contents of the section title, but without references
                # and unnecessary stuff
                visitor = SphinxContentsFilter(document)
                title.walkabout(visitor)
                nodetext = visitor.get_entry_text()
                if not numentries[0]:
                    # for the very first toc entry, don't add an anchor
                    # as it is the file's title anyway
                    anchorname = ''
                else:
                    anchorname = '#' + sectionnode['ids'][0]
                numentries[0] += 1
                # make these nodes:
                # list_item -> compact_paragraph -> reference
                reference = nodes.reference(
                    '', '', internal=True, refuri=docname,
                    anchorname=anchorname, *nodetext)
                para = addnodes.compact_paragraph('', '', reference)
                item = nodes.list_item('', para)
                if maxdepth == 0 or depth < maxdepth:
                    item += build_toc(sectionnode, depth+1)
                entries.append(item)
            if entries:
                return nodes.bullet_list('', *entries)
            return []
        toc = build_toc(document)
        if toc:
            self.tocs[docname] = toc
        else:
            self.tocs[docname] = nodes.bullet_list('')
        self.toc_num_entries[docname] = numentries[0]

    def get_toc_for(self, docname, builder):
        """Return a TOC nodetree -- for use on the same page only!"""
        try:
            toc = self.tocs[docname].deepcopy()
        except KeyError:
            # the document does not exist anymore: return a dummy node that
            # renders to nothing
            return nodes.paragraph()
        self.process_only_nodes(toc, builder, docname)
        for node in toc.traverse(nodes.reference):
            node['refuri'] = node['anchorname'] or '#'
        return toc

    def get_toctree_for(self, docname, builder, collapse, **kwds):
        """Return the global TOC nodetree."""
        doctree = self.get_doctree(self.config.master_doc)
        toctrees = []
        if 'includehidden' not in kwds:
            kwds['includehidden'] = True
        if 'maxdepth' not in kwds:
            kwds['maxdepth'] = 0
        kwds['collapse'] = collapse
        for toctreenode in doctree.traverse(addnodes.toctree):
            toctree = self.resolve_toctree(docname, builder, toctreenode,
                                           prune=True, **kwds)
            toctrees.append(toctree)
        if not toctrees:
            return None
        result = toctrees[0]
        for toctree in toctrees[1:]:
            result.extend(toctree.children)
        return result

    def get_domain(self, domainname):
        """Return the domain instance with the specified name.

        Raises an ExtensionError if the domain is not registered.
        """
        try:
            return self.domains[domainname]
        except KeyError:
            raise ExtensionError('Domain %r is not registered' % domainname)

    # --------- RESOLVING REFERENCES AND TOCTREES ------------------------------

    def get_doctree(self, docname):
        """Read the doctree for a file from the pickle and return it."""
        doctree_filename = self.doc2path(docname, self.doctreedir, '.doctree')
        f = open(doctree_filename, 'rb')
        try:
            doctree = pickle.load(f)
        finally:
            f.close()
        doctree.settings.env = self
        doctree.reporter = Reporter(self.doc2path(docname), 2, 5,
                                    stream=WarningStream(self._warnfunc))
        return doctree


    def get_and_resolve_doctree(self, docname, builder, doctree=None,
                                prune_toctrees=True):
        """Read the doctree from the pickle, resolve cross-references and
        toctrees and return it.
        """
        if doctree is None:
            doctree = self.get_doctree(docname)

        # resolve all pending cross-references
        self.resolve_references(doctree, docname, builder)

        # now, resolve all toctree nodes
        for toctreenode in doctree.traverse(addnodes.toctree):
            result = self.resolve_toctree(docname, builder, toctreenode,
                                          prune=prune_toctrees)
            if result is None:
                toctreenode.replace_self([])
            else:
                toctreenode.replace_self(result)

        return doctree

    def resolve_toctree(self, docname, builder, toctree, prune=True, maxdepth=0,
                        titles_only=False, collapse=False, includehidden=False):
        """Resolve a *toctree* node into individual bullet lists with titles
        as items, returning None (if no containing titles are found) or
        a new node.

        If *prune* is True, the tree is pruned to *maxdepth*, or if that is 0,
        to the value of the *maxdepth* option on the *toctree* node.
        If *titles_only* is True, only toplevel document titles will be in the
        resulting tree.
        If *collapse* is True, all branches not containing docname will
        be collapsed.
        """
        if toctree.get('hidden', False) and not includehidden:
            return None

        def _walk_depth(node, depth, maxdepth):
            """Utility: Cut a TOC at a specified depth."""

            # For reading this function, it is useful to keep in mind the node
            # structure of a toctree (using HTML-like node names for brevity):
            #
            # <ul>
            #   <li>
            #     <p><a></p>
            #     <p><a></p>
            #     ...
            #     <ul>
            #       ...
            #     </ul>
            #   </li>
            # </ul>

            for subnode in node.children[:]:
                if isinstance(subnode, (addnodes.compact_paragraph,
                                        nodes.list_item)):
                    # for <p> and <li>, just indicate the depth level and
                    # recurse to children
                    subnode['classes'].append('toctree-l%d' % (depth-1))
                    _walk_depth(subnode, depth, maxdepth)

                elif isinstance(subnode, nodes.bullet_list):
                    # for <ul>, determine if the depth is too large or if the
                    # entry is to be collapsed
                    if maxdepth > 0 and depth > maxdepth:
                        subnode.parent.replace(subnode, [])
                    else:
                        # to find out what to collapse, *first* walk subitems,
                        # since that determines which children point to the
                        # current page
                        _walk_depth(subnode, depth+1, maxdepth)
                        # cull sub-entries whose parents aren't 'current'
                        if (collapse and depth > 1 and
                            'iscurrent' not in subnode.parent):
                            subnode.parent.remove(subnode)

                elif isinstance(subnode, nodes.reference):
                    # for <a>, identify which entries point to the current
                    # document and therefore may not be collapsed
                    if subnode['refuri'] == docname:
                        if not subnode['anchorname']:
                            # give the whole branch a 'current' class
                            # (useful for styling it differently)
                            branchnode = subnode
                            while branchnode:
                                branchnode['classes'].append('current')
                                branchnode = branchnode.parent
                        # mark the list_item as "on current page"
                        if subnode.parent.parent.get('iscurrent'):
                            # but only if it's not already done
                            return
                        while subnode:
                            subnode['iscurrent'] = True
                            subnode = subnode.parent

        def _entries_from_toctree(toctreenode, parents,
                                  separate=False, subtree=False):
            """Return TOC entries for a toctree node."""
            refs = [(e[0], str(e[1])) for e in toctreenode['entries']]
            entries = []
            for (title, ref) in refs:
                try:
                    refdoc = None
                    if url_re.match(ref):
                        reference = nodes.reference('', '', internal=False,
                                                    refuri=ref, anchorname='',
                                                    *[nodes.Text(title)])
                        para = addnodes.compact_paragraph('', '', reference)
                        item = nodes.list_item('', para)
                        toc = nodes.bullet_list('', item)
                    elif ref == 'self':
                        # 'self' refers to the document from which this
                        # toctree originates
                        ref = toctreenode['parent']
                        if not title:
                            title = clean_astext(self.titles[ref])
                        reference = nodes.reference('', '', internal=True,
                                                    refuri=ref,
                                                    anchorname='',
                                                    *[nodes.Text(title)])
                        para = addnodes.compact_paragraph('', '', reference)
                        item = nodes.list_item('', para)
                        # don't show subitems
                        toc = nodes.bullet_list('', item)
                    else:
                        if ref in parents:
                            self.warn(ref, 'circular toctree references '
                                      'detected, ignoring: %s <- %s' %
                                      (ref, ' <- '.join(parents)))
                            continue
                        refdoc = ref
                        toc = self.tocs[ref].deepcopy()
                        self.process_only_nodes(toc, builder, ref)
                        if title and toc.children and len(toc.children) == 1:
                            child = toc.children[0]
                            for refnode in child.traverse(nodes.reference):
                                if refnode['refuri'] == ref and \
                                       not refnode['anchorname']:
                                    refnode.children = [nodes.Text(title)]
                    if not toc.children:
                        # empty toc means: no titles will show up in the toctree
                        self.warn_node(
                            'toctree contains reference to document %r that '
                            'doesn\'t have a title: no link will be generated'
                            % ref, toctreenode)
                except KeyError:
                    # this is raised if the included file does not exist
                    self.warn_node(
                        'toctree contains reference to nonexisting document %r'
                        % ref, toctreenode)
                else:
                    # if titles_only is given, only keep the main title and
                    # sub-toctrees
                    if titles_only:
                        # delete everything but the toplevel title(s)
                        # and toctrees
                        for toplevel in toc:
                            # nodes with length 1 don't have any children anyway
                            if len(toplevel) > 1:
                                subtrees = toplevel.traverse(addnodes.toctree)
                                toplevel[1][:] = subtrees
                    # resolve all sub-toctrees
                    for toctreenode in toc.traverse(addnodes.toctree):
                        if not (toctreenode.get('hidden', False)
                                and not includehidden):
                            i = toctreenode.parent.index(toctreenode) + 1
                            for item in _entries_from_toctree(
                                    toctreenode, [refdoc] + parents,
                                    subtree=True):
                                toctreenode.parent.insert(i, item)
                                i += 1
                            toctreenode.parent.remove(toctreenode)
                    if separate:
                        entries.append(toc)
                    else:
                        entries.extend(toc.children)
            if not subtree and not separate:
                ret = nodes.bullet_list()
                ret += entries
                return [ret]
            return entries

        maxdepth = maxdepth or toctree.get('maxdepth', -1)
        if not titles_only and toctree.get('titlesonly', False):
            titles_only = True

        # NOTE: previously, this was separate=True, but that leads to artificial
        # separation when two or more toctree entries form a logical unit, so
        # separating mode is no longer used -- it's kept here for history's sake
        tocentries = _entries_from_toctree(toctree, [], separate=False)
        if not tocentries:
            return None

        newnode = addnodes.compact_paragraph('', '', *tocentries)
        newnode['toctree'] = True

        # prune the tree to maxdepth and replace titles, also set level classes
        _walk_depth(newnode, 1, prune and maxdepth or 0)

        # set the target paths in the toctrees (they are not known at TOC
        # generation time)
        for refnode in newnode.traverse(nodes.reference):
            if not url_re.match(refnode['refuri']):
                refnode['refuri'] = builder.get_relative_uri(
                    docname, refnode['refuri']) + refnode['anchorname']
        return newnode

    def resolve_references(self, doctree, fromdocname, builder):
        for node in doctree.traverse(addnodes.pending_xref):
            contnode = node[0].deepcopy()
            newnode = None

            typ = node['reftype']
            target = node['reftarget']
            refdoc = node.get('refdoc', fromdocname)
            domain = None

            try:
                if 'refdomain' in node and node['refdomain']:
                    # let the domain try to resolve the reference
                    try:
                        domain = self.domains[node['refdomain']]
                    except KeyError:
                        raise NoUri
                    newnode = domain.resolve_xref(self, fromdocname, builder,
                                                  typ, target, node, contnode)
                # really hardwired reference types
                elif typ == 'doc':
                    # directly reference to document by source name;
                    # can be absolute or relative
                    docname = docname_join(refdoc, target)
                    if docname in self.all_docs:
                        if node['refexplicit']:
                            # reference with explicit title
                            caption = node.astext()
                        else:
                            caption = clean_astext(self.titles[docname])
                        innernode = nodes.emphasis(caption, caption)
                        newnode = nodes.reference('', '', internal=True)
                        newnode['refuri'] = builder.get_relative_uri(
                            fromdocname, docname)
                        newnode.append(innernode)
                elif typ == 'citation':
                    docname, labelid = self.citations.get(target, ('', ''))
                    if docname:
                        newnode = make_refnode(builder, fromdocname, docname,
                                               labelid, contnode)
                # no new node found? try the missing-reference event
                if newnode is None:
                    newnode = builder.app.emit_firstresult(
                        'missing-reference', self, node, contnode)
                    # still not found? warn if in nit-picky mode
                    if newnode is None:
                        self._warn_missing_reference(
                            fromdocname, typ, target, node, domain)
            except NoUri:
                newnode = contnode
            node.replace_self(newnode or contnode)

        # remove only-nodes that do not belong to our builder
        self.process_only_nodes(doctree, builder, fromdocname)

        # allow custom references to be resolved
        builder.app.emit('doctree-resolved', doctree, fromdocname)

    def _warn_missing_reference(self, fromdoc, typ, target, node, domain):
        warn = node.get('refwarn')
        if self.config.nitpicky:
            warn = True
            if self._nitpick_ignore:
                dtype = domain and '%s:%s' % (domain.name, typ) or typ
                if (dtype, target) in self._nitpick_ignore:
                    warn = False
        if not warn:
            return
        if domain and typ in domain.dangling_warnings:
            msg = domain.dangling_warnings[typ]
        elif typ == 'doc':
            msg = 'unknown document: %(target)s'
        elif typ == 'citation':
            msg = 'citation not found: %(target)s'
        elif node.get('refdomain', 'std') != 'std':
            msg = '%s:%s reference target not found: %%(target)s' % \
                  (node['refdomain'], typ)
        else:
            msg = '%s reference target not found: %%(target)s' % typ
        self.warn_node(msg % {'target': target}, node)

    def process_only_nodes(self, doctree, builder, fromdocname=None):
        # A comment on the comment() nodes being inserted: replacing by [] would
        # result in a "Losing ids" exception if there is a target node before
        # the only node, so we make sure docutils can transfer the id to
        # something, even if it's just a comment and will lose the id anyway...
        for node in doctree.traverse(addnodes.only):
            try:
                ret = builder.tags.eval_condition(node['expr'])
            except Exception, err:
                self.warn_node('exception while evaluating only '
                               'directive expression: %s' % err, node)
                node.replace_self(node.children or nodes.comment())
            else:
                if ret:
                    node.replace_self(node.children or nodes.comment())
                else:
                    node.replace_self(nodes.comment())

    def assign_section_numbers(self):
        """Assign a section number to each heading under a numbered toctree."""
        # a list of all docnames whose section numbers changed
        rewrite_needed = []

        old_secnumbers = self.toc_secnumbers
        self.toc_secnumbers = {}

        def _walk_toc(node, secnums, depth, titlenode=None):
            # titlenode is the title of the document, it will get assigned a
            # secnumber too, so that it shows up in next/prev/parent rellinks
            for subnode in node.children:
                if isinstance(subnode, nodes.bullet_list):
                    numstack.append(0)
                    _walk_toc(subnode, secnums, depth-1, titlenode)
                    numstack.pop()
                    titlenode = None
                elif isinstance(subnode, nodes.list_item):
                    _walk_toc(subnode, secnums, depth, titlenode)
                    titlenode = None
                elif isinstance(subnode, addnodes.only):
                    # at this stage we don't know yet which sections are going
                    # to be included; just include all of them, even if it leads
                    # to gaps in the numbering
                    _walk_toc(subnode, secnums, depth, titlenode)
                    titlenode = None
                elif isinstance(subnode, addnodes.compact_paragraph):
                    numstack[-1] += 1
                    if depth > 0:
                        number = tuple(numstack)
                    else:
                        number = None
                    secnums[subnode[0]['anchorname']] = \
                        subnode[0]['secnumber'] = number
                    if titlenode:
                        titlenode['secnumber'] = number
                        titlenode = None
                elif isinstance(subnode, addnodes.toctree):
                    _walk_toctree(subnode, depth)

        def _walk_toctree(toctreenode, depth):
            if depth == 0:
                return
            for (title, ref) in toctreenode['entries']:
                if url_re.match(ref) or ref == 'self':
                    # don't mess with those
                    continue
                if ref in self.tocs:
                    secnums = self.toc_secnumbers[ref] = {}
                    _walk_toc(self.tocs[ref], secnums, depth,
                              self.titles.get(ref))
                    if secnums != old_secnumbers.get(ref):
                        rewrite_needed.append(ref)

        for docname in self.numbered_toctrees:
            doctree = self.get_doctree(docname)
            for toctreenode in doctree.traverse(addnodes.toctree):
                depth = toctreenode.get('numbered', 0)
                if depth:
                    # every numbered toctree gets new numbering
                    numstack = [0]
                    _walk_toctree(toctreenode, depth)

        return rewrite_needed

    def create_index(self, builder, group_entries=True,
                     _fixre=re.compile(r'(.*) ([(][^()]*[)])')):
        """Create the real index from the collected index entries."""
        new = {}

        def add_entry(word, subword, link=True, dic=new):
            entry = dic.get(word)
            if not entry:
                dic[word] = entry = [[], {}]
            if subword:
                add_entry(subword, '', link=link, dic=entry[1])
            elif link:
                try:
                    uri = builder.get_relative_uri('genindex', fn) + '#' + tid
                except NoUri:
                    pass
                else:
                    entry[0].append((main, uri))

        for fn, entries in self.indexentries.iteritems():
            # new entry types must be listed in directives/other.py!
            for type, value, tid, main in entries:
                try:
                    if type == 'single':
                        try:
                            entry, subentry = split_into(2, 'single', value)
                        except ValueError:
                            entry, = split_into(1, 'single', value)
                            subentry = ''
                        add_entry(entry, subentry)
                    elif type == 'pair':
                        first, second = split_into(2, 'pair', value)
                        add_entry(first, second)
                        add_entry(second, first)
                    elif type == 'triple':
                        first, second, third = split_into(3, 'triple', value)
                        add_entry(first, second+' '+third)
                        add_entry(second, third+', '+first)
                        add_entry(third, first+' '+second)
                    elif type == 'see':
                        first, second = split_into(2, 'see', value)
                        add_entry(first, _('see %s') % second, link=False)
                    elif type == 'seealso':
                        first, second = split_into(2, 'see', value)
                        add_entry(first, _('see also %s') % second, link=False)
                    else:
                        self.warn(fn, 'unknown index entry type %r' % type)
                except ValueError, err:
                    self.warn(fn, str(err))

        # sort the index entries; put all symbols at the front, even those
        # following the letters in ASCII, this is where the chr(127) comes from
        def keyfunc(entry, lcletters=string.ascii_lowercase + '_'):
            lckey = unicodedata.normalize('NFD', entry[0].lower())
            if lckey[0:1] in lcletters:
                return chr(127) + lckey
            return lckey
        newlist = new.items()
        newlist.sort(key=keyfunc)

        if group_entries:
            # fixup entries: transform
            #   func() (in module foo)
            #   func() (in module bar)
            # into
            #   func()
            #     (in module foo)
            #     (in module bar)
            oldkey = ''
            oldsubitems = None
            i = 0
            while i < len(newlist):
                key, (targets, subitems) = newlist[i]
                # cannot move if it has subitems; structure gets too complex
                if not subitems:
                    m = _fixre.match(key)
                    if m:
                        if oldkey == m.group(1):
                            # prefixes match: add entry as subitem of the
                            # previous entry
                            oldsubitems.setdefault(m.group(2), [[], {}])[0].\
                                        extend(targets)
                            del newlist[i]
                            continue
                        oldkey = m.group(1)
                    else:
                        oldkey = key
                oldsubitems = subitems
                i += 1

        # group the entries by letter
        def keyfunc2(item, letters=string.ascii_uppercase + '_'):
            # hack: mutating the subitems dicts to a list in the keyfunc
            k, v = item
            v[1] = sorted((si, se) for (si, (se, void)) in v[1].iteritems())
            # now calculate the key
            letter = unicodedata.normalize('NFD', k[0])[0].upper()
            if letter in letters:
                return letter
            else:
                # get all other symbols under one heading
                return 'Symbols'
        return [(key, list(group))
                for (key, group) in groupby(newlist, keyfunc2)]

    def collect_relations(self):
        relations = {}
        getinc = self.toctree_includes.get
        def collect(parents, parents_set, docname, previous, next):
            # circular relationship?
            if docname in parents_set:
                # we will warn about this in resolve_toctree()
                return
            includes = getinc(docname)
            # previous
            if not previous:
                # if no previous sibling, go to parent
                previous = parents[0][0]
            else:
                # else, go to previous sibling, or if it has children, to
                # the last of its children, or if that has children, to the
                # last of those, and so forth
                while 1:
                    previncs = getinc(previous)
                    if previncs:
                        previous = previncs[-1]
                    else:
                        break
            # next
            if includes:
                # if it has children, go to first of them
                next = includes[0]
            elif next:
                # else, if next sibling, go to it
                pass
            else:
                # else, go to the next sibling of the parent, if present,
                # else the grandparent's sibling, if present, and so forth
                for parname, parindex in parents:
                    parincs = getinc(parname)
                    if parincs and parindex + 1 < len(parincs):
                        next = parincs[parindex+1]
                        break
                # else it will stay None
            # same for children
            if includes:
                for subindex, args in enumerate(izip(includes,
                                                     [None] + includes,
                                                     includes[1:] + [None])):
                    collect([(docname, subindex)] + parents,
                            parents_set.union([docname]), *args)
            relations[docname] = [parents[0][0], previous, next]
        collect([(None, 0)], set(), self.config.master_doc, None, None)
        return relations

    def check_consistency(self):
        """Do consistency checks."""
        for docname in sorted(self.all_docs):
            if docname not in self.files_to_rebuild:
                if docname == self.config.master_doc:
                    # the master file is not included anywhere ;)
                    continue
                if 'orphan' in self.metadata[docname]:
                    continue
                self.warn(docname, 'document isn\'t included in any toctree')

