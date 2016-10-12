# -*- coding: utf-8 -*-
"""
    sphinx.environment.managers.indexentries
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Index entries manager for sphinx.environment.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import re
import bisect
import unicodedata
import string
from itertools import groupby

from six import text_type

from sphinx import addnodes
from sphinx.util import iteritems, split_index_msg, split_into
from sphinx.locale import _
from sphinx.environment.managers import EnvironmentManager


class IndexEntries(EnvironmentManager):
    name = 'indices'

    def __init__(self, env):
        super(IndexEntries, self).__init__(env)
        self.data = env.indexentries

    def clear_doc(self, docname):
        self.data.pop(docname, None)

    def merge_other(self, docnames, other):
        for docname in docnames:
            self.data[docname] = other.indexentries[docname]

    def process_doc(self, docname, doctree):
        entries = self.data[docname] = []
        for node in doctree.traverse(addnodes.index):
            try:
                for entry in node['entries']:
                    split_index_msg(entry[0], entry[1])
            except ValueError as exc:
                self.env.warn_node(exc, node)
                node.parent.remove(node)
            else:
                for entry in node['entries']:
                    if len(entry) == 5:
                        # Since 1.4: new index structure including index_key (5th column)
                        entries.append(entry)
                    else:
                        entries.append(entry + (None,))

    def create_index(self, builder, group_entries=True,
                     _fixre=re.compile(r'(.*) ([(][^()]*[)])')):
        """Create the real index from the collected index entries."""
        from sphinx.environment import NoUri

        new = {}

        def add_entry(word, subword, main, link=True, dic=new, key=None):
            # Force the word to be unicode if it's a ASCII bytestring.
            # This will solve problems with unicode normalization later.
            # For instance the RFC role will add bytestrings at the moment
            word = text_type(word)
            entry = dic.get(word)
            if not entry:
                dic[word] = entry = [[], {}, key]
            if subword:
                add_entry(subword, '', main, link=link, dic=entry[1], key=key)
            elif link:
                try:
                    uri = builder.get_relative_uri('genindex', fn) + '#' + tid
                except NoUri:
                    pass
                else:
                    # maintain links in sorted/deterministic order
                    bisect.insort(entry[0], (main, uri))

        for fn, entries in iteritems(self.data):
            # new entry types must be listed in directives/other.py!
            for type, value, tid, main, index_key in entries:
                try:
                    if type == 'single':
                        try:
                            entry, subentry = split_into(2, 'single', value)
                        except ValueError:
                            entry, = split_into(1, 'single', value)
                            subentry = ''
                        add_entry(entry, subentry, main, key=index_key)
                    elif type == 'pair':
                        first, second = split_into(2, 'pair', value)
                        add_entry(first, second, main, key=index_key)
                        add_entry(second, first, main, key=index_key)
                    elif type == 'triple':
                        first, second, third = split_into(3, 'triple', value)
                        add_entry(first, second + ' ' + third, main, key=index_key)
                        add_entry(second, third + ', ' + first, main, key=index_key)
                        add_entry(third, first + ' ' + second, main, key=index_key)
                    elif type == 'see':
                        first, second = split_into(2, 'see', value)
                        add_entry(first, _('see %s') % second, None,
                                  link=False, key=index_key)
                    elif type == 'seealso':
                        first, second = split_into(2, 'see', value)
                        add_entry(first, _('see also %s') % second, None,
                                  link=False, key=index_key)
                    else:
                        self.env.warn(fn, 'unknown index entry type %r' % type)
                except ValueError as err:
                    self.env.warn(fn, str(err))

        # sort the index entries; put all symbols at the front, even those
        # following the letters in ASCII, this is where the chr(127) comes from
        def keyfunc(entry, lcletters=string.ascii_lowercase + '_'):
            lckey = unicodedata.normalize('NFD', entry[0].lower())
            if lckey[0:1] in lcletters:
                lckey = chr(127) + lckey
            # ensure a determinstic order *within* letters by also sorting on
            # the entry itself
            return (lckey, entry[0])
        newlist = sorted(new.items(), key=keyfunc)

        if group_entries:
            # fixup entries: transform
            #   func() (in module foo)
            #   func() (in module bar)
            # into
            #   func()
            #     (in module foo)
            #     (in module bar)
            oldkey = ''
            oldsubitems = None
            i = 0
            while i < len(newlist):
                key, (targets, subitems, _key) = newlist[i]
                # cannot move if it has subitems; structure gets too complex
                if not subitems:
                    m = _fixre.match(key)
                    if m:
                        if oldkey == m.group(1):
                            # prefixes match: add entry as subitem of the
                            # previous entry
                            oldsubitems.setdefault(m.group(2), [[], {}, _key])[0].\
                                extend(targets)
                            del newlist[i]
                            continue
                        oldkey = m.group(1)
                    else:
                        oldkey = key
                oldsubitems = subitems
                i += 1

        # group the entries by letter
        def keyfunc2(item, letters=string.ascii_uppercase + '_'):
            # hack: mutating the subitems dicts to a list in the keyfunc
            k, v = item
            v[1] = sorted((si, se) for (si, (se, void, void)) in iteritems(v[1]))
            if v[2] is None:
                # now calculate the key
                letter = unicodedata.normalize('NFD', k[0])[0].upper()
                if letter in letters:
                    return letter
                else:
                    # get all other symbols under one heading
                    return _('Symbols')
            else:
                return v[2]
        return [(key_, list(group))
                for (key_, group) in groupby(newlist, keyfunc2)]
