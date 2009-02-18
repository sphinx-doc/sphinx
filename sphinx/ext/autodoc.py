# -*- coding: utf-8 -*-
"""
    sphinx.ext.autodoc
    ~~~~~~~~~~~~~~~~~~

    Automatically insert docstrings for functions, classes or whole modules into
    the doctree, thus avoiding duplication between docstrings and documentation
    for those who like elaborate docstrings.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
import inspect
from types import ModuleType, FunctionType, BuiltinFunctionType, MethodType, \
     ClassType

from docutils import nodes
from docutils.utils import assemble_option_dict
from docutils.statemachine import ViewList

from sphinx.util import rpartition, nested_parse_with_titles, force_decode
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.application import ExtensionError
from sphinx.util.compat import Directive
from sphinx.util.docstrings import prepare_docstring


try:
    base_exception = BaseException
except NameError:
    base_exception = Exception


py_ext_sig_re = re.compile(
    r'''^ ([\w.]+::)?            # explicit module name
          ([\w.]+\.)?            # module and/or class name(s)
          (\w+)  \s*             # thing name
          (?: \((.*)\)           # optional: arguments
           (?:\s* -> \s* (.*))?  #           return annotation
          )? $                   # and nothing more
          ''', re.VERBOSE)


class DefDict(dict):
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
    def __getattr__(self, name):
        try:
            return self[name.replace('_', '-')]
        except KeyError:
            return False


ALL = object()

def members_option(arg):
    if arg is None:
        return ALL
    return [x.strip() for x in arg.split(',')]

def bool_option(arg):
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
        if 'line' in kwargs:
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
    """
    Return a listener that removes the first *pre* and last *post*
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

def between(marker, what=None, keepempty=False):
    """
    Return a listener that only keeps lines between lines that match the
    *marker* regular expression.  If no line matches, the resulting docstring
    would be empty, so no change will be made unless *keepempty* is true.

    If *what* is a sequence of strings, only docstrings of a type in *what* will
    be processed.
    """
    marker_re = re.compile(marker)
    def process(app, what_, name, obj, options, lines):
        if what and what_ not in what:
            return
        deleted = 0
        delete = True
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


def isdescriptor(x):
    """Check if the object is some kind of descriptor."""
    for item in '__get__', '__set__', '__delete__':
        if hasattr(getattr(x, item, None), '__call__'):
            return True
    return False


