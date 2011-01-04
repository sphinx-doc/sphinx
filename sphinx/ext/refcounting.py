# -*- coding: utf-8 -*-
"""
    sphinx.ext.refcounting
    ~~~~~~~~~~~~~~~~~~~~~~

    Supports reference count annotations for C API functions.  Based on
    refcount.py and anno-api.py in the old Python documentation tools.

    Usage: Set the `refcount_file` config value to the path to the reference
    count data file.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path
from docutils import nodes

from sphinx import addnodes


# refcount annotation
class refcount(nodes.emphasis): pass


class RCEntry:
    def __init__(self, name):
        self.name = name
        self.args = []
        self.result_type = ''
        self.result_refs = None


class Refcounts(dict):
    @classmethod
    def fromfile(cls, filename):
        d = cls()
        fp = open(filename, 'r')
        try:
            for line in fp:
                line = line.strip()
                if line[:1] in ("", "#"):
                    # blank lines and comments
                    continue
                parts = line.split(":", 4)
                if len(parts) != 5:
                    raise ValueError("Wrong field count in %r" % line)
                function, type, arg, refcount, comment = parts
                # Get the entry, creating it if needed:
                try:
                    entry = d[function]
                except KeyError:
                    entry = d[function] = RCEntry(function)
                if not refcount or refcount == "null":
                    refcount = None
                else:
                    refcount = int(refcount)
                # Update the entry with the new parameter or the result
                # information.
                if arg:
                    entry.args.append((arg, type, refcount))
                else:
                    entry.result_type = type
                    entry.result_refs = refcount
        finally:
            fp.close()
        return d

    def add_refcount_annotations(self, app, doctree):
        for node in doctree.traverse(addnodes.desc_content):
            par = node.parent
            if par['domain'] != 'c' or par['objtype'] != 'function':
                continue
            if not par[0].has_key('names') or not par[0]['names']:
                continue
            entry = self.get(par[0]['names'][0])
            if not entry:
                continue
            elif entry.result_type not in ("PyObject*", "PyVarObject*"):
                continue
            rc = 'Return value: '
            if entry.result_refs is None:
                rc += "Always NULL."
            else:
                rc += (entry.result_refs and "New" or "Borrowed") + \
                      " reference."
            node.insert(0, refcount(rc, rc))


def init_refcounts(app):
    if app.config.refcount_file:
        refcounts = Refcounts.fromfile(
            path.join(app.srcdir, app.config.refcount_file))
        app.connect('doctree-read', refcounts.add_refcount_annotations)


def setup(app):
    app.add_node(refcount)
    app.add_config_value('refcount_file', '', True)
    app.connect('builder-inited', init_refcounts)
