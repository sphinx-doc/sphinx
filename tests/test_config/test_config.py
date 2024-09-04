"""Test the sphinx.config.Config class."""

from __future__ import annotations

import pickle
import time
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest import mock

import pytest

import sphinx
from sphinx.builders.gettext import _gettext_compact_validator
from sphinx.config import (
    ENUM,
    Config,
    _Opt,
    check_confval_types,
    correct_copyright_year,
    is_serializable,
)
from sphinx.deprecation import RemovedInSphinx90Warning
from sphinx.errors import ConfigError, ExtensionError, VersionRequirementError

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import TypeAlias

    CircularList: TypeAlias = list[int | 'CircularList']
    CircularDict: TypeAlias = dict[str, int | 'CircularDict']


def check_is_serializable(subject: object, *, circular: bool) -> None:
    assert is_serializable(subject)

    if circular:

        class UselessGuard(frozenset[int]):
            def __or__(self, other: object, /) -> UselessGuard:
                # do nothing
                return self

            def union(self, *args: Iterable[object]) -> UselessGuard:
                # do nothing
                return self

        # check that without recursive guards, a recursion error occurs
        with pytest.raises(RecursionError):
            assert is_serializable(subject, _seen=UselessGuard())


def test_is_serializable() -> None:
    subject = [1, [2, {3, 'a'}], {'x': {'y': frozenset((4, 5))}}]
    check_is_serializable(subject, circular=False)

    a, b = [1], [2]  # type: (CircularList, CircularList)
    a.append(b)
    b.append(a)
    check_is_serializable(a, circular=True)
    check_is_serializable(b, circular=True)

    x: CircularDict = {'a': 1, 'b': {'c': 1}}
    x['b'] = x
    check_is_serializable(x, circular=True)


def test_config_opt_deprecated(recwarn):
    opt = _Opt('default', '', ())

    with pytest.warns(RemovedInSphinx90Warning):
        default, rebuild, valid_types = opt

    with pytest.warns(RemovedInSphinx90Warning):
        _ = opt[0]

    with pytest.warns(RemovedInSphinx90Warning):
        _ = list(opt)


@pytest.mark.sphinx(
    'html',
    testroot='config',
    confoverrides={
        'root_doc': 'root',
        'nonexisting_value': 'True',
        'latex_elements.maketitle': 'blah blah blah',
        'modindex_common_prefix': 'path1,path2',
    },
)
def test_core_config(app):
    cfg = app.config

    # simple values
    assert 'project' in cfg.__dict__
    assert cfg.project == 'Sphinx <Tests>'
    assert cfg.templates_path == ['_templates']

    # overrides
    assert cfg.root_doc == 'root'
    assert cfg.latex_elements['maketitle'] == 'blah blah blah'
    assert cfg.modindex_common_prefix == ['path1', 'path2']

    # simple default values
    assert 'locale_dirs' in cfg.__dict__
    assert cfg.locale_dirs == ['locales']
    assert cfg.trim_footnote_reference_space is False

    # complex default values
    assert 'html_title' not in cfg.__dict__
    assert cfg.html_title == 'Sphinx <Tests> 0.6alpha1 documentation'

    # complex default values mustn't raise
    for valuename in cfg.config_values:
        getattr(cfg, valuename)

    # "contains" gives True both for set and unset values
    assert 'project' in cfg
    assert 'html_title' in cfg
    assert 'nonexisting_value' not in cfg

    # invalid values
    with pytest.raises(AttributeError):
        _ = cfg._value
    with pytest.raises(AttributeError):
        _ = cfg.nonexisting_value

    # non-value attributes are deleted from the namespace
    with pytest.raises(AttributeError):
        _ = cfg.sys

    # setting attributes
    cfg.project = 'Foo'
    assert cfg.project == 'Foo'

    # alternative access via item interface
    cfg['project'] = 'Sphinx Tests'
    assert cfg['project'] == cfg.project == 'Sphinx Tests'


def test_config_not_found(tmp_path):
    with pytest.raises(ConfigError):
        Config.read(tmp_path)


