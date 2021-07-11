"""
    test_intersphinx
    ~~~~~~~~~~~~~~~~

    Test the intersphinx extension.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import http.server
import os
import unittest
from unittest import mock

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.ext.intersphinx import (INVENTORY_FILENAME, _get_safe_url, _strip_basic_auth,
                                    fetch_inventory, inspect_main, load_mappings,
                                    missing_reference, normalize_intersphinx_mapping)
from sphinx.ext.intersphinx import setup as intersphinx_setup

from .test_util_inventory import inventory_v2, inventory_v2_not_having_version
from .utils import http_server


def fake_node(domain, type, target, content, **attrs):
    contnode = nodes.emphasis(content, content)
    node = addnodes.pending_xref('')
    node['reftarget'] = target
    node['reftype'] = type
    node['refdomain'] = domain
    node.attributes.update(attrs)
    node += contnode
    return node, contnode


def reference_check(app, *args, **kwds):
    node, contnode = fake_node(*args, **kwds)
    return missing_reference(app, app.env, node, contnode)


@mock.patch('sphinx.ext.intersphinx.InventoryFile')
@mock.patch('sphinx.ext.intersphinx._read_from_url')
def test_fetch_inventory_redirection(_read_from_url, InventoryFile, app, status, warning):
    intersphinx_setup(app)
    _read_from_url().readline.return_value = b'# Sphinx inventory version 2'

    # same uri and inv, not redirected
    _read_from_url().url = 'http://hostname/' + INVENTORY_FILENAME
    fetch_inventory(app, 'http://hostname/', 'http://hostname/' + INVENTORY_FILENAME)
    assert 'intersphinx inventory has moved' not in status.getvalue()
    assert InventoryFile.load.call_args[0][1] == 'http://hostname/'

    # same uri and inv, redirected
    status.seek(0)
    status.truncate(0)
    _read_from_url().url = 'http://hostname/new/' + INVENTORY_FILENAME

    fetch_inventory(app, 'http://hostname/', 'http://hostname/' + INVENTORY_FILENAME)
    assert status.getvalue() == ('intersphinx inventory has moved: '
                                 'http://hostname/%s -> http://hostname/new/%s\n' %
                                 (INVENTORY_FILENAME, INVENTORY_FILENAME))
    assert InventoryFile.load.call_args[0][1] == 'http://hostname/new'

    # different uri and inv, not redirected
    status.seek(0)
    status.truncate(0)
    _read_from_url().url = 'http://hostname/new/' + INVENTORY_FILENAME

    fetch_inventory(app, 'http://hostname/', 'http://hostname/new/' + INVENTORY_FILENAME)
    assert 'intersphinx inventory has moved' not in status.getvalue()
    assert InventoryFile.load.call_args[0][1] == 'http://hostname/'

    # different uri and inv, redirected
    status.seek(0)
    status.truncate(0)
    _read_from_url().url = 'http://hostname/other/' + INVENTORY_FILENAME

    fetch_inventory(app, 'http://hostname/', 'http://hostname/new/' + INVENTORY_FILENAME)
    assert status.getvalue() == ('intersphinx inventory has moved: '
                                 'http://hostname/new/%s -> http://hostname/other/%s\n' %
                                 (INVENTORY_FILENAME, INVENTORY_FILENAME))
    assert InventoryFile.load.call_args[0][1] == 'http://hostname/'


@pytest.mark.xfail(os.name != 'posix', reason="Path separator mismatch issue")
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
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)
    inv = app.env.intersphinx_inventory

    assert inv['py:module']['module2'] == \
        ('foo', '2.0', 'https://docs.python.org/foo.html#module-module2', '-')

    # check resolution when a target is found
    rn = reference_check(app, 'py', 'func', 'module1.func', 'foo')
    assert isinstance(rn, nodes.reference)
    assert rn['refuri'] == 'https://docs.python.org/sub/foo.html#module1.func'
    assert rn['reftitle'] == '(in foo v2.0)'
    assert rn[0].astext() == 'foo'

    # create unresolvable nodes and check None return value
    assert reference_check(app, 'py', 'foo', 'module1.func', 'foo') is None
    assert reference_check(app, 'py', 'func', 'foo', 'foo') is None
    assert reference_check(app, 'py', 'func', 'foo', 'foo') is None

    # check handling of prefixes

    # prefix given, target found: prefix is stripped
    rn = reference_check(app, 'py', 'mod', 'py3k:module2', 'py3k:module2')
    assert rn[0].astext() == 'module2'

    # prefix given, but not in title: nothing stripped
    rn = reference_check(app, 'py', 'mod', 'py3k:module2', 'module2')
    assert rn[0].astext() == 'module2'

    # prefix given, but explicit: nothing stripped
    rn = reference_check(app, 'py', 'mod', 'py3k:module2', 'py3k:module2',
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
    rn = reference_check(app, 'py', 'mod', 'py3krel:module1', 'foo')
    assert rn['refuri'] == 'py3k/foo.html#module-module1'

    rn = reference_check(app, 'py', 'mod', 'py3krelparent:module1', 'foo')
    assert rn['refuri'] == '../../py3k/foo.html#module-module1'

    rn = reference_check(app, 'py', 'mod', 'py3krel:module1', 'foo', refdoc='sub/dir/test')
    assert rn['refuri'] == '../../py3k/foo.html#module-module1'

    rn = reference_check(app, 'py', 'mod', 'py3krelparent:module1', 'foo',
                         refdoc='sub/dir/test')
    assert rn['refuri'] == '../../../../py3k/foo.html#module-module1'

    # check refs of standard domain
    rn = reference_check(app, 'std', 'doc', 'docname', 'docname')
    assert rn['refuri'] == 'https://docs.python.org/docname.html'


def test_missing_reference_pydomain(tempdir, app, status, warning):
    inv_file = tempdir / 'inventory'
    inv_file.write_bytes(inventory_v2)
    app.config.intersphinx_mapping = {
        'https://docs.python.org/': inv_file,
    }
    app.config.intersphinx_cache_limit = 0

    # load the inventory and check if it's done correctly
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)

    # no context data
    kwargs = {}
    node, contnode = fake_node('py', 'func', 'func', 'func()', **kwargs)
    rn = missing_reference(app, app.env, node, contnode)
    assert rn is None

    # py:module context helps to search objects
    kwargs = {'py:module': 'module1'}
    node, contnode = fake_node('py', 'func', 'func', 'func()', **kwargs)
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == 'func()'

    # py:attr context helps to search objects
    kwargs = {'py:module': 'module1'}
    node, contnode = fake_node('py', 'attr', 'Foo.bar', 'Foo.bar', **kwargs)
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == 'Foo.bar'

    # term reference (normal)
    node, contnode = fake_node('std', 'term', 'a term', 'a term')
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == 'a term'

    # term reference (case insensitive)
    node, contnode = fake_node('std', 'term', 'A TERM', 'A TERM')
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == 'A TERM'


def test_missing_reference_stddomain(tempdir, app, status, warning):
    inv_file = tempdir / 'inventory'
    inv_file.write_bytes(inventory_v2)
    app.config.intersphinx_mapping = {
        'cmd': ('https://docs.python.org/', inv_file),
    }
    app.config.intersphinx_cache_limit = 0

    # load the inventory and check if it's done correctly
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)

    # no context data
    kwargs = {}
    node, contnode = fake_node('std', 'option', '-l', '-l', **kwargs)
    rn = missing_reference(app, app.env, node, contnode)
    assert rn is None

    # std:program context helps to search objects
    kwargs = {'std:program': 'ls'}
    node, contnode = fake_node('std', 'option', '-l', 'ls -l', **kwargs)
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == 'ls -l'

    # refers inventory by name
    kwargs = {}
    node, contnode = fake_node('std', 'option', 'cmd:ls -l', '-l', **kwargs)
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == '-l'


@pytest.mark.sphinx('html', testroot='ext-intersphinx-cppdomain')
def test_missing_reference_cppdomain(tempdir, app, status, warning):
    inv_file = tempdir / 'inventory'
    inv_file.write_bytes(inventory_v2)
    app.config.intersphinx_mapping = {
        'https://docs.python.org/': inv_file,
    }
    app.config.intersphinx_cache_limit = 0

    # load the inventory and check if it's done correctly
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)

    app.build()
    html = (app.outdir / 'index.html').read_text()
    assert ('<a class="reference external"'
            ' href="https://docs.python.org/index.html#cpp_foo_bar"'
            ' title="(in foo v2.0)">'
            '<code class="xref cpp cpp-class docutils literal notranslate">'
            '<span class="pre">Bar</span></code></a>' in html)
    assert ('<a class="reference external"'
            ' href="https://docs.python.org/index.html#foons"'
            ' title="(in foo v2.0)"><span class="n"><span class="pre">foons</span></span></a>' in html)
    assert ('<a class="reference external"'
            ' href="https://docs.python.org/index.html#foons_bartype"'
            ' title="(in foo v2.0)"><span class="n"><span class="pre">bartype</span></span></a>' in html)


def test_missing_reference_jsdomain(tempdir, app, status, warning):
    inv_file = tempdir / 'inventory'
    inv_file.write_bytes(inventory_v2)
    app.config.intersphinx_mapping = {
        'https://docs.python.org/': inv_file,
    }
    app.config.intersphinx_cache_limit = 0

    # load the inventory and check if it's done correctly
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)

    # no context data
    kwargs = {}
    node, contnode = fake_node('js', 'meth', 'baz', 'baz()', **kwargs)
    rn = missing_reference(app, app.env, node, contnode)
    assert rn is None

    # js:module and js:object context helps to search objects
    kwargs = {'js:module': 'foo', 'js:object': 'bar'}
    node, contnode = fake_node('js', 'meth', 'baz', 'baz()', **kwargs)
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == 'baz()'


@pytest.mark.xfail(os.name != 'posix', reason="Path separator mismatch issue")
def test_inventory_not_having_version(tempdir, app, status, warning):
    inv_file = tempdir / 'inventory'
    inv_file.write_bytes(inventory_v2_not_having_version)
    app.config.intersphinx_mapping = {
        'https://docs.python.org/': inv_file,
    }
    app.config.intersphinx_cache_limit = 0

    # load the inventory and check if it's done correctly
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)

    rn = reference_check(app, 'py', 'mod', 'module1', 'foo')
    assert isinstance(rn, nodes.reference)
    assert rn['refuri'] == 'https://docs.python.org/foo.html#module-module1'
    assert rn['reftitle'] == '(in foo)'
    assert rn[0].astext() == 'Long Module desc'


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
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)
    assert warning.getvalue().count('\n') == 1


def test_load_mappings_fallback(tempdir, app, status, warning):
    inv_file = tempdir / 'inventory'
    inv_file.write_bytes(inventory_v2)
    app.config.intersphinx_cache_limit = 0

    # connect to invalid path
    app.config.intersphinx_mapping = {
        'fallback': ('https://docs.python.org/py3k/', '/invalid/inventory/path'),
    }
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)
    assert "failed to reach any of the inventories" in warning.getvalue()

    rn = reference_check(app, 'py', 'func', 'module1.func', 'foo')
    assert rn is None

    # clear messages
    status.truncate(0)
    warning.truncate(0)

    # add fallbacks to mapping
    app.config.intersphinx_mapping = {
        'fallback': ('https://docs.python.org/py3k/', ('/invalid/inventory/path',
                                                       inv_file)),
    }
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)
    assert "encountered some issues with some of the inventories" in status.getvalue()
    assert "" == warning.getvalue()

    rn = reference_check(app, 'py', 'func', 'module1.func', 'foo')
    assert isinstance(rn, nodes.reference)


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


def test_inspect_main_noargs(capsys):
    """inspect_main interface, without arguments"""
    with pytest.raises(SystemExit):
        inspect_main([])

    expected = (
        "Print out an inventory file.\n"
        "Error: must specify local path or URL to an inventory file."
    )
    stdout, stderr = capsys.readouterr()
    assert stdout == ""
    assert stderr == expected + "\n"


def test_inspect_main_file(capsys, tempdir):
    """inspect_main interface, with file argument"""
    inv_file = tempdir / 'inventory'
    inv_file.write_bytes(inventory_v2)

    inspect_main([str(inv_file)])

    stdout, stderr = capsys.readouterr()
    assert stdout.startswith("c:function\n")
    assert stderr == ""


def test_inspect_main_url(capsys):
    """inspect_main interface, with url argument"""
    class InventoryHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200, "OK")
            self.end_headers()
            self.wfile.write(inventory_v2)

        def log_message(*args, **kwargs):
            # Silenced.
            pass

    url = 'http://localhost:7777/' + INVENTORY_FILENAME

    with http_server(InventoryHandler):
        inspect_main([url])

    stdout, stderr = capsys.readouterr()
    assert stdout.startswith("c:function\n")
    assert stderr == ""
