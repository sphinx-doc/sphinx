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
def test_class_IndexRack_function_catalog(app):
    # one function
    testcase01 = {'doc1': [ ('single','func1() (aaa module)','id-111','',None), ] }
    bld = builder(testcase01)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'F'
    assert index[0][1] == [('func1() (aaa module)', [[('', 'doc1.html#id-111')],
                                                     [], None]), ]

    # two functions
    testcase02 = {'doc1': [ ('single','func1() (doc1 module)','id-211','',None),],
                  'doc2': [ ('single','func1() (doc2 module)','id-221','',None),], }
    bld = builder(testcase02)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'F'
    assert index[0][1] == [('func1()', [[],
                                        [('(doc1 module)', [('', 'doc1.html#id-211')]),
                                         ('(doc2 module)', [('', 'doc2.html#id-221')])],
                                        None]), ]

    # two functions/module name
    testcase03 = {'doc1': [ ('single','func1() (bbbb module)','id-311','',None),],
                  'doc2': [ ('single','func1() (aaaa module)','id-321','',None),], }
    bld = builder(testcase03)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'F'
    assert index[0][1] == [('func1()', [[],
                                        [('(aaaa module)', [('', 'doc2.html#id-321')]),
                                         ('(bbbb module)', [('', 'doc1.html#id-311')])],
                                        None])]

    # two sets of function
    testcase04 = {'doc1': [ ('single','func1() (doc1 module)','id-411','',None),],
                  'doc2': [ ('single','func2() (doc2 module)','id-421','',None),],
                  'doc3': [ ('single','func1() (doc3 module)','id-431','',None),],
                  'doc4': [ ('single','func2() (odc4 module)','id-441','',None),], }
    bld = builder(testcase04)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 2
    assert index[0][0] == 'F'
    assert index[0][1] == [('func1()', [[],
                                        [('(doc1 module)', [('', 'doc1.html#id-411')]),
                                         ('(doc3 module)', [('', 'doc3.html#id-431')])],
                                        None]),
                           ('func2()', [[],
                                        [('(doc2 module)', [('', 'doc2.html#id-421')]),
                                         ('(odc4 module)', [('', 'doc4.html#id-441')])],
                                        None])]

    # two sets of function/module name
    testcase05 = {'doc1': [ ('single','func1() (bbbb module)','id-511','',None),],
                  'doc2': [ ('single','func2() (bbbb module)','id-521','',None),],
                  'doc3': [ ('single','func1() (aaaa module)','id-531','',None),],
                  'doc4': [ ('single','func2() (aaaa module)','id-541','',None),], }
    bld = builder(testcase05)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 2
    assert index[0][0] == 'F'
    assert index[0][1] == [('func1()', [[],
                                        [('(aaaa module)', [('', 'doc3.html#id-531')]),
                                         ('(bbbb module)', [('', 'doc1.html#id-511')])],
                                        None]),
                           ('func2()', [[],
                                        [('(aaaa module)', [('', 'doc4.html#id-541')]),
                                         ('(bbbb module)', [('', 'doc2.html#id-521')])],
                                        None])]

    # mixing
    testcase06 = {'doc1': [ ('single','func1()','id-611','',None),],
                  'doc2': [ ('single','func1() (doc2 module)','id-621','',None),],
                  'doc3': [ ('single','func1() (doc3 module)','id-631','',None),],
                  'doc4': [ ('single','func1()','id-641','',None),], }
    bld = builder(testcase06)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'F'
    assert index[0][1] == [('func1()', [[('', 'doc1.html#id-611'),
                                         ('', 'doc4.html#id-641')],
                                        [('(doc2 module)', [('', 'doc2.html#id-621')]),
                                         ('(doc3 module)', [('', 'doc3.html#id-631')])],
                                        None])]

    # mixing/main
    testcase07 = {'doc1': [ ('single','func1()','id-711','',None),],
                  'doc2': [ ('single','func1() (doc2 module)','id-721','',None),],
                  'doc3': [ ('single','func1() (doc3 module)','id-731','',None),],
                  'doc4': [ ('single','func1()','id-741','main',None),], }
    bld = builder(testcase07)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'F'
    assert index[0][1] == [('func1()', [[('main', 'doc4.html#id-741'),
                                         ('', 'doc1.html#id-711')],
                                        [('(doc2 module)', [('', 'doc2.html#id-721')]),
                                         ('(doc3 module)', [('', 'doc3.html#id-731')])],
                                         None])]

    # subterm
    testcase08 = {'doc1': [ ('single','func1() (doc1 module); sphinx','id-811','',None),],
                  'doc2': [ ('single','func2() (doc2 module); sphinx','id-821','',None),],
                  'doc3': [ ('single','func1() (doc3 module); python','id-831','',None),],
                  'doc4': [ ('single','func2() (odc4 module); python','id-841','',None),], }
    bld = builder(testcase08)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 2
    assert index[0][0] == 'F'
    assert index[0][1] == [('func1()', [[],
                                        [('(doc1 module), sphinx',
                                            [('', 'doc1.html#id-811')]),
                                         ('(doc3 module), python',
                                            [('', 'doc3.html#id-831')])],
                                        None]),
                           ('func2()', [[],
                                        [('(doc2 module), sphinx',
                                            [('', 'doc2.html#id-821')]),
                                         ('(odc4 module), python',
                                            [('', 'doc4.html#id-841')])],
                                        None])]


