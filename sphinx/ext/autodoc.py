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

import types
import inspect
import textwrap

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList

from sphinx.util import rpartition

try:
    base_exception = BaseException
except NameError:
    base_exception = Exception


def prepare_docstring(s):
    """
    Convert a docstring into lines of parseable reST.  Return it as a list of
    lines usable for inserting into a docutils ViewList (used as argument
    of nested_parse().)  An empty line is added to act as a separator between
    this docstring and following content.
    """
    if not s or s.isspace():
        return ['']
    nl = s.expandtabs().rstrip().find('\n')
    if nl == -1:
        # Only one line...
        return [s.strip(), '']
    # The first line may be indented differently...
    firstline = s[:nl].strip()
    otherlines = textwrap.dedent(s[nl+1:])
    return [firstline] + otherlines.splitlines() + ['']


def generate_rst(what, name, members, undoc, add_content,
                 document, lineno, indent=''):
    env = document.settings.env

    # find out what to import
    if what == 'module':
        mod = obj = name
        objpath = []
    elif what in ('class', 'exception', 'function'):
        mod, obj = rpartition(name, '.')
        if not mod and hasattr(env, 'autodoc_current_module'):
            mod = env.autodoc_current_module
        if not mod:
            mod = env.currmodule
        objpath = [obj]
    else:
        mod_cls, obj = rpartition(name, '.')
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

    result = ViewList()

    try:
        todoc = module = __import__(mod, None, None, ['foo'])
        for part in objpath:
            todoc = getattr(todoc, part)
        if hasattr(todoc, '__module__'):
            if todoc.__module__ != mod:
                return [], result
        docstring = todoc.__doc__
    except (ImportError, AttributeError):
        warning = document.reporter.warning(
            'autodoc can\'t import/find %s %r, check your spelling '
            'and sys.path' % (what, str(name)), line=lineno)
        return [warning], result

    # add directive header
    try:
        if what == 'class':
            args = inspect.formatargspec(*inspect.getargspec(todoc.__init__))
        elif what in ('function', 'method'):
            args = inspect.formatargspec(*inspect.getargspec(todoc))
            if what == 'method':
                if args[1:7] == 'self, ':
                    args = '(' + args[7:]
                elif args == '(self)':
                    args = '()'
        else:
            args = ''
    except:
        args = ''
    if len(objpath) == 2:
        qualname = '%s.%s' % (cls, obj)
    else:
        qualname = obj
    result.append(indent + '.. %s:: %s%s' % (what, qualname, args), '<autodoc>')
    result.append('', '<autodoc>')

    # the module directive doesn't like content
    if what != 'module':
        indent += '   '

    # add docstring content
    if what == 'module' and env.config.automodule_skip_lines:
        docstring = '\n'.join(docstring.splitlines()
                              [env.config.automodule_skip_lines:])
    docstring = prepare_docstring(docstring)
    for i, line in enumerate(docstring):
        result.append(indent + line, '<docstring of %s>' % name, i)

    # add source content, if present
    if add_content:
        for line, src in zip(add_content.data, add_content.items):
            result.append(indent + line, src[0], src[1])

    if not members or what in ('function', 'method', 'attribute'):
        return [], result

    env.autodoc_current_module = mod
    if objpath:
        env.autodoc_current_class = objpath[0]

    warnings = []
    # add members, if possible
    _all = members == ['__all__']
    if _all:
        all_members = sorted(inspect.getmembers(todoc))
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
            elif isinstance(member, property):
                memberwhat = 'attribute'
            else:
                # XXX: todo -- attribute docs
                continue
        full_membername = name + '.' + membername
        subwarn, subres = generate_rst(memberwhat, full_membername, ['__all__'],
                                       undoc, None, document, lineno, indent)
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
    undoc = 'undoc-members' in options

    warnings, result = generate_rst(what, name, members, undoc, content,
                                    state.document, lineno)

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
    options = {'members': members_directive, 'undoc-members': directives.flag}
    app.add_directive('automodule', auto_directive_withmembers,
                      1, (1, 0, 1), **options)
    app.add_directive('autoclass', auto_directive_withmembers,
                      1, (1, 0, 1), **options)
    app.add_directive('autoexception', auto_directive_withmembers,
                      1, (1, 0, 1), **options)
    app.add_directive('autofunction', auto_directive, 1, (1, 0, 1))
    app.add_directive('automethod', auto_directive, 1, (1, 0, 1))
    app.add_directive('autoattribute', auto_directive, 1, (1, 0, 1))
    app.add_config_value('automodule_skip_lines', 0, True)
