"""Test the intersphinx extension."""

from __future__ import annotations

import http.server
import time
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.builders.html import INVENTORY_FILENAME
from sphinx.config import Config
from sphinx.errors import ConfigError
from sphinx.ext.intersphinx import setup as intersphinx_setup
from sphinx.ext.intersphinx._cli import inspect_main
from sphinx.ext.intersphinx._load import (
    _display_failures,
    _fetch_inventory_data,
    _fetch_inventory_group,
    _get_safe_url,
    _InvConfig,
    _load_inventory,
    _strip_basic_auth,
    load_mappings,
    validate_intersphinx_mapping,
)
from sphinx.ext.intersphinx._resolve import missing_reference
from sphinx.ext.intersphinx._shared import _IntersphinxProject
from sphinx.util.inventory import _Inventory, _InventoryItem

from tests.test_util.intersphinx_data import (
    INVENTORY_V2,
    INVENTORY_V2_AMBIGUOUS_TERMS,
    INVENTORY_V2_NO_VERSION,
    INVENTORY_V2_TEXT_VERSION,
)
from tests.utils import http_server

if TYPE_CHECKING:
    from typing import NoReturn

    from sphinx.ext.intersphinx._shared import InventoryCacheEntry
    from sphinx.testing.util import SphinxTestApp
    from sphinx.util.typing import Inventory


class FakeList(list[str]):  # NoQA: FURB189
    def __iter__(self) -> NoReturn:
        raise NotImplementedError


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


def set_config(app, mapping):
    # copy *mapping* so that normalization does not alter it
    app.config.intersphinx_mapping = mapping.copy()
    app.config.intersphinx_cache_limit = 0
    app.config.intersphinx_disabled_reftypes = []
    app.config.intersphinx_resolve_self = ''
    app.config.intersphinx_timeout = None


@mock.patch('sphinx.ext.intersphinx._load.InventoryFile')
@mock.patch('sphinx.ext.intersphinx._load.requests.get')
@pytest.mark.sphinx('html', testroot='root')
def test_fetch_inventory_redirection(get_request, InventoryFile, app):
    mocked_get = get_request.return_value.__enter__.return_value
    intersphinx_setup(app)
    mocked_get.content = b'# Sphinx inventory version 2'

    # same uri and inv, not redirected
    mocked_get.url = 'https://hostname/' + INVENTORY_FILENAME
    target_uri = 'https://hostname/'
    raw_data, target_uri = _fetch_inventory_data(
        target_uri=target_uri,
        inv_location='https://hostname/' + INVENTORY_FILENAME,
        config=_InvConfig.from_config(app.config),
        srcdir=app.srcdir,
        cache_path=None,
    )
    _load_inventory(raw_data, target_uri=target_uri)
    assert 'intersphinx inventory has moved' not in app.status.getvalue()
    assert InventoryFile.loads.call_args[1]['uri'] == 'https://hostname/'

    # same uri and inv, redirected
    app.status.seek(0)
    app.status.truncate(0)
    mocked_get.url = 'https://hostname/new/' + INVENTORY_FILENAME

    target_uri = 'https://hostname/'
    raw_data, target_uri = _fetch_inventory_data(
        target_uri=target_uri,
        inv_location='https://hostname/' + INVENTORY_FILENAME,
        config=_InvConfig.from_config(app.config),
        srcdir=app.srcdir,
        cache_path=None,
    )
    _load_inventory(raw_data, target_uri=target_uri)
    assert app.status.getvalue() == (
        'intersphinx inventory has moved: '
        'https://hostname/%s -> https://hostname/new/%s\n'
        % (INVENTORY_FILENAME, INVENTORY_FILENAME)
    )
    assert InventoryFile.loads.call_args[1]['uri'] == 'https://hostname/new'

    # different uri and inv, not redirected
    app.status.seek(0)
    app.status.truncate(0)
    mocked_get.url = 'https://hostname/new/' + INVENTORY_FILENAME

    target_uri = 'https://hostname/'
    raw_data, target_uri = _fetch_inventory_data(
        target_uri=target_uri,
        inv_location='https://hostname/new/' + INVENTORY_FILENAME,
        config=_InvConfig.from_config(app.config),
        srcdir=app.srcdir,
        cache_path=None,
    )
    _load_inventory(raw_data, target_uri=target_uri)
    assert 'intersphinx inventory has moved' not in app.status.getvalue()
    assert InventoryFile.loads.call_args[1]['uri'] == 'https://hostname/'

    # different uri and inv, redirected
    app.status.seek(0)
    app.status.truncate(0)
    mocked_get.url = 'https://hostname/other/' + INVENTORY_FILENAME

    target_uri = 'https://hostname/'
    raw_data, target_uri = _fetch_inventory_data(
        target_uri=target_uri,
        inv_location='https://hostname/new/' + INVENTORY_FILENAME,
        config=_InvConfig.from_config(app.config),
        srcdir=app.srcdir,
        cache_path=None,
    )
    _load_inventory(raw_data, target_uri=target_uri)
    assert app.status.getvalue() == (
        'intersphinx inventory has moved: '
        'https://hostname/new/%s -> https://hostname/other/%s\n'
        % (INVENTORY_FILENAME, INVENTORY_FILENAME)
    )
    assert InventoryFile.loads.call_args[1]['uri'] == 'https://hostname/'


