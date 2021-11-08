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

# Update separately from the package version, since 2021-11-07
__version__ = "1.4.20211108"
# x.y.YYYYMMDD[.HHMI]
# - x: changes that need to be addressed by the user.
# - y: changes that do not require a response from the user.

logger = logging.getLogger(__name__)


# ------------------------------------------------------------


def chop_mark(rawtext):
    text = normalize('NFD', rawtext)
    if text.startswith('\N{RIGHT-TO-LEFT MARK}'):
        text = text[1:]
    return text


def sort_key(text):
    if not text:
        return (0, '')
    elif text[0].upper().isalpha() or text.startswith('_'):
        return (1, text.upper())
    else:
        return (0, text.upper())


class Text(nodes.Text):

    whatiam = 'term'

    def assort(self):
        text = chop_mark(self)

        if self.whatiam == 'classifier' and text == _('Symbols'):
            return (0, text)

        return sort_key(text)

# ------------------------------------------------------------


class Represent(object):
    def represent(self, data, end=None):
        name = self.__class__.__name__
        rpr  = f"<{name}: {data}"
        if end:
            for o in self[0:end]: rpr += repr(o)
            if self[end].astext(): rpr += repr(self[end])
        else:
            for o in self: rpr += repr(o)
        return rpr + ">"


# ------------------------------------------------------------


class Subterm(Represent, nodes.Element):
    def __init__(self, link, *terms):
        if   link == 1: template = _('see %s')
        elif link == 2: template = _('see also %s')
        else: template = None

        _terms = []
        for term in terms:
            if term.astext(): _terms.append(term)

        super().__init__(''.join([repr(term) for term in terms]), *_terms, delimiter=' ', template=template)

    def __repr__(self, attr=""):
        attr += f"len={len(self)} "
        if self['delimiter'] != ' ': attr += f"delimiter='{self['delimiter']}' "
        if self['template']: attr += f"tpl='{self['template']}' "
        return self.represent(attr)

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

    def assort(self):
        text = chop_mark(self.astext())
        return sort_key(text)


# ------------------------------------------------------------


UNIT_CLSF = 0  # a classifier. The index_key and category_key are variable names.
UNIT_TERM = 1  # a primary term.
UNIT_SBTM = 2  # a secondary term.


class IndexUnit(Represent, nodes.Element):

    def __init__(self, term, subterm, link_type, main, file_name, target, index_key):

        super().__init__(repr(term)+repr(subterm),  # rawsource used for debug.
                         nodes.Text(''), term, subterm, link_type=link_type,
                         main=main, file_name=file_name, target=target, index_key=index_key)
        # Text is used to avoid errors in Element.__init__.
        # Since it is always overwritten in IndexRack, consideration for extensibility isn't needed.

    def __repr__(self, attr=""):
        if self['main']: attr += f"main "
        if self['file_name']: attr += f"file_name='{self['file_name']}' "
        if self['target']: attr += f"target='{self['target']}' "
        return self.represent(attr, 2)

    def set_subterm_delimiter(self, delimiter=', '):
        self[UNIT_SBTM]['delimiter'] = delimiter


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


