"""
A Sphinx Indexer
"""

import re
from typing import Any, List, Tuple, Pattern, cast

from docutils import nodes

from sphinx.domains.index import IndexDomain
from sphinx.errors import NoUri
from sphinx.locale import _, __
from sphinx.util import logging

logger = logging.getLogger(__name__)

# ------------------------------------------------------------


class Empty(str):
    def __repr__(self):
        return '<#empty>'

    def __str__(self):
        return ''

    def __bool__(self):
        return False


# ------------------------------------------------------------


class Subterm(object):
    def __init__(self, emphasis, *terms):
        self._delimiter = ' '

        if   emphasis == '8': self._template = _('see %s')
        elif emphasis == '9': self._template = _('see also %s')
        else: self._template = None

        self._terms = []
        for term in terms:
            if term.astext():
                self.append(term)

    def append(self, subterm):
        self._terms.append(subterm)

    def set_delimiter(self, delimiter):
        self._delimiter = delimiter

    def __repr__(self):
        rpr  = f"<{self.__class__.__name__}: len={len(self)} "
        if self._template: rpr += f"tpl='{self._template}' "
        for s in self._terms:
            rpr += repr(s)
        rpr += ">"
        return rpr

    def __str__(self):
        """Jinja2"""
        return self.astext()

    def __eq__(self, other):
        """unittest、IndexRack.generate_genindex_data."""
        return self.astext() == other

    def __len__(self):
        return len(self._terms)

    def astext(self):
        if self._template and len(self) == 1:
            return self._template % self._terms[0].astext()

        text = ""
        for subterm in self._terms:
            text += subterm.astext() + self._delimiter
        return text[:-len(self._delimiter)]


# ------------------------------------------------------------


class IndexUnit(object):

    CLSF, TERM, SBTM, EMPH = 0, 1, 2, 3

    def __init__(self, term, subterm, sort_code, main, file_name, target, index_key):
        self._display_data = ['', term, subterm]
        self._link_data = (main, file_name, target)
        self._index_key = index_key
        self._sort_order = sort_code

    def __getitem__(self, key):
        if isinstance(key, str):
            if key == 'main'     : return self._link_data[0]
            if key == 'file_name': return self._link_data[1]
            if key == 'target'   : return self._link_data[2]
            if key == 'index_key': return self._index_key
            raise KeyError(key)
        elif isinstance(key, int):
            if key == self.CLSF:
                if self._display_data[self.CLSF]:
                    return self._display_data[self.CLSF]  # classifier
                else: return Empty()
            if key == self.TERM: return self._display_data[self.TERM]  # term
            if key == self.SBTM: return self._display_data[self.SBTM]  # subterm
            if key == self.EMPH: return self._link_data[0]             # emphasis(main)
            raise KeyError(key)
        else:
            raise TypeError(key)

    def __setitem__(self, key, value):
        """Only the key of the data to be updated will be supported."""
        if isinstance(key, int):
            if key == self.CLSF: self._display_data[self.CLSF] = value
            elif key == self.TERM: self._display_data[self.TERM] = value
            elif key == self.SBTM: self._display_data[self.SBTM] = value
            else: raise KeyError(key)
        else:
            raise TypeError(key)

    def __repr__(self):
        name = self.__class__.__name__
        main = self['main']
        fn = self['file_name']
        tid = self['target']
        rpr  = f"<{name}: "
        if main: rpr += f"main='{main}' "
        if fn: rpr += f"file_name='{fn}' "
        if tid: rpr += f"target='{tid}' "
        if self[0]:
            rpr += repr(self[0])
        else:
            rpr += repr(Empty())
        rpr += repr(self[1])
        if len(self[2]) > 0: rpr += repr(self[2])
        rpr += ">"
        return rpr

    def get_children(self):
        children = [self[self.TERM]]
        if self[2]:
            for child in self[self.SBTM]._terms:
                children.append(child)
        return children

    def set_subterm_delimiter(self, delimiter=', '):
        self[self.SBTM].set_delimiter(delimiter)

    def astexts(self):
        texts = [self[self.TERM].astext()]

        for subterm in self[self.SBTM]._terms:
            texts.append(subterm.astext())

        return texts


# ------------------------------------------------------------


_each_words = re.compile(r' *; *')