@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_IndexRack_classifier_catalog(app):
    # basic/doc1 has classifier.
    testcase01 = {'doc1': [ ('single','sphinx','id-111','','clf'), ],
                  'doc2': [ ('single','sphinx','id-121','',None), ], }
    bld = builder(testcase01)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'clf'
    assert index[0][1] == [('sphinx', [[('', 'doc1.html#id-111'),
                                        ('', 'doc2.html#id-121'), ],
                                       [],
                                       'clf'])]

    # basic/doc2 has classifier.
    testcase02 = {'doc1': [ ('single','sphinx','id-211','',None), ],
                  'doc2': [ ('single','sphinx','id-221','','clf'), ], }
    bld = builder(testcase02)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'clf'
    assert index[0][1] == [('sphinx', [[('', 'doc1.html#id-211'),
                                        ('', 'doc2.html#id-221')],
                                       [], None])]



@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_IndexRack_see_and_seealso(app):
    # see
    testcase01 = {'doc1': [ ('single','python','id-111','',None), ],
                  'doc2': [ ('see','sphinx; python','id-121','',None), ], }
    bld = builder(testcase01)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[('', 'doc1.html#id-111')], [], None])]
    assert index[1][1] == [('sphinx', [[], [('see python', [])], None])]

    # seealso
    testcase02 = {'doc1': [ ('single','python','id-211','',None), ],
                  'doc2': [ ('seealso','sphinx; python','id-221','',None), ], }
    bld = builder(testcase02)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[('', 'doc1.html#id-211')], [], None])]
    assert index[1][1] == [('sphinx', [[], [('see also python', [])], None])]

    # see
    testcase03 = {'doc1': [ ('single','python','id-311','',None), ],
                  'doc2': [ ('single','sphinx; directive','id-321','',None), ],
                  'doc3': [ ('see','sphinx; python','id-331','',None), ],
                  'doc4': [ ('single','sphinx; role','id-341','',None), ], }
    bld = builder(testcase03)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[('', 'doc1.html#id-311')], [], None])]
    assert index[1][1] == [('sphinx', [[],
                                       [('see python', []),
                                        ('directive', [('', 'doc2.html#id-321')]),
                                        ('role', [('', 'doc4.html#id-341')])],
                                       None])]

    # seealso
    testcase04 = {'doc1': [ ('single','python','id-411','',None), ],
                  'doc2': [ ('single','sphinx; directive','id-421','',None), ],
                  'doc3': [ ('seealso','sphinx; python','id-431','',None), ],
                  'doc4': [ ('single','sphinx; role','id-441','',None), ], }
    bld = builder(testcase04)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[('', 'doc1.html#id-411')], [], None])]
    assert index[1][1] == [('sphinx', [[],
                                       [('see also python', []),
                                        ('directive', [('', 'doc2.html#id-421')]),
                                        ('role', [('', 'doc4.html#id-441')])],
                                      None])]