@pytest.mark.parametrize('protocol', list(range(pickle.HIGHEST_PROTOCOL)))
def test_config_pickle_protocol(tmp_path, protocol: int):
    config = Config()

    pickled_config = pickle.loads(pickle.dumps(config, protocol))

    assert list(config._options) == list(pickled_config._options)
    assert repr(config) == repr(pickled_config)


def test_config_pickle_circular_reference_in_list():
    a, b = [1], [2]  # type: (CircularList, CircularList)
    a.append(b)
    b.append(a)

    check_is_serializable(a, circular=True)
    check_is_serializable(b, circular=True)

    config = Config()
    config.add('a', [], '', types=list)
    config.add('b', [], '', types=list)
    config.a, config.b = a, b

    actual = pickle.loads(pickle.dumps(config))
    assert isinstance(actual.a, list)
    check_is_serializable(actual.a, circular=True)

    assert isinstance(actual.b, list)
    check_is_serializable(actual.b, circular=True)

    assert actual.a[0] == 1
    assert actual.a[1][0] == 2
    assert actual.a[1][1][0] == 1
    assert actual.a[1][1][1][0] == 2

    assert actual.b[0] == 2
    assert actual.b[1][0] == 1
    assert actual.b[1][1][0] == 2
    assert actual.b[1][1][1][0] == 1

    assert len(actual.a) == 2
    assert len(actual.a[1]) == 2
    assert len(actual.a[1][1]) == 2
    assert len(actual.a[1][1][1]) == 2
    assert len(actual.a[1][1][1][1]) == 2

    assert len(actual.b) == 2
    assert len(actual.b[1]) == 2
    assert len(actual.b[1][1]) == 2
    assert len(actual.b[1][1][1]) == 2
    assert len(actual.b[1][1][1][1]) == 2

    def check(
        u: list[list[object] | int],
        v: list[list[object] | int],
        *,
        counter: Counter[type, int] | None = None,
        guard: frozenset[int] = frozenset(),
    ) -> Counter[type, int]:
        counter = Counter() if counter is None else counter

        if id(u) in guard and id(v) in guard:
            return counter

        if isinstance(u, int):
            assert v.__class__ is u.__class__
            assert u == v
            counter[type(u)] += 1
            return counter

        assert isinstance(u, list)
        assert v.__class__ is u.__class__
        for u_i, v_i in zip(u, v, strict=True):
            counter[type(u)] += 1
            check(u_i, v_i, counter=counter, guard=guard | {id(u), id(v)})

        return counter

    counter = check(actual.a, a)
    # check(actual.a, a)
    #   check(actual.a[0], a[0]) -> ++counter[dict]
    #       ++counter[int] (a[0] is an int)
    #   check(actual.a[1], a[1]) -> ++counter[dict]
    #       check(actual.a[1][0], a[1][0]) -> ++counter[dict]
    #           ++counter[int] (a[1][0] is an int)
    #       check(actual.a[1][1], a[1][1]) -> ++counter[dict]
    #           recursive guard since a[1][1] == a
    assert counter[type(a[0])] == 2
    assert counter[type(a[1])] == 4

    # same logic as above
    counter = check(actual.b, b)
    assert counter[type(b[0])] == 2
    assert counter[type(b[1])] == 4


