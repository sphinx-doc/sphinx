"""
    sphinx.ext.apidoc
    ~~~~~~~~~~~~~~~~~

    Parses a directory tree looking for Python modules and packages and creates
    ReST files appropriately to create code documentation with Sphinx.  It also
    creates a modules index (named modules.<suffix>).

    This is derived from the "sphinx-autopackage" script, which is:
    Copyright 2008 Société des arts technologiques (SAT),
    https://sat.qc.ca/

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import argparse
import glob
import importlib
import inspect
import locale
import os
import re
import sys
import warnings
from fnmatch import fnmatch
from functools import partial
from importlib.machinery import EXTENSION_SUFFIXES
from os import path
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import jinja2
from docutils import nodes
from docutils.parsers.rst.states import RSTStateMachine, state_classes
from docutils.utils import new_document, Reporter as NullReporter

import sphinx.locale
from sphinx import __display_version__, package_dir
from sphinx.cmd.quickstart import EXTENSIONS
from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.ext.autodoc import (AttributeDocumenter, ClassDocumenter,
                                DataDocumenter, DecoratorDocumenter,
                                Documenter, ExceptionDocumenter,
                                FunctionDocumenter,
                                InstanceAttributeDocumenter, MethodDocumenter,
                                ModuleDocumenter, PropertyDocumenter,
                                SlotsAttributeDocumenter)
from sphinx.ext.autosummary import FakeDirective
from sphinx.locale import __
from sphinx.util import rst
from sphinx.util.inspect import safe_getattr
from sphinx.util.osutil import FileAvoidWrite, ensuredir
from sphinx.util.template import ReSTRenderer

# automodule options
if 'SPHINX_APIDOC_OPTIONS' in os.environ:
    OPTIONS = os.environ['SPHINX_APIDOC_OPTIONS'].split(',')
else:
    OPTIONS = [
        'members',
        'undoc-members',
        # 'inherited-members', # disabled because there's a bug in sphinx
        'show-inheritance',
    ]

INITPY = '__init__.py'
PY_SUFFIXES = ('.py', '.pyx') + tuple(EXTENSION_SUFFIXES)

template_dir = path.join(package_dir, 'templates', 'apidoc')


def makename(package: str, module: str) -> str:
    """Join package and module with a dot."""
    warnings.warn('makename() is deprecated.',
                  RemovedInSphinx40Warning)
    # Both package and module can be None/empty.
    if package:
        name = package
        if module:
            name += '.' + module
    else:
        name = module
    return name


def module_join(*modnames: str) -> str:
    """Join module names with dots."""
    return '.'.join(filter(None, modnames))


def write_file(name: str, text: str, opts: Any) -> None:
    """Write the output file for module/package <name>."""
    fname = path.join(opts.destdir, '%s.%s' % (name, opts.suffix))
    if opts.dryrun:
        print(__('Would create file %s.') % fname)
        return
    if not opts.force and path.isfile(fname):
        print(__('File %s already exists, skipping.') % fname)
    else:
        print(__('Creating file %s.') % fname)
        with FileAvoidWrite(fname) as f:
            f.write(text)


def format_heading(level: int, text: str, escape: bool = True) -> str:
    """Create a heading of <level> [1, 2 or 3 supported]."""
    warnings.warn('format_warning() is deprecated.',
                  RemovedInSphinx40Warning)
    if escape:
        text = rst.escape(text)
    underlining = ['=', '-', '~', ][level - 1] * len(text)
    return '%s\n%s\n\n' % (text, underlining)


def format_directive(module: str, package: str = None) -> str:
    """Create the automodule directive and add the options."""
    warnings.warn('format_directive() is deprecated.',
                  RemovedInSphinx40Warning)
    directive = '.. automodule:: %s\n' % module_join(package, module)
    for option in OPTIONS:
        directive += '    :%s:\n' % option
    return directive


def create_module_file(package: Optional[str], basename: str, opts: Any,
                       user_template_dir: str = None) -> None:
    """Build the text of the file and write the file."""
    qualname = module_join(package, basename)
    context = {
        'show_headings': not opts.noheadings,
        'basename': basename,
        'qualname': qualname,
        'automodule_options': OPTIONS}
    renderer = ReSTRenderer([user_template_dir, template_dir])
    _add_get_members_to_template_env(renderer.env, qualname, opts)
    text = renderer.render('module.rst_t', context)
    write_file(qualname, text, opts)


def create_package_file(root: str, master_package: str, subroot: str, py_files: List[str],
                        opts: Any, subs: List[str], is_namespace: bool,
                        excludes: List[str] = [], user_template_dir: str = None) -> None:
    """Build the text of the file and write the file."""
    # build a list of sub packages (directories containing an INITPY file)
    subpackages = [sub for sub in subs if not
                   shall_skip(path.join(root, sub, INITPY), opts, excludes)]
    subpackages = [module_join(master_package, subroot, pkgname)
                   for pkgname in subpackages]
    # build a list of sub modules
    submodules = [path.splitext(sub)[0] for sub in py_files
                  if not is_skipped_module(path.join(root, sub), opts, excludes) and
                  sub != INITPY]
    submodules = [module_join(master_package, subroot, modname)
                  for modname in submodules]

    pkgname = module_join(master_package, subroot)
    context = {
        'pkgname': pkgname,
        'subpackages': subpackages,
        'submodules': submodules,
        'is_namespace': is_namespace,
        'modulefirst': opts.modulefirst,
        'separatemodules': opts.separatemodules,
        'automodule_options': OPTIONS,
        'show_headings': not opts.noheadings,
    }
    renderer = ReSTRenderer([user_template_dir, template_dir])
    _add_get_members_to_template_env(renderer.env, pkgname, opts)
    text = renderer.render('package.rst_t', context)
    write_file(pkgname, text, opts)

    if submodules and opts.separatemodules:
        for submodule in submodules:
            create_module_file(None, submodule, opts, user_template_dir)


def create_modules_toc_file(modules: List[str], opts: Any, name: str = 'modules',
                            user_template_dir: str = None) -> None:
    """Create the module's index."""
    modules.sort()
    prev_module = ''
    for module in modules[:]:
        # look if the module is a subpackage and, if yes, ignore it
        if module.startswith(prev_module + '.'):
            modules.remove(module)
        else:
            prev_module = module

    context = {
        'header': opts.header,
        'maxdepth': opts.maxdepth,
        'docnames': modules,
    }
    renderer = ReSTRenderer([user_template_dir, template_dir])
    text = renderer.render('toc.rst_t', context)
    write_file(name, text, opts)