@pytest.mark.sphinx('html', testroot='root')
def test_missing_reference(tmp_path, app):
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2)
    set_config(
        app,
        {
            'python': ('https://docs.python.org/', str(inv_file)),
            'py3k': ('https://docs.python.org/py3k/', str(inv_file)),
            'py3krel': ('py3k', str(inv_file)),  # relative path
            'py3krelparent': ('../../py3k', str(inv_file)),  # relative path, parent dir
        },
    )

    # load the inventory and check if it's done correctly
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)
    inv: Inventory = app.env.intersphinx_inventory

    assert inv['py:module']['module2'] == _InventoryItem(
        project_name='foo',
        project_version='2.0',
        uri='https://docs.python.org/foo.html#module-module2',
        display_name='-',
    )

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
    rn = reference_check(
        app, 'py', 'mod', 'py3k:module2', 'py3k:module2', refexplicit=True
    )
    assert rn[0].astext() == 'py3k:module2'

    # prefix given, target not found and nonexplicit title: prefix is not stripped
    node, contnode = fake_node(
        'py', 'mod', 'py3k:unknown', 'py3k:unknown', refexplicit=False
    )
    rn = missing_reference(app, app.env, node, contnode)
    assert rn is None
    assert contnode[0].astext() == 'py3k:unknown'

    # prefix given, target not found and explicit title: nothing is changed
    node, contnode = fake_node(
        'py', 'mod', 'py3k:unknown', 'py3k:unknown', refexplicit=True
    )
    rn = missing_reference(app, app.env, node, contnode)
    assert rn is None
    assert contnode[0].astext() == 'py3k:unknown'

    # check relative paths
    rn = reference_check(app, 'py', 'mod', 'py3krel:module1', 'foo')
    assert rn['refuri'] == 'py3k/foo.html#module-module1'

    rn = reference_check(app, 'py', 'mod', 'py3krelparent:module1', 'foo')
    assert rn['refuri'] == '../../py3k/foo.html#module-module1'

    rn = reference_check(
        app, 'py', 'mod', 'py3krel:module1', 'foo', refdoc='sub/dir/test'
    )
    assert rn['refuri'] == '../../py3k/foo.html#module-module1'

    rn = reference_check(
        app, 'py', 'mod', 'py3krelparent:module1', 'foo', refdoc='sub/dir/test'
    )
    assert rn['refuri'] == '../../../../py3k/foo.html#module-module1'

    # check refs of standard domain
    rn = reference_check(app, 'std', 'doc', 'docname', 'docname')
    assert rn['refuri'] == 'https://docs.python.org/docname.html'