def test_config_pickle_circular_reference_in_dict():
    x: CircularDict = {'a': 1, 'b': {'c': 1}}
    x['b'] = x
    check_is_serializable(x, circular=True)

    config = Config()
    config.add('x', [], '', types=dict)
    config.x = x

    actual = pickle.loads(pickle.dumps(config))
    check_is_serializable(actual.x, circular=True)
    assert isinstance(actual.x, dict)

    assert actual.x['a'] == 1
    assert actual.x['b']['a'] == 1

    assert len(actual.x) == 2
    assert len(actual.x['b']) == 2
    assert len(actual.x['b']['b']) == 2

    def check(
        u: dict[str, dict[str, object] | int],
        v: dict[str, dict[str, object] | int],
        *,
        counter: Counter[type, int] | None = None,
        guard: frozenset[int] = frozenset(),
    ) -> Counter:
        counter = Counter() if counter is None else counter

        if id(u) in guard and id(v) in guard:
            return counter

        if isinstance(u, int):
            assert v.__class__ is u.__class__
            assert u == v
            counter[type(u)] += 1
            return counter

        assert isinstance(u, dict)
        assert v.__class__ is u.__class__
        for u_i, v_i in zip(u, v, strict=True):
            counter[type(u)] += 1
            check(u[u_i], v[v_i], counter=counter, guard=guard | {id(u), id(v)})
        return counter

    counters = check(actual.x, x, counter=Counter())
    # check(actual.x, x)
    #   check(actual.x['a'], x['a']) -> ++counter[dict]
    #       ++counter[int] (x['a'] is an int)
    #   check(actual.x['b'], x['b']) -> ++counter[dict]
    #       recursive guard since x['b'] == x
    assert counters[type(x['a'])] == 1
    assert counters[type(x['b'])] == 2


def test_extension_values():
    config = Config()

    # check standard settings
    assert config.root_doc == 'index'

    # can't override it by add_config_value()
    with pytest.raises(ExtensionError) as excinfo:
        config.add('root_doc', 'index', 'env', None)
    assert 'already present' in str(excinfo.value)

    # add a new config value
    config.add('value_from_ext', [], 'env', None)
    assert config.value_from_ext == []

    # can't override it by add_config_value()
    with pytest.raises(ExtensionError) as excinfo:
        config.add('value_from_ext', [], 'env', None)
    assert 'already present' in str(excinfo.value)


def test_overrides():
    config = Config(
        {'value1': '1', 'value2': 2, 'value6': {'default': 6}},
        {
            'value2': 999,
            'value3': '999',
            'value5.attr1': 999,
            'value6.attr1': 999,
            'value7': 'abc,def,ghi',
            'value8': 'abc,def,ghi',
        },
    )
    config.add('value1', None, 'env', ())
    config.add('value2', None, 'env', ())
    config.add('value3', 0, 'env', ())
    config.add('value4', 0, 'env', ())
    config.add('value5', {'default': 0}, 'env', ())
    config.add('value6', {'default': 0}, 'env', ())
    config.add('value7', None, 'env', ())
    config.add('value8', [], 'env', ())

    assert config.value1 == '1'
    assert config.value2 == 999
    assert config.value3 == 999
    assert config.value4 == 0
    assert config.value5 == {'attr1': 999}
    assert config.value6 == {'default': 6, 'attr1': 999}
    assert config.value7 == 'abc,def,ghi'
    assert config.value8 == ['abc', 'def', 'ghi']


def test_overrides_boolean():
    config = Config({}, {'value1': '1', 'value2': '0', 'value3': '0'})
    config.add('value1', None, 'env', [bool])
    config.add('value2', None, 'env', [bool])
    config.add('value3', True, 'env', ())

    assert config.value1 is True
    assert config.value2 is False
    assert config.value3 is False


@mock.patch('sphinx.config.logger')
def test_overrides_dict_str(logger):
    config = Config({}, {'spam': 'lobster'})

    config.add('spam', {'ham': 'eggs'}, 'env', {dict, str})

    assert config.spam == {'ham': 'eggs'}

    # assert len(caplog.records) == 1
    # msg = caplog.messages[0]
    assert logger.method_calls
    msg = str(logger.method_calls[0].args[1])
    assert msg == (
        "cannot override dictionary config setting 'spam', "
        "ignoring (use 'spam.key=value' to set individual elements)"
    )


def test_callable_defer():
    config = Config()
    config.add('alias', lambda c: c.master_doc, '', str)

    assert config.master_doc == 'index'
    assert config.alias == 'index'

    config.master_doc = 'contents'
    assert config.alias == 'contents'

    config.master_doc = 'master_doc'
    config.alias = 'spam'
    assert config.alias == 'spam'