def shall_skip(module: str, opts: Any, excludes: List[str] = []) -> bool:
    """Check if we want to skip this module."""
    # skip if the file doesn't exist and not using implicit namespaces
    if not opts.implicit_namespaces and not path.exists(module):
        return True

    # Are we a package (here defined as __init__.py, not the folder in itself)
    if os.path.basename(module) == INITPY:
        # Yes, check if we have any non-excluded modules at all here
        all_skipped = True
        basemodule = path.dirname(module)
        for submodule in glob.glob(path.join(basemodule, '*.py')):
            if not is_excluded(path.join(basemodule, submodule), excludes):
                # There's a non-excluded module here, we won't skip
                all_skipped = False
        if all_skipped:
            return True

    # skip if it has a "private" name and this is selected
    filename = path.basename(module)
    if filename != '__init__.py' and filename.startswith('_') and \
       not opts.includeprivate:
        return True
    return False


def is_skipped_module(filename: str, opts: Any, excludes: List[str]) -> bool:
    """Check if we want to skip this module."""
    if not path.exists(filename):
        # skip if the file doesn't exist
        return True
    elif path.basename(filename).startswith('_') and not opts.includeprivate:
        # skip if the module has a "private" name
        return True
    else:
        return False


def recurse_tree(rootpath: str, excludes: List[str], opts: Any,
                 user_template_dir: str = None) -> List[str]:
    """
    Look for every file in the directory tree and create the corresponding
    ReST files.
    """
    followlinks = getattr(opts, 'followlinks', False)
    includeprivate = getattr(opts, 'includeprivate', False)
    implicit_namespaces = getattr(opts, 'implicit_namespaces', False)

    # check if the base directory is a package and get its name
    if INITPY in os.listdir(rootpath) or implicit_namespaces:
        root_package = rootpath.split(path.sep)[-1]
    else:
        # otherwise, the base is a directory with packages
        root_package = None

    toplevels = []
    for root, subs, files in os.walk(rootpath, followlinks=followlinks):
        # document only Python module files (that aren't excluded)
        py_files = sorted(f for f in files
                          if f.endswith(PY_SUFFIXES) and
                          not is_excluded(path.join(root, f), excludes))
        is_pkg = INITPY in py_files
        is_namespace = INITPY not in py_files and implicit_namespaces
        if is_pkg:
            py_files.remove(INITPY)
            py_files.insert(0, INITPY)
        elif root != rootpath:
            # only accept non-package at toplevel unless using implicit namespaces
            if not implicit_namespaces:
                del subs[:]
                continue
        # remove hidden ('.') and private ('_') directories, as well as
        # excluded dirs
        if includeprivate:
            exclude_prefixes = ('.',)  # type: Tuple[str, ...]
        else:
            exclude_prefixes = ('.', '_')
        subs[:] = sorted(sub for sub in subs if not sub.startswith(exclude_prefixes) and
                         not is_excluded(path.join(root, sub), excludes))

        if is_pkg or is_namespace:
            # we are in a package with something to document
            if subs or len(py_files) > 1 or not shall_skip(path.join(root, INITPY), opts):
                subpackage = root[len(rootpath):].lstrip(path.sep).\
                    replace(path.sep, '.')
                # if this is not a namespace or
                # a namespace and there is something there to document
                if not is_namespace or len(py_files) > 0:
                    create_package_file(root, root_package, subpackage,
                                        py_files, opts, subs, is_namespace, excludes,
                                        user_template_dir)
                    toplevels.append(module_join(root_package, subpackage))
        else:
            # if we are at the root level, we don't require it to be a package
            assert root == rootpath and root_package is None
            for py_file in py_files:
                if not is_skipped_module(path.join(rootpath, py_file), opts, excludes):
                    module = py_file.split('.')[0]
                    create_module_file(root_package, module, opts, user_template_dir)
                    toplevels.append(module)

    return toplevels


