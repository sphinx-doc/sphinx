"""
    test_config
    ~~~~~~~~~~~

    Test the sphinx.config.Config class and its handling in the
    Application class.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest import mock

import pytest

import sphinx
from sphinx.config import ENUM, Config, check_confval_types
from sphinx.errors import ConfigError, ExtensionError, VersionRequirementError
from sphinx.testing.path import path


@pytest.mark.sphinx(testroot='config', confoverrides={
    'root_doc': 'root',
    'nonexisting_value': 'True',
    'latex_elements.maketitle': 'blah blah blah',
    'modindex_common_prefix': 'path1,path2'})
def test_core_config(app, status, warning):
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
    assert 'locale_dirs' not in cfg.__dict__
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
        getattr(cfg, '_value')
    with pytest.raises(AttributeError):
        getattr(cfg, 'nonexisting_value')

    # non-value attributes are deleted from the namespace
    with pytest.raises(AttributeError):
        getattr(cfg, 'sys')

    # setting attributes
    cfg.project = 'Foo'
    assert cfg.project == 'Foo'

    # alternative access via item interface
    cfg['project'] = 'Sphinx Tests'
    assert cfg['project'] == cfg.project == 'Sphinx Tests'


def test_config_not_found(tempdir):
    with pytest.raises(ConfigError):
        Config.read(tempdir)


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
    config = Config({'value1': '1', 'value2': 2, 'value6': {'default': 6}},
                    {'value2': 999, 'value3': '999', 'value5.attr1': 999, 'value6.attr1': 999,
                     'value7': 'abc,def,ghi', 'value8': 'abc,def,ghi'})
    config.add('value1', None, 'env', ())
    config.add('value2', None, 'env', ())
    config.add('value3', 0, 'env', ())
    config.add('value4', 0, 'env', ())
    config.add('value5', {'default': 0}, 'env', ())
    config.add('value6', {'default': 0}, 'env', ())
    config.add('value7', None, 'env', ())
    config.add('value8', [], 'env', ())
    config.init_values()

    assert config.value1 == '1'
    assert config.value2 == 999
    assert config.value3 == 999
    assert config.value4 == 0
    assert config.value5 == {'attr1': 999}
    assert config.value6 == {'default': 6, 'attr1': 999}
    assert config.value7 == 'abc,def,ghi'
    assert config.value8 == ['abc', 'def', 'ghi']


def test_overrides_boolean():
    config = Config({}, {'value1': '1',
                         'value2': '0',
                         'value3': '0'})
    config.add('value1', None, 'env', [bool])
    config.add('value2', None, 'env', [bool])
    config.add('value3', True, 'env', ())
    config.init_values()

    assert config.value1 is True
    assert config.value2 is False
    assert config.value3 is False


@mock.patch("sphinx.config.logger")
def test_errors_warnings(logger, tempdir):
    # test the error for syntax errors in the config file
    (tempdir / 'conf.py').write_text('project = \n', encoding='ascii')
    with pytest.raises(ConfigError) as excinfo:
        Config.read(tempdir, {}, None)
    assert 'conf.py' in str(excinfo.value)

    # test the automatic conversion of 2.x only code in configs
    (tempdir / 'conf.py').write_text('project = u"Jägermeister"\n')
    cfg = Config.read(tempdir, {}, None)
    cfg.init_values()
    assert cfg.project == 'Jägermeister'
    assert logger.called is False


def test_errors_if_setup_is_not_callable(tempdir, make_app):
    # test the error to call setup() in the config file
    (tempdir / 'conf.py').write_text('setup = 1')
    with pytest.raises(ConfigError) as excinfo:
        make_app(srcdir=tempdir)
    assert 'callable' in str(excinfo.value)


@pytest.fixture
def make_app_with_empty_project(make_app, tempdir):
    (tempdir / 'conf.py').write_text('')

    def _make_app(*args, **kw):
        kw.setdefault('srcdir', path(tempdir))
        return make_app(*args, **kw)
    return _make_app


@mock.patch.object(sphinx, '__display_version__', '1.3.4')
def test_needs_sphinx(make_app_with_empty_project):
    make_app = make_app_with_empty_project
    # micro version
    make_app(confoverrides={'needs_sphinx': '1.3.3'})  # OK: less
    make_app(confoverrides={'needs_sphinx': '1.3.4'})  # OK: equals
    with pytest.raises(VersionRequirementError):
        make_app(confoverrides={'needs_sphinx': '1.3.5'})  # NG: greater

    # minor version
    make_app(confoverrides={'needs_sphinx': '1.2'})  # OK: less
    make_app(confoverrides={'needs_sphinx': '1.3'})  # OK: equals
    with pytest.raises(VersionRequirementError):
        make_app(confoverrides={'needs_sphinx': '1.4'})  # NG: greater

    # major version
    make_app(confoverrides={'needs_sphinx': '0'})  # OK: less
    make_app(confoverrides={'needs_sphinx': '1'})  # OK: equals
    with pytest.raises(VersionRequirementError):
        make_app(confoverrides={'needs_sphinx': '2'})  # NG: greater


@mock.patch("sphinx.config.logger")
def test_config_eol(logger, tempdir):
    # test config file's eol patterns: LF, CRLF
    configfile = tempdir / 'conf.py'
    for eol in (b'\n', b'\r\n'):
        configfile.write_bytes(b'project = "spam"' + eol)
        cfg = Config.read(tempdir, {}, None)
        cfg.init_values()
        assert cfg.project == 'spam'
        assert logger.called is False


@pytest.mark.sphinx(confoverrides={'root_doc': 123,
                                   'language': 'foo',
                                   'primary_domain': None})
def test_builtin_conf(app, status, warning):
    warnings = warning.getvalue()
    assert 'root_doc' in warnings, (
        'override on builtin "root_doc" should raise a type warning')
    assert 'language' not in warnings, (
        'explicitly permitted override on builtin "language" should NOT raise '
        'a type warning')
    assert 'primary_domain' not in warnings, (
        'override to None on builtin "primary_domain" should NOT raise a type '
        'warning')


# example classes for type checking
class A:
    pass


class B(A):
    pass


class C(A):
    pass


# name, default, annotation, actual, warned
TYPECHECK_WARNINGS = [
    ('value1', 'string', None, 123, True),                      # wrong type
    ('value2', lambda _: [], None, 123, True),                  # lambda with wrong type
    ('value3', lambda _: [], None, [], False),                  # lambda with correct type
    ('value4', 100, None, True, True),                          # child type
    ('value5', False, None, True, False),                       # parent type
    ('value6', [], None, (), True),                             # other sequence type
    ('value7', 'string', [list], ['foo'], False),               # explicit type annotation
    ('value8', B(), None, C(), False),                          # sibling type
    ('value9', None, None, 'foo', False),                       # no default or no annotations
    ('value10', None, None, 123, False),                        # no default or no annotations
    ('value11', None, [str], 'bar', False),                     # str
    ('value12', 'string', None, 'bar', False),                  # str
]


@mock.patch("sphinx.config.logger")
@pytest.mark.parametrize("name,default,annotation,actual,warned", TYPECHECK_WARNINGS)
def test_check_types(logger, name, default, annotation, actual, warned):
    config = Config({name: actual})
    config.add(name, default, 'env', annotation or ())
    config.init_values()
    check_confval_types(None, config)
    assert logger.warning.called == warned


TYPECHECK_WARNING_MESSAGES = [
    ('value1', 'string', [str], ['foo', 'bar'],
        "The config value `value1' has type `list'; expected `str'."),
    ('value1', 'string', [str, int], ['foo', 'bar'],
        "The config value `value1' has type `list'; expected `str' or `int'."),
    ('value1', 'string', [str, int, tuple], ['foo', 'bar'],
        "The config value `value1' has type `list'; expected `str', `int', or `tuple'."),
]


@mock.patch("sphinx.config.logger")
@pytest.mark.parametrize("name,default,annotation,actual,message", TYPECHECK_WARNING_MESSAGES)
def test_conf_warning_message(logger, name, default, annotation, actual, message):
    config = Config({name: actual})
    config.add(name, default, False, annotation or ())
    config.init_values()
    check_confval_types(None, config)
    assert logger.warning.called
    assert logger.warning.call_args[0][0] == message


@mock.patch("sphinx.config.logger")
def test_check_enum(logger):
    config = Config()
    config.add('value', 'default', False, ENUM('default', 'one', 'two'))
    config.init_values()
    check_confval_types(None, config)
    logger.warning.assert_not_called()  # not warned


@mock.patch("sphinx.config.logger")
def test_check_enum_failed(logger):
    config = Config({'value': 'invalid'})
    config.add('value', 'default', False, ENUM('default', 'one', 'two'))
    config.init_values()
    check_confval_types(None, config)
    assert logger.warning.called


@mock.patch("sphinx.config.logger")
def test_check_enum_for_list(logger):
    config = Config({'value': ['one', 'two']})
    config.add('value', 'default', False, ENUM('default', 'one', 'two'))
    config.init_values()
    check_confval_types(None, config)
    logger.warning.assert_not_called()  # not warned


@mock.patch("sphinx.config.logger")
def test_check_enum_for_list_failed(logger):
    config = Config({'value': ['one', 'two', 'invalid']})
    config.add('value', 'default', False, ENUM('default', 'one', 'two'))
    config.init_values()
    check_confval_types(None, config)
    assert logger.warning.called


nitpick_warnings = [
    "WARNING: py:const reference target not found: prefix.anything.postfix",
    "WARNING: py:class reference target not found: prefix.anything",
    "WARNING: py:class reference target not found: anything.postfix",
    "WARNING: js:class reference target not found: prefix.anything.postfix",
]


@pytest.mark.sphinx(testroot='nitpicky-warnings')
def test_nitpick_base(app, status, warning):
    app.builder.build_all()

    warning = warning.getvalue().strip().split('\n')
    assert len(warning) == len(nitpick_warnings)
    for actual, expected in zip(warning, nitpick_warnings):
        assert expected in actual


@pytest.mark.sphinx(testroot='nitpicky-warnings', confoverrides={
    'nitpick_ignore': [
        ('py:const', 'prefix.anything.postfix'),
        ('py:class', 'prefix.anything'),
        ('py:class', 'anything.postfix'),
        ('js:class', 'prefix.anything.postfix'),
    ],
})
def test_nitpick_ignore(app, status, warning):
    app.builder.build_all()
    assert not len(warning.getvalue().strip())


@pytest.mark.sphinx(testroot='nitpicky-warnings', confoverrides={
    'nitpick_ignore_regex': [
        (r'py:.*', r'.*postfix'),
        (r'.*:class', r'prefix.*'),
    ]
})
def test_nitpick_ignore_regex1(app, status, warning):
    app.builder.build_all()
    assert not len(warning.getvalue().strip())


@pytest.mark.sphinx(testroot='nitpicky-warnings', confoverrides={
    'nitpick_ignore_regex': [
        (r'py:.*', r'prefix.*'),
        (r'.*:class', r'.*postfix'),
    ]
})
def test_nitpick_ignore_regex2(app, status, warning):
    app.builder.build_all()
    assert not len(warning.getvalue().strip())


@pytest.mark.sphinx(testroot='nitpicky-warnings', confoverrides={
    'nitpick_ignore_regex': [
        # None of these should match
        (r'py:', r'.*'),
        (r':class', r'.*'),
        (r'', r'.*'),
        (r'.*', r'anything'),
        (r'.*', r'prefix'),
        (r'.*', r'postfix'),
        (r'.*', r''),
    ]
})
def test_nitpick_ignore_regex_fullmatch(app, status, warning):
    app.builder.build_all()

    warning = warning.getvalue().strip().split('\n')
    assert len(warning) == len(nitpick_warnings)
    for actual, expected in zip(warning, nitpick_warnings):
        assert expected in actual
