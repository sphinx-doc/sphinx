# -*- coding: utf-8 -*-
"""
    sphinx.ext.autosummary
    ~~~~~~~~~~~~~~~~~~~~~~

    Sphinx extension that adds an autosummary:: directive, which can be
    used to generate function/method/attribute/etc. summary lists, similar
    to those output eg. by Epydoc and other API doc generation tools.

    An :autolink: role is also provided.

    autosummary directive
    ---------------------

    The autosummary directive has the form::

        .. autosummary::
           :nosignatures:
           :toctree: generated/

           module.function_1
           module.function_2
           ...

    and it generates an output table (containing signatures, optionally)

        ========================  =============================================
        module.function_1(args)   Summary line from the docstring of function_1
        module.function_2(args)   Summary line from the docstring
        ...
        ========================  =============================================

    If the :toctree: option is specified, files matching the function names
    are inserted to the toctree with the given prefix:

        generated/module.function_1
        generated/module.function_2
        ...

    Note: The file names contain the module:: or currentmodule:: prefixes.

    .. seealso:: autosummary_generate.py


    autolink role
    -------------

    The autolink role functions as ``:obj:`` when the name referred can be
    resolved to a Python object, and otherwise it becomes simple emphasis.
    This can be used as the default role to make links 'smart'.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
import inspect
import posixpath
from os import path

from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from docutils import nodes

from sphinx import addnodes, roles
from sphinx.util import patfilter
from sphinx.util.compat import Directive

import sphinx.ext.autodoc


# -- autosummary_toc node ------------------------------------------------------

class autosummary_toc(nodes.comment):
    pass

def process_autosummary_toc(app, doctree):
    """
    Insert items described in autosummary:: to the TOC tree, but do
    not generate the toctree:: list.
    """
    env = app.builder.env
    crawled = {}
    def crawl_toc(node, depth=1):
        crawled[node] = True
        for j, subnode in enumerate(node):
            try:
                if (isinstance(subnode, autosummary_toc)
                    and isinstance(subnode[0], addnodes.toctree)):
                    env.note_toctree(env.docname, subnode[0])
                    continue
            except IndexError:
                continue
            if not isinstance(subnode, nodes.section):
                continue
            if subnode not in crawled:
                crawl_toc(subnode, depth+1)
    crawl_toc(doctree)

def autosummary_toc_visit_html(self, node):
    """Hide autosummary toctree list in HTML output."""
    raise nodes.SkipNode

def autosummary_toc_visit_latex(self, node):
    """Show autosummary toctree (= put the referenced pages here) in Latex."""
    pass

def autosummary_noop(self, node):
    pass

# -- autodoc integration -------------------------------------------------------

def get_documenter(obj):
    """
    Get an autodoc.Documenter class suitable for documenting the given object
    """
    reg = sphinx.ext.autodoc.AutoDirective._registry
    if inspect.isclass(obj):
        if issubclass(obj, Exception):
            return reg.get('exception')
        return reg.get('class')
    elif inspect.ismodule(obj):
        return reg.get('module')
    elif inspect.ismethod(obj) or inspect.ismethoddescriptor(obj):
        return reg.get('method')
    elif inspect.ismemberdescriptor(obj) or inspect.isgetsetdescriptor(obj):
        return reg.get('attribute')
    elif inspect.isroutine(obj):
        return reg.get('function')
    else:
        return reg.get('data')

# -- .. autosummary:: ----------------------------------------------------------

class Autosummary(Directive):
    """
    Pretty table containing short signatures and summaries of functions etc.

    autosummary also generates a (hidden) toctree:: node.
    """

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True
    option_spec = {
        'toctree': directives.unchanged,
        'nosignatures': directives.flag,
    }

    def warn(self, msg):
        self.warnings.append(self.state.document.reporter.warning(
            msg, line=self.lineno))

    def run(self):
        self.env = env = self.state.document.settings.env
        self.genopt = {}
        self.warnings = []

        names = []
        names += [x.strip() for x in self.content if x.strip()]

        table, real_names = self.get_table(names)
        nodes = [table]

        suffix = env.config.source_suffix
        all_docnames = env.found_docs.copy()
        dirname = posixpath.dirname(env.docname)

        if 'toctree' in self.options:
            tree_prefix = self.options['toctree'].strip()
            docnames = []
            for name in names:
                name = real_names.get(name, name)

                docname = posixpath.join(tree_prefix, name)
                if docname.endswith(suffix):
                    docname = docname[:-len(suffix)]
                docname = posixpath.normpath(posixpath.join(dirname, docname))
                if docname not in env.found_docs:
                    self.warn('toctree references unknown document %r'
                              % docname)
                docnames.append(docname)

            tocnode = addnodes.toctree()
            tocnode['includefiles'] = docnames
            tocnode['entries'] = [(None, docname) for docname in docnames]
            tocnode['maxdepth'] = -1
            tocnode['glob'] = None

            tocnode = autosummary_toc('', '', tocnode)
            nodes.append(tocnode)

        return self.warnings + nodes

    def get_table(self, names, no_signatures=False):
        """
        Generate a proper table node for autosummary:: directive.

        *names* is a list of names of Python objects to be imported
        and added to the table.

        """
        state = self.state
        document = state.document

        prefixes = ['']
        prefixes.insert(0, document.settings.env.currmodule)

        real_names = {}

        table = nodes.table('')
        group = nodes.tgroup('', cols=2)
        table.append(group)
        group.append(nodes.colspec('', colwidth=10))
        group.append(nodes.colspec('', colwidth=90))
        body = nodes.tbody('')
        group.append(body)

        def append_row(*column_texts):
            row = nodes.row('')
            for text in column_texts:
                node = nodes.paragraph('')
                vl = ViewList()
                vl.append(text, '<autosummary>')
                state.nested_parse(vl, 0, node)
                row.append(nodes.entry('', node))
            body.append(row)

        for name in names:
            try:
                obj, real_name = import_by_name(name, prefixes=prefixes)
            except ImportError:
                self.warn('failed to import %s' % name)
                append_row(':obj:`%s`' % name, '')
                continue

            documenter = get_documenter(obj)(self, real_name)
            if not documenter.parse_name():
                append_row(':obj:`%s`' % name, '')
                continue
            if not documenter.import_object():
                append_row(':obj:`%s`' % name, '')
                continue

            real_names[name] = documenter.fullname

            sig = documenter.format_signature()
            if not sig or 'nosignatures' in self.options:
                sig = ''
            else:
                sig = mangle_signature(sig)

            doc = list(documenter.process_doc(documenter.get_doc()))
            if doc:
                # grab the summary
                while doc and not doc[0].strip():
                    doc.pop(0)
                m = re.search(r"^([A-Z].*?\.\s)", " ".join(doc).strip())
                if m:
                    summary = m.group(1).strip()
                else:
                    summary = doc[0].strip()
            else:
                summary = ''

            qualifier = 'obj'
            col1 = ':' + qualifier + r':`%s <%s>`\ %s' % (name, real_name, sig)
            col2 = summary
            append_row(col1, col2)

        return table, real_names

def mangle_signature(sig, max_chars=30):
    """
    Reformat function signature to a more compact form.

    """
    sig = re.sub(r"^\((.*)\)$", r"\1", sig) + ", "
    r = re.compile(r"(?P<name>[a-zA_Z0-9_*]+)(?P<default>=.*?)?, ")
    items = r.findall(sig)

    args = []
    opts = []

    total_len = 4
    for name, default in items:
        if default:
            opts.append(name)
        else:
            args.append(name)
        total_len += len(name) + 2

        if total_len > max_chars:
            if opts:
                opts.append('...')
            else:
                args.append('...')
            break

    if opts:
        sig = ", ".join(args) + "[, " + ", ".join(opts) + "]"
    else:
        sig = ", ".join(args)

    sig = unicode(sig).replace(u" ", u"\u00a0")
    return u"(%s)" % sig

# -- Importing items -----------------------------------------------------------

def import_by_name(name, prefixes=[None]):
    """
    Import a Python object that has the given *name*, under one of the
    *prefixes*.  The first name that succeeds is used.
    """
    tried = []
    for prefix in prefixes:
        try:
            if prefix:
                prefixed_name = '.'.join([prefix, name])
            else:
                prefixed_name = name
            return _import_by_name(prefixed_name), prefixed_name
        except ImportError:
            tried.append(prefixed_name)
    raise ImportError('no module named %s' % ' or '.join(tried))

def _import_by_name(name):
    """Import a Python object given its full name."""
    try:
        # try first interpret `name` as MODNAME.OBJ
        name_parts = name.split('.')
        try:
            modname = '.'.join(name_parts[:-1])
            __import__(modname)
            return getattr(sys.modules[modname], name_parts[-1])
        except (ImportError, IndexError, AttributeError):
            pass

        # ... then as MODNAME, MODNAME.OBJ1, MODNAME.OBJ1.OBJ2, ...
        last_j = 0
        modname = None
        for j in reversed(range(1, len(name_parts)+1)):
            last_j = j
            modname = '.'.join(name_parts[:j])
            try:
                __import__(modname)
            except ImportError:
                continue
            if modname in sys.modules:
                break

        if last_j < len(name_parts):
            obj = sys.modules[modname]
            for obj_name in name_parts[last_j:]:
                obj = getattr(obj, obj_name)
            return obj
        else:
            return sys.modules[modname]
    except (ValueError, ImportError, AttributeError, KeyError), e:
        raise ImportError(*e.args)


# -- :autolink: (smart default role) -------------------------------------------

def autolink_role(typ, rawtext, etext, lineno, inliner,
                  options={}, content=[]):
    """
    Smart linking role.

    Expands to ':obj:`text`' if `text` is an object that can be imported;
    otherwise expands to '*text*'.
    """
    r = roles.xfileref_role('obj', rawtext, etext, lineno, inliner,
                            options, content)
    pnode = r[0][0]

    prefixes = [None]
    #prefixes.insert(0, inliner.document.settings.env.currmodule)
    try:
        obj, name = import_by_name(pnode['reftarget'], prefixes)
    except ImportError:
        content = pnode[0]
        r[0][0] = nodes.emphasis(rawtext, content[0].astext(),
                                 classes=content['classes'])
    return r


def process_generate_options(app):
    genfiles = app.config.autosummary_generate
    if not genfiles:
        return
    from sphinx.ext.autosummary.generate import generate_autosummary_docs

    ext = app.config.source_suffix
    genfiles = [path.join(app.srcdir, genfile +
                          (not genfile.endswith(ext) and ext or ''))
                for genfile in genfiles]
    generate_autosummary_docs(genfiles, warn=app.warn, info=app.info,
                              suffix=ext)


def setup(app):
    # I need autodoc
    app.setup_extension('sphinx.ext.autodoc')
    app.add_node(autosummary_toc,
                 html=(autosummary_toc_visit_html, autosummary_noop),
                 latex=(autosummary_toc_visit_latex, autosummary_noop),
                 text=(autosummary_noop, autosummary_noop))
    app.add_directive('autosummary', Autosummary)
    app.add_role('autolink', autolink_role)
    app.connect('doctree-read', process_autosummary_toc)
    app.connect('builder-inited', process_generate_options)
    app.add_config_value('autosummary_generate', [], True)