def is_excluded(root: str, excludes: List[str]) -> bool:
    """Check if the directory is in the exclude list.

    Note: by having trailing slashes, we avoid common prefix issues, like
          e.g. an exclude "foo" also accidentally excluding "foobar".
    """
    for exclude in excludes:
        if fnmatch(root, exclude):
            return True
    return False


def _get_default_documenter(obj: Any, parent: Any) -> Type[Documenter]:
    """Get default Sphinx documenter for the given `parent.obj`.

    This is useful for determining the "type" of `obj` (module, class,
    exception, data, function, method, attribute, property, ...)
    """

    documenters = [
        ModuleDocumenter, ClassDocumenter, ExceptionDocumenter, DataDocumenter,
        FunctionDocumenter, DecoratorDocumenter, MethodDocumenter,
        AttributeDocumenter, PropertyDocumenter, InstanceAttributeDocumenter,
        SlotsAttributeDocumenter
    ]  # type: List[Type[Documenter]]

    if inspect.ismodule(obj):
        # ModuleDocumenter.can_document_member always returns False
        return ModuleDocumenter

    # Construct a fake documenter for *parent*
    if parent is None:
        parent_doc_cls = ModuleDocumenter  # type: Type[Documenter]
    else:
        parent_doc_cls = _get_default_documenter(parent, None)

    if hasattr(parent, '__name__'):
        parent_doc = parent_doc_cls(FakeDirective(), parent.__name__)
    else:
        parent_doc = parent_doc_cls(FakeDirective(), "")

    classes = [
        cls for cls in documenters
        if cls.can_document_member(obj, '', False, parent_doc)
    ]
    if classes:
        classes.sort(key=lambda cls: cls.priority)
        return classes[-1]
    else:
        return DataDocumenter


def _get_fullname(name: str, obj: Any) -> str:
    if hasattr(obj, '__qualname__'):
        try:
            ref = obj.__module__ + '.' + obj.__qualname__
        except AttributeError:
            ref = obj.__name__
        except TypeError:  # e.g. obj.__name__ is None
            ref = name
    elif hasattr(obj, '__name__'):
        try:
            ref = obj.__module__ + '.' + obj.__name__
        except AttributeError:
            ref = obj.__name__
        except TypeError:  # e.g. obj.__name__ is None
            ref = name
    else:
        ref = name
    return ref


def _get_member_ref_str(
        name: str,
        obj: Any,
        role: str = 'obj',
        known_refs: Optional[Dict] = None) -> str:
    """generate a ReST-formmated reference link to the given `obj` of type
    `role`, using `name` as the link text"""
    if known_refs is not None:
        if name in known_refs:
            return known_refs[name]
    ref = _get_fullname(name, obj)
    return ":%s:`%s <%s>`" % (role, name, ref)


