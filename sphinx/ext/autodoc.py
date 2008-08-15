# -*- coding: utf-8 -*-
"""
    sphinx.ext.autodoc
    ~~~~~~~~~~~~~~~~~~

    Automatically insert docstrings for functions, classes or whole modules into
    the doctree, thus avoiding duplication between docstrings and documentation
    for those who like elaborate docstrings.

    :copyright: 2008 by Georg Brandl, Pauli Virtanen.
    :license: BSD.
"""

import re
import sys
import types
import inspect
import textwrap
import linecache
from types import FunctionType, BuiltinMethodType, MethodType

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList

from sphinx.util import rpartition
from sphinx.directives.desc import py_sig_re

try:
    base_exception = BaseException
except NameError:
    base_exception = Exception

_charset_re = re.compile(r'coding[:=]\s*([-\w.]+)')
_module_charsets = {}


class Options(object):
    pass


def is_static_method(obj):
    """Check if the object given is a static method."""
    if isinstance(obj, (FunctionType, classmethod)):
        return True
    elif isinstance(obj, BuiltinMethodType):
        return obj.__self__ is not None
    elif isinstance(obj, MethodType):
        return obj.im_self is not None
    return False


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
        if callable(getattr(x, item, None)):
            return True
    return False


def prepare_docstring(s):
    """
    Convert a docstring into lines of parseable reST.  Return it as a list of
    lines usable for inserting into a docutils ViewList (used as argument
    of nested_parse().)  An empty line is added to act as a separator between
    this docstring and following content.
    """
    lines = s.expandtabs().splitlines()
    # Find minimum indentation of any non-blank lines after first line.
    margin = sys.maxint
    for line in lines[1:]:
        content = len(line.lstrip())
        if content:
            indent = len(line) - content
            margin = min(margin, indent)
    # Remove indentation.
    if lines:
        lines[0] = lines[0].lstrip()
    if margin < sys.maxint:
        for i in range(1, len(lines)): lines[i] = lines[i][margin:]
    # Remove any leading blank lines.
    while lines and not lines[0]:
        lines.pop(0)
    # make sure there is an empty line at the end
    if lines and lines[-1]:
        lines.append('')
    return lines


