from __future__ import annotations

import dataclasses
import glob
import os
import os.path
from importlib.machinery import EXTENSION_SUFFIXES
from pathlib import Path
from typing import TYPE_CHECKING

from sphinx import package_dir
from sphinx.ext.apidoc._shared import LOGGER
from sphinx.locale import __
from sphinx.util.osutil import FileAvoidWrite
from sphinx.util.template import ReSTRenderer

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator, Sequence


# automodule options
if 'SPHINX_APIDOC_OPTIONS' in os.environ:
    OPTIONS = set(os.environ['SPHINX_APIDOC_OPTIONS'].split(','))
else:
    OPTIONS = {
        'members',
        'undoc-members',
        # 'inherited-members', # disabled because there's a bug in sphinx
        'show-inheritance',
    }

PY_SUFFIXES = ('.py', '.pyx', *EXTENSION_SUFFIXES)

template_dir = os.path.join(package_dir, 'templates', 'apidoc')


def is_initpy(filename: str | Path) -> bool:
    """Check *filename* is __init__ file or not."""
    basename = Path(filename).name
    return any(
        basename == '__init__' + suffix
        for suffix in sorted(PY_SUFFIXES, key=len, reverse=True)
    )


def module_join(*modnames: str | None) -> str:
    """Join module names with dots."""
    return '.'.join(filter(None, modnames))


def is_packagedir(dirname: str | None = None, files: list[str] | None = None) -> bool:
    """Check given *files* contains __init__ file."""
    if files is None and dirname is None:
        return False

    if files is None:
        files = os.listdir(dirname)
    return any(f for f in files if is_initpy(f))


def write_file(name: str, text: str, opts: ApidocOptions) -> Path:
    """Write the output file for module/package <name>."""
    fname = Path(opts.destdir, f'{name}.{opts.suffix}')
    if opts.dryrun:
        if not opts.quiet:
            LOGGER.info(__('Would create file %s.'), fname)
        return fname
    if not opts.force and fname.is_file():
        if not opts.quiet:
            LOGGER.info(__('File %s already exists, skipping.'), fname)
    else:
        if not opts.quiet:
            LOGGER.info(__('Creating file %s.'), fname)
        with FileAvoidWrite(fname) as f:
            f.write(text)
    return fname


def create_module_file(
    package: str | None,
    basename: str,
    opts: ApidocOptions,
    user_template_dir: str | None = None,
) -> Path:
    """Build the text of the file and write the file."""
    options = set(OPTIONS if not opts.automodule_options else opts.automodule_options)
    if opts.includeprivate:
        options.add('private-members')

    qualname = module_join(package, basename)
    context = {
        'show_headings': not opts.noheadings,
        'basename': basename,
        'qualname': qualname,
        'automodule_options': sorted(options),
    }
    if user_template_dir is not None:
        template_path = [user_template_dir, template_dir]
    else:
        template_path = [template_dir]
    text = ReSTRenderer(template_path).render('module.rst.jinja', context)
    return write_file(qualname, text, opts)


def create_package_file(
    root: str,
    master_package: str | None,
    subroot: str,
    py_files: list[str],
    opts: ApidocOptions,
    subs: list[str],
    is_namespace: bool,
    excludes: Sequence[re.Pattern[str]] = (),
    user_template_dir: str | None = None,
) -> list[Path]:
    """Build the text of the file and write the file.

    Also create submodules if necessary.

    :returns: list of written files
    """
    # build a list of sub packages (directories containing an __init__ file)
    subpackages = [
        module_join(master_package, subroot, pkgname)
        for pkgname in subs
        if not is_skipped_package(Path(root, pkgname), opts, excludes)
    ]
    # build a list of sub modules
    submodules = [
        sub.split('.')[0]
        for sub in py_files
        if not is_skipped_module(Path(root, sub), opts, excludes) and not is_initpy(sub)
    ]
    submodules = sorted(set(submodules))
    submodules = [
        module_join(master_package, subroot, modname) for modname in submodules
    ]
    options = OPTIONS.copy()
    if opts.includeprivate:
        options.add('private-members')

    pkgname = module_join(master_package, subroot)
    context = {
        'pkgname': pkgname,
        'subpackages': subpackages,
        'submodules': submodules,
        'is_namespace': is_namespace,
        'modulefirst': opts.modulefirst,
        'separatemodules': opts.separatemodules,
        'automodule_options': sorted(options),
        'show_headings': not opts.noheadings,
        'maxdepth': opts.maxdepth,
    }
    if user_template_dir is not None:
        template_path = [user_template_dir, template_dir]
    else:
        template_path = [template_dir]

    written: list[Path] = []

    text = ReSTRenderer(template_path).render('package.rst.jinja', context)
    written.append(write_file(pkgname, text, opts))

    if submodules and opts.separatemodules:
        written.extend([
            create_module_file(None, submodule, opts, user_template_dir)
            for submodule in submodules
        ])

    return written


def create_modules_toc_file(
    modules: list[str],
    opts: ApidocOptions,
    name: str = 'modules',
    user_template_dir: str | None = None,
) -> Path:
    """Create the module's index."""
    modules.sort()
    prev_module = ''
    for module in modules.copy():
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
    if user_template_dir is not None:
        template_path = [user_template_dir, template_dir]
    else:
        template_path = [template_dir]
    text = ReSTRenderer(template_path).render('toc.rst.jinja', context)
    return write_file(name, text, opts)