def _get_members(
        mod: ModuleType,
        typ: Optional[str] = None,
        include_imported: bool = False,
        out_format: str = 'names',
        in_list: Optional[Union[str, Tuple[str]]] = None,
        known_refs: Optional[Union[str, Dict]] = None) \
        -> Tuple[List[str], List[str]]:
    """Get (filtered) public/total members of the module or package `mod`.

    See the documentation of the `get_members` function inside
    :func:`_add_get_members_to_template_env` for details.

    Returns:
        lists `public` and `items`. The lists contains the public and private +
        public members, as strings.
    """
    roles = {'function': 'func', 'module': 'mod', 'class': 'class',
             'exception': 'exc', 'data': 'data'}
    # not included, because they cannot occur at module level:
    #   'method': 'meth', 'attribute': 'attr', 'instanceattribute': 'attr'

    out_formats = ['names', 'fullnames', 'refs', 'table']
    if out_format not in out_formats:
        raise ValueError("out_format %s not in %r" % (out_format, out_formats))

    def check_typ(typ, mod, member):
        """Check if mod.member is of the desired typ"""
        if inspect.ismodule(member):
            return False
        documenter = _get_default_documenter(obj=member, parent=mod)
        if typ is None:
            return True
        if typ == getattr(documenter, 'objtype', None):
            return True
        if hasattr(documenter, 'directivetype'):
            return roles[typ] == getattr(documenter, 'directivetype')

    def is_local(mod, member, name):
        """Check whether mod.member is defined locally in module mod"""
        if hasattr(member, '__module__'):
            return getattr(member, '__module__') == mod.__name__
        else:
            # we take missing __module__ to mean the member is a data object;
            # it is recommended to filter data by e.g. __all__
            return True

    if typ is not None and typ not in roles:
        raise ValueError("typ must be None or one of %s"
                         % str(list(roles.keys())))
    items = []  # type: List[str]
    public = []  # type: List[str]
    item_table_tuples = []  # type: List[Tuple[str, str]]
    public_table_tuples = []  # type: List[Tuple[str, str]]
    known_refs_dict = {}  # type: Dict[str, str]
    if isinstance(known_refs, str):
        known_refs_dict = getattr(mod, known_refs, {})
    elif isinstance(known_refs, dict):
        known_refs_dict = known_refs
    listed_members = []  # type: List[str]
    if in_list is not None:
        # combine the lists mod.<attr> for each <attr> in `in_list` into the
        # combined list `listed_members`
        if isinstance(in_list, str):
            in_list = (in_list, )
        for attr_name in in_list:
            try:
                listed_members.extend(getattr(mod, attr_name))
            except AttributeError:
                pass
    for name in dir(mod):
        if name.startswith('__'):
            continue
        try:
            member = safe_getattr(mod, name)
        except AttributeError:
            continue
        if check_typ(typ, mod, member):
            if in_list is not None:
                if name not in listed_members:
                    continue
            if not (include_imported or is_local(mod, member, name)):
                continue
            if out_format in ['table', 'refs']:
                documenter = _get_default_documenter(obj=member, parent=mod)
                role = roles.get(documenter.objtype, 'obj')
                ref = _get_member_ref_str(name, obj=member, role=role,
                                          known_refs=known_refs_dict)
            if out_format == 'table':
                docsummary = _extract_summary(member)
                item_table_tuples.append((ref, docsummary))
                if not name.startswith('_'):
                    public_table_tuples.append((ref, docsummary))
            elif out_format == 'refs':
                items.append(ref)
                if not name.startswith('_'):
                    public.append(ref)
            elif out_format == 'fullnames':
                fullname = _get_fullname(name, obj=member)
                items.append(fullname)
                if not name.startswith('_'):
                    public.append(fullname)
            else:
                items.append(name)
                if not name.startswith('_'):
                    public.append(name)
    if out_format == 'table':
        return (_assemble_table(public_table_tuples),
                _assemble_table(item_table_tuples))
    else:
        return public, items


def _assemble_table(rows: List[Tuple[str, str]]) -> List[str]:
    if len(rows) == 0:
        return []
    lines = []
    lines.append('.. list-table::')
    lines.append('')
    for row in rows:
        lines.append('   * - %s' % row[0])
        for col in row[1:]:
            lines.append('     - %s' % col)
    lines.append('')
    return lines