@mock.patch('sphinx.config.logger')
def test_errors_warnings(logger, tmp_path):
    # test the error for syntax errors in the config file
    (tmp_path / 'conf.py').write_text('project = \n', encoding='ascii')
    with pytest.raises(ConfigError) as excinfo:
        Config.read(tmp_path, {}, None)
    assert 'conf.py' in str(excinfo.value)

    # test the automatic conversion of 2.x only code in configs
    (tmp_path / 'conf.py').write_text('project = u"Jägermeister"\n', encoding='utf8')
    cfg = Config.read(tmp_path, {}, None)
    assert cfg.project == 'Jägermeister'
    assert logger.called is False


def test_errors_if_setup_is_not_callable(tmp_path, make_app):
    # test the error to call setup() in the config file
    (tmp_path / 'conf.py').write_text('setup = 1', encoding='utf8')
    with pytest.raises(ConfigError) as excinfo:
        make_app(srcdir=tmp_path)
    assert 'callable' in str(excinfo.value)


@pytest.fixture
def make_app_with_empty_project(make_app, tmp_path):
    (tmp_path / 'conf.py').touch()

    def _make_app(*args, **kw):
        kw.setdefault('srcdir', Path(tmp_path))
        return make_app(*args, **kw)

    return _make_app


@mock.patch.object(sphinx, '__display_version__', '1.6.4')
def test_needs_sphinx(make_app_with_empty_project):
    make_app = make_app_with_empty_project
    # micro version
    make_app(confoverrides={'needs_sphinx': '1.6.3'})  # OK: less
    make_app(confoverrides={'needs_sphinx': '1.6.4'})  # OK: equals
    with pytest.raises(VersionRequirementError):
        make_app(confoverrides={'needs_sphinx': '1.6.5'})  # NG: greater

    # minor version
    make_app(confoverrides={'needs_sphinx': '1.5'})  # OK: less
    make_app(confoverrides={'needs_sphinx': '1.6'})  # OK: equals
    with pytest.raises(VersionRequirementError):
        make_app(confoverrides={'needs_sphinx': '1.7'})  # NG: greater

    # major version
    make_app(confoverrides={'needs_sphinx': '0'})  # OK: less
    make_app(confoverrides={'needs_sphinx': '1'})  # OK: equals
    with pytest.raises(VersionRequirementError):
        make_app(confoverrides={'needs_sphinx': '2'})  # NG: greater


@mock.patch('sphinx.config.logger')
def test_config_eol(logger, tmp_path):
    # test config file's eol patterns: LF, CRLF
    configfile = tmp_path / 'conf.py'
    for eol in (b'\n', b'\r\n'):
        configfile.write_bytes(b'project = "spam"' + eol)
        cfg = Config.read(tmp_path, {}, None)
        assert cfg.project == 'spam'
        assert logger.called is False


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={'root_doc': 123, 'language': 'foo', 'primary_domain': None},
)
def test_builtin_conf(app):
    warnings = app.warning.getvalue()
    assert (
        'root_doc'
    ) in warnings, 'override on builtin "root_doc" should raise a type warning'
    assert 'language' not in warnings, (
        'explicitly permitted override on builtin "language" should NOT raise '
        'a type warning'
    )
    assert 'primary_domain' not in warnings, (
        'override to None on builtin "primary_domain" should NOT raise a type '
        'warning'
    )


# example classes for type checking
class A:
    pass


class B(A):
    pass


class C(A):
    pass


# name, default, annotation, actual, warned
TYPECHECK_WARNINGS = [
    ('value1', 'string', None, 123, True),              # wrong type
    ('value2', lambda _: [], None, 123, True),          # lambda with wrong type
    ('value3', lambda _: [], None, [], False),          # lambda with correct type
    ('value4', 100, None, True, True),                  # child type
    ('value5', False, None, True, False),               # parent type
    ('value6', [], None, (), True),                     # other sequence type
    ('value7', 'string', [list], ['foo'], False),       # explicit type annotation
    ('value8', B(), None, C(), False),                  # sibling type
    ('value9', None, None, 'foo', False),               # no default or no annotations
    ('value10', None, None, 123, False),                # no default or no annotations
    ('value11', None, [str], 'bar', False),             # str
    ('value12', 'string', None, 'bar', False),          # str
]  # fmt: skip