@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_IndexRack_triple(app):
    # basic
    testcase01 = {'doc1': [ ('triple','bash; perl; tcsh','id-111','',None), ], }
    bld = builder(testcase01)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 3
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert len(index[2][1]) == 1
    assert index[0][0] == 'B'
    assert index[1][0] == 'P'
    assert index[2][0] == 'T'
    assert index[0][1] == [('bash', [[],
                                     [('perl tcsh', [('', 'doc1.html#id-111'), ]), ],
                                     None]), ]
    assert index[1][1] == [('perl', [[],
                                     [('tcsh, bash', [('', 'doc1.html#id-111'), ]), ],
                                     None]), ]
    assert index[2][1] == [('tcsh', [[],
                                     [('bash perl', [('', 'doc1.html#id-111'), ]), ],
                                     None]), ]

    # one triple and single(two terms)
    testcase02 = {'doc1': [ ('triple','bash; perl; tcsh','id-211','',None), ],
                  'doc2': [ ('single','bash; perl','id-221','',None), ],
                  'doc3': [ ('single','perl; tcsh','id-231','',None), ],
                  'doc4': [ ('single','tcsh; bash','id-241','',None), ], }
    bld = builder(testcase02)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 3
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert len(index[2][1]) == 1
    assert index[0][0] == 'B'
    assert index[1][0] == 'P'
    assert index[2][0] == 'T'
    assert index[0][1] == [('bash', [[],
                                     [('perl', [('', 'doc2.html#id-221'), ]),
                                      ('perl tcsh', [('', 'doc1.html#id-211'), ]), ],
                                     None])]
    assert index[1][1] == [('perl', [[],
                                     [('tcsh', [('', 'doc3.html#id-231')]),
                                      ('tcsh, bash', [('', 'doc1.html#id-211'), ]), ],
                                     None])]
    assert index[2][1] == [('tcsh', [[],
                                     [('bash', [('', 'doc4.html#id-241'), ]),
                                      ('bash perl', [('', 'doc1.html#id-211')])],
                                     None]), ]

    # one triple and single(two terms)
    testcase03 = {'doc1': [ ('triple','bash; perl; tcsh','id-311','',None), ],
                  'doc2': [ ('single','bash; perl tcsh','id-321','',None), ],
                  'doc3': [ ('single','perl; tcsh, bash','id-331','',None), ],
                  'doc4': [ ('single','tcsh; bash perl','id-341','',None), ], }
    bld = builder(testcase03)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 3
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert len(index[2][1]) == 1
    assert index[0][0] == 'B'
    assert index[1][0] == 'P'
    assert index[2][0] == 'T'
    assert index[0][1] == [('bash', [[],
                                     [('perl tcsh', [('', 'doc1.html#id-311'),
                                                     ('', 'doc2.html#id-321'), ]), ],
                                     None])]
    assert index[1][1] == [('perl', [[],
                                     [('tcsh, bash', [('', 'doc1.html#id-311'),
                                                      ('', 'doc3.html#id-331'), ]), ],
                                     None])]
    assert index[2][1] == [('tcsh', [[],
                                     [('bash perl', [('', 'doc1.html#id-311'),
                                                     ('', 'doc4.html#id-341'), ]), ],
                                     None])]

    # one triple and single(two terms)/main
    testcase04 = {'doc1': [ ('triple','bash; perl; tcsh','id-411','',None), ],
                  'doc2': [ ('single','bash; perl tcsh','id-421','main',None), ],
                  'doc3': [ ('single','perl; tcsh, bash','id-431','main',None), ],
                  'doc4': [ ('single','tcsh; bash perl','id-441','main',None), ], }
    bld = builder(testcase04)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 3
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert len(index[2][1]) == 1
    assert index[0][0] == 'B'
    assert index[1][0] == 'P'
    assert index[2][0] == 'T'
    assert index[0][1] == [('bash', [[],
                                     [('perl tcsh', [('main', 'doc2.html#id-421'),
                                                     ('', 'doc1.html#id-411'), ]), ],
                                     None])]
    assert index[1][1] == [('perl', [[],
                                     [('tcsh, bash', [('main', 'doc3.html#id-431'),
                                                      ('', 'doc1.html#id-411'), ]), ],
                                     None]), ]
    assert index[2][1] == [('tcsh', [[],
                                     [('bash perl', [('main', 'doc4.html#id-441'),
                                                     ('', 'doc1.html#id-411'), ]), ],
                                     None])]

    # one triple and single(two terms)/main
    testcase05 = {'doc1': [ ('single','bash; perl tcsh','id-511','',None), ],
                  'doc2': [ ('single','perl; tcsh, bash','id-521','',None), ],
                  'doc3': [ ('single','tcsh; bash perl','id-531','',None), ],
                  'doc4': [ ('triple','bash; perl; tcsh','id-541','main',None), ], }
    bld = builder(testcase05)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 3
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert len(index[2][1]) == 1
    assert index[0][0] == 'B'
    assert index[1][0] == 'P'
    assert index[2][0] == 'T'
    assert index[0][1] == [('bash', [[],
                                     [('perl tcsh', [('main', 'doc4.html#id-541'),
                                                     ('', 'doc1.html#id-511'), ]), ],
                                     None]), ]
    assert index[1][1] == [('perl', [[],
                                     [('tcsh, bash', [('main', 'doc4.html#id-541'),
                                                      ('', 'doc2.html#id-521'), ]), ],
                                     None]), ]
    assert index[2][1] == [('tcsh', [[],
                                     [('bash perl', [('main', 'doc4.html#id-541'),
                                                     ('', 'doc3.html#id-531'), ]), ],
                                     None]), ]


