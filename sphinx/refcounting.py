# -*- coding: utf-8 -*-
"""
    sphinx.refcounting
    ~~~~~~~~~~~~~~~~~~

    Handle reference counting annotations, based on refcount.py
    and anno-api.py.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

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
                # Update the entry with the new parameter or the result information.
                if arg:
                    entry.args.append((arg, type, refcount))
                else:
                    entry.result_type = type
                    entry.result_refs = refcount
        finally:
            fp.close()
        return d