@pytest.mark.sphinx('html', testroot='root')
def test_missing_reference_pydomain(tmp_path, app):
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2)
    set_config(
        app,
        {
            'python': ('https://docs.python.org/', str(inv_file)),
        },
    )

    # load the inventory and check if it's done correctly
    validate_intersphinx_mapping(app, app.config)
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


@pytest.mark.sphinx('html', testroot='root')
def test_missing_reference_stddomain(tmp_path, app):
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2)
    set_config(
        app,
        {
            'cmd': ('https://docs.python.org/', str(inv_file)),
        },
    )

    # load the inventory and check if it's done correctly
    validate_intersphinx_mapping(app, app.config)
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

    # term reference (normal)
    node, contnode = fake_node('std', 'term', 'a term', 'a term')
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == 'a term'

    # term reference (case insensitive)
    node, contnode = fake_node('std', 'term', 'A TERM', 'A TERM')
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == 'A TERM'

    # label reference (normal)
    node, contnode = fake_node('std', 'ref', 'The-Julia-Domain', 'The-Julia-Domain')
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == 'The Julia Domain'

    # label reference (case insensitive)
    node, contnode = fake_node('std', 'ref', 'the-julia-domain', 'the-julia-domain')
    rn = missing_reference(app, app.env, node, contnode)
    assert rn.astext() == 'The Julia Domain'


@pytest.mark.parametrize(
    ('term', 'expected_ambiguity'),
    [
        ('A TERM', False),
        ('B TERM', True),
    ],
)
@pytest.mark.sphinx('html', testroot='root')
def test_ambiguous_reference_handling(term, expected_ambiguity, tmp_path, app, warning):
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2_AMBIGUOUS_TERMS)
    set_config(
        app,
        {
            'cmd': ('https://docs.python.org/', str(inv_file)),
        },
    )

    # load the inventory
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)

    # term reference (case insensitive)
    node, contnode = fake_node('std', 'term', term, term)
    missing_reference(app, app.env, node, contnode)

    ambiguity = f'multiple matches found for std:term:{term}' in warning.getvalue()
    assert ambiguity is expected_ambiguity


@pytest.mark.sphinx('html', testroot='ext-intersphinx-cppdomain')
def test_missing_reference_cppdomain(tmp_path, app):
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2)
    set_config(
        app,
        {
            'python': ('https://docs.python.org/', str(inv_file)),
        },
    )

    # load the inventory and check if it's done correctly
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)

    app.build()
    html = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<a class="reference external"'
        ' href="https://docs.python.org/index.html#cpp_foo_bar"'
        ' title="(in foo v2.0)">'
        '<code class="xref cpp cpp-class docutils literal notranslate">'
        '<span class="pre">Bar</span></code></a>'
    ) in html
    assert (
        '<a class="reference external"'
        ' href="https://docs.python.org/index.html#foons"'
        ' title="(in foo v2.0)"><span class="n"><span class="pre">foons</span></span></a>'
    ) in html
    assert (
        '<a class="reference external"'
        ' href="https://docs.python.org/index.html#foons_bartype"'
        ' title="(in foo v2.0)"><span class="n"><span class="pre">bartype</span></span></a>'
    ) in html


@pytest.mark.sphinx('html', testroot='root')
def test_missing_reference_jsdomain(tmp_path, app):
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2)
    set_config(
        app,
        {
            'python': ('https://docs.python.org/', str(inv_file)),
        },
    )

    # load the inventory and check if it's done correctly
    validate_intersphinx_mapping(app, app.config)
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