@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_IndexRack_pair(app):
    # basic
    testcase01 = { 'doc1': [ ('pair','sphinx; reST','id-111','',None), ], }
    bld = builder(testcase01)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'R'
    assert index[1][0] == 'S'
    assert index[0][1] == [('reST',
                           [[],
                            [('sphinx', [('', 'doc1.html#id-111')]), ],
                            None]), ]
    assert index[1][1] == [('sphinx',
                           [[],
                            [('reST', [('', 'doc1.html#id-111')]), ],
                            None]), ]

    # two sets. one is cicle.
    testcase02 = {'doc1': [ ('pair','sphinx; reST','id-211','',None), ],
                  'doc2': [ ('pair','python; ruby','id-221','',None), ],
                  'doc3': [ ('pair','ruby; php',   'id-231','',None), ],
                  'doc4': [ ('pair','php; python', 'id-241','',None), ], }
    bld = builder(testcase02)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 3
    assert len(index[0][1]) == 2
    assert len(index[1][1]) == 2
    assert len(index[2][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'R'
    assert index[2][0] == 'S'
    assert index[0][1] == [('php', [[],
                                    [('python', [('', 'doc4.html#id-241'), ]),
                                     ('ruby', [('', 'doc3.html#id-231')], )],
                                    None]),
                           ('python',
                                   [[],
                                    [('php', [('', 'doc4.html#id-241')]),
                                     ('ruby', [('', 'doc2.html#id-221'), ]), ],
                                    None]), ]
    assert index[1][1] == [('reST', [[],
                                     [('sphinx', [('', 'doc1.html#id-211'), ]), ],
                                     None]),
                           ('ruby', [[],
                                     [('php', [('', 'doc3.html#id-231')]),
                                      ('python', [('', 'doc2.html#id-221'), ]), ],
                                     None]), ]
    assert index[2][1] == [('sphinx',
                                    [[],
                                     [('reST', [('', 'doc1.html#id-211')])],
                                     None]), ]

    # pair and single(one term)
    testcase03 = {'doc1': [ ('pair','sphinx; python','id-311','',None), ],
                  'doc2': [ ('single','sphinx','id-321','',None), ],
                  'doc3': [ ('single','python','id-331','',None), ], }
    bld = builder(testcase03)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[('', 'doc3.html#id-331'), ],
                                       [('sphinx', [('', 'doc1.html#id-311'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[('', 'doc2.html#id-321'), ],
                                       [('python', [('', 'doc1.html#id-311'), ]), ],
                                       None]), ]

    # pair and single(two terms)
    testcase04 = {'doc1': [ ('pair','sphinx; python','id-411','',None), ],
                  'doc2': [ ('single','sphinx; python','id-421','',None), ],
                  'doc3': [ ('single','python; sphinx','id-431','',None), ], }
    bld = builder(testcase04)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('sphinx', [('', 'doc1.html#id-411'),
                                                    ('', 'doc3.html#id-431')]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('python', [('', 'doc1.html#id-411'),
                                                    ('', 'doc2.html#id-421')]), ],
                                       None])]

    # pair and single(two terms)/main
    testcase05 = {'doc1': [ ('pair','sphinx; python','id-511','',None), ],
                  'doc2': [ ('single','sphinx; python','id-521','main',None), ],
                  'doc3': [ ('single','python; sphinx','id-531','main',None), ], }
    bld = builder(testcase05)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('sphinx', [('main', 'doc3.html#id-531'),
                                                    ('', 'doc1.html#id-511'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('python', [('main', 'doc2.html#id-521'),
                                                    ('', 'doc1.html#id-511'), ]), ],
                                       None]), ]

    # pair and single(two terms)/file name
    testcase06 = {'doc3': [ ('pair','sphinx; python','id-611','',None), ],
                  'doc1': [ ('single','sphinx; python','id-621','',None), ],
                  'doc2': [ ('single','python; sphinx','id-631','',None), ], }
    bld = builder(testcase06)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('sphinx', [('', 'doc2.html#id-631'),
                                                    ('', 'doc3.html#id-611'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('python', [('', 'doc1.html#id-621'),
                                                    ('', 'doc3.html#id-611'), ]), ],
                                       None])]

    # pair and single(two terms)/main -> file name
    testcase07 = {'doc3': [ ('pair','sphinx; python','id-711','main',None), ],
                  'doc1': [ ('single','sphinx; python','id-721','',None), ],
                  'doc2': [ ('single','python; sphinx','id-731','',None), ], }
    bld = builder(testcase07)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('sphinx', [('main', 'doc3.html#id-711'),
                                                    ('', 'doc2.html#id-731'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('python', [('main', 'doc3.html#id-711'),
                                                    ('', 'doc1.html#id-721'), ]), ],
                                       None])]