@mock.patch('sphinx.config.logger')
@pytest.mark.parametrize(
    ('name', 'default', 'annotation', 'actual', 'warned'),
    TYPECHECK_WARNINGS,
)
def test_check_types(logger, name, default, annotation, actual, warned):
    config = Config({name: actual})
    config.add(name, default, 'env', annotation or ())
    check_confval_types(None, config)
    assert logger.warning.called == warned


TYPECHECK_WARNING_MESSAGES = [
    (
        'value1',
        'string',
        [str],
        ['foo', 'bar'],
        "The config value `value1' has type `list'; expected `str'.",
    ),
    (
        'value1',
        'string',
        [str, int],
        ['foo', 'bar'],
        "The config value `value1' has type `list'; expected `int' or `str'.",
    ),
    (
        'value1',
        'string',
        [str, int, tuple],
        ['foo', 'bar'],
        "The config value `value1' has type `list'; expected `int', `str', or `tuple'.",
    ),
]


@mock.patch('sphinx.config.logger')
@pytest.mark.parametrize(
    ('name', 'default', 'annotation', 'actual', 'message'),
    TYPECHECK_WARNING_MESSAGES,
)
def test_conf_warning_message(logger, name, default, annotation, actual, message):
    config = Config({name: actual})
    config.add(name, default, False, annotation or ())
    check_confval_types(None, config)
    assert logger.warning.called
    assert logger.warning.call_args[0][0] == message


@mock.patch('sphinx.config.logger')
def test_check_enum(logger):
    config = Config()
    config.add('value', 'default', False, ENUM('default', 'one', 'two'))
    check_confval_types(None, config)
    logger.warning.assert_not_called()  # not warned


@mock.patch('sphinx.config.logger')
def test_check_enum_failed(logger):
    config = Config({'value': 'invalid'})
    config.add('value', 'default', False, ENUM('default', 'one', 'two'))
    check_confval_types(None, config)
    assert logger.warning.called


@mock.patch('sphinx.config.logger')
def test_check_enum_for_list(logger):
    config = Config({'value': ['one', 'two']})
    config.add('value', 'default', False, ENUM('default', 'one', 'two'))
    check_confval_types(None, config)
    logger.warning.assert_not_called()  # not warned


@mock.patch('sphinx.config.logger')
def test_check_enum_for_list_failed(logger):
    config = Config({'value': ['one', 'two', 'invalid']})
    config.add('value', 'default', False, ENUM('default', 'one', 'two'))
    check_confval_types(None, config)
    assert logger.warning.called


@mock.patch('sphinx.config.logger')
def test_check_any(logger):
    config = Config({'value': None})
    config.add('value', 'default', '', Any)
    check_confval_types(None, config)
    logger.warning.assert_not_called()  # not warned


nitpick_warnings = [
    'WARNING: py:const reference target not found: prefix.anything.postfix',
    'WARNING: py:class reference target not found: prefix.anything',
    'WARNING: py:class reference target not found: anything.postfix',
    'WARNING: js:class reference target not found: prefix.anything.postfix',
]


@pytest.mark.sphinx('html', testroot='nitpicky-warnings')
def test_nitpick_base(app):
    app.build(force_all=True)

    warning = app.warning.getvalue().strip().split('\n')
    for actual, expected in zip(warning, nitpick_warnings, strict=True):
        assert expected in actual


@pytest.mark.sphinx(
    'html',
    testroot='nitpicky-warnings',
    confoverrides={
        'nitpick_ignore': {
            ('py:const', 'prefix.anything.postfix'),
            ('py:class', 'prefix.anything'),
            ('py:class', 'anything.postfix'),
            ('js:class', 'prefix.anything.postfix'),
        },
    },
)
def test_nitpick_ignore(app):
    app.build(force_all=True)
    assert not len(app.warning.getvalue().strip())


@pytest.mark.sphinx(
    'html',
    testroot='nitpicky-warnings',
    confoverrides={
        'nitpick_ignore_regex': [
            (r'py:.*', r'.*postfix'),
            (r'.*:class', r'prefix.*'),
        ],
    },
)
def test_nitpick_ignore_regex1(app):
    app.build(force_all=True)
    assert not len(app.warning.getvalue().strip())