class IndexEntry(Represent, nodes.Element):

    other_entry_types = ('list')

    textclass = Text
    packclass = Subterm
    unitclass = IndexUnit

    def __init__(self, rawtext, entry_type='single', file_name=None, target=None,
                 main='', index_key=''):
        """
        - textclass is to expand functionality for multi-byte language.
        - textclass is given by IndexRack class.
        """

        self.delimiter = '; '

        rawwords = _each_words.split(rawtext)

        terms = []
        for rawword in rawwords:
            terms.append(self.textclass(rawword, rawword))

        super().__init__(rawtext, *terms, entry_type=entry_type,
                         file_name=file_name, target=target, main=main, index_key=index_key)

    def __repr__(self, attr=""):
        """
        >>> entry = IndexEntry('sphinx; python', 'single', 'document', 'term-1')
        >>> entry
        <IndexEntry: entry_type='single' file_name='document' target='term-1' <#text: 'sphinx'><#text: 'python'>>
        """

        if self['entry_type']: attr += f"entry_type='{self['entry_type']}' "
        if self['main']      : attr += f"main "
        if self['file_name'] : attr += f"file_name='{self['file_name']}' "
        if self['target']    : attr += f"target='{self['target']}' "
        if self['index_key'] : attr += f"index_key='{self['index_key']}' "

        return self.represent(attr)

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
        [<IndexUnit: main file_name='document' target='term-1' <#text: ''><#text: 'sphinx'>>]
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
                index_units.append(_index_unit(self[0], self[1], self[2]))  # the delimiter is ' '
                index_units.append(_index_unit(self[1], self[2], self[0]))  # the delimiter should be ', '
                index_units.append(_index_unit(self[2], self[0], self[1]))  # the delimiter is ' '
                index_units[1].set_subterm_delimiter()  # the delimiter became ', '
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

    textclass = Text
    packclass = Subterm
    unitclass = IndexUnit
    entryclass = IndexEntry

    def __init__(self, builder):

        # Save control information.
        self.env = builder.env
        self.config = builder.config
        self.get_relative_uri = builder.get_relative_uri

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
                entry = self.entryclass(value, entry_type, fn, tid, main, ikey)
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
        self.put_in_classifier_catalog(unit['index_key'], unit[UNIT_TERM].astext())
        unit[UNIT_TERM].whatiam = 'term'

        # Gather information.
        if self._group_entries:
            self.put_in_function_catalog(unit, self._fixre)

        # Put the unit on the rack.
        self._rack.append(unit)

    def extend(self, units):
        for unit in units:
            self.append(unit)

    def put_in_classifier_catalog(self, index_key, word):
        if not index_key: return
        if not word: raise ValueError(repr(self))

        if word not in self._classifier_catalog:
            # No overwriting. (To make the situation in "make clean" true)
            self._classifier_catalog[word] = index_key

    def put_in_function_catalog(self, unit, _fixre):
        m = _fixre.match(unit[UNIT_TERM].astext())
        if m:
            try:
                self._function_catalog[m.group(1)] += 1
            except KeyError:
                self._function_catalog[m.group(1)] = 1
        else:
            pass

    def update_units(self):
        """Update with the catalog."""

        for unit in self._rack:
            assert [unit[UNIT_TERM]]

            # Update multiple functions of the same name.
            if self._group_entries:
                self.update_unit_with_function_catalog(unit)

            # Set the classifier.
            self.update_unit_with_classifier_catalog(unit)

    def update_unit_with_classifier_catalog(self, unit):

        ikey = unit['index_key']
        term = unit[UNIT_TERM]
        word = term.astext()

        # Important: The order in which if/elif decisions are made.
        if ikey:
            _key, _raw = chop_mark(ikey), ikey
        elif word in self._classifier_catalog:
            _key, _raw = chop_mark(self._classifier_catalog[word]), word
        else:
            _key = chop_mark(term.astext())
            _key, _raw = self.make_classifier_from_first_letter(_key), term.astext()

        unit[UNIT_CLSF] = self.textclass(_key, _raw)
        unit[UNIT_CLSF].whatiam = 'classifier'

    def make_classifier_from_first_letter(self, text):
        if text[0].upper().isalpha() or text.startswith('_'):
            return text[0].upper()
        else:
            return _('Symbols')

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
        i_tm = unit[UNIT_TERM]
        m = self._fixre.match(i_tm.astext())

        # If you have a function name and a module name in the format that _fixre expects,
        # and you have multiple functions with the same name.
        if m and self._function_catalog[m.group(1)] > 1:
            unit[UNIT_TERM] = self.textclass(m.group(1))

            if unit[UNIT_SBTM].astext():
                subterm = unit[UNIT_SBTM].astext()
                term = self.textclass(m.group(2) + ', ' + subterm)
            else:
                term = self.textclass(m.group(2))

            unit[UNIT_SBTM] = self.packclass(unit['link_type'], term)

    def sort_units(self):
        """What is done in Text is done in Text, and what is done in IndexUnit is done in IndexUnit."""
        self._rack.sort(key=lambda unit: (
            unit[UNIT_CLSF].assort(),  # classifier
            unit[UNIT_TERM].assort(),  # primary term
            unit['link_type'],  # see Convert. 1:'see', 2:'seealso', 3:'uri'.
            unit[UNIT_SBTM].assort(),  # secondary term
            unit['main'],       # see Convert. 3:'main', 4:''.
            unit['file_name'],
            unit['target']), )
        # about x['file_name'], x['target'].
        # Reversing it will make it dependent on the presence of "make clean".

    def generate_genindex_data(self):
        rtnlist = []

        _clf, _tm, _sub = -1, -1, -1
        for unit in self._rack:  # take a unit from the rack.
            i_clf = unit[UNIT_CLSF]
            i_tm  = unit[UNIT_TERM]
            i_sub = unit[UNIT_SBTM]
            i_em  = unit['main']
            i_lnk = unit['link_type']
            i_fn  = unit['file_name']
            i_tid = unit['target']
            i_iky = unit['index_key']

            # see: KanaText.__eq__
            if len(rtnlist) == 0 or not rtnlist[_clf][0] == i_clf.astext():
                # Enter a clsssifier.
                rtnlist.append((i_clf, []))

                # Post-processing.
                _clf, _tm, _sub = _clf + 1, -1, -1
                # Update _clf to see "(clf, [])" added. Reset the others.

            r_clsfr = rtnlist[_clf]  # [classifier, [term, term, ..]]
            r_clfnm = r_clsfr[0]     # classifier is KanaText object.
            r_terms = r_clsfr[1]     # [term, term, ..]

            # see: KanaText.__eq__
            if len(r_terms) == 0 or not r_terms[_tm][0] == i_tm.astext():
                # Enter a term.
                r_terms.append((i_tm, [[], [], i_iky]))

                # Post-processing.
                _tm, _sub = _tm + 1, -1
                # Update _tm to see "(i_tm, [[], [], i_iky])" added. Reset the other.
            else:
                pass

            r_term = r_terms[_tm]        # [term, [links, [subterm, subterm, ..], index_key]
            r_term_value = r_term[0]     # term_value is KanaText object.
            r_term_links = r_term[1][0]  # [(main, uri), (main, uri), ..]
            r_subterms = r_term[1][1]    # [subterm, subterm, ..]

            # if it's see/seealso, reset file_name for no uri. see Convert.
            if i_lnk == 3:
                # Change the code to string.
                r_main = _cnv.code2main(i_em)

                # uri
                try:
                    r_uri = self.get_relative_uri('genindex', i_fn) + '#' + i_tid
                except NoUri:
                    continue
            else:
                r_uri= None


            # sub(class Subterm): [], [KanaText], [KanaText, KanaText].
            if len(i_sub) == 0:
                if r_uri: r_term_links.append((r_main, r_uri))
            elif len(r_subterms) == 0 or not r_subterms[_sub][0] == i_sub.astext():
                # Enter a subterm.
                r_subterms.append((i_sub, []))

                # Post-processing.
                _sub = _sub + 1
                r_subterm = r_subterms[_sub]
                r_subterm_value = r_subterm[0]
                r_subterm_links = r_subterm[1]

                # Enter a link.
                if r_uri: r_subterm_links.append((r_main, r_uri))
            else:
                # Enter a link.
                if r_uri: r_subterm_links.append((r_main, r_uri))

        return rtnlist


# ------------------------------------------------------------