@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_IndexRack_single_mixing(app):
    # same term
    testcase01 = {'doc1': [ ('single','sphinx; reST','id-711','',None), ],
                  'doc2': [ ('single','python; ruby','id-721','',None), ],
                  'doc3': [ ('single','sphinx','id-731','',None), ],
                  'doc4': [ ('single','python','id-741','',None), ],
                  'doc5': [ ('single','sphinx','id-751','',None), ],
                  'doc6': [ ('single','python','id-761','',None), ], }
    bld = builder(testcase01)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[('', 'doc4.html#id-741'),
                                        ('', 'doc6.html#id-761'), ],
                                       [('ruby', [('', 'doc2.html#id-721'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[('', 'doc3.html#id-731'),
                                        ('', 'doc5.html#id-751'), ],
                                       [('reST', [('', 'doc1.html#id-711'), ]), ],
                                       None]), ]

    # same term/main
    testcase02 = {'doc1': [ ('single','sphinx; reST','id-811','',None), ],
                  'doc2': [ ('single','python; ruby','id-821','',None), ],
                  'doc3': [ ('single','sphinx','id-831','',None), ],
                  'doc4': [ ('single','python','id-841','',None), ],
                  'doc5': [ ('single','sphinx','id-851','main',None), ],
                  'doc6': [ ('single','python','id-861','main',None), ], }
    bld = builder(testcase02)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[('main', 'doc6.html#id-861'),
                                        ('', 'doc4.html#id-841'), ],
                                       [('ruby', [('', 'doc2.html#id-821')])],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[('main', 'doc5.html#id-851'),
                                        ('', 'doc3.html#id-831'), ],
                                       [('reST', [('', 'doc1.html#id-811')]), ],
                                       None]), ]

    # same term/file name
    testcase03 = {'doc1': [ ('single','sphinx; reST','id-911','',None), ],
                  'doc2': [ ('single','python; ruby','id-921','',None), ],
                  'doc5': [ ('single','sphinx','id-931','',None), ],
                  'doc6': [ ('single','python','id-941','',None), ],
                  'doc3': [ ('single','sphinx','id-951','',None), ],
                  'doc4': [ ('single','python','id-961','',None), ], }
    bld = builder(testcase03)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[('', 'doc4.html#id-961'),
                                        ('', 'doc6.html#id-941'), ],
                                       [('ruby', [('', 'doc2.html#id-921'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[('', 'doc3.html#id-951'),
                                        ('', 'doc5.html#id-931'), ],
                                       [('reST', [('', 'doc1.html#id-911')]), ],
                                       None])]


@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_IndexRack_single_two_terms(app):
    #basic
    testcase01 = {'doc1': [ ('single','sphinx; bash','id-111','',None), ],
                  'doc2': [ ('single','python; php','id-121','',None), ], }
    bld = builder(testcase01)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('php', [('', 'doc2.html#id-121')]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('bash', [('', 'doc1.html#id-111')]), ],
                                       None]), ]

    #basic
    testcase02 = {'doc1': [ ('single','sphinx; tcsh','id-211','',None), ],
                  'doc2': [ ('single','python; ruby','id-221','',None), ],
                  'doc3': [ ('single','sphinx; bash','id-231','',None), ],
                  'doc4': [ ('single','python; perl','id-241','',None), ], }
    bld = builder(testcase02)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('perl', [('', 'doc4.html#id-241')]),
                                        ('ruby', [('', 'doc2.html#id-221')]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('bash', [('', 'doc3.html#id-231')]),
                                        ('tcsh', [('', 'doc1.html#id-211')]), ],
                                       None]), ]

    # same subterm
    testcase03 = {'doc1': [ ('single','sphinx; sphinx','id-311','',None), ],
                  'doc2': [ ('single','python; python','id-321','',None), ],
                  'doc3': [ ('single','sphinx; sphinx','id-331','',None), ],
                  'doc4': [ ('single','python; python','id-341','',None), ], }
    bld = builder(testcase03)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('python', [('', 'doc2.html#id-321'),
                                                    ('', 'doc4.html#id-341'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('sphinx', [('', 'doc1.html#id-311'),
                                                    ('', 'doc3.html#id-331'), ]), ],
                                       None])]

    # same subterm/main
    testcase04 = {'doc1': [ ('single','sphinx; sphinx','id-411','',None), ],
                  'doc2': [ ('single','python; python','id-421','',None), ],
                  'doc3': [ ('single','sphinx; sphinx','id-431','main',None), ],
                  'doc4': [ ('single','python; python','id-441','main',None), ], }
    bld = builder(testcase04)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('python', [('main', 'doc4.html#id-441'),
                                                    ('', 'doc2.html#id-421'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('sphinx', [('main', 'doc3.html#id-431'),
                                                    ('', 'doc1.html#id-411'), ])],
                                       None]), ]

    # same subterm/main/file name
    testcase05 = {'doc1': [ ('single','sphinx; sphinx','id-511','',None), ],
                  'doc2': [ ('single','python; python','id-521','',None), ],
                  'doc5': [ ('single','sphinx; sphinx','id-531','main',None), ],
                  'doc6': [ ('single','python; python','id-541','main',None), ],
                  'doc3': [ ('single','sphinx; sphinx','id-551','main',None), ],
                  'doc4': [ ('single','python; python','id-561','main',None), ], }
    bld = builder(testcase05)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('python', [('main', 'doc4.html#id-561'),
                                                    ('main', 'doc6.html#id-541'),
                                                    ('', 'doc2.html#id-521'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('sphinx', [('main', 'doc3.html#id-551'),
                                                    ('main', 'doc5.html#id-531'),
                                                    ('', 'doc1.html#id-511'), ]), ],
                                       None]), ]

    # same subterm/file name
    testcase06 = {'doc3': [ ('single','sphinx; reST','id-611','',None), ],
                  'doc4': [ ('single','python; ruby','id-621','',None), ],
                  'doc1': [ ('single','sphinx; reST','id-631','',None), ],
                  'doc2': [ ('single','python; ruby','id-641','',None), ], }
    bld = builder(testcase06)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('ruby', [('', 'doc2.html#id-641'),
                                                  ('', 'doc4.html#id-621'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('reST', [('', 'doc1.html#id-631'),
                                                  ('', 'doc3.html#id-611'), ]), ],
                                       None]), ]

    # same subterm/file name
    testcase07 = {'doc1': [ ('single','sphinx; ruby','id-711','',None), ],
                  'doc2': [ ('single','python; ruby','id-721','',None), ],
                  'doc3': [ ('single','sphinx; reST','id-731','',None), ],
                  'doc4': [ ('single','python; reST','id-741','',None), ], }
    bld = builder(testcase07)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 2
    assert len(index[0][1]) == 1
    assert len(index[1][1]) == 1
    assert index[0][0] == 'P'
    assert index[1][0] == 'S'
    assert index[0][1] == [('python', [[],
                                       [('reST', [('', 'doc4.html#id-741'), ]),
                                        ('ruby', [('', 'doc2.html#id-721'), ]), ],
                                       None]), ]
    assert index[1][1] == [('sphinx', [[],
                                       [('reST', [('', 'doc3.html#id-731'), ]),
                                        ('ruby', [('', 'doc1.html#id-711'), ]), ],
                                       None]), ]

    #same term, same subterm.
    testcase08 = {'doc1': [ ('single','sphinx; python','id-811','',None), ],
                  'doc2': [ ('single','sphinx; python','id-821','',None), ], }
    bld = builder(testcase08)
    index = irack.IndexRack(bld).create_index()
    assert len(index) == 1
    assert len(index[0][1]) == 1
    assert index[0][0] == 'S'
    assert index[0][1] == [('sphinx', [[],
                                       [('python', [('', 'doc1.html#id-811'),
                                                    ('', 'doc2.html#id-821'), ]), ],
                                       None]), ]


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
    assert index[0][1] == [('sphinx', [[('', 'doc1.html#id-211'),
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
    assert index[0][1] == [('sphinx', [[('main', 'doc1.html#id-311'),
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
    assert index[0][1] == [('sphinx', [[('main', 'doc2.html#id-421'),
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
    assert index[0][1] == [('sphinx', [[('main', 'doc1.html#id-511'),
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
    assert index[0][1] == [('python', [[('', 'doc3.html#id-631'),
                                        ('', 'doc4.html#id-641')],
                                       [], None]), ]
    assert index[1][1] == [('sphinx', [[('', 'doc1.html#id-611'),
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
    assert index[0][1] == [('python', [[('main', 'doc4.html#id-741'),
                                        ('', 'doc3.html#id-731')],
                                       [], None]), ]
    assert index[1][1] == [('sphinx', [[('main', 'doc2.html#id-721'),
                                        ('', 'doc1.html#id-711')],
                                       [], None]), ]


@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_IndexEntry_repr(app):
    main = "3"

    # single/one
    entry = irack.IndexEntry('sphinx', 'single', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='single' " \
                           "main file_name='doc1' target='term-1' index_key='key' " \
                           "<#text: 'sphinx'>>"
    assert entry.astext() == "sphinx"
    units = entry.make_index_units()
    assert repr(units[0]) ==  "<IndexUnit: main file_name='doc1' target='term-1' " \
                              "<#text: ''><#text: 'sphinx'>>"

    # single/two
    entry = irack.IndexEntry('sphinx; python', 'single', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='single' " \
                          "main file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main file_name='doc1' target='term-1' " \
                            "<#text: ''><#text: 'sphinx'><Subterm: len=1 <#text: 'python'>>>"

    # pair
    entry = irack.IndexEntry('sphinx; python', 'pair', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='pair' " \
                          "main file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main file_name='doc1' target='term-1' " \
                             "<#text: ''><#text: 'sphinx'><Subterm: len=1 <#text: 'python'>>>"
    assert repr(units[1]) == "<IndexUnit: main file_name='doc1' target='term-1' " \
                             "<#text: ''><#text: 'python'><Subterm: len=1 <#text: 'sphinx'>>>"

    # triple
    value = 'docutils; sphinx; python'
    entry = irack.IndexEntry(value, 'triple', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='triple' " \
                          "main file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'docutils'><#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "docutils; sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main file_name='doc1' target='term-1' " \
                             "<#text: ''><#text: 'docutils'>" \
                             "<Subterm: len=2 <#text: 'sphinx'><#text: 'python'>>>"
    assert repr(units[1]) == "<IndexUnit: main file_name='doc1' target='term-1' " \
                             "<#text: ''><#text: 'sphinx'>" \
                             "<Subterm: len=2 delimiter=', ' <#text: 'python'><#text: 'docutils'>>>"
    assert repr(units[2]) == "<IndexUnit: main file_name='doc1' target='term-1' " \
                             "<#text: ''><#text: 'python'>" \
                             "<Subterm: len=2 <#text: 'docutils'><#text: 'sphinx'>>>"

    # see
    entry = irack.IndexEntry('sphinx; python', 'see', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='see' " \
                          "main file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main file_name='doc1' target='term-1' " \
                             "<#text: ''><#text: 'sphinx'>" \
                             "<Subterm: len=1 tpl='see %s' <#text: 'python'>>>"

    # seealso
    entry = irack.IndexEntry('sphinx; python', 'seealso', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='seealso' " \
                          "main file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main file_name='doc1' target='term-1' " \
                             "<#text: ''><#text: 'sphinx'>" \
                             "<Subterm: len=1 tpl='see also %s' <#text: 'python'>>>"

    # other entry type
    value = 'docutils; sphinx; python'
    entry = irack.IndexEntry(value, 'list', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='list' " \
                          "main file_name='doc1' target='term-1' index_key='key' " \
                          "<#text: 'docutils'><#text: 'sphinx'><#text: 'python'>>"
    assert entry.astext() == "docutils; sphinx; python"
    units = entry.make_index_units()
    assert repr(units[0]) == "<IndexUnit: main file_name='doc1' target='term-1' " \
                             "<#text: ''><#text: 'docutils'>>"

    # exception
    value = 'docutils; sphinx; python'
    entry = irack.IndexEntry(value, 'foobar', 'doc1', 'term-1', 'main', 'key')
    assert repr(entry) == "<IndexEntry: entry_type='foobar' " \
                          "main file_name='doc1' target='term-1' index_key='key' " \
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
    assert repr(unit) == "<IndexUnit: main file_name='doc1' target='term-1' " \
                         "<#text: ''><#text: 'docutils'>" \
                         "<Subterm: len=2 <#text: 'sphinx'><#text: 'python'>>>"

    # triple/repr
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    unit[0] = txtcls(unit['index_key'])
    assert repr(unit) == "<IndexUnit: main file_name='doc1' target='term-1' " \
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
    assert repr(unit[0]) == "<#text: ''>"
    assert repr(unit[1]) == "<#text: 'docutils'>"
    assert repr(unit[2]) == repr00
    assert unit['main'] == main
    unit[0] = txtcls(unit['index_key'])
    unit[1] = txtcls(unit[1])
    unit[2] = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    assert repr(unit[0]) == "<#text: 'clsf'>"
    assert repr(unit[1]) == "<#text: 'docutils'>"
    assert repr(unit[2]) == repr00

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
    with pytest.raises(IndexError):
        a = unit[99]

    # exception
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    with pytest.raises(TypeError):
        a = unit[(99,'a')]

    # exception
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    with pytest.raises(AttributeError):
        unit[99] = 1

    # exception
    pack = irack.Subterm(main, txtcls('sphinx'), txtcls('python'))
    unit = irack.IndexUnit(txtcls('docutils'), pack, '2', main, 'doc1', 'term-1', 'clsf')
    with pytest.raises(TypeError):
        unit[(99,'a')] = 1


@pytest.mark.sphinx('dummy', freshenv=True)
def test_class_Subterm_repr(app):
    # no text
    pack = irack.Subterm(3)
    assert str(pack) == ''
    assert repr(pack) == '<Subterm: len=0 >'

    # no text/see
    pack = irack.Subterm(1)
    assert str(pack) == ''
    assert repr(pack) == "<Subterm: len=0 tpl='see %s' >"

    # no text/seealso
    pack = irack.Subterm(2)
    assert str(pack) == ''
    assert repr(pack) == "<Subterm: len=0 tpl='see also %s' >"

    # text
    pack = irack.Subterm(3, txtcls('sphinx'))
    assert str(pack) == 'sphinx'
    assert repr(pack) == "<Subterm: len=1 <#text: 'sphinx'>>"

    # text/see
    pack = irack.Subterm(1, txtcls('sphinx'))
    assert str(pack) == 'see sphinx'
    assert repr(pack) == "<Subterm: len=1 tpl='see %s' <#text: 'sphinx'>>"

    pack = irack.Subterm(3, txtcls('sphinx'), txtcls('python'))
    assert str(pack) == 'sphinx python'
    assert repr(pack) == "<Subterm: len=2 <#text: 'sphinx'><#text: 'python'>>"
    pack['delimiter'] = ', '
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
                                         [('see foo', []), ('see also bar', []) ],
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