def is_skipped_package(
    dirname: str | Path, opts: ApidocOptions, excludes: Sequence[re.Pattern[str]] = ()
) -> bool:
    """Check if we want to skip this module."""
    if not Path(dirname).is_dir():
        return False

    files = glob.glob(str(Path(dirname, '*.py')))
    regular_package = any(f for f in files if is_initpy(f))
    if not regular_package and not opts.implicit_namespaces:
        # *dirname* is not both a regular package and an implicit namespace package
        return True

    # Check there is some showable module inside package
    return all(is_excluded(Path(dirname, f), excludes) for f in files)


def is_skipped_module(
    filename: str | Path, opts: ApidocOptions, _excludes: Sequence[re.Pattern[str]]
) -> bool:
    """Check if we want to skip this module."""
    filename = Path(filename)
    if not filename.exists():
        # skip if the file doesn't exist
        return True
    # skip if the module has a "private" name
    return filename.name.startswith('_') and not opts.includeprivate


def walk(
    rootpath: str,
    excludes: Sequence[re.Pattern[str]],
    opts: ApidocOptions,
) -> Iterator[tuple[str, list[str], list[str]]]:
    """Walk through the directory and list files and subdirectories up."""
    for root, subs, files in os.walk(rootpath, followlinks=opts.followlinks):
        # document only Python module files (that aren't excluded)
        files = sorted(
            f
            for f in files
            if f.endswith(PY_SUFFIXES) and not is_excluded(Path(root, f), excludes)
        )

        # remove hidden ('.') and private ('_') directories, as well as
        # excluded dirs
        if opts.includeprivate:
            exclude_prefixes: tuple[str, ...] = ('.',)
        else:
            exclude_prefixes = ('.', '_')

        subs[:] = sorted(
            sub
            for sub in subs
            if not sub.startswith(exclude_prefixes)
            and not is_excluded(Path(root, sub), excludes)
        )

        yield root, subs, files


def has_child_module(
    rootpath: str, excludes: Sequence[re.Pattern[str]], opts: ApidocOptions
) -> bool:
    """Check the given directory contains child module/s (at least one)."""
    return any(files for _root, _subs, files in walk(rootpath, excludes, opts))


def recurse_tree(
    rootpath: str | os.PathLike[str],
    excludes: Sequence[re.Pattern[str]],
    opts: ApidocOptions,
    user_template_dir: str | None = None,
) -> tuple[list[Path], list[str]]:
    """
    Look for every file in the directory tree and create the corresponding
    ReST files.
    """
    # check if the base directory is a package and get its name
    rootpath = os.fspath(rootpath)
    if is_packagedir(rootpath) or opts.implicit_namespaces:
        root_package = rootpath.split(os.path.sep)[-1]
    else:
        # otherwise, the base is a directory with packages
        root_package = None

    toplevels = []
    written_files = []
    for root, subs, files in walk(rootpath, excludes, opts):
        is_pkg = is_packagedir(None, files)
        is_namespace = not is_pkg and opts.implicit_namespaces
        if is_pkg:
            for f in files.copy():
                if is_initpy(f):
                    files.remove(f)
                    files.insert(0, f)
        elif root != rootpath:
            # only accept non-package at toplevel unless using implicit namespaces
            if not opts.implicit_namespaces:
                subs.clear()
                continue

        if is_pkg or is_namespace:
            # we are in a package with something to document
            if subs or len(files) > 1 or not is_skipped_package(root, opts):
                subpackage = (
                    root[len(rootpath) :].lstrip(os.path.sep).replace(os.path.sep, '.')
                )
                # if this is not a namespace or
                # a namespace and there is something there to document
                if not is_namespace or has_child_module(root, excludes, opts):
                    written_files.extend(
                        create_package_file(
                            root,
                            root_package,
                            subpackage,
                            files,
                            opts,
                            subs,
                            is_namespace,
                            excludes,
                            user_template_dir,
                        )
                    )
                    toplevels.append(module_join(root_package, subpackage))
        else:
            # if we are at the root level, we don't require it to be a package
            assert root == rootpath
            assert root_package is None
            for py_file in files:
                if not is_skipped_module(Path(rootpath, py_file), opts, excludes):
                    module = py_file.split('.')[0]
                    written_files.append(
                        create_module_file(
                            root_package, module, opts, user_template_dir
                        )
                    )
                    toplevels.append(module)

    return written_files, toplevels


def is_excluded(root: str | Path, excludes: Sequence[re.Pattern[str]]) -> bool:
    """Check if the directory is in the exclude list.

    Note: by having trailing slashes, we avoid common prefix issues, like
          e.g. an exclude "foo" also accidentally excluding "foobar".
    """
    root_str = str(root)
    return any(exclude.match(root_str) for exclude in excludes)


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ApidocOptions:
    """Options for apidoc."""

    module_path: Path
    exclude_pattern: list[str]
    destdir: Path
    quiet: bool = False
    maxdepth: int = 4
    force: bool = False
    followlinks: bool = False
    dryrun: bool = False
    separatemodules: bool = False
    includeprivate: bool = False
    tocfile: str = 'modules'
    noheadings: bool = False
    modulefirst: bool = False
    implicit_namespaces: bool = False
    automodule_options: set[str] = dataclasses.field(default_factory=set)
    suffix: str = 'rst'

    remove_old: bool = False

    # --full only
    full: bool = False
    append_syspath: bool = False
    header: str = ''
    author: str | None = None
    version: str | None = None
    release: str | None = None
    extensions: list[str] | None = None
    templatedir: str | None = None