def _extract_summary(obj: Any) -> str:
    """Extract summary from docstring.

    This is used for the "table" output of ``get_members``.
    """

    periods_re = re.compile(r'\.(?:\s+)')

    try:
        doc = inspect.getdoc(obj).split("\n")
    except AttributeError:
        doc = []

    # Skip a blank lines at the top
    while doc and not doc[0].strip():
        doc.pop(0)

    # If there's a blank line, then we can assume the first sentence /
    # paragraph has ended, so anything after shouldn't be part of the
    # summary
    for i, piece in enumerate(doc):
        if not piece.strip():
            doc = doc[:i]
            break

    # Try to find the "first sentence", which may span multiple lines
    sentences = periods_re.split(" ".join(doc))
    if len(sentences) == 1:
        summary = sentences[0].strip()
    else:
        summary = ''
        state_machine = RSTStateMachine(state_classes, 'Body')
        while sentences:
            summary += sentences.pop(0) + '.'
            node = new_document('')
            node.reporter = NullReporter('', 999, 4)
            node.settings.pep_references = None
            node.settings.rfc_references = None
            node.settings.character_level_inline_markup = False
            state_machine.run([summary], node)
            if not node.traverse(nodes.system_message):
                # considered as that splitting by period does not break inline
                # markups
                break

    return summary


def _add_get_members_to_template_env(
        template_env: jinja2.Environment,
        fullname: str,
        opts: argparse.Namespace):
    """Add `get_members` function to Jinja environment."""

    def get_members(
            fullname, typ=None, include_imported=False, out_format='names',
            in_list=None, include_private=opts.includeprivate,
            known_refs=None):
        """Return a list of members.

        See the apidoc manpage in the Sphinx documentation for details.
        """
        try:
            mod = importlib.import_module(fullname)
        except ImportError as exc_info:
            warnings.warn(
                "Cannot get members of %s: %s. Use --append-syspath, "
                "or make sure the packages/modules processed by apidoc are "
                "properly installed." % (fullname, exc_info)
            )
            return []
        if include_private:
            return _get_members(
                mod, typ=typ, include_imported=include_imported,
                out_format=out_format, in_list=in_list, known_refs=known_refs
            )[1]
        else:
            return _get_members(
                mod, typ=typ, include_imported=include_imported,
                out_format=out_format, in_list=in_list, known_refs=known_refs
            )[0]

    template_env.globals['get_members'] = partial(
        get_members, fullname=fullname
    )


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS] -o <OUTPUT_PATH> <MODULE_PATH> '
              '[EXCLUDE_PATTERN, ...]',
        epilog=__('For more information, visit <http://sphinx-doc.org/>.'),
        description=__("""
Look recursively in <MODULE_PATH> for Python modules and packages and create
one reST file with automodule directives per package in the <OUTPUT_PATH>.

The <EXCLUDE_PATTERN>s can be file and/or directory patterns that will be
excluded from generation.

Note: By default this script will not overwrite already created files."""))

    parser.add_argument('--version', action='version', dest='show_version',
                        version='%%(prog)s %s' % __display_version__)

    parser.add_argument('module_path',
                        help=__('path to module to document'))
    parser.add_argument('exclude_pattern', nargs='*',
                        help=__('fnmatch-style file and/or directory patterns '
                                'to exclude from generation'))

    parser.add_argument('-o', '--output-dir', action='store', dest='destdir',
                        required=True,
                        help=__('directory to place all output'))
    parser.add_argument('-d', '--maxdepth', action='store', dest='maxdepth',
                        type=int, default=4,
                        help=__('maximum depth of submodules to show in the TOC '
                                '(default: 4)'))
    parser.add_argument('-f', '--force', action='store_true', dest='force',
                        help=__('overwrite existing files'))
    parser.add_argument('-l', '--follow-links', action='store_true',
                        dest='followlinks', default=False,
                        help=__('follow symbolic links. Powerful when combined '
                                'with collective.recipe.omelette.'))
    parser.add_argument('-n', '--dry-run', action='store_true', dest='dryrun',
                        help=__('run the script without creating files'))
    parser.add_argument('-e', '--separate', action='store_true',
                        dest='separatemodules',
                        help=__('put documentation for each module on its own page'))
    parser.add_argument('-P', '--private', action='store_true',
                        dest='includeprivate',
                        help=__('include "_private" modules'))
    parser.add_argument('--tocfile', action='store', dest='tocfile', default='modules',
                        help=__("filename of table of contents (default: modules)"))
    parser.add_argument('-T', '--no-toc', action='store_false', dest='tocfile',
                        help=__("don't create a table of contents file"))
    parser.add_argument('-E', '--no-headings', action='store_true',
                        dest='noheadings',
                        help=__("don't create headings for the module/package "
                                "packages (e.g. when the docstrings already "
                                "contain them)"))
    parser.add_argument('-M', '--module-first', action='store_true',
                        dest='modulefirst',
                        help=__('put module documentation before submodule '
                                'documentation'))
    parser.add_argument('--implicit-namespaces', action='store_true',
                        dest='implicit_namespaces',
                        help=__('interpret module paths according to PEP-0420 '
                                'implicit namespaces specification'))
    parser.add_argument('-s', '--suffix', action='store', dest='suffix',
                        default='rst',
                        help=__('file suffix (default: rst)'))
    parser.add_argument('-F', '--full', action='store_true', dest='full',
                        help=__('generate a full project with sphinx-quickstart'))
    parser.add_argument('-a', '--append-syspath', action='store_true',
                        dest='append_syspath',
                        help=__('append module_path to sys.path'))
    parser.add_argument('-H', '--doc-project', action='store', dest='header',
                        help=__('project name (default: root module name)'))
    parser.add_argument('-A', '--doc-author', action='store', dest='author',
                        help=__('project author(s), used when --full is given'))
    parser.add_argument('-V', '--doc-version', action='store', dest='version',
                        help=__('project version, used when --full is given'))
    parser.add_argument('-R', '--doc-release', action='store', dest='release',
                        help=__('project release, used when --full is given, '
                                'defaults to --doc-version'))

    group = parser.add_argument_group(__('extension options'))
    group.add_argument('--extensions', metavar='EXTENSIONS', dest='extensions',
                       action='append', help=__('enable arbitrary extensions'))
    for ext in EXTENSIONS:
        group.add_argument('--ext-%s' % ext, action='append_const',
                           const='sphinx.ext.%s' % ext, dest='extensions',
                           help=__('enable %s extension') % ext)

    group = parser.add_argument_group(__('Project templating'))
    group.add_argument('-t', '--templatedir', metavar='TEMPLATEDIR',
                       dest='templatedir',
                       help=__('template directory for template files'))

    return parser