class Documenter(object):
    # name by which the directive is called (auto...) and the default
    # generated directive name
    objtype = 'object'
    # indentation by which to indent the directive content
    content_indent = u'   '
    # priority if multiple documenters return True from can_document_member
    priority = 0

    option_spec = {'noindex': bool_option}

    special_attrgetters = {}

    @classmethod
    def get_attr(cls, obj, name, *defargs):
        """getattr() override for types such as Zope interfaces."""
        for typ, func in cls.special_attrgetters.iteritems():
            if isinstance(obj, typ):
                return func(obj, name, *defargs)
        return getattr(obj, name, *defargs)

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
        # the module analyzer to get at attribute docs, or None
        self.analyzer = None

    def add_line(self, line, source, *lineno):
        self.directive.result.append(self.indent + line, source, *lineno)

    def resolve_name(self, modname, parents, path, base):
        raise NotImplementedError('must be implemented in subclasses')

    def parse_name(self):
        """
        Determine what module to import and what attribute to document.

        Returns True if parsing and resolving was successful.
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
        self.fullname = (self.modname or '') + (self.objpath and
                                                '.' + '.'.join(self.objpath) or '')
        return True

    def import_object(self):
        try:
            __import__(self.modname)
            obj = self.module = sys.modules[self.modname]
            for part in self.objpath:
                obj = self.get_attr(obj, part)
            self.object = obj
            return True
        except (ImportError, AttributeError), err:
            self.directive.warn(
                'autodoc can\'t import/find %s %r, it reported error: '
                '"%s", please check your spelling and sys.path' %
                (self.objtype, str(self.fullname), err))
            return False

    def get_real_modname(self):
        return self.get_attr(self.object, '__module__', None) or self.modname

    def check_module(self):
        modname = self.get_attr(self.object, '__module__', None)
        if modname and modname != self.modname:
            return False
        return True

    def format_args(self):
        return None

    def format_signature(self):
        if self.args is not None:
            # signature given explicitly
            args = "(%s)" % self.args
        else:
            # try to introspect the signature
            args = self.format_args()
        if args is None:
            return ''
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
        directive = getattr(self, 'directivetype', self.objtype)
        # the name to put into the generated directive -- doesn't contain
        # the module (except for module directive of course)
        name_in_directive = '.'.join(self.objpath) or self.modname
        self.add_line(u'.. %s:: %s%s' % (directive, name_in_directive, sig),
                      '<autodoc>')
        if self.options.noindex:
            self.add_line(u'   :noindex:', '<autodoc>')
        if self.objpath:
            # Be explicit about the module, this is necessary since .. class::
            # etc. don't support a prepended module name
            self.add_line(u'   :module: %s' % self.modname, '<autodoc>')

    def get_doc(self, encoding=None):
        """Decode and return lines of the docstring(s) for the object."""
        docstring = self.get_attr(self.object, '__doc__', None)
        if docstring:
            # make sure we have Unicode docstrings, then sanitize and split
            # into lines
            return [prepare_docstring(force_decode(docstring, encoding))]
        return []

    def process_doc(self, docstrings):
        """Let the user process the docstrings."""
        for docstringlines in docstrings:
            if self.env.app:
                # let extensions preprocess docstrings
                self.env.app.emit('autodoc-process-docstring',
                                  self.objtype, self.fullname, self.object,
                                  self.options, docstringlines)
            for line in docstringlines:
                yield line

    def add_content(self, more_content, no_docstring=False):
        # set sourcename and add content from attribute documentation
        if self.analyzer:
            # prevent encoding errors when the file name is non-ASCII
            filename = unicode(self.analyzer.srcname,
                               sys.getfilesystemencoding(), 'replace')
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
            for i, line in enumerate(self.process_doc(docstrings)):
                self.add_line(line, sourcename, i)

        # add additional content (e.g. from document), if present
        if more_content:
            for line, src in zip(more_content.data, more_content.items):
                self.add_line(line, src[0], src[1])

    def get_object_members(self, want_all):
        if not want_all:
            if not self.options.members:
                return False, []
            # specific members given
            ret = []
            for mname in self.options.members:
                try:
                    ret.append((mname, self.get_attr(self.object, mname)))
                except AttributeError:
                    self.directive.warn('missing attribute %s in object %s'
                                        % (mname, self.fullname))
            return False, ret
        elif self.options.inherited_members:
            # getmembers() uses dir() which pulls in members from all
            # base classes
            return False, inspect.getmembers(self.object)
        else:
            # __dict__ contains only the members directly defined in
            # the class (but get them via getattr anyway, to e.g. get
            # unbound method objects instead of function objects)
            return False, sorted([(mname, self.get_attr(self.object, mname))
                                  for mname in self.object.__dict__])

    def filter_members(self, members, want_all):
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

            if want_all and membername.startswith('_'):
                # ignore members whose name starts with _ by default
                skip = True
            elif (namespace, membername) in attr_docs:
                # keep documented attributes
                skip = False
                isattr = True
            else:
                # ignore undocumented members if :undoc-members:
                # is not given
                doc = self.get_attr(member, '__doc__', None)
                skip = not self.options.undoc_members and not doc

            # give the user a chance to decide whether this member
            # should be skipped
            if self.env.app:
                # let extensions preprocess docstrings
                skip_user = self.env.app.emit_firstresult(
                    'autodoc-skip-member', self.objtype, membername, member,
                    skip, self.options)
                if skip_user is not None:
                    skip = skip_user
            if skip:
                continue

            ret.append((membername, member, isattr))

        return ret

    def document_members(self, all_members=False):
        # set current namespace for finding members
        self.env.autodoc_current_module = self.modname
        if self.objpath:
            self.env.autodoc_current_class = self.objpath[0]

        want_all = all_members or self.options.inherited_members or \
                   self.options.members is ALL
        # find out which members are documentable
        members_check_module, members = self.get_object_members(want_all)

        # document non-skipped members
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
            memberdocmtr = classes[-1](self.directive, full_mname,
                                       self.indent)
            memberdocmtr.generate(all_members=True,
                                  real_modname=self.real_modname,
                                  check_module=members_check_module)

        # reset current objects
        self.env.autodoc_current_module = None
        self.env.autodoc_current_class = None

    def generate(self, more_content=None, real_modname=None,
                 check_module=False, all_members=False):
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
            # parse right now, to get PycodeErrors on parsing
            self.analyzer.parse()
        except PycodeError, err:
            # no source file -- e.g. for builtin and C modules
            self.analyzer = None
        else:
            self.directive.filename_set.add(self.analyzer.srcname)

        # check __module__ of object (for members not given explicitly)
        if check_module:
            if not self.check_module():
                return

        # make sure that the result starts with an empty line.  This is
        # necessary for some situations where another directive preprocesses
        # reST and no starting newline is present
        self.add_line(u'', '')

        # format the object's signature, if any
        try:
            sig = self.format_signature()
        except Exception, err:
            self.directive.warn('error while formatting signature for '
                                '%s: %s' % (self.fullname, err))
            sig = ''

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
    objtype = 'module'
    content_indent = u''

    option_spec = {
        'members': members_option, 'undoc-members': bool_option,
        'noindex': bool_option, 'inherited-members': bool_option,
        'show-inheritance': bool_option, 'synopsis': identity,
        'platform': identity, 'deprecated': bool_option,
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
                return True, inspect.getmembers(self.object)
            else:
                memberlist = self.object.__all__
        else:
            memberlist = self.options.members or []
        ret = []
        for mname in memberlist:
            try:
                ret.append((mname, getattr(self.object, mname)))
            except AttributeError:
                self.directive.warn('missing attribute mentioned in :members: '
                                    'or __all__: module %s, attribute %s' %
                                    (self.object.__name__, mname))
        return False, ret


class ModuleLevelDocumenter(Documenter):
    def resolve_name(self, modname, parents, path, base):
        if modname is None:
            if path:
                modname = path.rstrip('.')
            else:
                # if documenting a toplevel object without explicit module,
                # it can be contained in another auto directive ...
                if hasattr(self.env, 'autodoc_current_module'):
                    modname = self.env.autodoc_current_module
                # ... or in the scope of a module directive
                if not modname:
                    modname = self.env.currmodule
                # ... else, it stays None, which means invalid
        return modname, parents + [base]


class ClassLevelDocumenter(Documenter):
    def resolve_name(self, modname, parents, path, base):
        if modname is None:
            if path:
                mod_cls = path.rstrip('.')
            else:
                mod_cls = None
                # if documenting a class-level object without path,
                # there must be a current class, either from a parent
                # auto directive ...
                if hasattr(self.env, 'autodoc_current_class'):
                    mod_cls = self.env.autodoc_current_class
                # ... or from a class directive
                if mod_cls is None:
                    mod_cls = self.env.currclass
                # ... if still None, there's no way to know
                if mod_cls is None:
                    return None, []
            modname, cls = rpartition(mod_cls, '.')
            parents = [cls]
            # if the module name is still missing, get it like above
            if not modname and hasattr(self.env, 'autodoc_current_module'):
                modname = self.env.autodoc_current_module
            if not modname:
                modname = self.env.currmodule
            # ... else, it stays None, which means invalid
        return modname, parents + [base]


class FunctionDocumenter(ModuleLevelDocumenter):
    objtype = 'function'

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, (FunctionType, BuiltinFunctionType))

    def format_args(self):
        if inspect.isbuiltin(self.object) or \
               inspect.ismethoddescriptor(self.object):
            # can never get arguments of a C function or method
            return None
        try:
            argspec = inspect.getargspec(self.object)
        except TypeError:
            # if a class should be documented as function (yay duck
            # typing) we try to use the constructor signature as function
            # signature without the first argument.
            try:
                argspec = inspect.getargspec(self.object.__new__)
            except TypeError:
                argspec = inspect.getargspec(self.object.__init__)
                if argspec[0]:
                    del argspec[0][0]
        return inspect.formatargspec(*argspec)

    def document_members(self, all_members=False):
        pass


class ClassDocumenter(ModuleLevelDocumenter):
    objtype = 'class'
    option_spec = {
        'members': members_option, 'undoc-members': bool_option,
        'noindex': bool_option, 'inherited-members': bool_option,
        'show-inheritance': bool_option,
    }

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, (type, ClassType))

    def import_object(self):
        ret = ModuleLevelDocumenter.import_object(self)
        # if the class is documented under another name, document it
        # as data/attribute
        if ret:
            self.doc_as_attr = (self.objpath[-1] != self.object.__name__)
        return ret

    def format_args(self):
        args = None
        # for classes, the relevant signature is the __init__ method's
        initmeth = self.get_attr(self.object, '__init__', None)
        # classes without __init__ method, default __init__ or
        # __init__ written in C?
        if initmeth is None or initmeth is object.__init__ or not \
               (inspect.ismethod(initmeth) or inspect.isfunction(initmeth)):
            return None
        argspec = inspect.getargspec(initmeth)
        if argspec[0] and argspec[0][0] in ('cls', 'self'):
            del argspec[0][0]
        return inspect.formatargspec(*argspec)

    def format_signature(self):
        if self.doc_as_attr:
            return ''
        return ModuleLevelDocumenter.format_signature(self)

    def add_directive_header(self, sig):
        if self.doc_as_attr:
            self.directivetype = 'attribute'
        Documenter.add_directive_header(self, sig)

        # add inheritance info, if wanted
        if not self.doc_as_attr and self.options.show_inheritance:
            self.add_line(u'', '<autodoc>')
            if len(self.object.__bases__):
                bases = [b.__module__ == '__builtin__' and
                         u':class:`%s`' % b.__name__ or
                         u':class:`%s.%s`' % (b.__module__, b.__name__)
                         for b in self.object.__bases__]
                self.add_line(_(u'   Bases: %s') % ', '.join(bases),
                              '<autodoc>')

    def get_doc(self, encoding=None):
        content = self.env.config.autoclass_content

        docstrings = []
        docstring = self.get_attr(self.object, '__doc__', None)
        if docstring:
            docstrings.append(docstring)

        # for classes, what the "docstring" is can be controlled via a
        # config value; the default is only the class docstring
        if content in ('both', 'init'):
            initdocstring = self.get_attr(
                self.get_attr(self.object, '__init__', None), '__doc__')
            # for new-style classes, no __init__ means default __init__
            if initdocstring == object.__init__.__doc__:
                initdocstring = None
            if initdocstring:
                if content == 'init':
                    docstrings = [initdocstring]
                else:
                    docstrings.append(initdocstring)

        return [prepare_docstring(force_decode(docstring, encoding))
                for docstring in docstrings]

    def add_content(self, more_content, no_docstring=False):
        if self.doc_as_attr:
            content = ViewList(
                [_('alias of :class:`%s`') % self.object.__name__], source='')
            ModuleLevelDocumenter.add_content(self, content, no_docstring=True)
        else:
            ModuleLevelDocumenter.add_content(self, more_content)

    def document_members(self, all_members=False):
        if self.doc_as_attr:
            return
        ModuleLevelDocumenter.document_members(self, all_members)


class ExceptionDocumenter(ClassDocumenter):
    objtype = 'exception'

    # needs a higher priority than ClassDocumenter
    priority = 10

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, (type, ClassType)) and \
               issubclass(member, base_exception)


class DataDocumenter(ModuleLevelDocumenter):
    objtype = 'data'

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(parent, ModuleDocumenter) and isattr

    def document_members(self, all_members=False):
        pass


class MethodDocumenter(ClassLevelDocumenter):
    objtype = 'method'

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        # other attributes are recognized via the module analyzer
        return inspect.isroutine(member) and \
               not isinstance(parent, ModuleDocumenter)

    def import_object(self):
        ret = ClassLevelDocumenter.import_object(self)
        if isinstance(self.object, classmethod) or \
               (isinstance(self.object, MethodType) and
                self.object.im_self is not None):
            self.directivetype = 'classmethod'
        elif isinstance(self.object, FunctionType) or \
             (isinstance(self.object, BuiltinFunctionType) and
              self.object.__self__ is not None):
            self.directivetype = 'staticmethod'
        else:
            self.directivetype = 'method'
        return ret

    def format_args(self):
        if inspect.isbuiltin(self.object) or \
               inspect.ismethoddescriptor(self.object):
            # can never get arguments of a C function or method
            return None
        argspec = inspect.getargspec(self.object)
        if argspec[0] and argspec[0][0] in ('cls', 'self'):
            del argspec[0][0]
        return inspect.formatargspec(*argspec)

    def document_members(self, all_members=False):
        pass


class AttributeDocumenter(ClassLevelDocumenter):
    objtype = 'attribute'

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isdescriptor(member) or \
               (not isinstance(parent, ModuleDocumenter) and isattr)

    def document_members(self, all_members=False):
        pass


class AutoDirective(Directive):
    # a registry of objtype -> documenter class
    _registry = {}

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

        # find out what documenter to call
        objtype = self.name[4:]
        doc_class = self._registry[objtype]
        # process the options with the selected documenter's option_spec
        self.genopt = Options(assemble_option_dict(
            self.options.items(), doc_class.option_spec))
        # generate the output
        documenter = doc_class(self, self.arguments[0])
        documenter.generate(more_content=self.content)
        if not self.result:
            return self.warnings

        # use a custom reporter that correctly assigns lines to source
        # filename/description and lineno
        old_reporter = self.state.memo.reporter
        self.state.memo.reporter = AutodocReporter(self.result,
                                                   self.state.memo.reporter)
        if self.name == 'automodule':
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
    if not issubclass(cls, Documenter):
        raise ExtensionError('autodoc documenter %r must be a subclass '
                             'of Documenter' % cls)
    if cls.objtype in AutoDirective._registry:
        raise ExtensionError('autodoc documenter for %r is already '
                             'registered' % cls.objtype)
    AutoDirective._registry[cls.objtype] = cls


def setup(app):
    app.add_autodocumenter(ModuleDocumenter)
    app.add_autodocumenter(ClassDocumenter)
    app.add_autodocumenter(ExceptionDocumenter)
    app.add_autodocumenter(DataDocumenter)
    app.add_autodocumenter(FunctionDocumenter)
    app.add_autodocumenter(MethodDocumenter)
    app.add_autodocumenter(AttributeDocumenter)

    app.add_config_value('autoclass_content', 'class', True)
    app.add_event('autodoc-process-docstring')
    app.add_event('autodoc-process-signature')
    app.add_event('autodoc-skip-member')
