# -*- coding: utf-8 -*-
"""
    test_intersphinx
    ~~~~~~~~~~~~~~~~

    Test the intersphinx extension.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import posixpath
import unittest
import zlib

from six import BytesIO
from docutils import nodes
import mock

from sphinx import addnodes
from sphinx.ext.intersphinx import setup as intersphinx_setup
from sphinx.ext.intersphinx import read_inventory, \
    load_mappings, missing_reference, _strip_basic_auth, _read_from_url, \
    _get_safe_url, fetch_inventory, INVENTORY_FILENAME

from util import with_app, with_tempdir


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
a term including:colon std:term -1 glossary.html#term-a-term-including-colon -
'''.encode('utf-8'))


def test_read_inventory_v1():
    f = BytesIO(inventory_v1)
    invdata = read_inventory(f, '/util', posixpath.join)
    assert invdata['py:module']['module'] == \
        ('foo', '1.0', '/util/foo.html#module-module', '-')
    assert invdata['py:class']['module.cls'] == \
        ('foo', '1.0', '/util/foo.html#module.cls', '-')


def test_read_inventory_v2():
    f = BytesIO(inventory_v2)
    invdata1 = read_inventory(f, '/util', posixpath.join)

    # try again with a small buffer size to test the chunking algorithm
    f = BytesIO(inventory_v2)
    invdata2 = read_inventory(f, '/util', posixpath.join, bufsize=5)

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
    assert invdata1['std:term']['a term including:colon'][2] == \
        '/util/glossary.html#term-a-term-including-colon'


@with_app()
@mock.patch('sphinx.ext.intersphinx.read_inventory')
@mock.patch('sphinx.ext.intersphinx._read_from_url')
def test_fetch_inventory_redirection(app, status, warning, _read_from_url, read_inventory):
    intersphinx_setup(app)
    _read_from_url().readline.return_value = '# Sphinx inventory version 2'.encode('utf-8')

    # same uri and inv, not redirected
    _read_from_url().url = 'http://hostname/' + INVENTORY_FILENAME
    fetch_inventory(app, 'http://hostname/', 'http://hostname/' + INVENTORY_FILENAME)
    assert 'intersphinx inventory has moved' not in status.getvalue()
    assert read_inventory.call_args[0][1] == 'http://hostname/'

    # same uri and inv, redirected
    status.seek(0)
    status.truncate(0)
    _read_from_url().url = 'http://hostname/new/' + INVENTORY_FILENAME

    fetch_inventory(app, 'http://hostname/', 'http://hostname/' + INVENTORY_FILENAME)
    assert status.getvalue() == ('intersphinx inventory has moved: '
                                 'http://hostname/%s -> http://hostname/new/%s\n' %
                                 (INVENTORY_FILENAME, INVENTORY_FILENAME))
    assert read_inventory.call_args[0][1] == 'http://hostname/new'

    # different uri and inv, not redirected
    status.seek(0)
    status.truncate(0)
    _read_from_url().url = 'http://hostname/new/' + INVENTORY_FILENAME

    fetch_inventory(app, 'http://hostname/', 'http://hostname/new/' + INVENTORY_FILENAME)
    assert 'intersphinx inventory has moved' not in status.getvalue()
    assert read_inventory.call_args[0][1] == 'http://hostname/'

    # different uri and inv, redirected
    status.seek(0)
    status.truncate(0)
    _read_from_url().url = 'http://hostname/other/' + INVENTORY_FILENAME

    fetch_inventory(app, 'http://hostname/', 'http://hostname/new/' + INVENTORY_FILENAME)
    assert status.getvalue() == ('intersphinx inventory has moved: '
                                 'http://hostname/new/%s -> http://hostname/other/%s\n' %
                                 (INVENTORY_FILENAME, INVENTORY_FILENAME))
    assert read_inventory.call_args[0][1] == 'http://hostname/'


@with_app()
@with_tempdir
def test_missing_reference(tempdir, app, status, warning):
    inv_file = tempdir / 'inventory'
    inv_file.write_bytes(inventory_v2)
    app.config.intersphinx_mapping = {
        'https://docs.python.org/': inv_file,
        'py3k': ('https://docs.python.org/py3k/', inv_file),
        'py3krel': ('py3k', inv_file),  # relative path
        'py3krelparent': ('../../py3k', inv_file),  # relative path, parent dir
    }
    app.config.intersphinx_cache_limit = 0

    # load the inventory and check if it's done correctly
    load_mappings(app)
    inv = app.env.intersphinx_inventory

    assert inv['py:module']['module2'] == \
        ('foo', '2.0', 'https://docs.python.org/foo.html#module-module2', '-')

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
    assert rn['refuri'] == 'https://docs.python.org/sub/foo.html#module1.func'
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

    # check relative paths
    rn = reference_check('py', 'mod', 'py3krel:module1', 'foo')
    assert rn['refuri'] == 'py3k/foo.html#module-module1'

    rn = reference_check('py', 'mod', 'py3krelparent:module1', 'foo')
    assert rn['refuri'] == '../../py3k/foo.html#module-module1'

    rn = reference_check('py', 'mod', 'py3krel:module1', 'foo', refdoc='sub/dir/test')
    assert rn['refuri'] == '../../py3k/foo.html#module-module1'

    rn = reference_check('py', 'mod', 'py3krelparent:module1', 'foo', refdoc='sub/dir/test')
    assert rn['refuri'] == '../../../../py3k/foo.html#module-module1'


@with_app()
@with_tempdir
def test_load_mappings_warnings(tempdir, app, status, warning):
    """
    load_mappings issues a warning if new-style mapping
    identifiers are not string
    """
    inv_file = tempdir / 'inventory'
    inv_file.write_bytes(inventory_v2)
    app.config.intersphinx_mapping = {
        'https://docs.python.org/': inv_file,
        'py3k': ('https://docs.python.org/py3k/', inv_file),
        'repoze.workflow': ('http://docs.repoze.org/workflow/', inv_file),
        'django-taggit': ('http://django-taggit.readthedocs.org/en/latest/',
                          inv_file),
        12345: ('http://www.sphinx-doc.org/en/stable/', inv_file),
    }

    app.config.intersphinx_cache_limit = 0
    # load the inventory and check if it's done correctly
    load_mappings(app)
    assert warning.getvalue().count('\n') == 1


class TestStripBasicAuth(unittest.TestCase):
    """Tests for sphinx.ext.intersphinx._strip_basic_auth()"""
    def test_auth_stripped(self):
        """basic auth creds stripped from URL containing creds"""
        url = 'https://user:12345@domain.com/project/objects.inv'
        expected = 'https://domain.com/project/objects.inv'
        actual = _strip_basic_auth(url)
        self.assertEqual(expected, actual)

    def test_no_auth(self):
        """url unchanged if param doesn't contain basic auth creds"""
        url = 'https://domain.com/project/objects.inv'
        expected = 'https://domain.com/project/objects.inv'
        actual = _strip_basic_auth(url)
        self.assertEqual(expected, actual)

    def test_having_port(self):
        """basic auth creds correctly stripped from URL containing creds even if URL
        contains port"""
        url = 'https://user:12345@domain.com:8080/project/objects.inv'
        expected = 'https://domain.com:8080/project/objects.inv'
        actual = _strip_basic_auth(url)
        self.assertEqual(expected, actual)


def test_getsafeurl_authed():
    """_get_safe_url() with a url with basic auth"""
    url = 'https://user:12345@domain.com/project/objects.inv'
    expected = 'https://user@domain.com/project/objects.inv'
    actual = _get_safe_url(url)
    assert expected == actual


def test_getsafeurl_authed_having_port():
    """_get_safe_url() with a url with basic auth having port"""
    url = 'https://user:12345@domain.com:8080/project/objects.inv'
    expected = 'https://user@domain.com:8080/project/objects.inv'
    actual = _get_safe_url(url)
    assert expected == actual


def test_getsafeurl_unauthed():
    """_get_safe_url() with a url without basic auth"""
    url = 'https://domain.com/project/objects.inv'
    expected = 'https://domain.com/project/objects.inv'
    actual = _get_safe_url(url)
    assert expected == actual