@pytest.mark.sphinx('html', testroot='root')
def test_missing_reference_disabled_domain(tmp_path, app):
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2)
    set_config(
        app,
        {
            'inv': ('https://docs.python.org/', str(inv_file)),
        },
    )

    # load the inventory and check if it's done correctly
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)

    def case(*, term, doc, py):
        def assert_(rn, expected):
            if expected is None:
                assert rn is None
            else:
                assert rn.astext() == expected

        kwargs = {}

        node, contnode = fake_node('std', 'term', 'a term', 'a term', **kwargs)
        rn = missing_reference(app, app.env, node, contnode)
        assert_(rn, 'a term' if term else None)

        node, contnode = fake_node('std', 'term', 'inv:a term', 'a term', **kwargs)
        rn = missing_reference(app, app.env, node, contnode)
        assert_(rn, 'a term')

        node, contnode = fake_node('std', 'doc', 'docname', 'docname', **kwargs)
        rn = missing_reference(app, app.env, node, contnode)
        assert_(rn, 'docname' if doc else None)

        node, contnode = fake_node('std', 'doc', 'inv:docname', 'docname', **kwargs)
        rn = missing_reference(app, app.env, node, contnode)
        assert_(rn, 'docname')

        # an arbitrary ref in another domain
        node, contnode = fake_node('py', 'func', 'module1.func', 'func()', **kwargs)
        rn = missing_reference(app, app.env, node, contnode)
        assert_(rn, 'func()' if py else None)

        node, contnode = fake_node('py', 'func', 'inv:module1.func', 'func()', **kwargs)
        rn = missing_reference(app, app.env, node, contnode)
        assert_(rn, 'func()')

    # the base case, everything should resolve
    assert app.config.intersphinx_disabled_reftypes == []
    case(term=True, doc=True, py=True)

    # disabled a single ref type
    app.config.intersphinx_disabled_reftypes = ['std:doc']
    case(term=True, doc=False, py=True)

    # disabled a whole domain
    app.config.intersphinx_disabled_reftypes = ['std:*']
    case(term=False, doc=False, py=True)

    # disabled all domains
    app.config.intersphinx_disabled_reftypes = ['*']
    case(term=False, doc=False, py=False)


@pytest.mark.sphinx('html', testroot='root')
def test_inventory_not_having_version(tmp_path, app):
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2_NO_VERSION)
    set_config(
        app,
        {
            'python': ('https://docs.python.org/', str(inv_file)),
        },
    )

    # load the inventory and check if it's done correctly
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)

    rn = reference_check(app, 'py', 'mod', 'module1', 'foo')
    assert isinstance(rn, nodes.reference)
    assert rn['refuri'] == 'https://docs.python.org/foo.html#module-module1'
    assert rn['reftitle'] == '(in foo)'
    assert rn[0].astext() == 'Long Module desc'


