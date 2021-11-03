"""
A Sphinx Indexer
"""

import re
from unicodedata import normalize
from typing import Any, List, Tuple, Pattern, cast

from docutils import nodes

from sphinx.domains.index import IndexDomain
from sphinx.errors import NoUri
from sphinx.locale import _, __
from sphinx.util import logging

logger = logging.getLogger(__name__)


# ------------------------------------------------------------


class Subterm(nodes.Element):
    def __init__(self, link, *terms):
        if   link == 1: template = _('see %s')
        elif link == 2: template = _('see also %s')
        else: template = None

        _terms = []
        for term in terms:
            if term.astext(): _terms.append(term)

        super().__init__(''.join([repr(term) for term in terms]), *_terms, delimiter=' ', template=template)

    def __repr__(self):
        rpr  = f"<{self.__class__.__name__}: len={len(self)} "
        if self['delimiter'] != ' ': rpr += f"delimiter='{self['delimiter']}' "
        if self['template']: rpr += f"tpl='{self['template']}' "
        for s in self: rpr += repr(s)
        rpr += ">"
        return rpr

    def __str__(self):
        """Jinja2"""
        return self.astext()

    def __eq__(self, other):
        """unittest、IndexRack.generate_genindex_data."""
        return self.astext() == other

    def astext(self):
        if self['template'] and len(self) == 1:
            return self['template'] % self[0].astext()

        text = ""
        for subterm in self:
            text += subterm.astext() + self['delimiter']
        return text[:-len(self['delimiter'])]


# ------------------------------------------------------------


class IndexUnit(nodes.Element):

    CLSF, TERM, SBTM = 0, 1, 2

    def __init__(self, term, subterm, link_type, main, file_name, target, index_key):

        super().__init__(repr(term)+repr(subterm),  # rawsource used for debug.
                         self.textclass(''), term, subterm, link_type=link_type,
                         main=main, file_name=file_name, target=target, index_key=index_key)

    def textclass(self, rawword, rawsource=""):
        return nodes.Text(rawword, rawsource)

    def __repr__(self):
        name = self.__class__.__name__
        main = self['main']
        fn = self['file_name']
        tid = self['target']
        rpr  = f"<{name}: "
        if main: rpr += f"main "
        if fn: rpr += f"file_name='{fn}' "
        if tid: rpr += f"target='{tid}' "
        rpr += repr(self[0])
        rpr += repr(self[1])
        if len(self[2]) > 0: rpr += repr(self[2])
        rpr += ">"
        return rpr

    def get_children(self):
        children = [self[self.TERM]]
        if self[2]:
            for child in self[self.SBTM]:
                children.append(child)
        return children

    def set_subterm_delimiter(self, delimiter=', '):
        self[self.SBTM]['delimiter'] = delimiter

    def astexts(self):
        texts = [self[self.TERM].astext()]

        for subterm in self[self.SBTM]:
            texts.append(subterm.astext())

        return texts


# ------------------------------------------------------------


class Convert(object):

    _type_to_link = {'see': 1, 'seealso': 2, 'uri': 3}

    _main_to_code = {'conf.py':1, 'rcfile':2, 'main':3, '': 4}
    _code_to_main = {1:'conf.py', 2:'rcfile', 3:'main', 4:''}

    def type2link(self, link):
        return self._type_to_link[link]

    def main2code(self, main):
        return self._main_to_code[main]

    def code2main(self, code):
        return self._code_to_main[code]

_cnv = Convert()


# ------------------------------------------------------------


_each_words = re.compile(r' *; *')


class IndexEntry(nodes.Element):

    other_entry_types = ('list')

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
            terms.append(textclass(rawword, rawword))

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
                link = _cnv.type2link(etype)
            else:
                link = _cnv.type2link('uri')

            emphasis = _cnv.main2code(main)

            if not sub1: sub1 = self.textclass('')
            if not sub2: sub2 = self.textclass('')
            subterm = self.packclass(link, sub1, sub2)

            index_unit = self.unitclass(term, subterm, link, emphasis, fn, tid, index_key)
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
            elif etype in self.other_entry_types:
                for i in range(len(self)):
                    index_units.append(_index_unit(self[i], '', ''))
            else:
                logger.warning(__('unknown index entry type %r'), etype, location=fn)
        except IndexError as err:
            raise IndexError(str(err), repr(self))
        except ValueError as err:
            logger.warning(str(err), location=fn)

        return index_units


class IndexRack(nodes.Element):
    """
    1. self.__init__() Initialization. Reading from settings.
    2. self.append() Importing the IndexUnit object. Preparing for self.update_units().
    3. self.update_units() Update each IndexUnit object and prepare for self.sort_units().
    4. self.sort_units() Sorting.
    5. self.generate_genindex_data()  Generating data for genindex.
    """

    UNIT_CLSF, UNIT_TERM, UNIT_SBTM = 0, 1, 2

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
            for entry_type, value, tid, main, ikey in entries:
                entry = self.entryclass(value, entry_type, fn, tid, main, ikey, self.textclass)
                entry.unitclass = self.unitclass
                entry.packclass = self.packclass
                index_units = entry.make_index_units()
                self += index_units

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
        text = normalize('NFD', text)
        if text.startswith('\N{RIGHT-TO-LEFT MARK}'):
            text = text[1:]

        if text[0].upper().isalpha() or text.startswith('_'):
            return text[0].upper()
        else:
            return _('Symbols')

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

        # Important: The order in which if/elif decisions are made.
        if ikey:
            _key, _raw = ikey, ikey
        elif word in self._classifier_catalog:
            _key, _raw = self._classifier_catalog[word], word
        else:
            _key, _raw = self.make_classifier_from_first_letter(term.astext()), term.astext()

        clsf = self.textclass(_key, _raw)
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

            if unit[self.UNIT_SBTM].astext():
                subterm = unit[self.UNIT_SBTM].astext()
                term = self.textclass(m.group(2) + ', ' + subterm)
            else:
                term = self.textclass(m.group(2))

            unit[self.UNIT_SBTM] = self.packclass(unit['link_type'], term)

    def for_sort(self, term):
        text = term.astext()
        if text == _('Symbols'):
            return (0, text)

        text = normalize('NFD', text.lower())
        if text.startswith('\N{RIGHT-TO-LEFT MARK}'):
            text = text[1:]

        if text[0:1].isalpha() or text.startswith('_'):
            return (1, text)
        else:
            # symbol
            return (0, text)

    def sort_units(self):
        self._rack.sort(key=lambda unit: (
            self.for_sort(unit[self.UNIT_CLSF]),  # classifier
            self.for_sort(unit[self.UNIT_TERM]),  # term
            unit['link_type'],                    # 1:'see', 2:'seealso', 3:'uri'. see Convert class.
            self.for_sort(unit[self.UNIT_SBTM]),  # subterm
            unit['main'],                         # 3:'main', 4:''. see Convert class.
            unit['file_name'],
            unit['target']), )
        # about x['file_name'], x['target'].
        # Reversing it will make it dependent on the presence of "make clean".

    def generate_genindex_data(self):
        rtnlist = []

        _clf, _tm, _sub = -1, -1, -1
        for unit in self._rack:  # take a unit from the rack.
            i_clf = unit[self.UNIT_CLSF]
            i_tm  = unit[self.UNIT_TERM]
            i_sub = unit[self.UNIT_SBTM]
            i_em  = unit['main']
            i_lnk = unit['link_type']
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
            r_main = _cnv.code2main(i_em)

            # if it's see/seealso, reset file_name for no uri.
            if i_lnk == 3:
                r_fn = i_fn
            else:
                r_fn = None

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
