# -*- coding: utf-8 -*-
"""
    sphinx.ext.autodoc
    ~~~~~~~~~~~~~~~~~~

    Automatically insert docstrings for functions, classes or whole modules into
    the doctree, thus avoiding duplication between docstrings and documentation
    for those who like elaborate docstrings.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
import inspect
import traceback
from types import FunctionType, BuiltinFunctionType, MethodType

from docutils import nodes
from docutils.utils import assemble_option_dict
from docutils.statemachine import ViewList

from sphinx.util import rpartition, force_decode
from sphinx.locale import _
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.application import ExtensionError
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.util.compat import Directive
from sphinx.util.inspect import getargspec, isdescriptor, safe_getmembers, \
     safe_getattr, safe_repr, is_builtin_class_method
from sphinx.util.pycompat import base_exception, class_types
from sphinx.util.docstrings import prepare_docstring


#: extended signature RE: with explicit module name separated by ::
py_ext_sig_re = re.compile(
    r'''^ ([\w.]+::)?            # explicit module name
          ([\w.]+\.)?            # module and/or class name(s)
          (\w+)  \s*             # thing name
          (?: \((.*)\)           # optional: arguments
           (?:\s* -> \s* (.*))?  #           return annotation
          )? $                   # and nothing more
          ''', re.VERBOSE)


class DefDict(dict):
    """A dict that returns a default on nonexisting keys."""
    def __init__(self, default):
        dict.__init__(self)
        self.default = default
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.default
    def __nonzero__(self):
        # docutils check "if option_spec"
        return True

identity = lambda x: x


class Options(dict):
    """A dict/attribute hybrid that returns None on nonexisting keys."""
    def __getattr__(self, name):
        try:
            return self[name.replace('_', '-')]
        except KeyError:
            return None


ALL = object()
INSTANCEATTR = object()

def members_option(arg):
    """Used to convert the :members: option to auto directives."""
    if arg is None:
        return ALL
    return [x.strip() for x in arg.split(',')]

def members_set_option(arg):
    """Used to convert the :members: option to auto directives."""
    if arg is None:
        return ALL
    return set(x.strip() for x in arg.split(','))

SUPPRESS = object()

def annotation_option(arg):
    if arg is None:
        # suppress showing the representation of the object
        return SUPPRESS
    else:
        return arg

def bool_option(arg):
    """Used to convert flag options to auto directives.  (Instead of
    directives.flag(), which returns None).
    """
    return True


class AutodocReporter(object):
    """
    A reporter replacement that assigns the correct source name
    and line number to a system message, as recorded in a ViewList.
    """
    def __init__(self, viewlist, reporter):
        self.viewlist = viewlist
        self.reporter = reporter

    def __getattr__(self, name):
        return getattr(self.reporter, name)

    def system_message(self, level, message, *children, **kwargs):
        if 'line' in kwargs and 'source' not in kwargs:
            try:
                source, line = self.viewlist.items[kwargs['line']]
            except IndexError:
                pass
            else:
                kwargs['source'] = source
                kwargs['line'] = line
        return self.reporter.system_message(level, message,
                                            *children, **kwargs)

    def debug(self, *args, **kwargs):
        if self.reporter.debug_flag:
            return self.system_message(0, *args, **kwargs)

    def info(self, *args, **kwargs):
        return self.system_message(1, *args, **kwargs)

    def warning(self, *args, **kwargs):
        return self.system_message(2, *args, **kwargs)

    def error(self, *args, **kwargs):
        return self.system_message(3, *args, **kwargs)

    def severe(self, *args, **kwargs):
        return self.system_message(4, *args, **kwargs)


# Some useful event listener factories for autodoc-process-docstring.

def cut_lines(pre, post=0, what=None):
    """Return a listener that removes the first *pre* and last *post*
    lines of every docstring.  If *what* is a sequence of strings,
    only docstrings of a type in *what* will be processed.

    Use like this (e.g. in the ``setup()`` function of :file:`conf.py`)::

       from sphinx.ext.autodoc import cut_lines
       app.connect('autodoc-process-docstring', cut_lines(4, what=['module']))

    This can (and should) be used in place of :confval:`automodule_skip_lines`.
    """
    def process(app, what_, name, obj, options, lines):
        if what and what_ not in what:
            return
        del lines[:pre]
        if post:
            # remove one trailing blank line.
            if lines and not lines[-1]:
                lines.pop(-1)
            del lines[-post:]
        # make sure there is a blank line at the end
        if lines and lines[-1]:
            lines.append('')
    return process

def between(marker, what=None, keepempty=False, exclude=False):
    """Return a listener that either keeps, or if *exclude* is True excludes,
    lines between lines that match the *marker* regular expression.  If no line
    matches, the resulting docstring would be empty, so no change will be made
    unless *keepempty* is true.

    If *what* is a sequence of strings, only docstrings of a type in *what* will
    be processed.
    """
    marker_re = re.compile(marker)
    def process(app, what_, name, obj, options, lines):
        if what and what_ not in what:
            return
        deleted = 0
        delete = not exclude
        orig_lines = lines[:]
        for i, line in enumerate(orig_lines):
            if delete:
                lines.pop(i - deleted)
                deleted += 1
            if marker_re.match(line):
                delete = not delete
                if delete:
                    lines.pop(i - deleted)
                    deleted += 1
        if not lines and not keepempty:
            lines[:] = orig_lines
        # make sure there is a blank line at the end
        if lines and lines[-1]:
            lines.append('')
    return process


class Documenter(object):
    """
    A Documenter knows how to autodocument a single object type.  When
    registered with the AutoDirective, it will be used to document objects
    of that type when needed by autodoc.

    Its *objtype* attribute selects what auto directive it is assigned to
    (the directive name is 'auto' + objtype), and what directive it generates
    by default, though that can be overridden by an attribute called
    *directivetype*.

    A Documenter has an *option_spec* that works like a docutils directive's;
    in fact, it will be used to parse an auto directive's options that matches
    the documenter.
    """
    #: name by which the directive is called (auto...) and the default
    #: generated directive name
    objtype = 'object'
    #: indentation by which to indent the directive content
    content_indent = u'   '
    #: priority if multiple documenters return True from can_document_member
    priority = 0
    #: order if autodoc_member_order is set to 'groupwise'
    member_order = 0
    #: true if the generated content may contain titles
    titles_allowed = False

    option_spec = {'noindex': bool_option}

    @staticmethod
    def get_attr(obj, name, *defargs):
        """getattr() override for types such as Zope interfaces."""
        for typ, func in AutoDirective._special_attrgetters.iteritems():
            if isinstance(obj, typ):
                return func(obj, name, *defargs)
        return safe_getattr(obj, name, *defargs)

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        """Called to see if a member can be documented by this documenter."""
        raise NotImplementedError('must be implemented in subclasses')

    def __init__(self, directive, name, indent=u''):
        self.directive = directive
        self.env = directive.env
        self.options = directive.genopt
        self.name = name
        self.indent = indent
        # the module and object path within the module, and the fully
        # qualified name (all set after resolve_name succeeds)
        self.modname = None
        self.module = None
        self.objpath = None
        self.fullname = None
        # extra signature items (arguments and return annotation,
        # also set after resolve_name succeeds)
        self.args = None
        self.retann = None
        # the object to document (set after import_object succeeds)
        self.object = None
        self.object_name = None
        # the parent/owner of the object to document
        self.parent = None
        # the module analyzer to get at attribute docs, or None
        self.analyzer = None

    def add_line(self, line, source, *lineno):
        """Append one line of generated reST to the output."""
        self.directive.result.append(self.indent + line, source, *lineno)

    def resolve_name(self, modname, parents, path, base):
        """Resolve the module and name of the object to document given by the
        arguments and the current module/class.

        Must return a pair of the module name and a chain of attributes; for
        example, it would return ``('zipfile', ['ZipFile', 'open'])`` for the
        ``zipfile.ZipFile.open`` method.
        """
        raise NotImplementedError('must be implemented in subclasses')

    def parse_name(self):
        """Determine what module to import and what attribute to document.

        Returns True and sets *self.modname*, *self.objpath*, *self.fullname*,
        *self.args* and *self.retann* if parsing and resolving was successful.
        """
        # first, parse the definition -- auto directives for classes and
        # functions can contain a signature which is then used instead of
        # an autogenerated one
        try:
            explicit_modname, path, base, args, retann = \
                 py_ext_sig_re.match(self.name).groups()
        except AttributeError:
            self.directive.warn('invalid signature for auto%s (%r)' %
                                (self.objtype, self.name))
            return False

        # support explicit module and class name separation via ::
        if explicit_modname is not None:
            modname = explicit_modname[:-2]
            parents = path and path.rstrip('.').split('.') or []
        else:
            modname = None
            parents = []

        self.modname, self.objpath = \
                      self.resolve_name(modname, parents, path, base)

        if not self.modname:
            return False

        self.args = args
        self.retann = retann
        self.fullname = (self.modname or '') + \
                        (self.objpath and '.' + '.'.join(self.objpath) or '')
        return True

    def import_object(self):
        """Import the object given by *self.modname* and *self.objpath* and set
        it as *self.object*.

        Returns True if successful, False if an error occurred.
        """
        dbg = self.env.app.debug
        if self.objpath:
            dbg('[autodoc] from %s import %s',
                self.modname, '.'.join(self.objpath))
        try:
            dbg('[autodoc] import %s', self.modname)
            __import__(self.modname)
            parent = None
            obj = self.module = sys.modules[self.modname]
            dbg('[autodoc] => %r', obj)
            for part in self.objpath:
                parent = obj
                dbg('[autodoc] getattr(_, %r)', part)
                obj = self.get_attr(obj, part)
                dbg('[autodoc] => %r', obj)
                self.object_name = part
            self.parent = parent
            self.object = obj
            return True
        # this used to only catch SyntaxError, ImportError and AttributeError,
        # but importing modules with side effects can raise all kinds of errors
        except Exception:
            if self.objpath:
                errmsg = 'autodoc: failed to import %s %r from module %r' % \
                         (self.objtype, '.'.join(self.objpath), self.modname)
            else:
                errmsg = 'autodoc: failed to import %s %r' % \
                         (self.objtype, self.fullname)
            errmsg += '; the following exception was raised:\n%s' % \
                      traceback.format_exc()
            dbg(errmsg)
            self.directive.warn(errmsg)
            self.env.note_reread()
            return False

    def get_real_modname(self):
        """Get the real module name of an object to document.

        It can differ from the name of the module through which the object was
        imported.
        """
        return self.get_attr(self.object, '__module__', None) or self.modname

    def check_module(self):
        """Check if *self.object* is really defined in the module given by
        *self.modname*.
        """
        if self.options.imported_members:
            return True

        modname = self.get_attr(self.object, '__module__', None)
        if modname and modname != self.modname:
            return False
        return True

    def format_args(self):
        """Format the argument signature of *self.object*.

        Should return None if the object does not have a signature.
        """
        return None

    def format_name(self):
        """Format the name of *self.object*.

        This normally should be something that can be parsed by the generated
        directive, but doesn't need to be (Sphinx will display it unparsed
        then).
        """
        # normally the name doesn't contain the module (except for module
        # directives of course)
        return '.'.join(self.objpath) or self.modname

    def format_signature(self):
        """Format the signature (arguments and return annotation) of the object.

        Let the user process it via the ``autodoc-process-signature`` event.
        """
        if self.args is not None:
            # signature given explicitly
            args = "(%s)" % self.args
        else:
            # try to introspect the signature
            try:
                args = self.format_args()
            except Exception, err:
                self.directive.warn('error while formatting arguments for '
                                    '%s: %s' % (self.fullname, err))
                args = None

        retann = self.retann

        result = self.env.app.emit_firstresult(
            'autodoc-process-signature', self.objtype, self.fullname,
            self.object, self.options, args, retann)
        if result:
            args, retann = result

        if args is not None:
            return args + (retann and (' -> %s' % retann) or '')
        else:
            return ''

    def add_directive_header(self, sig):
        """Add the directive header and options to the generated content."""
        domain = getattr(self, 'domain', 'py')
        directive = getattr(self, 'directivetype', self.objtype)
        name = self.format_name()
        self.add_line(u'.. %s:%s:: %s%s' % (domain, directive, name, sig),
                      '<autodoc>')
        if self.options.noindex:
            self.add_line(u'   :noindex:', '<autodoc>')
        if self.objpath:
            # Be explicit about the module, this is necessary since .. class::
            # etc. don't support a prepended module name
            self.add_line(u'   :module: %s' % self.modname, '<autodoc>')

    def get_doc(self, encoding=None, ignore=1):
        """Decode and return lines of the docstring(s) for the object."""
        docstring = self.get_attr(self.object, '__doc__', None)
        # make sure we have Unicode docstrings, then sanitize and split
        # into lines
        if isinstance(docstring, unicode):
            return [prepare_docstring(docstring, ignore)]
        elif isinstance(docstring, str):  # this will not trigger on Py3
            return [prepare_docstring(force_decode(docstring, encoding),
                                      ignore)]
        # ... else it is something strange, let's ignore it
        return []

    def process_doc(self, docstrings):
        """Let the user process the docstrings before adding them."""
        for docstringlines in docstrings:
            if self.env.app:
                # let extensions preprocess docstrings
                self.env.app.emit('autodoc-process-docstring',
                                  self.objtype, self.fullname, self.object,
                                  self.options, docstringlines)
            for line in docstringlines:
                yield line

    def add_content(self, more_content, no_docstring=False):
        """Add content from docstrings, attribute documentation and user."""
        # set sourcename and add content from attribute documentation
        if self.analyzer:
            # prevent encoding errors when the file name is non-ASCII
            if not isinstance(self.analyzer.srcname, unicode):
                filename = unicode(self.analyzer.srcname,
                                   sys.getfilesystemencoding(), 'replace')
            else:
                filename = self.analyzer.srcname
            sourcename = u'%s:docstring of %s' % (filename, self.fullname)

            attr_docs = self.analyzer.find_attr_docs()
            if self.objpath:
                key = ('.'.join(self.objpath[:-1]), self.objpath[-1])
                if key in attr_docs:
                    no_docstring = True
                    docstrings = [attr_docs[key]]
                    for i, line in enumerate(self.process_doc(docstrings)):
                        self.add_line(line, sourcename, i)
        else:
            sourcename = u'docstring of %s' % self.fullname

        # add content from docstrings
        if not no_docstring:
            encoding = self.analyzer and self.analyzer.encoding
            docstrings = self.get_doc(encoding)
            if not docstrings:
                # append at least a dummy docstring, so that the event
                # autodoc-process-docstring is fired and can add some
                # content if desired
                docstrings.append([])
            for i, line in enumerate(self.process_doc(docstrings)):
                self.add_line(line, sourcename, i)

        # add additional content (e.g. from document), if present
        if more_content:
            for line, src in zip(more_content.data, more_content.items):
                self.add_line(line, src[0], src[1])

    def get_object_members(self, want_all):
        """Return `(members_check_module, members)` where `members` is a
        list of `(membername, member)` pairs of the members of *self.object*.

        If *want_all* is True, return all members.  Else, only return those
        members given by *self.options.members* (which may also be none).
        """
        analyzed_member_names = set()
        if self.analyzer:
            attr_docs = self.analyzer.find_attr_docs()
            namespace = '.'.join(self.objpath)
            for item in attr_docs.iteritems():
                if item[0][0] == namespace:
                    analyzed_member_names.add(item[0][1])
        if not want_all:
            if not self.options.members:
                return False, []
            # specific members given
            members = []
            for mname in self.options.members:
                try:
                    members.append((mname, self.get_attr(self.object, mname)))
                except AttributeError:
                    if mname not in analyzed_member_names:
                        self.directive.warn('missing attribute %s in object %s'
                                            % (mname, self.fullname))
        elif self.options.inherited_members:
            # safe_getmembers() uses dir() which pulls in members from all
            # base classes
            members = safe_getmembers(self.object, attr_getter=self.get_attr)
        else:
            # __dict__ contains only the members directly defined in
            # the class (but get them via getattr anyway, to e.g. get
            # unbound method objects instead of function objects);
            # using keys() because apparently there are objects for which
            # __dict__ changes while getting attributes
            try:
                obj_dict = self.get_attr(self.object, '__dict__')
            except AttributeError:
                members = []
            else:
                members = [(mname, self.get_attr(self.object, mname, None))
                           for mname in obj_dict.keys()]
        membernames = set(m[0] for m in members)
        # add instance attributes from the analyzer
        for aname in analyzed_member_names:
            if aname not in membernames and \
               (want_all or aname in self.options.members):
                members.append((aname, INSTANCEATTR))
        return False, sorted(members)

    def filter_members(self, members, want_all):
        """Filter the given member list.

        Members are skipped if

        - they are private (except if given explicitly or the private-members
          option is set)
        - they are special methods (except if given explicitly or the
          special-members option is set)
        - they are undocumented (except if the undoc-members option is set)

        The user can override the skipping decision by connecting to the
        ``autodoc-skip-member`` event.
        """
        ret = []

        # search for members in source code too
        namespace = '.'.join(self.objpath)  # will be empty for modules

        if self.analyzer:
            attr_docs = self.analyzer.find_attr_docs()
        else:
            attr_docs = {}

        # process members and determine which to skip
        for (membername, member) in members:
            # if isattr is True, the member is documented as an attribute
            isattr = False

            doc = self.get_attr(member, '__doc__', None)
            # if the member __doc__ is the same as self's __doc__, it's just
            # inherited and therefore not the member's doc
            cls = self.get_attr(member, '__class__', None)
            if cls:
                cls_doc = self.get_attr(cls, '__doc__', None)
                if cls_doc == doc:
                    doc = None
            has_doc = bool(doc)

            keep = False
            if want_all and membername.startswith('__') and \
                   membername.endswith('__') and len(membername) > 4:
                # special __methods__
                if self.options.special_members is ALL and \
                        membername != '__doc__':
                    keep = has_doc or self.options.undoc_members
                elif self.options.special_members and \
                     self.options.special_members is not ALL and \
                        membername in self.options.special_members:
                    keep = has_doc or self.options.undoc_members
            elif want_all and membername.startswith('_'):
                # ignore members whose name starts with _ by default
                keep = self.options.private_members and \
                       (has_doc or self.options.undoc_members)
            elif (namespace, membername) in attr_docs:
                # keep documented attributes
                keep = True
                isattr = True
            else:
                # ignore undocumented members if :undoc-members: is not given
                keep = has_doc or self.options.undoc_members

            # give the user a chance to decide whether this member
            # should be skipped
            if self.env.app:
                # let extensions preprocess docstrings
                skip_user = self.env.app.emit_firstresult(
                    'autodoc-skip-member', self.objtype, membername, member,
                    not keep, self.options)
                if skip_user is not None:
                    keep = not skip_user

            if keep:
                ret.append((membername, member, isattr))

        return ret

    def document_members(self, all_members=False):
        """Generate reST for member documentation.

        If *all_members* is True, do all members, else those given by
        *self.options.members*.
        """
        # set current namespace for finding members
        self.env.temp_data['autodoc:module'] = self.modname
        if self.objpath:
            self.env.temp_data['autodoc:class'] = self.objpath[0]

        want_all = all_members or self.options.inherited_members or \
                   self.options.members is ALL
        # find out which members are documentable
        members_check_module, members = self.get_object_members(want_all)

        # remove members given by exclude-members
        if self.options.exclude_members:
            members = [(membername, member) for (membername, member) in members
                       if membername not in self.options.exclude_members]

        # document non-skipped members
        memberdocumenters = []
        for (mname, member, isattr) in self.filter_members(members, want_all):
            classes = [cls for cls in AutoDirective._registry.itervalues()
                       if cls.can_document_member(member, mname, isattr, self)]
            if not classes:
                # don't know how to document this member
                continue
            # prefer the documenter with the highest priority
            classes.sort(key=lambda cls: cls.priority)
            # give explicitly separated module name, so that members
            # of inner classes can be documented
            full_mname = self.modname + '::' + \
                              '.'.join(self.objpath + [mname])
            documenter = classes[-1](self.directive, full_mname, self.indent)
            memberdocumenters.append((documenter, isattr))
        member_order = self.options.member_order or \
                       self.env.config.autodoc_member_order
        if member_order == 'groupwise':
            # sort by group; relies on stable sort to keep items in the
            # same group sorted alphabetically
            memberdocumenters.sort(key=lambda e: e[0].member_order)
        elif member_order == 'bysource' and self.analyzer:
            # sort by source order, by virtue of the module analyzer
            tagorder = self.analyzer.tagorder
            def keyfunc(entry):
                fullname = entry[0].name.split('::')[1]
                return tagorder.get(fullname, len(tagorder))
            memberdocumenters.sort(key=keyfunc)

        for documenter, isattr in memberdocumenters:
            documenter.generate(
                all_members=True, real_modname=self.real_modname,
                check_module=members_check_module and not isattr)

        # reset current objects
        self.env.temp_data['autodoc:module'] = None
        self.env.temp_data['autodoc:class'] = None

    def generate(self, more_content=None, real_modname=None,
                 check_module=False, all_members=False):
        """Generate reST for the object given by *self.name*, and possibly for
        its members.

        If *more_content* is given, include that content. If *real_modname* is
        given, use that module name to find attribute docs. If *check_module* is
        True, only generate if the object is defined in the module name it is
        imported from. If *all_members* is True, document all members.
        """
        if not self.parse_name():
            # need a module to import
            self.directive.warn(
                'don\'t know which module to import for autodocumenting '
                '%r (try placing a "module" or "currentmodule" directive '
                'in the document, or giving an explicit module name)'
                % self.name)
            return

        # now, import the module and get object to document
        if not self.import_object():
            return

        # If there is no real module defined, figure out which to use.
        # The real module is used in the module analyzer to look up the module
        # where the attribute documentation would actually be found in.
        # This is used for situations where you have a module that collects the
        # functions and classes of internal submodules.
        self.real_modname = real_modname or self.get_real_modname()

        # try to also get a source code analyzer for attribute docs
        try:
            self.analyzer = ModuleAnalyzer.for_module(self.real_modname)
            # parse right now, to get PycodeErrors on parsing (results will
            # be cached anyway)
            self.analyzer.find_attr_docs()
        except PycodeError, err:
            self.env.app.debug('[autodoc] module analyzer failed: %s', err)
            # no source file -- e.g. for builtin and C modules
            self.analyzer = None
            # at least add the module.__file__ as a dependency
            if hasattr(self.module, '__file__') and self.module.__file__:
                self.directive.filename_set.add(self.module.__file__)
        else:
            self.directive.filename_set.add(self.analyzer.srcname)

        # check __module__ of object (for members not given explicitly)
        if check_module:
            if not self.check_module():
                return

        # make sure that the result starts with an empty line.  This is
        # necessary for some situations where another directive preprocesses
        # reST and no starting newline is present
        self.add_line(u'', '<autodoc>')

        # format the object's signature, if any
        sig = self.format_signature()

        # generate the directive header and options, if applicable
        self.add_directive_header(sig)
        self.add_line(u'', '<autodoc>')

        # e.g. the module directive doesn't have content
        self.indent += self.content_indent

        # add all content (from docstrings, attribute docs etc.)
        self.add_content(more_content)

        # document members, if possible
        self.document_members(all_members)


class ModuleDocumenter(Documenter):
    """
    Specialized Documenter subclass for modules.
    """
    objtype = 'module'
    content_indent = u''
    titles_allowed = True

    option_spec = {
        'members': members_option, 'undoc-members': bool_option,
        'noindex': bool_option, 'inherited-members': bool_option,
        'show-inheritance': bool_option, 'synopsis': identity,
        'platform': identity, 'deprecated': bool_option,
        'member-order': identity, 'exclude-members': members_set_option,
        'private-members': bool_option, 'special-members': members_option,
        'imported-members': bool_option,
    }

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        # don't document submodules automatically
        return False

    def resolve_name(self, modname, parents, path, base):
        if modname is not None:
            self.directive.warn('"::" in automodule name doesn\'t make sense')
        return (path or '') + base, []

    def parse_name(self):
        ret = Documenter.parse_name(self)
        if self.args or self.retann:
            self.directive.warn('signature arguments or return annotation '
                                'given for automodule %s' % self.fullname)
        return ret

    def add_directive_header(self, sig):
        Documenter.add_directive_header(self, sig)

        # add some module-specific options
        if self.options.synopsis:
            self.add_line(
                u'   :synopsis: ' + self.options.synopsis, '<autodoc>')
        if self.options.platform:
            self.add_line(
                u'   :platform: ' + self.options.platform, '<autodoc>')
        if self.options.deprecated:
            self.add_line(u'   :deprecated:', '<autodoc>')

    def get_object_members(self, want_all):
        if want_all:
            if not hasattr(self.object, '__all__'):
                # for implicit module members, check __module__ to avoid
                # documenting imported objects
                return True, safe_getmembers(self.object)
            else:
                memberlist = self.object.__all__
        else:
            memberlist = self.options.members or []
        ret = []
        for mname in memberlist:
            try:
                ret.append((mname, safe_getattr(self.object, mname)))
            except AttributeError:
                self.directive.warn(
                    'missing attribute mentioned in :members: or __all__: '
                    'module %s, attribute %s' % (
                    safe_getattr(self.object, '__name__', '???'), mname))
        return False, ret


class ModuleLevelDocumenter(Documenter):
    """
    Specialized Documenter subclass for objects on module level (functions,
    classes, data/constants).
    """
    def resolve_name(self, modname, parents, path, base):
        if modname is None:
            if path:
                modname = path.rstrip('.')
            else:
                # if documenting a toplevel object without explicit module,
                # it can be contained in another auto directive ...
                modname = self.env.temp_data.get('autodoc:module')
                # ... or in the scope of a module directive
                if not modname:
                    modname = self.env.temp_data.get('py:module')
                # ... else, it stays None, which means invalid
        return modname, parents + [base]


class ClassLevelDocumenter(Documenter):
    """
    Specialized Documenter subclass for objects on class level (methods,
    attributes).
    """
    def resolve_name(self, modname, parents, path, base):
        if modname is None:
            if path:
                mod_cls = path.rstrip('.')
            else:
                mod_cls = None
                # if documenting a class-level object without path,
                # there must be a current class, either from a parent
                # auto directive ...
                mod_cls = self.env.temp_data.get('autodoc:class')
                # ... or from a class directive
                if mod_cls is None:
                    mod_cls = self.env.temp_data.get('py:class')
                # ... if still None, there's no way to know
                if mod_cls is None:
                    return None, []
            modname, cls = rpartition(mod_cls, '.')
            parents = [cls]
            # if the module name is still missing, get it like above
            if not modname:
                modname = self.env.temp_data.get('autodoc:module')
            if not modname:
                modname = self.env.temp_data.get('py:module')
            # ... else, it stays None, which means invalid
        return modname, parents + [base]


class DocstringSignatureMixin(object):
    """
    Mixin for FunctionDocumenter and MethodDocumenter to provide the
    feature of reading the signature from the docstring.
    """

    def _find_signature(self, encoding=None):
        docstrings = Documenter.get_doc(self, encoding)
        if len(docstrings) != 1:
            return
        doclines = docstrings[0]
        setattr(self, '__new_doclines', doclines)
        if not doclines:
            return
        # match first line of docstring against signature RE
        match = py_ext_sig_re.match(doclines[0])
        if not match:
            return
        exmod, path, base, args, retann = match.groups()
        # the base name must match ours
        if not self.objpath or base != self.objpath[-1]:
            return
        # re-prepare docstring to ignore indentation after signature
        docstrings = Documenter.get_doc(self, encoding, 2)
        doclines = docstrings[0]
        # ok, now jump over remaining empty lines and set the remaining
        # lines as the new doclines
        i = 1
        while i < len(doclines) and not doclines[i].strip():
            i += 1
        setattr(self, '__new_doclines', doclines[i:])
        return args, retann

    def get_doc(self, encoding=None, ignore=1):
        lines = getattr(self, '__new_doclines', None)
        if lines is not None:
            return [lines]
        return Documenter.get_doc(self, encoding, ignore)

    def format_signature(self):
        if self.args is None and self.env.config.autodoc_docstring_signature:
            # only act if a signature is not explicitly given already, and if
            # the feature is enabled
            result = self._find_signature()
            if result is not None:
                self.args, self.retann = result
        return Documenter.format_signature(self)


class FunctionDocumenter(DocstringSignatureMixin, ModuleLevelDocumenter):
    """
    Specialized Documenter subclass for functions.
    """
    objtype = 'function'
    member_order = 30

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, (FunctionType, BuiltinFunctionType))

    def format_args(self):
        if inspect.isbuiltin(self.object) or \
               inspect.ismethoddescriptor(self.object):
            # cannot introspect arguments of a C function or method
            return None
        try:
            argspec = getargspec(self.object)
        except TypeError:
            if (is_builtin_class_method(self.object, '__new__') and
               is_builtin_class_method(self.object, '__init__')):
                raise TypeError('%r is a builtin class' % self.object)

            # if a class should be documented as function (yay duck
            # typing) we try to use the constructor signature as function
            # signature without the first argument.
            try:
                argspec = getargspec(self.object.__new__)
            except TypeError:
                argspec = getargspec(self.object.__init__)
                if argspec[0]:
                    del argspec[0][0]
        args = inspect.formatargspec(*argspec)
        # escape backslashes for reST
        args = args.replace('\\', '\\\\')
        return args

    def document_members(self, all_members=False):
        pass


class ClassDocumenter(ModuleLevelDocumenter):
    """
    Specialized Documenter subclass for classes.
    """
    objtype = 'class'
    member_order = 20
    option_spec = {
        'members': members_option, 'undoc-members': bool_option,
        'noindex': bool_option, 'inherited-members': bool_option,
        'show-inheritance': bool_option, 'member-order': identity,
        'exclude-members': members_set_option,
        'private-members': bool_option, 'special-members': members_option,
    }

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, class_types)

    def import_object(self):
        ret = ModuleLevelDocumenter.import_object(self)
        # if the class is documented under another name, document it
        # as data/attribute
        if ret:
            if hasattr(self.object, '__name__'):
                self.doc_as_attr = (self.objpath[-1] != self.object.__name__)
            else:
                self.doc_as_attr = True
        return ret

    def format_args(self):
        # for classes, the relevant signature is the __init__ method's
        initmeth = self.get_attr(self.object, '__init__', None)
        # classes without __init__ method, default __init__ or
        # __init__ written in C?
        if initmeth is None or \
               is_builtin_class_method(self.object, '__init__') or \
               not(inspect.ismethod(initmeth) or inspect.isfunction(initmeth)):
            return None
        try:
            argspec = getargspec(initmeth)
        except TypeError:
            # still not possible: happens e.g. for old-style classes
            # with __init__ in C
            return None
        if argspec[0] and argspec[0][0] in ('cls', 'self'):
            del argspec[0][0]
        return inspect.formatargspec(*argspec)

    def format_signature(self):
        if self.doc_as_attr:
            return ''

        # get __init__ method signature from __init__.__doc__
        if self.env.config.autodoc_docstring_signature:
            # only act if the feature is enabled
            init_doc = MethodDocumenter(self.directive, '__init__')
            init_doc.object = self.get_attr(self.object, '__init__', None)
            init_doc.objpath = ['__init__']
            result = init_doc._find_signature()
            if result is not None:
                # use args only for Class signature
                return '(%s)' % result[0]

        return ModuleLevelDocumenter.format_signature(self)

    def add_directive_header(self, sig):
        if self.doc_as_attr:
            self.directivetype = 'attribute'
        Documenter.add_directive_header(self, sig)

        # add inheritance info, if wanted
        if not self.doc_as_attr and self.options.show_inheritance:
            self.add_line(u'', '<autodoc>')
            if hasattr(self.object, '__bases__') and len(self.object.__bases__):
                bases = [b.__module__ == '__builtin__' and
                         u':class:`%s`' % b.__name__ or
                         u':class:`%s.%s`' % (b.__module__, b.__name__)
                         for b in self.object.__bases__]
                self.add_line(_(u'   Bases: %s') % ', '.join(bases),
                              '<autodoc>')

    def get_doc(self, encoding=None, ignore=1):
        content = self.env.config.autoclass_content

        docstrings = []
        attrdocstring = self.get_attr(self.object, '__doc__', None)
        if attrdocstring:
            docstrings.append(attrdocstring)

        # for classes, what the "docstring" is can be controlled via a
        # config value; the default is only the class docstring
        if content in ('both', 'init'):
            # get __init__ method document from __init__.__doc__
            if self.env.config.autodoc_docstring_signature:
                # only act if the feature is enabled
                init_doc = MethodDocumenter(self.directive, '__init__')
                init_doc.object = self.get_attr(self.object, '__init__', None)
                init_doc.objpath = ['__init__']
                init_doc._find_signature()  # this effects to get_doc() result
                initdocstring = '\n'.join(
                    ['\n'.join(l) for l in init_doc.get_doc(encoding)])
            else:
                initdocstring = self.get_attr(
                    self.get_attr(self.object, '__init__', None), '__doc__')
            # for new-style classes, no __init__ means default __init__
            if (initdocstring is not None and
                (initdocstring == object.__init__.__doc__ or  # for pypy
                 initdocstring.strip() == object.__init__.__doc__)):  #for !pypy
                initdocstring = None
            if initdocstring:
                if content == 'init':
                    docstrings = [initdocstring]
                else:
                    docstrings.append(initdocstring)
        doc = []
        for docstring in docstrings:
            if not isinstance(docstring, unicode):
                docstring = force_decode(docstring, encoding)
            doc.append(prepare_docstring(docstring))
        return doc

    def add_content(self, more_content, no_docstring=False):
        if self.doc_as_attr:
            classname = safe_getattr(self.object, '__name__', None)
            if classname:
                content = ViewList(
                    [_('alias of :class:`%s`') % classname], source='')
                ModuleLevelDocumenter.add_content(self, content,
                                                  no_docstring=True)
        else:
            ModuleLevelDocumenter.add_content(self, more_content)

    def document_members(self, all_members=False):
        if self.doc_as_attr:
            return
        ModuleLevelDocumenter.document_members(self, all_members)


class ExceptionDocumenter(ClassDocumenter):
    """
    Specialized ClassDocumenter subclass for exceptions.
    """
    objtype = 'exception'
    member_order = 10

    # needs a higher priority than ClassDocumenter
    priority = 10

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, class_types) and \
               issubclass(member, base_exception)


class DataDocumenter(ModuleLevelDocumenter):
    """
    Specialized Documenter subclass for data items.
    """
    objtype = 'data'
    member_order = 40
    priority = -10
    option_spec = dict(ModuleLevelDocumenter.option_spec)
    option_spec["annotation"] = annotation_option

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(parent, ModuleDocumenter) and isattr

    def add_directive_header(self, sig):
        ModuleLevelDocumenter.add_directive_header(self, sig)
        if not self.options.annotation:
            try:
                objrepr = safe_repr(self.object)
            except ValueError:
                pass
            else:
                self.add_line(u'   :annotation: = ' + objrepr, '<autodoc>')
        elif self.options.annotation is SUPPRESS:
            pass
        else:
            self.add_line(u'   :annotation: %s' % self.options.annotation,
                          '<autodoc>')

    def document_members(self, all_members=False):
        pass


class MethodDocumenter(DocstringSignatureMixin, ClassLevelDocumenter):
    """
    Specialized Documenter subclass for methods (normal, static and class).
    """
    objtype = 'method'
    member_order = 50
    priority = 1  # must be more than FunctionDocumenter

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return inspect.isroutine(member) and \
               not isinstance(parent, ModuleDocumenter)

    if sys.version_info >= (3, 0):
        def import_object(self):
            ret = ClassLevelDocumenter.import_object(self)
            obj_from_parent = self.parent.__dict__.get(self.object_name)
            if isinstance(obj_from_parent, classmethod):
                self.directivetype = 'classmethod'
                self.member_order = self.member_order - 1
            elif isinstance(obj_from_parent, staticmethod):
                self.directivetype = 'staticmethod'
                self.member_order = self.member_order - 1
            else:
                self.directivetype = 'method'
            return ret
    else:
        def import_object(self):
            ret = ClassLevelDocumenter.import_object(self)
            if isinstance(self.object, classmethod) or \
                   (isinstance(self.object, MethodType) and
                    self.object.im_self is not None):
                self.directivetype = 'classmethod'
                # document class and static members before ordinary ones
                self.member_order = self.member_order - 1
            elif isinstance(self.object, FunctionType) or \
                 (isinstance(self.object, BuiltinFunctionType) and
                  hasattr(self.object, '__self__') and
                  self.object.__self__ is not None):
                self.directivetype = 'staticmethod'
                # document class and static members before ordinary ones
                self.member_order = self.member_order - 1
            else:
                self.directivetype = 'method'
            return ret

    def format_args(self):
        if inspect.isbuiltin(self.object) or \
               inspect.ismethoddescriptor(self.object):
            # can never get arguments of a C function or method
            return None
        argspec = getargspec(self.object)
        if argspec[0] and argspec[0][0] in ('cls', 'self'):
            del argspec[0][0]
        return inspect.formatargspec(*argspec)

    def document_members(self, all_members=False):
        pass


class AttributeDocumenter(ClassLevelDocumenter):
    """
    Specialized Documenter subclass for attributes.
    """
    objtype = 'attribute'
    member_order = 60
    option_spec = dict(ModuleLevelDocumenter.option_spec)
    option_spec["annotation"] = annotation_option

    # must be higher than the MethodDocumenter, else it will recognize
    # some non-data descriptors as methods
    priority = 10

    method_types = (FunctionType, BuiltinFunctionType, MethodType)

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        isdatadesc = isdescriptor(member) and not \
                     isinstance(member, cls.method_types) and not \
                     type(member).__name__ in ("type", "method_descriptor",
                                               "instancemethod")
        return isdatadesc or (not isinstance(parent, ModuleDocumenter)
                              and not inspect.isroutine(member)
                              and not isinstance(member, class_types))

    def document_members(self, all_members=False):
        pass

    def import_object(self):
        ret = ClassLevelDocumenter.import_object(self)
        if isdescriptor(self.object) and \
               not isinstance(self.object, self.method_types):
            self._datadescriptor = True
        else:
            # if it's not a data descriptor
            self._datadescriptor = False
        return ret

    def get_real_modname(self):
        return self.get_attr(self.parent or self.object, '__module__', None) \
               or self.modname

    def add_directive_header(self, sig):
        ClassLevelDocumenter.add_directive_header(self, sig)
        if not self.options.annotation:
            if not self._datadescriptor:
                try:
                    objrepr = safe_repr(self.object)
                except ValueError:
                    pass
                else:
                    self.add_line(u'   :annotation: = ' + objrepr, '<autodoc>')
        elif self.options.annotation is SUPPRESS:
            pass
        else:
            self.add_line(u'   :annotation: %s' % self.options.annotation,
                          '<autodoc>')

    def add_content(self, more_content, no_docstring=False):
        if not self._datadescriptor:
            # if it's not a data descriptor, its docstring is very probably the
            # wrong thing to display
            no_docstring = True
        ClassLevelDocumenter.add_content(self, more_content, no_docstring)


class InstanceAttributeDocumenter(AttributeDocumenter):
    """
    Specialized Documenter subclass for attributes that cannot be imported
    because they are instance attributes (e.g. assigned in __init__).
    """
    objtype = 'instanceattribute'
    directivetype = 'attribute'
    member_order = 60

    # must be higher than AttributeDocumenter
    priority = 11

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        """This documents only INSTANCEATTR members."""
        return isattr and (member is INSTANCEATTR)

    def import_object(self):
        """Never import anything."""
        # disguise as an attribute
        self.objtype = 'attribute'
        self._datadescriptor = False
        return True

    def add_content(self, more_content, no_docstring=False):
        """Never try to get a docstring from the object."""
        AttributeDocumenter.add_content(self, more_content, no_docstring=True)


class AutoDirective(Directive):
    """
    The AutoDirective class is used for all autodoc directives.  It dispatches
    most of the work to one of the Documenters, which it selects through its
    *_registry* dictionary.

    The *_special_attrgetters* attribute is used to customize ``getattr()``
    calls that the Documenters make; its entries are of the form ``type:
    getattr_function``.

    Note: When importing an object, all items along the import chain are
    accessed using the descendant's *_special_attrgetters*, thus this
    dictionary should include all necessary functions for accessing
    attributes of the parents.
    """
    # a registry of objtype -> documenter class
    _registry = {}

    # a registry of type -> getattr function
    _special_attrgetters = {}

    # flags that can be given in autodoc_default_flags
    _default_flags = set([
        'members', 'undoc-members', 'inherited-members', 'show-inheritance',
        'private-members', 'special-members',
    ])

    # standard docutils directive settings
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    # allow any options to be passed; the options are parsed further
    # by the selected Documenter
    option_spec = DefDict(identity)

    def warn(self, msg):
        self.warnings.append(self.reporter.warning(msg, line=self.lineno))

    def run(self):
        self.filename_set = set()  # a set of dependent filenames
        self.reporter = self.state.document.reporter
        self.env = self.state.document.settings.env
        self.warnings = []
        self.result = ViewList()

        try:
            source, lineno = self.reporter.get_source_and_line(self.lineno)
        except AttributeError:
            source = lineno = None
        self.env.app.debug('[autodoc] %s:%s: input:\n%s',
                           source, lineno, self.block_text)

        # find out what documenter to call
        objtype = self.name[4:]
        doc_class = self._registry[objtype]
        # add default flags
        for flag in self._default_flags:
            if flag not in doc_class.option_spec:
                continue
            negated = self.options.pop('no-' + flag, 'not given') is None
            if flag in self.env.config.autodoc_default_flags and \
               not negated:
                self.options[flag] = None
        # process the options with the selected documenter's option_spec
        try:
            self.genopt = Options(assemble_option_dict(
                self.options.items(), doc_class.option_spec))
        except (KeyError, ValueError, TypeError), err:
            # an option is either unknown or has a wrong type
            msg = self.reporter.error('An option to %s is either unknown or '
                                      'has an invalid value: %s' % (self.name, err),
                                      line=self.lineno)
            return [msg]
        # generate the output
        documenter = doc_class(self, self.arguments[0])
        documenter.generate(more_content=self.content)
        if not self.result:
            return self.warnings

        self.env.app.debug2('[autodoc] output:\n%s', '\n'.join(self.result))

        # record all filenames as dependencies -- this will at least
        # partially make automatic invalidation possible
        for fn in self.filename_set:
            self.state.document.settings.record_dependencies.add(fn)

        # use a custom reporter that correctly assigns lines to source
        # filename/description and lineno
        old_reporter = self.state.memo.reporter
        self.state.memo.reporter = AutodocReporter(self.result,
                                                   self.state.memo.reporter)

        if documenter.titles_allowed:
            node = nodes.section()
            # necessary so that the child nodes get the right source/line set
            node.document = self.state.document
            nested_parse_with_titles(self.state, self.result, node)
        else:
            node = nodes.paragraph()
            node.document = self.state.document
            self.state.nested_parse(self.result, 0, node)
        self.state.memo.reporter = old_reporter
        return self.warnings + node.children


def add_documenter(cls):
    """Register a new Documenter."""
    if not issubclass(cls, Documenter):
        raise ExtensionError('autodoc documenter %r must be a subclass '
                             'of Documenter' % cls)
    # actually, it should be possible to override Documenters
    #if cls.objtype in AutoDirective._registry:
    #    raise ExtensionError('autodoc documenter for %r is already '
    #                         'registered' % cls.objtype)
    AutoDirective._registry[cls.objtype] = cls


def setup(app):
    app.add_autodocumenter(ModuleDocumenter)
    app.add_autodocumenter(ClassDocumenter)
    app.add_autodocumenter(ExceptionDocumenter)
    app.add_autodocumenter(DataDocumenter)
    app.add_autodocumenter(FunctionDocumenter)
    app.add_autodocumenter(MethodDocumenter)
    app.add_autodocumenter(AttributeDocumenter)
    app.add_autodocumenter(InstanceAttributeDocumenter)

    app.add_config_value('autoclass_content', 'class', True)
    app.add_config_value('autodoc_member_order', 'alphabetic', True)
    app.add_config_value('autodoc_default_flags', [], True)
    app.add_config_value('autodoc_docstring_signature', True, True)
    app.add_event('autodoc-process-docstring')
    app.add_event('autodoc-process-signature')
    app.add_event('autodoc-skip-member')


class testcls:
    """test doc string"""

    def __getattr__(self, x):
        return x

    def __setattr__(self, x, y):
        """Attr setter."""