def main(argv: List[str] = sys.argv[1:]) -> int:
    """Parse and check the command line arguments."""
    sphinx.locale.setlocale(locale.LC_ALL, '')
    sphinx.locale.init_console(os.path.join(package_dir, 'locale'), 'sphinx')

    parser = get_parser()
    args = parser.parse_args(argv)

    rootpath = path.abspath(args.module_path)
    if args.append_syspath:
        # required for `get_members`
        sys.path.append(rootpath)

    # normalize opts

    if args.header is None:
        args.header = rootpath.split(path.sep)[-1]
    if args.suffix.startswith('.'):
        args.suffix = args.suffix[1:]
    if not path.isdir(rootpath):
        print(__('%s is not a directory.') % rootpath, file=sys.stderr)
        sys.exit(1)
    if not args.dryrun:
        ensuredir(args.destdir)
    excludes = [path.abspath(exclude) for exclude in args.exclude_pattern]
    modules = recurse_tree(rootpath, excludes, args, args.templatedir)

    if args.full:
        from sphinx.cmd import quickstart as qs
        modules.sort()
        prev_module = ''
        text = ''
        for module in modules:
            if module.startswith(prev_module + '.'):
                continue
            prev_module = module
            text += '   %s\n' % module
        d = {
            'path': args.destdir,
            'sep': False,
            'dot': '_',
            'project': args.header,
            'author': args.author or 'Author',
            'version': args.version or '',
            'release': args.release or args.version or '',
            'suffix': '.' + args.suffix,
            'master': 'index',
            'epub': True,
            'extensions': ['sphinx.ext.autodoc', 'sphinx.ext.viewcode',
                           'sphinx.ext.todo'],
            'makefile': True,
            'batchfile': True,
            'make_mode': True,
            'mastertocmaxdepth': args.maxdepth,
            'mastertoctree': text,
            'language': 'en',
            'module_path': rootpath,
            'append_syspath': args.append_syspath,
        }
        if args.extensions:
            d['extensions'].extend(args.extensions)

        for ext in d['extensions'][:]:
            if ',' in ext:
                d['extensions'].remove(ext)
                d['extensions'].extend(ext.split(','))

        if not args.dryrun:
            qs.generate(d, silent=True, overwrite=args.force,
                        templatedir=args.templatedir)
    elif args.tocfile:
        create_modules_toc_file(modules, args, args.tocfile, args.templatedir)

    return 0


# So program can be started with "python -m sphinx.apidoc ..."
if __name__ == "__main__":
    main()
