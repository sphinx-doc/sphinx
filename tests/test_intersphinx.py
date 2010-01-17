# -*- coding: utf-8 -*-
"""
    test_intersphinx
    ~~~~~~~~~~~~~~~~

    Test the intersphinx extension.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import zlib
import posixpath
from cStringIO import StringIO

from docutils import nodes

from sphinx import addnodes
from sphinx.ext.intersphinx import read_inventory_v1, read_inventory_v2, \
     load_mappings, missing_reference

from util import *


inventory_v1 = '''\
# Sphinx inventory version 1
# Project: foo
# Version: 1.0
module mod foo.html
module.cls class foo.html
'''

inventory_v2 = '''\
# Sphinx inventory version 2
# Project: foo
# Version: 2.0
# The remainder of this file is compressed with zlib.
''' + zlib.compress('''\
module1 py:module 0 foo.html#module-module1
module2 py:module 0 foo.html#module-$
module1.func py:function 1 sub/foo.html#$
CFunc c:function 2 cfunc.html#CFunc
''')


def test_read_inventory_v1():
    f = StringIO(inventory_v1)
    f.readline()
    invdata = read_inventory_v1(f, '/util', posixpath.join)
    assert invdata['py:module']['module'] == \
           ('foo', '1.0', '/util/foo.html#module-module')
    assert invdata['py:class']['module.cls'] == \
           ('foo', '1.0', '/util/foo.html#module.cls')


def test_read_inventory_v2():
    f = StringIO(inventory_v2)
    f.readline()
    invdata1 = read_inventory_v2(f, '/util', posixpath.join)

    # try again with a small buffer size to test the chunking algorithm
    f = StringIO(inventory_v2)
    f.readline()
    invdata2 = read_inventory_v2(f, '/util', posixpath.join, bufsize=5)

    assert invdata1 == invdata2

    assert len(invdata1['py:module']) == 2
    assert invdata1['py:module']['module1'] == \
           ('foo', '2.0', '/util/foo.html#module-module1')
    assert invdata1['py:module']['module2'] == \
           ('foo', '2.0', '/util/foo.html#module-module2')
    assert invdata1['py:function']['module1.func'][2] == \
           '/util/sub/foo.html#module1.func'
    assert invdata1['c:function']['CFunc'][2] == '/util/cfunc.html#CFunc'


@with_app(confoverrides={'extensions': 'sphinx.ext.intersphinx'})
@with_tempdir
def test_missing_reference(tempdir, app):
    inv_file = tempdir / 'inventory'
    write_file(inv_file, inventory_v2)
    app.config.intersphinx_mapping = {'http://docs.python.org/': inv_file}
    app.config.intersphinx_cache_limit = 0

    # load the inventory and check if it's done correctly
    load_mappings(app)
    inv = app.env.intersphinx_inventory

    assert inv['py:module']['module2'] == \
           ('foo', '2.0', 'http://docs.python.org/foo.html#module-module2')

    # create fake nodes and check referencing
    contnode = nodes.emphasis('foo')
    refnode = addnodes.pending_xref('')
    refnode['reftarget'] = 'module1.func'
    refnode['reftype'] = 'func'
    refnode['refdomain'] = 'py'

    rn = missing_reference(app, app.env, refnode, contnode)
    assert isinstance(rn, nodes.reference)
    assert rn['refuri'] == 'http://docs.python.org/sub/foo.html#module1.func'
    assert rn['reftitle'] == '(in foo v2.0)'
    assert rn[0] is contnode

    # create unresolvable nodes and check None return value
    refnode['reftype'] = 'foo'
    assert missing_reference(app, app.env, refnode, contnode) is None

    refnode['reftype'] = 'function'
    refnode['reftarget'] = 'foo.func'
    assert missing_reference(app, app.env, refnode, contnode) is None
