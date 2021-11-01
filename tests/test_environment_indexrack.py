"""
    test_environment_indexrack
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the sphinx.environment.managers.indexrack.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest

from docutils.nodes import Text as txtcls
from sphinx.environment.adapters import indexrack as irack
from sphinx.testing import restructuredtext


@pytest.mark.sphinx('dummy', freshenv=True)
def test_create_single_index(app):
    text = (".. index:: docutils\n"
            ".. index:: Python\n"
            ".. index:: pip; install\n"
            ".. index:: pip; upgrade\n"
            ".. index:: Sphinx\n"
            ".. index:: Ель\n"
            ".. index:: ёлка\n"
            ".. index:: ‏עברית‎\n"
            ".. index:: 9-symbol\n"
            ".. index:: &-symbol\n"
            ".. index:: £100\n")
    restructuredtext.parse(app, text)
    index = irack.IndexRack(app.builder).create_index()
    assert len(index) == 6
    assert index[0] == ('Symbols', [('&-symbol', [[('', '#index-9')], [], None]),
                                    ('9-symbol', [[('', '#index-8')], [], None]),
                                    ('£100', [[('', '#index-10')], [], None])])
    assert index[1] == ('D', [('docutils', [[('', '#index-0')], [], None])])
    assert index[2] == ('P', [('pip', [[], [('install', [('', '#index-2')]),
                                            ('upgrade', [('', '#index-3')])], None]),
                              ('Python', [[('', '#index-1')], [], None])])
    assert index[3] == ('S', [('Sphinx', [[('', '#index-4')], [], None])])
    assert index[4] == ('Е',
                        [('ёлка', [[('', '#index-6')], [], None]),
                         ('Ель', [[('', '#index-5')], [], None])])
    # Here the word starts with U+200F RIGHT-TO-LEFT MARK, which should be
    # ignored when getting the first letter.
    assert index[5] == ('ע', [('‏עברית‎', [[('', '#index-7')], [], None])])

@pytest.mark.sphinx('dummy', freshenv=True)
def test_create_pair_index(app):
    text = (".. index:: pair: docutils; reStructuredText\n"
            ".. index:: pair: Python; interpreter\n"
            ".. index:: pair: Sphinx; documentation tool\n"
            ".. index:: pair: Sphinx; :+1:\n"
            ".. index:: pair: Sphinx; Ель\n"
            ".. index:: pair: Sphinx; ёлка\n")
    restructuredtext.parse(app, text)
    index = irack.IndexRack(app.builder).create_index()
    assert len(index) == 7
    assert index[0] == ('Symbols', [(':+1:', [[], [('Sphinx', [('', '#index-3')])], None])])
    assert index[1] == ('D',
                        [('documentation tool', [[], [('Sphinx', [('', '#index-2')])], None]),
                         ('docutils', [[], [('reStructuredText', [('', '#index-0')])], None])])
    assert index[2] == ('I', [('interpreter', [[], [('Python', [('', '#index-1')])], None])])
    assert index[3] == ('P', [('Python', [[], [('interpreter', [('', '#index-1')])], None])])
    assert index[4] == ('R',
                        [('reStructuredText', [[], [('docutils', [('', '#index-0')])], None])])
    assert index[5] == ('S',
                        [('Sphinx', [[],
                                     [(':+1:', [('', '#index-3')]),
                                      ('documentation tool', [('', '#index-2')]),
                                      ('ёлка', [('', '#index-5')]),
                                      ('Ель', [('', '#index-4')])],
                                     None])])
    assert index[6] == ('Е',
                        [('ёлка', [[], [('Sphinx', [('', '#index-5')])], None]),
                         ('Ель', [[], [('Sphinx', [('', '#index-4')])], None])])


@pytest.mark.sphinx('dummy', freshenv=True)
def test_create_triple_index(app):
    text = (".. index:: triple: foo; bar; baz\n"
            ".. index:: triple: Python; Sphinx; reST\n")
    restructuredtext.parse(app, text)
    index = irack.IndexRack(app.builder).create_index()
    assert len(index) == 5
    assert index[0] == ('B', [('bar', [[], [('baz, foo', [('', '#index-0')])], None]),
                              ('baz', [[], [('foo bar', [('', '#index-0')])], None])])
    assert index[1] == ('F', [('foo', [[], [('bar baz', [('', '#index-0')])], None])])
    assert index[2] == ('P', [('Python', [[], [('Sphinx reST', [('', '#index-1')])], None])])
    assert index[3] == ('R', [('reST', [[], [('Python Sphinx', [('', '#index-1')])], None])])
    assert index[4] == ('S', [('Sphinx', [[], [('reST, Python', [('', '#index-1')])], None])])


@pytest.mark.sphinx('dummy', freshenv=True)
def test_create_see_index(app):
    text = (".. index:: see: docutils; reStructuredText\n"
            ".. index:: see: Python; interpreter\n"
            ".. index:: see: Sphinx; documentation tool\n")
    restructuredtext.parse(app, text)
    index = irack.IndexRack(app.builder).create_index()
    assert len(index) == 3
    assert index[0] == ('D', [('docutils', [[], [('see reStructuredText', [])], None])])
    assert index[1] == ('P', [('Python', [[], [('see interpreter', [])], None])])
    assert index[2] == ('S', [('Sphinx', [[], [('see documentation tool', [])], None])])


@pytest.mark.sphinx('dummy', freshenv=True)
def test_create_seealso_index(app):
    text = (".. index:: seealso: docutils; reStructuredText\n"
            ".. index:: seealso: Python; interpreter\n"
            ".. index:: seealso: Sphinx; documentation tool\n")
    restructuredtext.parse(app, text)
    index = irack.IndexRack(app.builder).create_index()
    assert len(index) == 3
    assert index[0] == ('D', [('docutils', [[], [('see also reStructuredText', [])], None])])
    assert index[1] == ('P', [('Python', [[], [('see also interpreter', [])], None])])
    assert index[2] == ('S', [('Sphinx', [[], [('see also documentation tool', [])], None])])


@pytest.mark.sphinx('dummy', freshenv=True)
def test_create_main_index(app):
    text = (".. index:: !docutils\n"
            ".. index:: docutils\n"
            ".. index:: pip; install\n"
            ".. index:: !pip; install\n")
    restructuredtext.parse(app, text)
    index = irack.IndexRack(app.builder).create_index()
    assert len(index) == 2
    assert index[0] == ('D', [('docutils', [[('main', '#index-0'),
                                             ('', '#index-1')], [], None])])
    assert index[1] == ('P', [('pip', [[], [('install', [('main', '#index-3'),
                                                         ('', '#index-2')])], None])])


@pytest.mark.sphinx('dummy', freshenv=True)
def test_create_index_with_name(app):
    text = (".. index:: single: docutils\n"
            "   :name: ref1\n"
            ".. index:: single: Python\n"
            "   :name: ref2\n"
            ".. index:: Sphinx\n")
    restructuredtext.parse(app, text)
    index = irack.IndexRack(app.builder).create_index()

    # check index is created correctly
    assert len(index) == 3
    assert index[0] == ('D', [('docutils', [[('', '#ref1')], [], None])])
    assert index[1] == ('P', [('Python', [[('', '#ref2')], [], None])])
    assert index[2] == ('S', [('Sphinx', [[('', '#index-0')], [], None])])

    # check the reference labels are created correctly
    std = app.env.get_domain('std')
    assert std.anonlabels['ref1'] == ('index', 'ref1')
    assert std.anonlabels['ref2'] == ('index', 'ref2')


@pytest.mark.sphinx('dummy', freshenv=True)
def test_create_index_by_key(app):
    # At present, only glossary directive is able to create index key
    text = (".. glossary::\n"
            "\n"
            "   docutils\n"
            "   Python\n"
            "   スフィンクス : ス\n")
    restructuredtext.parse(app, text)
    index = irack.IndexRack(app.builder).create_index()
    assert len(index) == 3
    assert index[0] == ('D', [('docutils', [[('main', '#term-docutils')], [], None])])
    assert index[1] == ('P', [('Python', [[('main', '#term-Python')], [], None])])
    assert index[2] == ('ス', [('スフィンクス', [[('main', '#term-0')], [], 'ス'])])


@pytest.mark.sphinx('dummy', freshenv=True)
def test_issue9795(app):
    text = (".. index:: Ель\n"
            ".. index:: ёлка\n")
    restructuredtext.parse(app, text)
    rack = irack.IndexRack(app.builder)
    index = rack.create_index()
    assert len(index) == 1
    assert index[0][0] == 'Е'
    assert index[0][1][1] == ('Ель', [[('', '#index-0')], [], None])
    assert index[0][1][0][1] == [[('', '#index-1')], [], None]
    assert rack._rack[0][1].rawsource == 'ёлка'
    assert rack._rack[0][1].astext() == 'ёлка'
    assert index[0][1][0][0] == 'ёлка'


#-------------------------------------------------------------------


class domain(object):
    def __init__(self, entries):
        self.entries = entries


class environment(object):
    def __init__(self, entries):
        self.domain = {}
        self.domain['index'] = domain(entries)
    def get_domain(self, domain_type):
        return self.domain[domain_type]


class config(object):
    def __init__(self):
        self.parameter_name = 'value'


class builder(object):
    def __init__(self, entries):
        self.env = environment(entries)
        self.get_domain = self.env.get_domain
        self.config = config()
    def get_relative_uri(self, uri_type, file_name):
        return f'{file_name}.html'


#-------------------------------------------------------------------


@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_IndexRack_single_one_term(app):
    # sort
    testcase01 = {'doc1': [ ('single','sphinx','id-111','',None), ],
                  'doc2': [ ('single','python','id-121','',None), ], }
    bld = builder(testcase01)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert index[0] == ('P', [('python', [[('', 'doc2.html#id-121')], [], None])])
    assert index[1] == ('S', [('sphinx', [[('', 'doc1.html#id-111')], [], None])])

    # sort/same string
    testcase02 = {'doc1': [ ('single','sphinx','id-211','',None), ],
                  'doc2': [ ('single','sphinx','id-221','',None), ], }
    bld = builder(testcase02)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'S'
    assert index[0][1] == [('sphinx',
                           [[('', 'doc1.html#id-211'),
                             ('', 'doc2.html#id-221')],
                            [], None]), ]

    # sort/main
    testcase03 = {'doc1': [ ('single','sphinx','id-311','main',None), ],
                  'doc2': [ ('single','sphinx','id-321','',None), ], }
    bld = builder(testcase03)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'S'
    assert index[0][1] == [('sphinx',
                           [[('main', 'doc1.html#id-311'),
                             ('', 'doc2.html#id-321')],
                            [], None]), ]

    # sort/main
    testcase04 = {'doc1': [ ('single','sphinx','id-411','',None), ],
                  'doc2': [ ('single','sphinx','id-421','main',None), ], }
    bld = builder(testcase04)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'S'
    assert index[0][1] == [('sphinx',
                           [[('main', 'doc2.html#id-421'),
                             ('', 'doc1.html#id-411')],
                            [], None]), ]

    # sort/main
    testcase05 = {'doc1': [ ('single','sphinx','id-511','main',None), ],
                  'doc2': [ ('single','sphinx','id-521','main',None), ], }
    bld = builder(testcase05)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'S'
    assert index[0][1] == [('sphinx',
                           [[('main', 'doc1.html#id-511'),
                             ('main', 'doc2.html#id-521')],
                            [], None]), ]

    # sort/two sets
    testcase06 = {'doc1': [ ('single','sphinx','id-611','',None), ],
                  'doc2': [ ('single','sphinx','id-621','',None), ],
                  'doc3': [ ('single','python','id-631','',None), ],
                  'doc4': [ ('single','python','id-641','',None), ], }
    bld = builder(testcase06)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python',
                           [[('', 'doc3.html#id-631'),
                             ('', 'doc4.html#id-641')],
                            [], None]), ]
    assert index[1][1] == [('sphinx',
                           [[('', 'doc1.html#id-611'),
                             ('', 'doc2.html#id-621')],
                            [], None]), ]

    # sort/two sets/main
    testcase07 = {'doc1': [ ('single','sphinx','id-711','',None), ],
                  'doc2': [ ('single','sphinx','id-721','main',None), ],
                  'doc3': [ ('single','python','id-731','',None), ],
                  'doc4': [ ('single','python','id-741','main',None), ], }
    bld = builder(testcase07)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python',
                           [[('main', 'doc4.html#id-741'),
                             ('', 'doc3.html#id-731')],
                            [], None]), ]
    assert index[1][1] == [('sphinx',
                           [[('main', 'doc2.html#id-721'),
                             ('', 'doc1.html#id-711')],
                            [], None]), ]


@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_IndexEntry_repr(app):
    main = "3"

    # single/one
    entry = irack.IndexEntry('sphinx', 'single', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='single' " \
                           "main='main' file_name='doc1' target='term-1' index_key='key' " \
                           "<#text: 'sphinx'>>"
    assert entry.astext() == "sphinx"
    units = entry.make_index_units()
    assert repr(units[0]) ==  "<IndexUnit: main='3' file_name='doc1' target='term-1' " \
                              "<#empty><#text: 'sphinx'>>"

    # single/two
    entry = irack.IndexEntry('sphinx; python', 'single', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='single' " \
                          "main='main' file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main='3' file_name='doc1' target='term-1' " \
                            "<#empty><#text: 'sphinx'><Subterm: len=1 <#text: 'python'>>>"

    # pair
    entry = irack.IndexEntry('sphinx; python', 'pair', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='pair' " \
                          "main='main' file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main='3' file_name='doc1' target='term-1' " \
                             "<#empty><#text: 'sphinx'><Subterm: len=1 <#text: 'python'>>>"
    assert repr(units[1]) == "<IndexUnit: main='3' file_name='doc1' target='term-1' " \
                             "<#empty><#text: 'python'><Subterm: len=1 <#text: 'sphinx'>>>"

    # triple
    value = 'docutils; sphinx; python'
    entry = irack.IndexEntry(value, 'triple', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='triple' " \
                          "main='main' file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'docutils'><#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "docutils; sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main='3' file_name='doc1' target='term-1' " \
                             "<#empty><#text: 'docutils'>" \
                             "<Subterm: len=2 <#text: 'sphinx'><#text: 'python'>>>"
    assert repr(units[1]) == "<IndexUnit: main='3' file_name='doc1' target='term-1' " \
                             "<#empty><#text: 'sphinx'>" \
                             "<Subterm: len=2 <#text: 'python'><#text: 'docutils'>>>"
    assert repr(units[2]) == "<IndexUnit: main='3' file_name='doc1' target='term-1' " \
                             "<#empty><#text: 'python'>" \
                             "<Subterm: len=2 <#text: 'docutils'><#text: 'sphinx'>>>"

    # see
    entry = irack.IndexEntry('sphinx; python', 'see', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='see' " \
                          "main='main' file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main='8' file_name='doc1' target='term-1' " \
                             "<#empty><#text: 'sphinx'>" \
                             "<Subterm: len=1 tpl='see %s' <#text: 'python'>>>"

    # seealso
    entry = irack.IndexEntry('sphinx; python', 'seealso', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='seealso' " \
                          "main='main' file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main='9' file_name='doc1' target='term-1' " \
                             "<#empty><#text: 'sphinx'>" \
                             "<Subterm: len=1 tpl='see also %s' <#text: 'python'>>>"

    # other entry type
    value = 'docutils; sphinx; python'
    entry = irack.IndexEntry(value, 'list', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='list' " \
                          "main='main' file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'docutils'><#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "docutils; sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main='3' file_name='doc1' target='term-1' " \
                             "<#empty><#text: 'docutils'>>"

    # exception
    value = 'docutils; sphinx; python'
    entry = irack.IndexEntry(value, 'foobar', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='foobar' " \
                          "main='main' file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'docutils'><#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "docutils; sphinx; python"
    units = entry.make_index_units()
    with pytest.raises(IndexError):
        a = repr(units[0])


@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_IndexUnit_repr(app):
    main = "3"
    repr00 = "<Subterm: len=2 <#text: 'sphinx'><#text: 'python'>>"

    # triple/repr
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    assert repr(pack) == repr00
    assert repr(unit) == "<IndexUnit: main='3' file_name='doc1' target='term-1' " \
                         "<#empty><#text: 'docutils'>" \
                         "<Subterm: len=2 <#text: 'sphinx'><#text: 'python'>>>"

    # triple/repr
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    unit[0] = txtcls(unit['index_key'])
    assert repr(unit) == "<IndexUnit: main='3' file_name='doc1' target='term-1' " \
                         "<#text: 'clsf'><#text: 'docutils'>" \
                         "<Subterm: len=2 <#text: 'sphinx'><#text: 'python'>>>"

    # triple/each attribute
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    assert unit['main'] == main
    assert unit['file_name'] == 'doc1'
    assert unit['target'] == 'term-1'
    assert unit['index_key'] == 'clsf'

    # triple/each object
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    assert repr(unit[0]) == "<#empty>"
    assert repr(unit[1]) == "<#text: 'docutils'>"
    assert repr(unit[2]) == repr00
    assert unit[3] == main
    unit[0] = txtcls(unit['index_key'])
    unit[1] = txtcls(unit[1])
    unit[2] = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    assert repr(unit[0]) == "<#text: 'clsf'>"
    assert repr(unit[1]) == "<#text: 'docutils'>"
    assert repr(unit[2]) == repr00

    # triple/method
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    children = unit.get_children()
    assert children == ['docutils', 'sphinx', 'python']

    # triple/method
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    texts = unit.astexts()
    assert texts == ['docutils', 'sphinx', 'python']
    unit.set_subterm_delimiter()
    text = unit[2].astext()
    assert text == 'sphinx, python'

    # exception
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    with pytest.raises(KeyError):
        a = unit['forbar']

    # exception
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    with pytest.raises(KeyError):
        a = unit[99]

    # exception
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    with pytest.raises(TypeError):
        a = unit[(99,'a')]

    # exception
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    with pytest.raises(KeyError):
        unit[99] = 1

    # exception
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    with pytest.raises(TypeError):
        unit[(99,'a')] = 1


@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_Subterm_repr(app):
    # no text
    pack = irack.Subterm('5')
    assert str(pack) == ''
    assert repr(pack) == '<Subterm: len=0 >'

    # no text/see
    pack = irack.Subterm('8')
    assert str(pack) == ''
    assert repr(pack) == "<Subterm: len=0 tpl='see %s' >"

    # no text/seealso
    pack = irack.Subterm('9')
    assert str(pack) == ''
    assert repr(pack) == "<Subterm: len=0 tpl='see also %s' >"

    # text
    pack = irack.Subterm('5', txtcls('sphinx'))
    assert str(pack) == 'sphinx'
    assert repr(pack) == "<Subterm: len=1 <#text: 'sphinx'>>"

    # text/see
    pack = irack.Subterm('8', txtcls('sphinx'))
    assert str(pack) == 'see sphinx'
    assert repr(pack) == "<Subterm: len=1 tpl='see %s' <#text: 'sphinx'>>"

    pack = irack.Subterm('5', txtcls('sphinx'), txtcls('python'))
    assert str(pack) == 'sphinx python'
    assert repr(pack) == "<Subterm: len=2 <#text: 'sphinx'><#text: 'python'>>"
    pack.set_delimiter(', ')
    assert str(pack) == 'sphinx, python'
    #assert repr(pack) == "<Subterm: len=2 <#text: 'sphinx'><#text: 'python'>>"


@pytest.mark.sphinx('dummy', freshenv=True)
def test_issue9744(app):
    # classifier
    testcase01 = { 
        'doc1': [('single', 'aaa', 'id-111', '', 'clf1'),
                 ('single', 'bbb', 'id-112', '', None), ],
        'doc2': [('single', 'aaa', 'id-121', '', None),
                 ('single', 'bbb', 'id-122', '', 'clf2'), ], }
    bld = builder(testcase01)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert index[0][0] == 'clf1'
    assert index[0][1] == [('aaa', [[('', 'doc1.html#id-111'), ('', 'doc2.html#id-121')],
                                    [], 'clf1']), ]
    assert index[1][0] == 'clf2'
    assert index[1][1] == [('bbb', [[('', 'doc1.html#id-112'), ('', 'doc2.html#id-122')],
                                    [], None]), ]

    # see/seealso
    testcase02 = {
        'doc1': [('see','hogehoge; foo','id-211','main',None),
                 ('seealso','hogehoge; bar','id-212','main',None), ], }
    bld = builder(testcase02)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert index[0][0] == 'H'
    assert index[0][1] == [('hogehoge', [[],
                                         [('see also bar', []), ('see foo', [])],
                                         None]), ]

    # function
    testcase03 = {
        'doc1': [('single','func1() (aaa module)','id-311','',None),
                 ('single','func1() (bbb module)','id-312','',None),
                 ('single','func1() (ccc module)','id-313','',None), ], }
    bld = builder(testcase03)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert index[0][0] == 'F'
    assert index[0][1] == [('func1()',
                           [[],
                            [('(aaa module)', [('', 'doc1.html#id-311')]),
                             ('(bbb module)', [('', 'doc1.html#id-312')]),
                             ('(ccc module)', [('', 'doc1.html#id-313')]), ],
                            None], ), ]

    # function with 'main'
    testcase04 = {
        'doc1': [('single','func1() (aaa module)','id-411','',None),
                 ('single','func1() (bbb module)','id-412','',None),
                 ('single','func1() (ccc module)','id-413','main',None), ], }
    bld = builder(testcase04)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert index[0][0] == 'F'
    assert index[0][1] == [('func1()',
                            [[],
                             [('(aaa module)', [('', 'doc1.html#id-411')]),
                              ('(bbb module)', [('', 'doc1.html#id-412')]),
                              ('(ccc module)', [('main', 'doc1.html#id-413')]), ],
                             None], ), ]
