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
    """Return the charset of the given module."""
    if module in _module_charsets:
        return _module_charsets[module]
    filename = __import__(module, None, None, ['']).__file__
    if filename[-4:] in ('.pyc', '.pyo'):
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


def generate_rst(what, name, members, inherited, undoc, add_content, document,
                 lineno, indent='', filename_set=None, check_module=False):
    env = document.settings.env

    # parse the definition
    try:
        mod, obj, signature = py_sig_re.match(name).groups()
    except:
        warning = document.reporter.warning(
            'invalid signature for auto%s (%r)' % (what, name), line=lineno)
        return [warning], ViewList()
    basename = (mod or '') + obj
    if mod:
        mod = mod.rstrip('.')

    warnings = []

    # find out what to import
    if what == 'module':
        mod = basename
        if signature:
            warnings.append(document.reporter.warning(
                'ignoring arguments for automodule %s' % mod, line=lineno))
        objpath = []
    elif what in ('class', 'exception', 'function'):
        if not mod and hasattr(env, 'autodoc_current_module'):
            mod = env.autodoc_current_module
        if not mod:
            mod = env.currmodule
        objpath = [obj]
    else:
        mod_cls = mod
        if not mod_cls and hasattr(env, 'autodoc_current_class'):
            mod_cls = env.autodoc_current_class
        if not mod_cls:
            mod_cls = env.currclass
        mod, cls = rpartition(mod_cls, '.')
        if not mod and hasattr(env, 'autodoc_current_module'):
            mod = env.autodoc_current_module
        if not mod:
            mod = env.currmodule
        objpath = [cls, obj]

    qualname = '.'.join(objpath) or mod
    result = ViewList()
    docstrings = []

    # make sure that the view list starts with an empty line.  This is
    # necessary for some situations where another directive preprocesses
    # rst and no starting newline is present
    result.append('', '')

    if mod is None:
        warnings.append(document.reporter.warning(
            'don\'t know which module to import for autodocumenting %r '
            '(try placing a "module" or "currentmodule" directive in the document, '
            'or giving an explicit module name)' % basename, line=lineno))
        return warnings, result

    # import module and get docstring of object to document
    try:
        todoc = module = __import__(mod, None, None, ['foo'])
        if filename_set is not None and hasattr(module, '__file__') and module.__file__:
            modfile = module.__file__
            if modfile.lower().endswith('.pyc') or modfile.lower().endswith('.pyo'):
                modfile = modfile[:-1]
            filename_set.add(modfile)
        for part in objpath:
            todoc = getattr(todoc, part)
        if check_module:
            # only checking __module__ for members not given explicitly
            if hasattr(todoc, '__module__'):
                if todoc.__module__ != mod:
                    return warnings, result
        if getattr(todoc, '__doc__', None):
            docstrings.append(todoc.__doc__)
    except (ImportError, AttributeError):
        warnings.append(document.reporter.warning(
            'autodoc can\'t import/find %s %r, check your spelling '
            'and sys.path' % (what, str(basename)), line=lineno))
        return warnings, result

    # add directive header
    if signature is not None:
        args = '(%s)' % signature
    else:
        try:
            if what == 'class':
                args = inspect.formatargspec(*inspect.getargspec(todoc.__init__))
                if args[1:7] == 'self, ':
                    args = '(' + args[7:]
                elif args == '(self)':
                    args = '()'
            elif what in ('function', 'method'):
                args = inspect.formatargspec(*inspect.getargspec(todoc))
                if what == 'method':
                    if args[1:7] == 'self, ':
                        args = '(' + args[7:]
                    elif args == '(self)':
                        args = '()'
            else:
                args = ''
        except Exception:
            args = ''
    result.append(indent + '.. %s:: %s%s' % (what, qualname, args), '<autodoc>')
    result.append('', '<autodoc>')

    # the module directive doesn't have content
    if what != 'module':
        indent += '   '

    # skip some lines in module docstrings if configured
    if what == 'module' and env.config.automodule_skip_lines and docstrings[0]:
        docstrings[0] = '\n'.join(docstring.splitlines()
                                  [env.config.automodule_skip_lines:])

    # for classes, what the "docstring" is can be controlled via an option
    if what in ('class', 'exception'):
        content = env.config.autoclass_content
        if content in ('both', 'init'):
            initdocstring = getattr(todoc, '__init__', None).__doc__
            # for new-style classes, no __init__ means default __init__
            if initdocstring == object.__init__.__doc__:
                initdocstring = None
            if initdocstring:
                if content == 'init':
                    docstrings = [initdocstring]
                else:
                    docstrings.append('\n\n' + initdocstring)
        # the default is only the class docstring

    # get the encoding of the docstring
    module = getattr(todoc, '__module__', None)
    if module is not None:
        charset = get_module_charset(module)
        docstrings = [docstring.decode(charset) for docstring in docstrings]

    # add docstring content
    for docstring in docstrings:
        docstring = prepare_docstring(docstring)
        for i, line in enumerate(docstring):
            result.append(indent + line, '<docstring of %s>' % basename, i)

    # add source content, if present
    if add_content:
        for line, src in zip(add_content.data, add_content.items):
            result.append(indent + line, src[0], src[1])

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
        if what == 'module':
            # for implicit module members, check __module__ to avoid documenting
            # imported objects
            members_check_module = True
            all_members = inspect.getmembers(todoc)
        else:
            if inherited:
                # getmembers() uses dir() which pulls in members from all base classes
                all_members = inspect.getmembers(todoc)
            else:
                # __dict__ contains only the members directly defined in the class
                all_members = sorted(todoc.__dict__.iteritems())
    else:
        all_members = [(mname, getattr(todoc, mname)) for mname in members]
    for (membername, member) in all_members:
        if _all and membername.startswith('_'):
            continue
        doc = getattr(member, '__doc__', None)
        if not undoc and not doc:
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
        full_membername = basename + '.' + membername
        subwarn, subres = generate_rst(memberwhat, full_membername, ['__all__'],
                                       inherited, undoc, None, document, lineno,
                                       indent, check_module=members_check_module)
        warnings.extend(subwarn)
        result.extend(subres)

    env.autodoc_current_module = None
    env.autodoc_current_class = None

    return warnings, result



def _auto_directive(dirname, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    what = dirname[4:]
    name = arguments[0]
    members = options.get('members', [])
    inherited = 'inherited-members' in options
    if inherited and not members:
        # :inherited-members: implies :members:
        members = ['__all__']
    undoc = 'undoc-members' in options

    filename_set = set()
    warnings, result = generate_rst(what, name, members, inherited, undoc, content,
                                    state.document, lineno, filename_set=filename_set)

    # record all filenames as dependencies -- this will at least partially make
    # automatic invalidation possible
    for fn in filename_set:
        state.document.settings.env.note_dependency(fn)

    if dirname == 'automodule':
        node = nodes.section()
        # hack around title style bookkeeping
        surrounding_title_styles = state.memo.title_styles
        surrounding_section_level = state.memo.section_level
        state.memo.title_styles = []
        state.memo.section_level = 0
        state.nested_parse(result, content_offset, node, match_titles=1)
        state.memo.title_styles = surrounding_title_styles
        state.memo.section_level = surrounding_section_level
    else:
        node = nodes.paragraph()
        state.nested_parse(result, content_offset, node)
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
                   'inherited-members': directives.flag}
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