class IndexEntry(nodes.Element):

    _number_of_terms = {'test': 99}

    def __init__(self, rawtext, entry_type='single', file_name=None, target=None,
                 main='', index_key='', textclass=None):
        """
        - textclass is to expand functionality for multi-byte language.
        - textclass is given by IndexRack class.
        """

        if textclass is None: textclass = nodes.Text
        # for doctest

        self.textclass = textclass
        self.unitclass = IndexUnit
        self.packclass = Subterm

        self.delimiter = '; '

        rawwords = _each_words.split(rawtext)

        terms = []
        for rawword in rawwords:
            terms.append(textclass(rawword))

        super().__init__(rawtext, *terms, entry_type=entry_type,
                         file_name=file_name, target=target, main=main, index_key=index_key)

    def __repr__(self):
        """
        >>> entry = IndexEntry('sphinx; python', 'single', 'document', 'term-1')
        >>> entry
        <IndexEntry: entry_type='single' file_name='document' target='term-1' <#text: 'sphinx'><#text: 'python'>>
        """

        name = self.__class__.__name__
        prop = f"<{name}: "

        etype, ikey = self['entry_type'], self['index_key']
        main, fn, tid = self['main'], self['file_name'], self['target']

        if etype: prop += f"entry_type='{etype}' "
        if main : prop += f"main='{main}' "
        if fn   : prop += f"file_name='{fn}' "
        if tid  : prop += f"target='{tid}' "
        if ikey : prop += f"index_key='{ikey}' "

        children = ''.join([repr(c) for c in self])
        prop += children + ">"

        return prop

    def astext(self):
        """
        >>> entry = IndexEntry('sphinx; python', 'single', 'document', 'term-1', None)
        >>> entry.astext()
        'sphinx; python'
        """
        text = self.delimiter.join(k.astext() for k in self)
        return text

    def make_index_units(self):
        """
        The parts where the data structure changes between IndexEntry and IndexUnit will be handled here.

        >>> entry = IndexEntry('sphinx', 'single', 'document', 'term-1')
        >>> entry.make_index_units()
        [<IndexUnit: main='5' file_name='document' target='term-1' <#empty><#text: 'sphinx'>>]
        """
        etype = self['entry_type']
        fn = self['file_name']
        tid = self['target']
        main = self['main']
        index_key = self['index_key']

        def _index_unit(term, sub1, sub2):
            if etype in ('see', 'seealso'):
                sort_code = '1'
                emphasis = _emphasis2char[etype]
            else:
                sort_code = '2'
                emphasis = _emphasis2char[main]

            if not sub1: sub1 = self.textclass('')
            if not sub2: sub2 = self.textclass('')
            subterm = self.packclass(emphasis, sub1, sub2)

            index_unit = self.unitclass(term, subterm, sort_code, emphasis, fn, tid, index_key)
            return index_unit

        index_units = []
        try:
            # _index_unit(term, subterm1, subterm2)
            if etype == 'single':
                try:
                    index_units.append(_index_unit(self[0], self[1], ''))
                except IndexError:
                    index_units.append(_index_unit(self[0], '', ''))
            elif etype == 'pair':
                index_units.append(_index_unit(self[0], self[1], ''))
                index_units.append(_index_unit(self[1], self[0], ''))
            elif etype == 'triple':
                index_units.append(_index_unit(self[0], self[1], self[2]))
                unit = _index_unit(self[1], self[2], self[0])
                unit.set_subterm_delimiter()
                index_units.append(unit)
                index_units.append(_index_unit(self[2], self[0], self[1]))
            elif etype == 'see':
                index_units.append(_index_unit(self[0], self[1], ''))
            elif etype == 'seealso':
                index_units.append(_index_unit(self[0], self[1], ''))
            elif etype in self._number_of_terms:
                for i in range(len(self)):
                    index_units.append(_index_unit(self[i], '', ''))
            else:
                logger.warning(__('unknown index entry type %r'), etype, location=fn)
        except IndexError as err:
            raise IndexError(str(err), repr(self))
        except ValueError as err:
            logger.warning(str(err), location=fn)

        return index_units


# ------------------------------------------------------------


