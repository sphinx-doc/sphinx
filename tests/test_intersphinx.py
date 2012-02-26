# -*- coding: utf-8 -*-
"""
    test_intersphinx
    ~~~~~~~~~~~~~~~~

    Test the intersphinx extension.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import zlib
import posixpath
try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO

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
'''.encode('utf-8')

inventory_v2 = '''\
# Sphinx inventory version 2
# Project: foo
# Version: 2.0
# The remainder of this file is compressed with zlib.
'''.encode('utf-8') + zlib.compress('''\
module1 py:module 0 foo.html#module-module1 Long Module desc
module2 py:module 0 foo.html#module-$ -
module1.func py:function 1 sub/foo.html#$ -
CFunc c:function 2 cfunc.html#CFunc -
a term std:term -1 glossary.html#term-a-term -
'''.encode('utf-8'))


def test_read_inventory_v1():
    f = BytesIO(inventory_v1)
    f.readline()
    invdata = read_inventory_v1(f, '/util', posixpath.join)
    assert invdata['py:module']['module'] == \
           ('foo', '1.0', '/util/foo.html#module-module', '-')
    assert invdata['py:class']['module.cls'] == \
           ('foo', '1.0', '/util/foo.html#module.cls', '-')


def test_read_inventory_v2():
    f = BytesIO(inventory_v2)
    f.readline()
    invdata1 = read_inventory_v2(f, '/util', posixpath.join)

    # try again with a small buffer size to test the chunking algorithm
    f = BytesIO(inventory_v2)
    f.readline()
    invdata2 = read_inventory_v2(f, '/util', posixpath.join, bufsize=5)

    assert invdata1 == invdata2

    assert len(invdata1['py:module']) == 2
    assert invdata1['py:module']['module1'] == \
           ('foo', '2.0', '/util/foo.html#module-module1', 'Long Module desc')
    assert invdata1['py:module']['module2'] == \
           ('foo', '2.0', '/util/foo.html#module-module2', '-')
    assert invdata1['py:function']['module1.func'][2] == \
           '/util/sub/foo.html#module1.func'
    assert invdata1['c:function']['CFunc'][2] == '/util/cfunc.html#CFunc'
    assert invdata1['std:term']['a term'][2] == \
           '/util/glossary.html#term-a-term'


@with_app(confoverrides={'extensions': 'sphinx.ext.intersphinx'})
@with_tempdir
def test_missing_reference(tempdir, app):
    inv_file = tempdir / 'inventory'
    write_file(inv_file, inventory_v2)
    app.config.intersphinx_mapping = {
        'http://docs.python.org/': inv_file,
        'py3k': ('http://docs.python.org/py3k/', inv_file),
    }
    app.config.intersphinx_cache_limit = 0

    # load the inventory and check if it's done correctly
    load_mappings(app)
    inv = app.env.intersphinx_inventory

    assert inv['py:module']['module2'] == \
           ('foo', '2.0', 'http://docs.python.org/foo.html#module-module2', '-')

    # create fake nodes and check referencing

    def fake_node(domain, type, target, content, **attrs):
        contnode = nodes.emphasis(content, content)
        node = addnodes.pending_xref('')
        node['reftarget'] = target
        node['reftype'] = type
        node['refdomain'] = domain
        node.attributes.update(attrs)
        node += contnode
        return node, contnode

    def reference_check(*args, **kwds):
        node, contnode = fake_node(*args, **kwds)
        return missing_reference(app, app.env, node, contnode)

    # check resolution when a target is found
    rn = reference_check('py', 'func', 'module1.func', 'foo')
    assert isinstance(rn, nodes.reference)
    assert rn['refuri'] == 'http://docs.python.org/sub/foo.html#module1.func'
    assert rn['reftitle'] == '(in foo v2.0)'
    assert rn[0].astext() == 'foo'

    # create unresolvable nodes and check None return value
    assert reference_check('py', 'foo', 'module1.func', 'foo') is None
    assert reference_check('py', 'func', 'foo', 'foo') is None
    assert reference_check('py', 'func', 'foo', 'foo') is None

    # check handling of prefixes

    # prefix given, target found: prefix is stripped
    rn = reference_check('py', 'mod', 'py3k:module2', 'py3k:module2')
    assert rn[0].astext() == 'module2'

    # prefix given, but not in title: nothing stripped
    rn = reference_check('py', 'mod', 'py3k:module2', 'module2')
    assert rn[0].astext() == 'module2'

    # prefix given, but explicit: nothing stripped
    rn = reference_check('py', 'mod', 'py3k:module2', 'py3k:module2',
                         refexplicit=True)
    assert rn[0].astext() == 'py3k:module2'

    # prefix given, target not found and nonexplicit title: prefix is stripped
    node, contnode = fake_node('py', 'mod', 'py3k:unknown', 'py3k:unknown',
                               refexplicit=False)
    rn = missing_reference(app, app.env, node, contnode)
    assert rn is None
    assert contnode[0].astext() == 'unknown'

    # prefix given, target not found and explicit title: nothing is changed
    node, contnode = fake_node('py', 'mod', 'py3k:unknown', 'py3k:unknown',
                               refexplicit=True)
    rn = missing_reference(app, app.env, node, contnode)
    assert rn is None
    assert contnode[0].astext() == 'py3k:unknown'


@with_app(confoverrides={'extensions': 'sphinx.ext.intersphinx'})
@with_tempdir
def test_load_mappings_warnings(tempdir, app):
    """
    load_mappings issues a warning if new-style mapping
    identifiers are not alphanumeric
    """
    inv_file = tempdir / 'inventory'
    write_file(inv_file, inventory_v2)
    app.config.intersphinx_mapping = {
        'http://docs.python.org/': inv_file,
        'py3k': ('http://docs.python.org/py3k/', inv_file),
        'repoze.workflow': ('http://docs.repoze.org/workflow/', inv_file),
        'django-taggit': ('http://django-taggit.readthedocs.org/en/latest/',
                          inv_file)
    }

    app.config.intersphinx_cache_limit = 0
    # load the inventory and check if it's done correctly
    load_mappings(app)
    assert len(app._warning.content) == 2