@pytest.mark.sphinx(
    'html',
    testroot='nitpicky-warnings',
    confoverrides={
        'nitpick_ignore_regex': [
            (r'py:.*', r'prefix.*'),
            (r'.*:class', r'.*postfix'),
        ],
    },
)
def test_nitpick_ignore_regex2(app):
    app.build(force_all=True)
    assert not len(app.warning.getvalue().strip())


@pytest.mark.sphinx(
    'html',
    testroot='nitpicky-warnings',
    confoverrides={
        'nitpick_ignore_regex': [
            # None of these should match
            (r'py:', r'.*'),
            (r':class', r'.*'),
            (r'', r'.*'),
            (r'.*', r'anything'),
            (r'.*', r'prefix'),
            (r'.*', r'postfix'),
            (r'.*', r''),
        ],
    },
)
def test_nitpick_ignore_regex_fullmatch(app):
    app.build(force_all=True)

    warning = app.warning.getvalue().strip().split('\n')
    for actual, expected in zip(warning, nitpick_warnings, strict=True):
        assert expected in actual


def test_conf_py_language_none(tmp_path):
    """Regression test for #10474."""
    # Given a conf.py file with language = None
    (tmp_path / 'conf.py').write_text('language = None', encoding='utf-8')

    # When we load conf.py into a Config object
    cfg = Config.read(tmp_path, {}, None)

    # Then the language is coerced to English
    assert cfg.language == 'en'


@mock.patch('sphinx.config.logger')
def test_conf_py_language_none_warning(logger, tmp_path):
    """Regression test for #10474."""
    # Given a conf.py file with language = None
    (tmp_path / 'conf.py').write_text('language = None', encoding='utf-8')

    # When we load conf.py into a Config object
    Config.read(tmp_path, {}, None)

    # Then a warning is raised
    assert logger.warning.called
    assert logger.warning.call_args[0][0] == (
        "Invalid configuration value found: 'language = None'. "
        'Update your configuration to a valid language code. '
        "Falling back to 'en' (English)."
    )


def test_conf_py_no_language(tmp_path):
    """Regression test for #10474."""
    # Given a conf.py file with no language attribute
    (tmp_path / 'conf.py').touch()

    # When we load conf.py into a Config object
    cfg = Config.read(tmp_path, {}, None)

    # Then the language is coerced to English
    assert cfg.language == 'en'


def test_conf_py_nitpick_ignore_list(tmp_path):
    """Regression test for #11355."""
    # Given a conf.py file with no language attribute
    (tmp_path / 'conf.py').touch()

    # When we load conf.py into a Config object
    cfg = Config.read(tmp_path, {}, None)

    # Then the default nitpick_ignore[_regex] is an empty list
    assert cfg.nitpick_ignore == []
    assert cfg.nitpick_ignore_regex == []


@pytest.fixture(
    params=[
        # test with SOURCE_DATE_EPOCH unset: no modification
        None,
        # test with SOURCE_DATE_EPOCH set: copyright year should be updated
        1293840000,
        1293839999,
    ]
)
def source_date_year(request, monkeypatch):
    sde = request.param
    with monkeypatch.context() as m:
        if sde:
            m.setenv('SOURCE_DATE_EPOCH', str(sde))
            yield time.gmtime(sde).tm_year
        else:
            m.delenv('SOURCE_DATE_EPOCH', raising=False)
            yield None