# 1-5: Priority order in IndexRack.put_in_kana_catalog.
# 3,5: The order in which links are displayed in the same term/subterm.
# 8,9: Assign here for convenience. The display order will be adjusted separately.
_emphasis2char = {
    '_rsvd0_': '0',  # reserved
    'conf.py': '1',  # parameter values of conf.py
    'valuerc': '2',  # values of a file
    'main'   : '3',  # glossaryで定義した用語. indexでは「!」が先頭にあるもの.
    '_rsvd4_': '4',  # reserved
    ''       : '5',  # 'main', 'see', 'seealso'以外.
    '_rsvd6_': '6',  # reserved
    '_rsvd7_': '7',  # reserved
    'see'    : '8',
    'seealso': '9',
}

_char2emphasis = {
    '0': '', '1': '', '2': '', '3': 'main', '4': '',
    '5': '', '6': '', '7': '', '8': 'see', '9': 'seealso',
}


class IndexRack(object):
    """
    1. self.__init__() Initialization. Reading from settings.
    2. self.append() Importing the IndexUnit object. Preparing for self.update_units().
    3. self.update_units() Update each IndexUnit object and prepare for self.sort_units().
    4. self.sort_units() Sorting.
    5. self.generate_genindex_data()  Generating data for genindex.
    """

    UNIT_CLSF, UNIT_TERM, UNIT_SBTM, UNIT_EMPH = 0, 1, 2, 3

    def __init__(self, builder):

        # Save control information.
        self.env = builder.env
        self.config = builder.config
        self.get_relative_uri = builder.get_relative_uri
        self.textclass = nodes.Text
        self.entryclass = IndexEntry
        self.unitclass = IndexUnit
        self.packclass = Subterm

    def create_index(self, group_entries: bool = True,
                     _fixre: Pattern = re.compile(r'(.*) ([(][^()]*[)])')
                     ) -> List[Tuple[str, List[Tuple[str, Any]]]]:
        """see sphinx/environment/adapters/indexentries.py"""

        # Save the arguments.
        self._group_entries = group_entries
        self._fixre = _fixre

        # Initialize the container.
        self._rack = []                # [IndexUnit, IndexUnit, ...]
        self._classifier_catalog = {}  # {term: classifier}
        self._function_catalog = {}    # {function name: number of homonymous funcion}

        domain = cast(IndexDomain, self.env.get_domain('index'))
        entries = domain.entries
        # entries: Dict{file name: List[Tuple(type, value, tid, main, index_key)]}

        for fn, entries in entries.items():
            for entry_type, value, tid, main, index_key in entries:
                entry = self.entryclass(value, entry_type, fn, tid, main, index_key, self.textclass)
                entry.unitclass = self.unitclass
                entry.packclass = self.packclass
                index_units = entry.make_index_units()
                self.extend(index_units)

        self.update_units()
        self.sort_units()

        return self.generate_genindex_data()

    def append(self, unit):
        """
        Gather information for the update process, which will be determined by looking at all units.
        """
        # Gather information.
        self.put_in_classifier_catalog(unit['index_key'], self.get_word(unit[self.UNIT_TERM]))
        unit[self.UNIT_TERM].whatiam = 'term'

        # Gather information.
        if self._group_entries:
            self.put_in_function_catalog(unit.astexts(), self._fixre)

        # Put the unit on the rack.
        self._rack.append(unit)

    def extend(self, units):
        for unit in units:
            self.append(unit)

    def put_in_classifier_catalog(self, index_key, word):
        if not index_key: return
        if not word: return

        if word not in self._classifier_catalog:
            # 上書きはしない.（∵「make clean」での状況を真とするため）
            self._classifier_catalog[word] = index_key

    def put_in_function_catalog(self, texts, _fixre):
        for text in texts:
            m = _fixre.match(text)
            if m:
                try:
                    self._function_catalog[m.group(1)] += 1
                except KeyError:
                    self._function_catalog[m.group(1)] = 1
            else:
                pass

    def make_classifier_from_first_letter(self, text):
        return text[:1].upper()

    def update_units(self):
        """Update with the catalog."""

        for unit in self._rack:
            assert [unit[self.UNIT_TERM]]

            # Update multiple functions of the same name.
            if self._group_entries:
                self.update_unit_with_function_catalog(unit)

            # Set the classifier.
            self.update_unit_with_classifier_catalog(unit)

    def get_word(self, term):
        return term.astext()

    def update_unit_with_classifier_catalog(self, unit):

        ikey = unit['index_key']
        term = unit[self.UNIT_TERM]
        word = self.get_word(term)

        # ［重要］if/elifの判定順
        if ikey:
            clsf = self.textclass(ikey)
        elif word in self._classifier_catalog:
            clsf = self.textclass(self._classifier_catalog[word])
        else:
            char = self.make_classifier_from_first_letter(term.astext())
            clsf = self.textclass(char)
        clsf.whatiam = 'classifier'
        unit[self.UNIT_CLSF] = clsf

    def update_unit_with_function_catalog(self, unit):
        """
        fixup entries: transform
          func() (in module foo)
          func() (in module bar)
        into
          func()
            (in module foo)
            (in module bar)
        """
        i_tm = unit[self.UNIT_TERM]
        m = self._fixre.match(i_tm.astext())

        # If you have a function name and a module name in the format that _fixre expects,
        # and you have multiple functions with the same name.
        if m and self._function_catalog[m.group(1)] > 1:
            unit[self.UNIT_TERM] = self.textclass(m.group(1))

            if unit[self.UNIT_SBTM]:
                subterm = unit[self.UNIT_SBTM].astext()
                term = self.textclass(m.group(2) + ', ' + subterm)
            else:
                term = self.textclass(m.group(2))

 
            unit[self.UNIT_SBTM] = self.packclass(unit[self.UNIT_EMPH], term)

    def sort_units(self):
        self._rack.sort(key=lambda x: (
            x[self.UNIT_CLSF].astext(),  # classifier
            x[self.UNIT_TERM].astext(),  # term
            x._sort_order,               # entry type in('see', 'seealso')
            x[self.UNIT_SBTM].astext(),  # subterm
            x[self.UNIT_EMPH],           # emphasis(main)
            x['file_name'], x['target']))
        # about x['file_name'], x['target'].
        # Reversing it will make it dependent on the presence of "make clean".

    def generate_genindex_data(self):
        rtnlist = []

        _clf, _tm, _sub = -1, -1, -1
        for unit in self._rack:  # take a unit from the rack.
            i_clf = unit[self.UNIT_CLSF]
            i_tm  = unit[self.UNIT_TERM]
            i_sub = unit[self.UNIT_SBTM]
            i_em  = unit[self.UNIT_EMPH]
            i_fn  = unit['file_name']
            i_tid = unit['target']
            i_iky = unit['index_key']

            # make a uri
            if i_fn:
                try:
                    r_uri = self.get_relative_uri('genindex', i_fn) + '#' + i_tid
                except NoUri:
                    continue

            # see: KanaText.__eq__
            if len(rtnlist) == 0 or not rtnlist[_clf][0] == i_clf.astext():
                rtnlist.append((i_clf, []))

                # Update _clf to see "(clf, [])" added. Reset the others.
                _clf, _tm, _sub = _clf + 1, -1, -1

            r_clsfr = rtnlist[_clf]  # [classifier, [term, term, ..]]
            r_clfnm = r_clsfr[0]     # classifier is KanaText object.
            r_subterms = r_clsfr[1]  # [term, term, ..]

            # see: KanaText.__eq__
            if len(r_subterms) == 0 or not r_subterms[_tm][0] == i_tm.astext():
                r_subterms.append((i_tm, [[], [], i_iky]))

                # Update _tm to see "(i_tm, [[], [], i_iky])" added. Reset the other.
                _tm, _sub = _tm + 1, -1

            r_term = r_subterms[_tm]     # [term, [links, [subterm, subterm, ..], index_key]
            r_term_value = r_term[0]     # term_value is KanaText object.
            r_term_links = r_term[1][0]  # [(main, uri), (main, uri), ..]
            r_subterms = r_term[1][1]    # [subterm, subterm, ..]

            # Change the code to string.
            r_main = _char2emphasis[i_em]

            # if it's see/seealso, reset file_name for no uri.
            if r_main in ('see', 'seealso'):
                r_fn = None
            else:
                r_fn = i_fn

            # sub(class Subterm): [], [KanaText], [KanaText, KanaText].
            if len(i_sub) == 0:
                if r_fn: r_term_links.append((r_main, r_uri))
            elif len(r_subterms) == 0 or not r_subterms[_sub][0] == i_sub.astext():
                r_subterms.append((i_sub, []))

                _sub = _sub + 1
                r_subterm = r_subterms[_sub]
                r_subterm_value = r_subterm[0]
                r_subterm_links = r_subterm[1]
                if r_fn: r_subterm_links.append((r_main, r_uri))
            else:
                if r_fn: r_subterm_links.append((r_main, r_uri))

        return rtnlist


# ------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod()
