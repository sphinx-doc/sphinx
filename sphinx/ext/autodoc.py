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
import linecache
from types import FunctionType, BuiltinFunctionType, MethodType, ClassType

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList

from sphinx.util import rpartition, nested_parse_with_titles, force_decode
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.util.docstrings import prepare_docstring

clstypes = (type, ClassType)
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


class Options(object):
    pass


def get_method_type(obj):
    """
    Return the method type for an object: method, staticmethod or classmethod.
    """
    if isinstance(obj, classmethod) or \
           (isinstance(obj, MethodType) and obj.im_self is not None):
        return 'classmethod'
    elif isinstance(obj, FunctionType) or \
             (isinstance(obj, BuiltinFunctionType) and obj.__self__ is not None):
        return 'staticmethod'
    else:
        return 'method'


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


class RstGenerator(object):
    def __init__(self, options, document, lineno):
        self.options = options
        self.env = document.settings.env
        self.reporter = document.reporter
        self.lineno = lineno
        self.filename_set = set()
        self.warnings = []
        self.result = ViewList()

    def warn(self, msg):
        self.warnings.append(self.reporter.warning(msg, line=self.lineno))

    def get_doc(self, what, obj, encoding=None):
        """Decode and return lines of the docstring(s) for the object."""
        docstrings = []

        # add the regular docstring if present
        if getattr(obj, '__doc__', None):
            docstrings.append(obj.__doc__)

        # skip some lines in module docstrings if configured (deprecated!)
        if what == 'module' and self.env.config.automodule_skip_lines and docstrings:
            docstrings[0] = '\n'.join(docstrings[0].splitlines()
                                      [self.env.config.automodule_skip_lines:])

        # for classes, what the "docstring" is can be controlled via an option
        if what in ('class', 'exception'):
            content = self.env.config.autoclass_content
            if content in ('both', 'init'):
                initdocstring = getattr(obj, '__init__', None).__doc__
                # for new-style classes, no __init__ means default __init__
                if initdocstring == object.__init__.__doc__:
                    initdocstring = None
                if initdocstring:
                    if content == 'init':
                        docstrings = [initdocstring]
                    else:
                        docstrings.append(initdocstring)
            # the default is only the class docstring

        # make sure we have Unicode docstrings, then sanitize and split into lines
        return [prepare_docstring(force_decode(docstring, encoding))
                for docstring in docstrings]

    def process_doc(self, docstrings, what, name, obj):
        """Let the user process the docstrings."""
        for docstringlines in docstrings:
            if self.env.app:
                # let extensions preprocess docstrings
                self.env.app.emit('autodoc-process-docstring',
                                  what, name, obj, self.options, docstringlines)
            for line in docstringlines:
                yield line

    def resolve_name(self, what, name):
        """
        Determine what module to import and what attribute to document.

        Returns a tuple of: the full name, the module name, a path of
        names to get via getattr, the signature and return annotation.
        """
        # first, parse the definition -- auto directives for classes and functions
        # can contain a signature which is then used instead of an autogenerated one
        try:
            mod, path, base, args, retann = py_ext_sig_re.match(name).groups()
        except:
            self.warn('invalid signature for auto%s (%r)' % (what, name))
            return None, [], None, None

        # support explicit module and class name separation via ::
        if mod is not None:
            mod = mod[:-2]
            parents = path and path.rstrip('.').split('.') or []
        else:
            parents = []

        if what == 'module':
            if mod is not None:
                self.warn('"::" in automodule name doesn\'t make sense')
            if args or retann:
                self.warn('ignoring signature arguments and return annotation '
                          'for automodule %s' % name)
            return (path or '') + base, [], None, None

        elif what in ('exception', 'function', 'class', 'data'):
            if mod is None:
                if path:
                    mod = path.rstrip('.')
                else:
                    # if documenting a toplevel object without explicit module, it can
                    # be contained in another auto directive ...
                    if hasattr(self.env, 'autodoc_current_module'):
                        mod = self.env.autodoc_current_module
                    # ... or in the scope of a module directive
                    if not mod:
                        mod = self.env.currmodule
            return mod, parents + [base], args, retann

        else:
            if mod is None:
                if path:
                    mod_cls = path.rstrip('.')
                else:
                    mod_cls = None
                    # if documenting a class-level object without path, there must be a
                    # current class, either from a parent auto directive ...
                    if hasattr(self.env, 'autodoc_current_class'):
                        mod_cls = self.env.autodoc_current_class
                    # ... or from a class directive
                    if mod_cls is None:
                        mod_cls = self.env.currclass
                    # ... if still None, there's no way to know
                    if mod_cls is None:
                        return None, [], None, None
                mod, cls = rpartition(mod_cls, '.')
                parents = [cls]
                # if the module name is still missing, get it like above
                if not mod and hasattr(self.env, 'autodoc_current_module'):
                    mod = self.env.autodoc_current_module
                if not mod:
                    mod = self.env.currmodule
            return mod, parents + [base], args, retann

    def format_signature(self, what, name, obj, args, retann):
        """
        Return the signature of the object, formatted for display.
        """
        if what not in ('class', 'method', 'staticmethod', 'classmethod',
                        'function'):
            return ''

        err = None
        if args is not None:
            # signature given explicitly
            args = "(%s)" % args
        else:
            # try to introspect the signature
            try:
                args = None
                getargs = True
                if what == 'class':
                    # for classes, the relevant signature is the __init__ method's
                    obj = getattr(obj, '__init__', None)
                    # classes without __init__ method, default __init__ or
                    # __init__ written in C?
                    if obj is None or obj is object.__init__ or not \
                       (inspect.ismethod(obj) or inspect.isfunction(obj)):
                        getargs = False
                elif inspect.isbuiltin(obj) or inspect.ismethoddescriptor(obj):
                    # can never get arguments of a C function or method
                    getargs = False
                if getargs:
                    try:
                        argspec = inspect.getargspec(obj)
                    except TypeError:
                        # if a class should be documented as function (yay duck
                        # typing) we try to use the constructor signature as function
                        # signature without the first argument.
                        try:
                            argspec = inspect.getargspec(obj.__new__)
                        except TypeError:
                            argspec = inspect.getargspec(obj.__init__)
                        if argspec[0]:
                            del argspec[0][0]
                    if what in ('class', 'method', 'staticmethod',
                                'classmethod') and argspec[0] and \
                           argspec[0][0] in ('cls', 'self'):
                        del argspec[0][0]
                    args = inspect.formatargspec(*argspec)
            except Exception, e:
                args = None
                err = e

        result = self.env.app.emit_firstresult('autodoc-process-signature', what,
                                               name, obj, self.options, args, retann)
        if result:
            args, retann = result

        if args is not None:
            return '%s%s' % (args, retann and (' -> %s' % retann) or '')
        elif err:
            # re-raise the error for perusal of the handler in generate()
            raise RuntimeError(err)
        else:
            return ''

    def generate(self, what, name, members, add_content, indent=u'', check_module=False,
                 no_docstring=False, real_module=None):
        """
        Generate reST for the object in self.result.
        """
        mod, objpath, args, retann = self.resolve_name(what, name)
        if not mod:
            # need a module to import
            self.warn('don\'t know which module to import for autodocumenting %r '
                      '(try placing a "module" or "currentmodule" directive in the '
                      'document, or giving an explicit module name)' % name)
            return
        # fully-qualified name
        fullname = mod + (objpath and '.' + '.'.join(objpath) or '')

        # the name to put into the generated directive -- doesn't contain the module
        name_in_directive = '.'.join(objpath) or mod

        # now, import the module and get object to document
        try:
            __import__(mod)
            todoc = module = sys.modules[mod]
            for part in objpath:
                todoc = getattr(todoc, part)
        except (ImportError, AttributeError), err:
            self.warn('autodoc can\'t import/find %s %r, it reported error: "%s", '
                      'please check your spelling and sys.path' %
                      (what, str(fullname), err))
            return

        # if there is no real-module defined figure out which to use.  The real module
        # is used in the module analyzer to look up the module where the attribute
        # documentation would actually be found in.
        # This is used for situations where you have a module that collects the
        # functions and classes of internal submodules.
        if real_module is None:
            real_module = getattr(todoc, '__module__', None) or mod

        # try to also get a source code analyzer for attribute docs
        try:
            analyzer = ModuleAnalyzer.for_module(real_module)
            # parse right now, to get PycodeErrors on parsing
            analyzer.parse()
        except PycodeError, err:
            # no source file -- e.g. for builtin and C modules
            analyzer = None
        else:
            self.filename_set.add(analyzer.srcname)

        # check __module__ of object if wanted (for members not given explicitly)
        if check_module:
            if hasattr(todoc, '__module__'):
                if todoc.__module__ != mod:
                    return

        # make sure that the result starts with an empty line.  This is
        # necessary for some situations where another directive preprocesses
        # reST and no starting newline is present
        self.result.append(u'', '')

        # format the object's signature, if any
        try:
            sig = self.format_signature(what, fullname, todoc, args, retann)
        except Exception, err:
            self.warn('error while formatting signature for %s: %s' %
                      (fullname, err))
            sig = ''

        # now, create the directive header
        if what == 'method':
            directive = get_method_type(todoc)
        else:
            directive = what
        self.result.append(indent + u'.. %s:: %s%s' %
                           (directive, name_in_directive, sig), '<autodoc>')
        if what == 'module':
            # Add some module-specific options
            if self.options.synopsis:
                self.result.append(indent + u'   :synopsis: ' + self.options.synopsis,
                              '<autodoc>')
            if self.options.platform:
                self.result.append(indent + u'   :platform: ' + self.options.platform,
                              '<autodoc>')
            if self.options.deprecated:
                self.result.append(indent + u'   :deprecated:', '<autodoc>')
        else:
            # Be explicit about the module, this is necessary since .. class:: doesn't
            # support a prepended module name
            self.result.append(indent + u'   :module: %s' % mod, '<autodoc>')
        if self.options.noindex:
            self.result.append(indent + u'   :noindex:', '<autodoc>')
        self.result.append(u'', '<autodoc>')

        # add inheritance info, if wanted
        if self.options.show_inheritance and what in ('class', 'exception'):
            if len(todoc.__bases__):
                bases = [b.__module__ == '__builtin__' and
                         u':class:`%s`' % b.__name__ or
                         u':class:`%s.%s`' % (b.__module__, b.__name__)
                         for b in todoc.__bases__]
                self.result.append(indent + _(u'   Bases: %s') % ', '.join(bases),
                                   '<autodoc>')
                self.result.append(u'', '<autodoc>')

        # the module directive doesn't have content
        if what != 'module':
            indent += u'   '

        # add content from attribute documentation
        if analyzer:
            # prevent encoding errors when the file name is non-ASCII
            srcname = unicode(analyzer.srcname,
                              sys.getfilesystemencoding(), 'replace')
            sourcename = u'%s:docstring of %s' % (srcname, fullname)
            attr_docs = analyzer.find_attr_docs()
            key = ('.'.join(objpath[:-1]), objpath[-1])
            if key in attr_docs:
                no_docstring = True
                docstrings = [attr_docs[key]]
                for i, line in enumerate(self.process_doc(docstrings, what,
                                                          fullname, todoc)):
                    self.result.append(indent + line, sourcename, i)
        else:
            sourcename = u'docstring of %s' % fullname
            attr_docs = {}

        # add content from docstrings
        if not no_docstring:
            encoding = analyzer and analyzer.encoding
            docstrings = self.get_doc(what, todoc, encoding)
            for i, line in enumerate(self.process_doc(docstrings, what,
                                                      fullname, todoc)):
                self.result.append(indent + line, sourcename, i)

        # add additional content (e.g. from document), if present
        if add_content:
            for line, src in zip(add_content.data, add_content.items):
                self.result.append(indent + line, src[0], src[1])

        # document members?
        if not members or what in ('function', 'method', 'staticmethod',
                                   'classmethod', 'data', 'attribute'):
            return

        # set current namespace for finding members
        self.env.autodoc_current_module = mod
        if objpath:
            self.env.autodoc_current_class = objpath[0]

        # look for members to include
        want_all_members = members == ['__all__']
        members_check_module = False
        if want_all_members:
            # unqualified :members: given
            if what == 'module':
                if hasattr(todoc, '__all__'):
                    members_check_module = False
                    all_members = []
                    for mname in todoc.__all__:
                        try:
                            all_members.append((mname, getattr(todoc, mname)))
                        except AttributeError:
                            self.warn('missing attribute mentioned in __all__: '
                                      'module %s, attribute %s' %
                                      (todoc.__name__, mname))
                else:
                    # for implicit module members, check __module__ to avoid
                    # documenting imported objects
                    members_check_module = True
                    all_members = inspect.getmembers(todoc)
            else:
                if self.options.inherited_members:
                    # getmembers() uses dir() which pulls in members from all
                    # base classes
                    all_members = inspect.getmembers(todoc)
                else:
                    # __dict__ contains only the members directly defined in the class
                    all_members = sorted(todoc.__dict__.iteritems())
        else:
            all_members = [(mname, getattr(todoc, mname)) for mname in members]

        # search for members in source code too
        namespace = '.'.join(objpath)  # will be empty for modules

        for (membername, member) in all_members:
            # if isattr is True, the member is documented as an attribute
            isattr = False
            # if content is not None, no extra content from docstrings will be added
            content = None

            if want_all_members and membername.startswith('_'):
                # ignore members whose name starts with _ by default
                skip = True
            else:
                if (namespace, membername) in attr_docs:
                    # keep documented attributes
                    skip = False
                    isattr = True
                else:
                    # ignore undocumented members if :undoc-members: is not given
                    doc = getattr(member, '__doc__', None)
                    skip = not self.options.undoc_members and not doc

            # give the user a chance to decide whether this member should be skipped
            if self.env.app:
                # let extensions preprocess docstrings
                skip_user = self.env.app.emit_firstresult(
                    'autodoc-skip-member', what, membername, member, skip, self.options)
                if skip_user is not None:
                    skip = skip_user
            if skip:
                continue

            # determine member type
            if what == 'module':
                if isinstance(member, (FunctionType, BuiltinFunctionType)):
                    memberwhat = 'function'
                elif isattr:
                    memberwhat = 'attribute'
                elif isinstance(member, clstypes):
                    if member.__name__ != membername:
                        # assume it's aliased
                        memberwhat = 'data'
                        content = ViewList([_('alias of :class:`%s`') % member.__name__],
                                           source='')
                    elif issubclass(member, base_exception):
                        memberwhat = 'exception'
                    else:
                        memberwhat = 'class'
                else:
                    continue
            else:
                if inspect.isroutine(member):
                    memberwhat = 'method'
                elif isattr:
                    memberwhat = 'attribute'
                elif isinstance(member, clstypes):
                    if member.__name__ != membername:
                        # assume it's aliased
                        memberwhat = 'attribute'
                        content = ViewList([_('alias of :class:`%s`') % member.__name__],
                                           source='')
                    else:
                        memberwhat = 'class'
                elif isdescriptor(member):
                    memberwhat = 'attribute'
                else:
                    continue

            # give explicitly separated module name, so that members of inner classes
            # can be documented
            full_membername = mod + '::' + '.'.join(objpath + [membername])
            self.generate(memberwhat, full_membername, ['__all__'],
                          add_content=content, no_docstring=bool(content),
                          indent=indent, check_module=members_check_module,
                          real_module=real_module)

        self.env.autodoc_current_module = None
        self.env.autodoc_current_class = None


