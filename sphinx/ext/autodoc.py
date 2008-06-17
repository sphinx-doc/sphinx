# -*- coding: utf-8 -*-
"""
    sphinx.ext.autodoc
    ~~~~~~~~~~~~~~~~~~

    Automatically insert docstrings for functions, classes or whole modules into
    the doctree, thus avoiding duplication between docstrings and documentation
    for those who like elaborate docstrings.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

import re
import types
import inspect
import textwrap
import linecache

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
    if not s or s.isspace():
        return ['']
    s = s.expandtabs()
    nl = s.rstrip().find('\n')
    if nl == -1:
        # Only one line...
        return [s.strip(), '']
    # The first line may be indented differently...
    firstline = s[:nl].strip()
    otherlines = textwrap.dedent(s[nl+1:])
    return [firstline] + otherlines.splitlines() + ['']


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


def get_doc(what, obj, env):
    """Format and yield lines of the docstring(s) for the object."""
    docstrings = []
    if getattr(obj, '__doc__', None):
        docstrings.append(obj.__doc__)
    # skip some lines in module docstrings if configured
    if what == 'module' and env.config.automodule_skip_lines and docstrings:
        docstrings[0] = '\n'.join(docstrings[0].splitlines()
                                  [env.config.automodule_skip_lines:])
    # for classes, what the "docstring" is can be controlled via an option
    if what in ('class', 'exception'):
        content = env.config.autoclass_content
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
        for line in prepare_docstring(docstring):
            yield line


def format_signature(what, obj):
    """Return the signature of the object, formatted for display."""
    if what not in ('class', 'method', 'function'):
        return ''
    remove_self = what in ('class', 'method')
    if what == 'class':
        # for classes, the relevant signature is the __init__ method's
        obj = getattr(obj, '__init__', None)
        # classes without __init__ method?
        if obj is None or obj is object.__init__:
            return ''
    argspec = inspect.getargspec(obj)
    if remove_self and argspec[0][0:1] == ['self']:
        del argspec[0][0]
    return inspect.formatargspec(*argspec)


def generate_rst(what, name, members, options, add_content, document, lineno,
                 indent=u'', filename_set=None, check_module=False):
    env = document.settings.env

    result = None

    # first, parse the definition -- auto directives for classes and functions
    # can contain a signature which is then used instead of an autogenerated one
    try:
        path, base, signature = py_sig_re.match(name).groups()
    except:
        warning = document.reporter.warning(
            'invalid signature for auto%s (%r)' % (what, name), line=lineno)
        return [warning], result
    # fullname is the fully qualified name, base the name after the last dot
    fullname = (path or '') + base
    # path is the name up to the last dot
    path = path and path.rstrip('.')

    warnings = []

    # determine what module to import -- mod is the module name, objpath the
    # path of names to get via getattr
    mod = None
    if what == 'module':
        mod = fullname
        if signature:
            warnings.append(document.reporter.warning(
                'ignoring arguments for automodule %s' % mod, line=lineno))
        objpath = []
    elif what in ('class', 'exception', 'function'):
        if path:
            mod = path
        else:
            # if documenting a toplevel object without explicit module, it can
            # be contained in another auto directive ...
            if hasattr(env, 'autodoc_current_module'):
                mod = env.autodoc_current_module
            # ... or in the scope of a module directive
            if not mod:
                mod = env.currmodule
        objpath = [base]
    else:
        if path:
            mod_cls = path
        else:
            # if documenting a class-level object without path, there must be a
            # current class, either from a parent auto directive ...
            if hasattr(env, 'autodoc_current_class'):
                mod_cls = env.autodoc_current_class
            # ... or from a class directive
            if not mod_cls:
                mod_cls = env.currclass
        mod, cls = rpartition(mod_cls, '.')
        # if the module name is still missing, get it like above
        if not mod and hasattr(env, 'autodoc_current_module'):
            mod = env.autodoc_current_module
        if not mod:
            mod = env.currmodule
        objpath = [cls, base]

    # by this time, a module *must* be determined
    if mod is None:
        warnings.append(document.reporter.warning(
            'don\'t know which module to import for autodocumenting %r '
            '(try placing a "module" or "currentmodule" directive in the document, '
            'or giving an explicit module name)' % fullname, line=lineno))
        return warnings, result

    # the name to put into the generated directive -- doesn't contain the module
    name_in_directive = '.'.join(objpath) or mod

    # now, import the module and get docstring(s) of object to document
    try:
        todoc = module = __import__(mod, None, None, ['foo'])
        if hasattr(module, '__file__') and module.__file__:
            modfile = module.__file__
            if modfile[-4:].lower() in ('.pyc', '.pyo'):
                modfile = modfile[:-1]
            if filename_set is not None:
                filename_set.add(modfile)
        else:
            modfile = None  # e.g. for builtin and C modules
        for part in objpath:
            todoc = getattr(todoc, part)
    except (ImportError, AttributeError):
        warnings.append(document.reporter.warning(
            'autodoc can\'t import/find %s %r, check your spelling '
            'and sys.path' % (what, str(fullname)), line=lineno))
        return warnings, result

    # check __module__ of object if wanted (for members not given explicitly)
    if check_module:
        if hasattr(todoc, '__module__'):
            if todoc.__module__ != mod:
                return warnings, result

    # format the object's signature, if any
    if signature is not None:
        # signature given explicitly -- the parentheses were stripped by the regex
        args = '(%s)' % signature
    else:
        try:
            args = format_signature(what, todoc)
        except Exception, err:
            warnings.append(document.reporter.warning(
                'error while formatting signature for %s: %s' %
                (fullname, err), line=lineno))
            args = ''

    # make sure that the view list starts with an empty line.  This is
    # necessary for some situations where another directive preprocesses
    # reST and no starting newline is present
    result = ViewList()
    result.append(u'', '')

    # now, create the directive header
    result.append(indent + u'.. %s:: %s%s' % (what, name_in_directive, args),
                  '<autodoc>')
    if what != 'module':
        # Be explicit about the module, this is necessary since .. class:: doesn't
        # support a prepended module name
        result.append(indent + u'   :module: %s' % mod, '<autodoc>')
    result.append(u'', '<autodoc>')

    if options.show_inheritance and what in ('class', 'exception'):
        if len(todoc.__bases__):
            bases = [b.__module__ == '__builtin__' and
                     u':class:`%s`' % b.__name__ or
                     u':class:`%s.%s`' % (b.__module__, b.__name__)
                     for b in todoc.__bases__]
            result.append(indent + u'   Bases: %s' % ', '.join(bases), '<autodoc>')

    # the module directive doesn't have content
    if what != 'module':
        indent += u'   '

    if modfile:
        sourcename = '%s:docstring of %s' % (modfile, fullname)
    else:
        sourcename = 'docstring of %s' % fullname

    # add content from docstrings
    for i, line in enumerate(get_doc(what, todoc, env)):
        result.append(indent + line, sourcename, i)

    # add source content, if present
    if add_content:
        for line, src in zip(add_content.data, add_content.items):
            result.append(indent + line, src[0], src[1])

    # document members?
    if not members or what in ('function', 'method', 'attribute'):
        return warnings, result

    # set current namespace for finding members
    env.autodoc_current_module = mod
    if objpath:
        env.autodoc_current_class = objpath[0]

    # add members, if possible
    _all = members == ['__all__']
    members_check_module = False
    if _all:
        # unqualified :members: given
        if what == 'module':
            # for implicit module members, check __module__ to avoid documenting
            # imported objects
            members_check_module = True
            all_members = inspect.getmembers(todoc)
        else:
            if options.inherited:
                # getmembers() uses dir() which pulls in members from all base classes
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
        if not options.undoc and not doc:
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
        subwarn, subres = generate_rst(memberwhat, full_membername, ['__all__'],
                                       options, None, document, lineno, indent,
                                       check_module=members_check_module)
        warnings.extend(subwarn)
        if subres is not None:
            result.extend(subres)

    env.autodoc_current_module = None
    env.autodoc_current_class = None

    return warnings, result


def _auto_directive(dirname, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    what = dirname[4:]  # strip "auto"
    name = arguments[0]
    genopt = Options()
    members = options.get('members', [])
    genopt.inherited = 'inherited-members' in options
    if genopt.inherited and not members:
        # :inherited-members: implies :members:
        members = ['__all__']
    genopt.undoc = 'undoc-members' in options
    genopt.show_inheritance = 'show-inheritance' in options

    filename_set = set()
    warnings, result = generate_rst(what, name, members, genopt, content, state.document,
                                    lineno, filename_set=filename_set)
    if result is None:
        return warnings

    # record all filenames as dependencies -- this will at least partially make
    # automatic invalidation possible
    for fn in filename_set:
        state.document.settings.env.note_dependency(fn)

    # use a custom reporter that correctly assigns lines to source and lineno
    old_reporter = state.memo.reporter
    state.memo.reporter = AutodocReporter(result, state.memo.reporter)
    if dirname == 'automodule':
        node = nodes.section()
        # hack around title style bookkeeping
        surrounding_title_styles = state.memo.title_styles
        surrounding_section_level = state.memo.section_level
        state.memo.title_styles = []
        state.memo.section_level = 0
        state.nested_parse(result, 0, node, match_titles=1)
        state.memo.title_styles = surrounding_title_styles
        state.memo.section_level = surrounding_section_level
    else:
        node = nodes.paragraph()
        state.nested_parse(result, 0, node)
    state.memo.reporter = old_reporter
    return warnings + node.children

def auto_directive(*args, **kwds):
    return _auto_directive(*args, **kwds)

def auto_directive_withmembers(*args, **kwds):
    return _auto_directive(*args, **kwds)


def members_directive(arg):
    if arg is None:
        return ['__all__']
    return [x.strip() for x in arg.split(',')]


def setup(app):
    mod_options = {'members': members_directive, 'undoc-members': directives.flag}
    cls_options = {'members': members_directive, 'undoc-members': directives.flag,
                   'inherited-members': directives.flag,
                   'show-inheritance': directives.flag}
    app.add_directive('automodule', auto_directive_withmembers,
                      1, (1, 0, 1), **mod_options)
    app.add_directive('autoclass', auto_directive_withmembers,
                      1, (1, 0, 1), **cls_options)
    app.add_directive('autoexception', auto_directive_withmembers,
                      1, (1, 0, 1), **cls_options)
    app.add_directive('autofunction', auto_directive, 1, (1, 0, 1))
    app.add_directive('automethod', auto_directive, 1, (1, 0, 1))
    app.add_directive('autoattribute', auto_directive, 1, (1, 0, 1))
    app.add_config_value('automodule_skip_lines', 0, True)
    app.add_config_value('autoclass_content', 'class', True)