def get_module_charset(module):
    """Return the charset of the given module (cached in _module_charsets)."""
    if module in _module_charsets:
        return _module_charsets[module]
    try:
        filename = __import__(module, None, None, ['']).__file__
    except (ImportError, AttributeError):
        return None
    if filename[-4:].lower() in ('.pyc', '.pyo'):
        filename = filename[:-1]
    for line in [linecache.getline(filename, x) for x in (1, 2)]:
        match = _charset_re.search(line)
        if match is not None:
            charset = match.group(1)
            break
    else:
        charset = 'ascii'
    _module_charsets[module] = charset
    return charset


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

    def get_doc(self, what, name, obj):
        """Format and yield lines of the docstring(s) for the object."""
        docstrings = []
        if getattr(obj, '__doc__', None):
            docstrings.append(obj.__doc__)
        # skip some lines in module docstrings if configured
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
                        docstrings.append('\n\n' + initdocstring)
            # the default is only the class docstring

        # decode the docstrings using the module's source encoding
        charset = None
        module = getattr(obj, '__module__', None)
        if module is not None:
            charset = get_module_charset(module)

        for docstring in docstrings:
            if isinstance(docstring, str):
                if charset:
                    docstring = docstring.decode(charset)
                else:
                    try:
                        # try decoding with utf-8, should only work for real UTF-8
                        docstring = docstring.decode('utf-8')
                    except UnicodeError:
                        # last resort -- can't fail
                        docstring = docstring.decode('latin1')
            docstringlines = prepare_docstring(docstring)
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
            path, base, args, retann = py_sig_re.match(name).groups()
        except:
            self.warn('invalid signature for auto%s (%r)' % (what, name))
            return
        # fullname is the fully qualified name, base the name after the last dot
        fullname = (path or '') + base

        if what == 'module':
            if args or retann:
                self.warn('ignoring signature arguments and return annotation '
                          'for automodule %s' % fullname)
            return fullname, fullname, [], None, None

        elif what in ('class', 'exception', 'function'):
            if path:
                mod = path.rstrip('.')
            else:
                mod = None
                # if documenting a toplevel object without explicit module, it can
                # be contained in another auto directive ...
                if hasattr(self.env, 'autodoc_current_module'):
                    mod = self.env.autodoc_current_module
                # ... or in the scope of a module directive
                if not mod:
                    mod = self.env.currmodule
            return fullname, mod, [base], args, retann

        else:
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
            mod, cls = rpartition(mod_cls, '.')
            # if the module name is still missing, get it like above
            if not mod and hasattr(self.env, 'autodoc_current_module'):
                mod = self.env.autodoc_current_module
            if not mod:
                mod = self.env.currmodule
            return fullname, mod, [cls, base], args, retann

    def format_signature(self, what, name, obj, args, retann):
        """
        Return the signature of the object, formatted for display.
        """
        if what not in ('class', 'method', 'function'):
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
                    argspec = inspect.getargspec(obj)
                    if what in ('class', 'method') and argspec[0] and \
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
            return '%s%s' % (args, retann or '')
        elif err:
            # re-raise the error for perusal of the handler in generate()
            raise RuntimeError(err)
        else:
            return ''

    def generate(self, what, name, members, add_content, indent=u'', check_module=False):
        """
        Generate reST for the object in self.result.
        """
        fullname, mod, objpath, args, retann = self.resolve_name(what, name)
        if not mod:
            # need a module to import
            self.warn('don\'t know which module to import for autodocumenting %r '
                      '(try placing a "module" or "currentmodule" directive in the '
                      'document, or giving an explicit module name)' % fullname)
            return

        # the name to put into the generated directive -- doesn't contain the module
        name_in_directive = '.'.join(objpath) or mod

        # now, import the module and get object to document
        try:
            todoc = module = __import__(mod, None, None, ['foo'])
            if hasattr(module, '__file__') and module.__file__:
                modfile = module.__file__
                if modfile[-4:].lower() in ('.pyc', '.pyo'):
                    modfile = modfile[:-1]
                self.filename_set.add(modfile)
            else:
                modfile = None  # e.g. for builtin and C modules
            for part in objpath:
                todoc = getattr(todoc, part)
        except (ImportError, AttributeError), err:
            self.warn('autodoc can\'t import/find %s %r, it reported error: "%s", '
                      'please check your spelling and sys.path' %
                      (what, str(fullname), err))
            return

        # check __module__ of object if wanted (for members not given explicitly)
        if check_module:
            if hasattr(todoc, '__module__'):
                if todoc.__module__ != mod:
                    return

        # format the object's signature, if any
        try:
            sig = self.format_signature(what, name, todoc, args, retann)
        except Exception, err:
            self.warn('error while formatting signature for %s: %s' %
                      (fullname, err))
            sig = ''

        # make sure that the result starts with an empty line.  This is
        # necessary for some situations where another directive preprocesses
        # reST and no starting newline is present
        self.result.append(u'', '')

        # now, create the directive header
        directive = (what == 'method' and is_static_method(todoc)) \
                    and 'staticmethod' or what
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

        if self.options.show_inheritance and what in ('class', 'exception'):
            if len(todoc.__bases__):
                bases = [b.__module__ == '__builtin__' and
                         u':class:`%s`' % b.__name__ or
                         u':class:`%s.%s`' % (b.__module__, b.__name__)
                         for b in todoc.__bases__]
                self.result.append(indent + u'   Bases: %s' % ', '.join(bases),
                                   '<autodoc>')
                self.result.append(u'', '<autodoc>')

        # the module directive doesn't have content
        if what != 'module':
            indent += u'   '

        if modfile:
            sourcename = '%s:docstring of %s' % (modfile, fullname)
        else:
            sourcename = 'docstring of %s' % fullname

        # add content from docstrings
        for i, line in enumerate(self.get_doc(what, fullname, todoc)):
            self.result.append(indent + line, sourcename, i)

        # add source content, if present
        if add_content:
            for line, src in zip(add_content.data, add_content.items):
                self.result.append(indent + line, src[0], src[1])

        # document members?
        if not members or what in ('function', 'method', 'attribute'):
            return

        # set current namespace for finding members
        self.env.autodoc_current_module = mod
        if objpath:
            self.env.autodoc_current_class = objpath[0]

        # add members, if possible
        _all = members == ['__all__']
        members_check_module = False
        if _all:
            # unqualified :members: given
            if what == 'module':
                if hasattr(todoc, '__all__'):
                    members_check_module = False
                    all_members = inspect.getmembers(todoc, lambda x: x in todoc.__all__)
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
        for (membername, member) in all_members:
            # ignore members whose name starts with _ by default
            if _all and membername.startswith('_'):
                continue
            # ignore undocumented members if :undoc-members: is not given
            doc = getattr(member, '__doc__', None)
            if not self.options.undoc_members and not doc:
                continue
            if what == 'module':
                if isinstance(member, types.FunctionType):
                    memberwhat = 'function'
                elif isinstance(member, types.ClassType) or \
                     isinstance(member, type):
                    if issubclass(member, base_exception):
                        memberwhat = 'exception'
                    else:
                        memberwhat = 'class'
                else:
                    # XXX: todo -- attribute docs
                    continue
            else:
                if callable(member):
                    memberwhat = 'method'
                elif isdescriptor(member):
                    memberwhat = 'attribute'
                else:
                    # XXX: todo -- attribute docs
                    continue
            full_membername = fullname + '.' + membername
            self.generate(memberwhat, full_membername, ['__all__'], None, indent,
                          check_module=members_check_module)

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
        # hack around title style bookkeeping
        surrounding_title_styles = state.memo.title_styles
        surrounding_section_level = state.memo.section_level
        state.memo.title_styles = []
        state.memo.section_level = 0
        state.nested_parse(generator.result, 0, node, match_titles=1)
        state.memo.title_styles = surrounding_title_styles
        state.memo.section_level = surrounding_section_level
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
