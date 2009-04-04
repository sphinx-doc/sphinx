# -*- coding: utf-8 -*-
"""
    sphinx.ext.autosummary.generate
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Usable as a library or script to generate automatic RST source files for
    items referred to in autosummary:: directives.

    Each generated RST file contains a single auto*:: directive which
    extracts the docstring of the referred item.

    Example Makefile rule::

       generate:
               sphinx-autogen source/*.rst source/generated

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os
import re
import sys
import optparse
import inspect

from jinja2 import Environment, PackageLoader

from sphinx.ext.autosummary import import_by_name, get_documenter
from sphinx.util import ensuredir

# create our own templating environment, for module template only
env = Environment(loader=PackageLoader('sphinx.ext.autosummary', 'templates'))


def _simple_info(msg):
    print msg

def _simple_warn(msg):
    print >>sys.stderr, 'WARNING: ' + msg

def generate_autosummary_docs(sources, output_dir=None, suffix='.rst',
                              warn=_simple_warn, info=_simple_info):
    info('generating autosummary for: %s' % ', '.join(sources))
    if output_dir:
        info('writing to %s' % output_dir)

    # read
    names = {}
    for name, loc in get_documented(sources).items():
        for (filename, sec_title, keyword, toctree) in loc:
            if toctree is not None:
                path = os.path.join(os.path.dirname(filename), toctree)
                names[name] = os.path.abspath(path)

    # write
    for name, path in sorted(names.items()):
        path = output_dir or path
        ensuredir(path)

        try:
            obj, name = import_by_name(name)
        except ImportError, e:
            warn('failed to import %r: %s' % (name, e))
            continue

        fn = os.path.join(path, name + suffix)
        # skip it if it exists
        if os.path.isfile(fn):
            continue

        f = open(fn, 'w')

        try:
            if inspect.ismodule(obj):
                # XXX replace this with autodoc's API?
                tmpl = env.get_template('module')

                def get_items(mod, typ):
                    return [getattr(mod, name).__name__
                            for name in dir(mod)
                            if get_documenter(getattr(mod,name)).objtype==typ]

                functions = get_items(obj, 'function')
                classes = get_items(obj, 'class')
                exceptions = get_items(obj, 'exception')

                rendered = tmpl.render(name=name,
                                       underline='='*len(name),
                                       functions=functions,
                                       classes=classes,
                                       exceptions=exceptions,
                                       len_functions=len(functions),
                                       len_classes=len(classes),
                                       len_exceptions=len(exceptions))
                f.write(rendered)
            else:
                f.write('%s\n%s\n\n' % (name, '='*len(name)))

                doc = get_documenter(obj)
                if doc.objtype in ('method', 'attribute'):
                    f.write(format_classmember(name, 'auto%s' % doc.objtype))
                else:
                    f.write(format_modulemember(name, 'auto%s' % doc.objtype))
        finally:
            f.close()


def format_modulemember(name, directive):
    parts = name.split('.')
    mod, name = '.'.join(parts[:-1]), parts[-1]
    return '.. currentmodule:: %s\n\n.. %s:: %s\n' % (mod, directive, name)


def format_classmember(name, directive):
    parts = name.split('.')
    mod, name = '.'.join(parts[:-2]), '.'.join(parts[-2:])
    return '.. currentmodule:: %s\n\n.. %s:: %s\n' % (mod, directive, name)


title_underline_re = re.compile('^[-=*_^#]{3,}\s*$')
autodoc_re = re.compile(r'.. auto(function|method|attribute|class|exception'
                        '|module)::\s*([A-Za-z0-9_.]+)\s*$')
autosummary_re = re.compile(r'^\.\.\s+autosummary::\s*')
module_re = re.compile(r'^\.\.\s+(current)?module::\s*([a-zA-Z0-9_.]+)\s*$')
autosummary_item_re = re.compile(r'^\s+([_a-zA-Z][a-zA-Z0-9_.]*)\s*.*?')
toctree_arg_re = re.compile(r'^\s+:toctree:\s*(.*?)\s*$')

def get_documented(filenames):
    """
    Find out what items are documented in the given filenames.

    Returns a dict of list of (filename, title, keyword, toctree) Keys are
    documented names of objects.  The value is a list of locations where the
    object was documented.  Each location is a tuple of filename, the current
    section title, the name of the directive, and the value of the :toctree:
    argument (if present) of the directive.
    """

    documented = {}

    for filename in filenames:
        current_title = []
        last_line = None
        toctree = None
        current_module = None
        in_autosummary = False

        f = open(filename, 'r')
        for line in f:
            try:
                if in_autosummary:
                    m = toctree_arg_re.match(line)
                    if m:
                        toctree = m.group(1)
                        continue

                    if line.strip().startswith(':'):
                        continue # skip options

                    m = autosummary_item_re.match(line)

                    if m:
                        name = m.group(1).strip()
                        if current_module and \
                               not name.startswith(current_module + '.'):
                            name = '%s.%s' % (current_module, name)
                        documented.setdefault(name, []).append(
                            (filename, current_title, 'autosummary', toctree))
                        continue
                    if line.strip() == '':
                        continue
                    in_autosummary = False

                m = autosummary_re.match(line)
                if m:
                    in_autosummary = True
                    continue

                m = autodoc_re.search(line)
                if m:
                    name = m.group(2).strip()
                    # XXX look in newer generate.py
                    if current_module and \
                           not name.startswith(current_module + '.'):
                        name = '%s.%s' % (current_module, name)
                    if m.group(1) == 'module':
                        current_module = name
                    documented.setdefault(name, []).append(
                        (filename, current_title, 'auto' + m.group(1), None))
                    continue

                m = title_underline_re.match(line)
                if m and last_line:
                    current_title = last_line.strip()
                    continue

                m = module_re.match(line)
                if m:
                    current_module = m.group(2)
                    continue
            finally:
                last_line = line
    return documented


def main(argv):
    usage = """%prog [OPTIONS] SOURCEFILE ..."""
    p = optparse.OptionParser(usage.strip())
    p.add_option("-o", "--output-dir", action="store", type="string",
                 dest="output_dir", default=None,
                 help="Directory to place all output in")
    p.add_option("-s", "--suffix", action="store", type="string",
                 dest="suffix", default="rst",
                 help="Default suffix for files (default: %default)")
    options, args = p.parse_args(argv[1:])

    if len(args) < 1:
        p.error('no input files given')

    generate_autosummary_docs(args, options.output_dir,
                              "." + options.suffix)

if __name__ == '__main__':
    main()