@pytest.mark.sphinx('html', testroot='root')
def test_validate_intersphinx_mapping_warnings(app: SphinxTestApp) -> None:
    """Check warnings in :func:`sphinx.ext.intersphinx.validate_intersphinx_mapping`."""
    bad_intersphinx_mapping = {
        '':                 ('789.example', None),     # invalid project name (value)
        12345:              ('456.example', None),     # invalid project name (type)
        None:               ('123.example', None),     # invalid project name (type)
        'https://example/': None,                      # Sphinx 0.5 style value (None)
        'https://server/':  'inventory',               # Sphinx 0.5 style value (str)
        'bad-dict-item':    0,                         # invalid dict item type
        'unpack-except-1':  [0],                       # invalid dict item size (native ValueError)
        'unpack-except-2':  FakeList(),                # invalid dict item size (custom exception)
        'bad-uri-type-1':   (123456789, None),         # invalid target URI type
        'bad-uri-type-2':   (None, None),              # invalid target URI type
        'bad-uri-value':    ('', None),                # invalid target URI value
        'good':             ('example.org', None),     # duplicated target URI (good entry)
        'dedup-good':       ('example.org', None),     # duplicated target URI
        'bad-location-1':   ('a.example', 1),          # invalid inventory location (single input, bad type)
        'bad-location-2':   ('b.example', ''),         # invalid inventory location (single input, bad string)
        'bad-location-3':   ('c.example', [2, 'x']),   # invalid inventory location (sequence input, bad type)
        'bad-location-4':   ('d.example', ['y', '']),  # invalid inventory location (sequence input, bad string)
        'good-target-1':    ('e.example', None),       # valid inventory location (None)
        'good-target-2':    ('f.example', ('x',)),     # valid inventory location (sequence input)
    }  # fmt: skip
    set_config(app, bad_intersphinx_mapping)

    # normalise the inventory and check if it's done correctly
    with pytest.raises(
        ConfigError,
        match=r'^Invalid `intersphinx_mapping` configuration \(16 errors\).$',
    ):
        validate_intersphinx_mapping(app, app.config)
    warnings = strip_escape_sequences(app.warning.getvalue()).splitlines()
    assert len(warnings) == len(bad_intersphinx_mapping) - 3
    assert warnings == [
        "ERROR: Invalid intersphinx project identifier `''` in intersphinx_mapping. Project identifiers must be non-empty strings.",
        'ERROR: Invalid intersphinx project identifier `12345` in intersphinx_mapping. Project identifiers must be non-empty strings.',
        'ERROR: Invalid intersphinx project identifier `None` in intersphinx_mapping. Project identifiers must be non-empty strings.',
        "ERROR: Invalid value `None` in intersphinx_mapping['https://example/']. Expected a two-element tuple or list.",
        "ERROR: Invalid value `'inventory'` in intersphinx_mapping['https://server/']. Expected a two-element tuple or list.",
        "ERROR: Invalid value `0` in intersphinx_mapping['bad-dict-item']. Expected a two-element tuple or list.",
        "ERROR: Invalid value `[0]` in intersphinx_mapping['unpack-except-1']. Values must be a (target URI, inventory locations) pair.",
        "ERROR: Invalid value `[]` in intersphinx_mapping['unpack-except-2']. Values must be a (target URI, inventory locations) pair.",
        "ERROR: Invalid target URI value `123456789` in intersphinx_mapping['bad-uri-type-1'][0]. Target URIs must be unique non-empty strings.",
        "ERROR: Invalid target URI value `None` in intersphinx_mapping['bad-uri-type-2'][0]. Target URIs must be unique non-empty strings.",
        "ERROR: Invalid target URI value `''` in intersphinx_mapping['bad-uri-value'][0]. Target URIs must be unique non-empty strings.",
        "ERROR: Invalid target URI value `'example.org'` in intersphinx_mapping['dedup-good'][0]. Target URIs must be unique (other instance in intersphinx_mapping['good']).",
        "ERROR: Invalid inventory location value `1` in intersphinx_mapping['bad-location-1'][1]. Inventory locations must be non-empty strings or None.",
        "ERROR: Invalid inventory location value `''` in intersphinx_mapping['bad-location-2'][1]. Inventory locations must be non-empty strings or None.",
        "ERROR: Invalid inventory location value `2` in intersphinx_mapping['bad-location-3'][1]. Inventory locations must be non-empty strings or None.",
        "ERROR: Invalid inventory location value `''` in intersphinx_mapping['bad-location-4'][1]. Inventory locations must be non-empty strings or None.",
    ]


@pytest.mark.sphinx('html', testroot='root')
def test_load_mappings_fallback(tmp_path, app):
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2)
    set_config(app, {})

    # connect to invalid path
    app.config.intersphinx_mapping = {
        'fallback': ('https://docs.python.org/py3k/', '/invalid/inventory/path'),
    }
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)
    assert 'failed to reach any of the inventories' in app.warning.getvalue()

    rn = reference_check(app, 'py', 'func', 'module1.func', 'foo')
    assert rn is None

    # clear messages
    app.status.truncate(0)
    app.warning.truncate(0)

    # add fallbacks to mapping
    app.config.intersphinx_mapping = {
        'fallback': (
            'https://docs.python.org/py3k/',
            ('/invalid/inventory/path', str(inv_file)),
        ),
    }
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)
    assert (
        'encountered some issues with some of the inventories'
    ) in app.status.getvalue()
    assert app.warning.getvalue() == ''

    rn = reference_check(app, 'py', 'func', 'module1.func', 'foo')
    assert isinstance(rn, nodes.reference)