def _auto_directive(dirname, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    what = dirname[4:]  # strip "auto"
    name = arguments[0]
    genopt = Options()
    members = options.get('members', [])
    genopt.inherited_members = 'inherited-members' in options
    if genopt.inherited_members and not members:
        # :inherited-members: implies :members:
        members = ['__all__']
    genopt.undoc_members = 'undoc-members' in options
    genopt.show_inheritance = 'show-inheritance' in options
    genopt.noindex = 'noindex' in options
    genopt.synopsis = options.get('synopsis', '')
    genopt.platform = options.get('platform', '')
    genopt.deprecated = 'deprecated' in options

    generator = RstGenerator(genopt, state.document, lineno)
    generator.generate(what, name, members, content)
    if not generator.result:
        return generator.warnings

    # record all filenames as dependencies -- this will at least partially make
    # automatic invalidation possible
    for fn in generator.filename_set:
        state.document.settings.env.note_dependency(fn)

    # use a custom reporter that correctly assigns lines to source and lineno
    old_reporter = state.memo.reporter
    state.memo.reporter = AutodocReporter(generator.result, state.memo.reporter)
    if dirname == 'automodule':
        node = nodes.section()
        nested_parse_with_titles(state, generator.result, node)
    else:
        node = nodes.paragraph()
        state.nested_parse(generator.result, 0, node)
    state.memo.reporter = old_reporter
    return generator.warnings + node.children

def auto_directive(*args, **kwds):
    return _auto_directive(*args, **kwds)

def automodule_directive(*args, **kwds):
    return _auto_directive(*args, **kwds)

def autoclass_directive(*args, **kwds):
    return _auto_directive(*args, **kwds)


def members_option(arg):
    if arg is None:
        return ['__all__']
    return [x.strip() for x in arg.split(',')]


def setup(app):
    mod_options = {'members': members_option, 'undoc-members': directives.flag,
                   'noindex': directives.flag, 'inherited-members': directives.flag,
                   'show-inheritance': directives.flag, 'synopsis': lambda x: x,
                   'platform': lambda x: x, 'deprecated': directives.flag}
    cls_options = {'members': members_option, 'undoc-members': directives.flag,
                   'noindex': directives.flag, 'inherited-members': directives.flag,
                   'show-inheritance': directives.flag}
    app.add_directive('automodule', automodule_directive,
                      1, (1, 0, 1), **mod_options)
    app.add_directive('autoclass', autoclass_directive,
                      1, (1, 0, 1), **cls_options)
    app.add_directive('autoexception', autoclass_directive,
                      1, (1, 0, 1), **cls_options)
    app.add_directive('autodata', auto_directive, 1, (1, 0, 1),
                      noindex=directives.flag)
    app.add_directive('autofunction', auto_directive, 1, (1, 0, 1),
                      noindex=directives.flag)
    app.add_directive('automethod', auto_directive, 1, (1, 0, 1),
                      noindex=directives.flag)
    app.add_directive('autoattribute', auto_directive, 1, (1, 0, 1),
                      noindex=directives.flag)
    # deprecated: remove in some future version.
    app.add_config_value('automodule_skip_lines', 0, True)
    app.add_config_value('autoclass_content', 'class', True)
    app.add_event('autodoc-process-docstring')
    app.add_event('autodoc-process-signature')
    app.add_event('autodoc-skip-member')