@pytest.mark.sphinx('html', testroot='copyright-multiline')
def test_multi_line_copyright(source_date_year, app):
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf-8')

    if source_date_year is None:
        # check the copyright footer line by line (empty lines ignored)
        assert '  &#169; Copyright 2006.<br/>\n' in content
        assert '  &#169; Copyright 2006-2009, Alice.<br/>\n' in content
        assert '  &#169; Copyright 2010-2013, Bob.<br/>\n' in content
        assert '  &#169; Copyright 2014-2017, Charlie.<br/>\n' in content
        assert '  &#169; Copyright 2018-2021, David.<br/>\n' in content
        assert '  &#169; Copyright 2022-2025, Eve.' in content

        # check the raw copyright footer block (empty lines included)
        assert (
            '      &#169; Copyright 2006.<br/>\n'
            '    \n'
            '      &#169; Copyright 2006-2009, Alice.<br/>\n'
            '    \n'
            '      &#169; Copyright 2010-2013, Bob.<br/>\n'
            '    \n'
            '      &#169; Copyright 2014-2017, Charlie.<br/>\n'
            '    \n'
            '      &#169; Copyright 2018-2021, David.<br/>\n'
            '    \n'
            '      &#169; Copyright 2022-2025, Eve.'
        ) in content
    else:
        # check the copyright footer line by line (empty lines ignored)
        assert f'  &#169; Copyright {source_date_year}.<br/>\n' in content
        assert f'  &#169; Copyright 2006-{source_date_year}, Alice.<br/>\n' in content
        assert f'  &#169; Copyright 2010-{source_date_year}, Bob.<br/>\n' in content
        assert f'  &#169; Copyright 2014-{source_date_year}, Charlie.<br/>\n' in content
        assert f'  &#169; Copyright 2018-{source_date_year}, David.<br/>\n' in content
        assert f'  &#169; Copyright 2022-{source_date_year}, Eve.' in content

        # check the raw copyright footer block (empty lines included)
        assert (
            f'      &#169; Copyright {source_date_year}.<br/>\n'
            f'    \n'
            f'      &#169; Copyright 2006-{source_date_year}, Alice.<br/>\n'
            f'    \n'
            f'      &#169; Copyright 2010-{source_date_year}, Bob.<br/>\n'
            f'    \n'
            f'      &#169; Copyright 2014-{source_date_year}, Charlie.<br/>\n'
            f'    \n'
            f'      &#169; Copyright 2018-{source_date_year}, David.<br/>\n'
            f'    \n'
            f'      &#169; Copyright 2022-{source_date_year}, Eve.'
        ) in content


@pytest.mark.parametrize(
    ('conf_copyright', 'expected_copyright'),
    [
        ('1970', '{current_year}'),
        # https://github.com/sphinx-doc/sphinx/issues/11913
        ('1970-1990', '1970-{current_year}'),
        ('1970-1990 Alice', '1970-{current_year} Alice'),
    ],
)
def test_correct_copyright_year(conf_copyright, expected_copyright, source_date_year):
    config = Config({}, {'copyright': conf_copyright})
    correct_copyright_year(_app=None, config=config)
    actual_copyright = config['copyright']

    if source_date_year is None:
        expected_copyright = conf_copyright
    else:
        expected_copyright = expected_copyright.format(current_year=source_date_year)
    assert actual_copyright == expected_copyright


def test_gettext_compact_command_line_true():
    config = Config({}, {'gettext_compact': '1'})
    config.add('gettext_compact', True, '', {bool, str})
    _gettext_compact_validator(..., config)

    # regression test for #8549 (-D gettext_compact=1)
    assert config.gettext_compact is True


def test_gettext_compact_command_line_false():
    config = Config({}, {'gettext_compact': '0'})
    config.add('gettext_compact', True, '', {bool, str})
    _gettext_compact_validator(..., config)

    # regression test for #8549 (-D gettext_compact=0)
    assert config.gettext_compact is False


def test_gettext_compact_command_line_str():
    config = Config({}, {'gettext_compact': 'spam'})
    config.add('gettext_compact', True, '', {bool, str})
    _gettext_compact_validator(..., config)

    # regression test for #8549 (-D gettext_compact=spam)
    assert config.gettext_compact == 'spam'


def test_root_doc_and_master_doc_are_synchronized():
    c = Config()
    assert c.master_doc == 'index'
    assert c.root_doc == c.master_doc

    c = Config()
    c.master_doc = '1234'
    assert c.master_doc == '1234'
    assert c.root_doc == c.master_doc

    c = Config()
    c.root_doc = '1234'
    assert c.master_doc == '1234'
    assert c.root_doc == c.master_doc