class TestStripBasicAuth:
    """Tests for sphinx.ext.intersphinx._strip_basic_auth()"""

    def test_auth_stripped(self):
        """Basic auth creds stripped from URL containing creds"""
        url = 'https://user:12345@domain.com/project/objects.inv'
        expected = 'https://domain.com/project/objects.inv'
        actual = _strip_basic_auth(url)
        assert actual == expected

    def test_no_auth(self):
        """Url unchanged if param doesn't contain basic auth creds"""
        url = 'https://domain.com/project/objects.inv'
        expected = 'https://domain.com/project/objects.inv'
        actual = _strip_basic_auth(url)
        assert actual == expected

    def test_having_port(self):
        """Basic auth creds correctly stripped from URL containing creds even if URL
        contains port
        """
        url = 'https://user:12345@domain.com:8080/project/objects.inv'
        expected = 'https://domain.com:8080/project/objects.inv'
        actual = _strip_basic_auth(url)
        assert actual == expected


def test_getsafeurl_authed() -> None:
    """_get_safe_url() with a url with basic auth"""
    url = 'https://user:12345@domain.com/project/objects.inv'
    expected = 'https://user@domain.com/project/objects.inv'
    actual = _get_safe_url(url)
    assert actual == expected


def test_getsafeurl_authed_having_port() -> None:
    """_get_safe_url() with a url with basic auth having port"""
    url = 'https://user:12345@domain.com:8080/project/objects.inv'
    expected = 'https://user@domain.com:8080/project/objects.inv'
    actual = _get_safe_url(url)
    assert actual == expected


def test_getsafeurl_unauthed() -> None:
    """_get_safe_url() with a url without basic auth"""
    url = 'https://domain.com/project/objects.inv'
    expected = 'https://domain.com/project/objects.inv'
    actual = _get_safe_url(url)
    assert actual == expected


def test_inspect_main_noargs(capsys):
    """inspect_main interface, without arguments"""
    assert inspect_main([]) == 1

    expected = (
        'Print out an inventory file.\n'
        'Error: must specify local path or URL to an inventory file.'
    )
    stdout, stderr = capsys.readouterr()
    assert stdout == ''
    assert stderr == expected + '\n'


def test_inspect_main_file(capsys, tmp_path):
    """inspect_main interface, with file argument"""
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2)

    inspect_main([str(inv_file)])

    stdout, stderr = capsys.readouterr()
    assert stdout.startswith('c:function\n')
    assert stderr == ''


def test_inspect_main_url(capsys):
    """inspect_main interface, with url argument"""

    class InventoryHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200, 'OK')
            self.end_headers()
            self.wfile.write(INVENTORY_V2)

        def log_message(*args, **kwargs):
            # Silenced.
            pass

    with http_server(InventoryHandler) as server:
        url = f'http://localhost:{server.server_port}/{INVENTORY_FILENAME}'
        inspect_main([url])

    stdout, stderr = capsys.readouterr()
    assert stdout.startswith('c:function\n')
    assert stderr == ''


