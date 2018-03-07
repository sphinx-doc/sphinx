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
from six import PY3, iteritems

import sphinx
from sphinx.config import Config
from sphinx.errors import ExtensionError, ConfigError, VersionRequirementError
from sphinx.testing.path import path


@pytest.mark.sphinx(confoverrides={
    'master_doc': 'master',
    'nonexisting_value': 'True',
    'latex_elements.docclass': 'scrartcl',
    'modindex_common_prefix': 'path1,path2'})
def test_core_config(app, status, warning):
    cfg = app.config

    # simple values
    assert 'project' in cfg.__dict__
    assert cfg.project == 'Sphinx <Tests>'
    assert cfg.templates_path == ['_templates']

    # overrides
    assert cfg.master_doc == 'master'
    assert cfg.latex_elements['docclass'] == 'scrartcl'
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


def test_extension_values(app, status, warning):
    cfg = app.config

    # default value
    assert cfg.value_from_ext == []
    # non-default value
    assert cfg.value_from_conf_py == 84

    # no duplicate values allowed
    with pytest.raises(ExtensionError) as excinfo:
        app.add_config_value('html_title', 'x', True)
    assert 'already present' in str(excinfo.value)
    with pytest.raises(ExtensionError) as excinfo:
        app.add_config_value('value_from_ext', 'x', True)
    assert 'already present' in str(excinfo.value)


@mock.patch("sphinx.config.logger")
def test_errors_warnings(logger, tempdir):
    # test the error for syntax errors in the config file
    (tempdir / 'conf.py').write_text(u'project = \n', encoding='ascii')
    with pytest.raises(ConfigError) as excinfo:
        Config(tempdir, 'conf.py', {}, None)
    assert 'conf.py' in str(excinfo.value)

    # test the automatic conversion of 2.x only code in configs
    (tempdir / 'conf.py').write_text(
        u'# -*- coding: utf-8\n\nproject = u"Jägermeister"\n',
        encoding='utf-8')
    cfg = Config(tempdir, 'conf.py', {}, None)
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
    cfg = Config(tempdir, 'conf.py', {}, None)

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
    app = make_app(confoverrides={'needs_sphinx': '1.3.3'})  # OK: less
    app.cleanup()
    app = make_app(confoverrides={'needs_sphinx': '1.3.4'})  # OK: equals
    app.cleanup()
    with pytest.raises(VersionRequirementError):
        make_app(confoverrides={'needs_sphinx': '1.3.5'})  # NG: greater

    # minor version
    app = make_app(confoverrides={'needs_sphinx': '1.2'})  # OK: less
    app.cleanup()
    app = make_app(confoverrides={'needs_sphinx': '1.3'})  # OK: equals
    app.cleanup()
    with pytest.raises(VersionRequirementError):
        make_app(confoverrides={'needs_sphinx': '1.4'})  # NG: greater

    # major version
    app = make_app(confoverrides={'needs_sphinx': '0'})  # OK: less
    app.cleanup()
    app = make_app(confoverrides={'needs_sphinx': '1'})  # OK: equals
    app.cleanup()
    with pytest.raises(VersionRequirementError):
        make_app(confoverrides={'needs_sphinx': '2'})  # NG: greater


@mock.patch("sphinx.config.logger")
def test_config_eol(logger, tempdir):
    # test config file's eol patterns: LF, CRLF
    configfile = tempdir / 'conf.py'
    for eol in (b'\n', b'\r\n'):
        configfile.write_bytes(b'project = "spam"' + eol)
        cfg = Config(tempdir, 'conf.py', {}, None)
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


# See roots/test-config/conf.py.
TYPECHECK_WARNINGS = {
    'value1': True,
    'value2': True,
    'value3': False,
    'value4': True,
    'value5': False,
    'value6': True,
    'value7': False,
    'value8': False,
    'value9': False,
    'value10': False,
    'value11': False if PY3 else True,
    'value12': False,
    'value13': False,
    'value14': False,
    'value15': False,
    'value16': False,
}


@pytest.mark.parametrize("key,should", iteritems(TYPECHECK_WARNINGS))
@pytest.mark.sphinx(testroot='config')
def test_check_types(warning, key, should):
    warn = warning.getvalue()
    if should:
        assert key in warn, (
            'override on "%s" should raise a type warning' % key
        )
    else:
        assert key not in warn, (
            'override on "%s" should NOT raise a type warning' % key
        )


@pytest.mark.sphinx(testroot='config')
def test_check_enum(app, status, warning):
    assert "The config value `value17` has to be a one of ('default', 'one', 'two'), " \
           not in warning.getvalue()


@pytest.mark.sphinx(testroot='config', confoverrides={'value17': 'invalid'})
def test_check_enum_failed(app, status, warning):
    assert "The config value `value17` has to be a one of ('default', 'one', 'two'), " \
           "but `invalid` is given." in warning.getvalue()


@pytest.mark.sphinx(testroot='config', confoverrides={'value17': ['one', 'two']})
def test_check_enum_for_list(app, status, warning):
    assert "The config value `value17` has to be a one of ('default', 'one', 'two'), " \
           not in warning.getvalue()


@pytest.mark.sphinx(testroot='config', confoverrides={'value17': ['one', 'two', 'invalid']})
def test_check_enum_for_list_failed(app, status, warning):
    assert "The config value `value17` has to be a one of ('default', 'one', 'two'), " \
           "but `['one', 'two', 'invalid']` is given." in warning.getvalue()
