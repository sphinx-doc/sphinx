# -*- coding: utf-8 -*-
"""
    test_config
    ~~~~~~~~~~~

    Test the sphinx.config.Config class and its handling in the
    Application class.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import mock
import pytest
from six import PY3

import sphinx
from sphinx.config import Config, ENUM, string_classes, check_confval_types
from sphinx.errors import ExtensionError, ConfigError, VersionRequirementError
from sphinx.testing.path import path


@pytest.mark.sphinx(testroot='config', confoverrides={
    'master_doc': 'master',
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
    assert cfg.master_doc == 'master'
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


def test_extension_values():
    config = Config()

    # check standard settings
    assert config.master_doc == 'contents'

    # can't override it by add_config_value()
    with pytest.raises(ExtensionError) as excinfo:
        config.add('master_doc', 'index', 'env', None)
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


@mock.patch("sphinx.config.logger")
def test_errors_warnings(logger, tempdir):
    # test the error for syntax errors in the config file
    (tempdir / 'conf.py').write_text(u'project = \n', encoding='ascii')
    with pytest.raises(ConfigError) as excinfo:
        Config.read(tempdir, {}, None)
    assert 'conf.py' in str(excinfo.value)

    # test the automatic conversion of 2.x only code in configs
    (tempdir / 'conf.py').write_text(
        u'# -*- coding: utf-8\n\nproject = u"Jägermeister"\n',
        encoding='utf-8')
    cfg = Config.read(tempdir, {}, None)
    cfg.init_values()
    assert cfg.project == u'Jägermeister'
    assert logger.called is False

    # test the warning for bytestrings with non-ascii content
    # bytestrings with non-ascii content are a syntax error in python3 so we
    # skip the test there
    if PY3:
        return
    (tempdir / 'conf.py').write_text(
        u'# -*- coding: latin-1\nproject = "fooä"\n', encoding='latin-1')
    cfg = Config.read(tempdir, {}, None)

    assert logger.warning.called is False
    cfg.check_unicode()
    assert logger.warning.called is True


def test_errors_if_setup_is_not_callable(tempdir, make_app):
    # test the error to call setup() in the config file
    (tempdir / 'conf.py').write_text(u'setup = 1')
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
        assert cfg.project == u'spam'
        assert logger.called is False


@pytest.mark.sphinx(confoverrides={'master_doc': 123,
                                   'language': 'foo',
                                   'primary_domain': None})
def test_builtin_conf(app, status, warning):
    warnings = warning.getvalue()
    assert 'master_doc' in warnings, (
        'override on builtin "master_doc" should raise a type warning')
    assert 'language' not in warnings, (
        'explicitly permitted override on builtin "language" should NOT raise '
        'a type warning')
    assert 'primary_domain' not in warnings, (
        'override to None on builtin "primary_domain" should NOT raise a type '
        'warning')


# example classes for type checking
class A(object):
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
    ('value11', None, [str], u'bar', False if PY3 else True),   # str vs unicode
    ('value12', 'string', None, u'bar', False),                 # str vs unicode
    ('value13', None, string_classes, 'bar', False),            # string_classes
    ('value14', None, string_classes, u'bar', False),           # string_classes
    ('value15', u'unicode', None, 'bar', False),                # str vs unicode
    ('value16', u'unicode', None, u'bar', False),               # str vs unicode
]


@mock.patch("sphinx.config.logger")
@pytest.mark.parametrize("name,default,annotation,actual,warned", TYPECHECK_WARNINGS)
def test_check_types(logger, name, default, annotation, actual, warned):
    config = Config({name: actual})
    config.add(name, default, 'env', annotation or ())
    config.init_values()
    check_confval_types(None, config)
    assert logger.warning.called == warned


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
    logger.warning.assert_called()


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
    logger.warning.assert_called()