@pytest.mark.sphinx('html', testroot='ext-intersphinx-role', copy_test_root=True)
def test_intersphinx_role(app: SphinxTestApp) -> None:
    inv_file = app.srcdir / 'inventory'
    inv_file.write_bytes(INVENTORY_V2)
    app.config.intersphinx_mapping = {
        'inv': ('https://example.org/', str(inv_file)),
    }
    app.config.intersphinx_cache_limit = 0
    app.config.nitpicky = True

    # load the inventory and check if it's done correctly
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)

    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    warnings = strip_escape_sequences(app.warning.getvalue()).splitlines()
    index_path = app.srcdir / 'index.rst'
    assert warnings == [
        f"{index_path}:21: WARNING: role for external cross-reference not found in domain 'py': 'nope' [intersphinx.external]",
        f"{index_path}:28: WARNING: role for external cross-reference not found in domains 'cpp', 'std': 'nope' [intersphinx.external]",
        f"{index_path}:39: WARNING: inventory for external cross-reference not found: 'invNope' [intersphinx.external]",
        f"{index_path}:44: WARNING: role for external cross-reference not found in domain 'c': 'function' (perhaps you meant one of: 'func', 'identifier', 'type') [intersphinx.external]",
        f"{index_path}:45: WARNING: role for external cross-reference not found in domains 'cpp', 'std': 'function' (perhaps you meant one of: 'cpp:func', 'cpp:identifier', 'cpp:type') [intersphinx.external]",
        f'{index_path}:9: WARNING: external py:mod reference target not found: module3 [ref.mod]',
        f'{index_path}:14: WARNING: external py:mod reference target not found: module10 [ref.mod]',
        f'{index_path}:19: WARNING: external py:meth reference target not found: inv:Foo.bar [ref.meth]',
    ]

    html = '<a class="reference external" href="https://example.org/{}" title="(in foo v2.0)">'
    assert html.format('foo.html#module-module1') in content
    assert html.format('foo.html#module-module2') in content

    assert html.format('sub/foo.html#module1.func') in content

    # default domain
    assert html.format('index.html#std_uint8_t') in content

    # std roles without domain prefix
    assert html.format('docname.html') in content
    assert html.format('index.html#cmdoption-ls-l') in content

    # explicit inventory
    assert html.format('cfunc.html#CFunc') in content

    # explicit title
    assert html.format('index.html#foons') in content


@pytest.mark.sphinx('html', testroot='root')
@pytest.mark.parametrize(
    ('cache_limit', 'expected_expired'),
    [
        (5, False),  # cache for 5 days
        (1, True),  # cache for 1 day
        (0, True),  # cache for 0 days
        (-1, False),  # cache forever
    ],
)
def test_intersphinx_cache_limit(app, monkeypatch, cache_limit, expected_expired):
    url = 'https://example.org/'
    app.config.intersphinx_cache_limit = cache_limit
    app.config.intersphinx_mapping = {
        'inv': (url, None),
    }
    app.config.intersphinx_timeout = None
    # load the inventory and check if it's done correctly
    intersphinx_cache: dict[str, InventoryCacheEntry] = {
        url: ('inv', 0, {}),  # Timestamp of last cache write is zero.
    }
    validate_intersphinx_mapping(app, app.config)

    # The test's `now` is two days after the cache was created.
    now = 2 * 86400
    monkeypatch.setattr('time.time', lambda: now)

    # `_fetch_inventory_group` calls `_fetch_inventory_data`.
    # We replace it with a mock to test whether it has been called.
    # If it has been called, it means the cache had expired.
    monkeypatch.setattr(
        'sphinx.ext.intersphinx._load._fetch_inventory_data',
        mock.Mock(return_value=(b'', '')),
    )
    mock_fetch_inventory = mock.Mock(return_value=_Inventory({}))
    monkeypatch.setattr(
        'sphinx.ext.intersphinx._load._load_inventory', mock_fetch_inventory
    )

    for name, (uri, locations) in app.config.intersphinx_mapping.values():
        project = _IntersphinxProject(name=name, target_uri=uri, locations=locations)
        updated = _fetch_inventory_group(
            project=project,
            cache=intersphinx_cache,
            now=now,
            config=_InvConfig.from_config(app.config),
            srcdir=app.srcdir,
            cache_dir=None,
        )
        # If we hadn't mocked `_fetch_inventory_data`, it would've made
        # a request to `https://example.org/` and found no inventory
        # file. That would've been an error, and `updated` would've been
        # False even if the cache had expired. The mock makes it behave
        # "correctly".
        assert updated is expected_expired
    # Double-check: If the cache was expired, `mock_fetch_inventory`
    # must've been called.
    assert mock_fetch_inventory.called is expected_expired


def test_intersphinx_fetch_inventory_group_url():
    class InventoryHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200, 'OK')
            self.end_headers()
            self.wfile.write(INVENTORY_V2)

        def log_message(*args, **kwargs):
            # Silenced.
            pass

    with http_server(InventoryHandler) as server:
        url1 = f'http://localhost:{server.server_port}'
        url2 = f'http://localhost:{server.server_port}/'

        config = Config()
        config.intersphinx_cache_limit = -1
        config.intersphinx_mapping = {
            '1': (url1, None),
            '2': (url2, None),
        }

        now = int(time.time())
        # we can use 'srcdir=None' since we are raising in _fetch_inventory_data
        kwds = {
            'cache': {},
            'now': now,
            'config': config,
            'srcdir': None,
            'cache_dir': None,
        }
        # We need an exception with its 'args' attribute set (see error
        # handling in sphinx.ext.intersphinx._load._fetch_inventory_group).
        side_effect = ValueError('')

        project1 = _IntersphinxProject(
            name='1', target_uri=url1, locations=(url1, None)
        )
        with mock.patch(
            'sphinx.ext.intersphinx._load._fetch_inventory_data',
            side_effect=side_effect,
        ) as mockfn:
            assert not _fetch_inventory_group(project=project1, **kwds)
        mockfn.assert_any_call(
            target_uri=url1,
            inv_location=url1,
            config=config,
            srcdir=None,
            cache_path=None,
        )
        mockfn.assert_any_call(
            target_uri=url1,
            inv_location=url1 + '/' + INVENTORY_FILENAME,
            config=config,
            srcdir=None,
            cache_path=None,
        )

        project2 = _IntersphinxProject(
            name='2', target_uri=url2, locations=(url2, None)
        )
        with mock.patch(
            'sphinx.ext.intersphinx._load._fetch_inventory_data',
            side_effect=side_effect,
        ) as mockfn:
            assert not _fetch_inventory_group(project=project2, **kwds)
        mockfn.assert_any_call(
            target_uri=url2,
            inv_location=url2,
            config=config,
            srcdir=None,
            cache_path=None,
        )
        mockfn.assert_any_call(
            target_uri=url2,
            inv_location=url2 + INVENTORY_FILENAME,
            config=config,
            srcdir=None,
            cache_path=None,
        )


@pytest.mark.sphinx('html', testroot='root')
def test_inventory_text_version(tmp_path, app):
    inv_file = tmp_path / 'inventory'
    inv_file.write_bytes(INVENTORY_V2_TEXT_VERSION)
    set_config(
        app,
        {
            'python': ('https://docs.python.org/', str(inv_file)),
        },
    )

    # load the inventory and check if non-numeric version is handled correctly
    validate_intersphinx_mapping(app, app.config)
    load_mappings(app)

    rn = reference_check(app, 'py', 'mod', 'module1', 'foo')
    assert isinstance(rn, nodes.reference)
    assert rn['refuri'] == 'https://docs.python.org/foo.html#module-module1'
    assert rn['reftitle'] == '(in foo stable)'
    assert rn[0].astext() == 'Long Module desc'


def test_display_failures():
    failures_args = [
        ('Failed to fetch %s from %s', 'inventory', 'http://example.com'),
        ('Timeout after %d seconds',),  # Only one argument
        (
            'intersphinx inventory has moved:',
            'http://example.com',
            'http://proxyhost.net',
        ),  # No '%'
    ]
    issues = _display_failures(failures_args)
    assert 'Failed to fetch inventory from http://example.com' in issues
    assert 'Timeout after %d seconds' in issues
    assert (
        'intersphinx inventory has moved: - http://example.com - http://proxyhost.net'
        in issues
    )
