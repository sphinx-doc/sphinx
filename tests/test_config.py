# -*- coding: utf-8 -*-
"""
    test_config
    ~~~~~~~~~~~

    Test the sphinx.config.Config class and its handling in the
    Application class.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from six import PY3, iteritems
import mock

from util import TestApp, with_app, gen_with_app, with_tempdir, \
    raises, raises_msg, assert_in, assert_not_in

import sphinx
from sphinx.config import Config
from sphinx.errors import ExtensionError, ConfigError, VersionRequirementError


@with_app(confoverrides={'master_doc': 'master', 'nonexisting_value': 'True',
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
    raises(AttributeError, getattr, cfg, '_value')
    raises(AttributeError, getattr, cfg, 'nonexisting_value')

    # non-value attributes are deleted from the namespace
    raises(AttributeError, getattr, cfg, 'sys')

    # setting attributes
    cfg.project = 'Foo'
    assert cfg.project == 'Foo'

    # alternative access via item interface
    cfg['project'] = 'Sphinx Tests'
    assert cfg['project'] == cfg.project == 'Sphinx Tests'


@with_app()
def test_extension_values(app, status, warning):
    cfg = app.config

    # default value
    assert cfg.value_from_ext == []
    # non-default value
    assert cfg.value_from_conf_py == 84

    # no duplicate values allowed
    raises_msg(ExtensionError, 'already present', app.add_config_value,
               'html_title', 'x', True)
    raises_msg(ExtensionError, 'already present', app.add_config_value,
               'value_from_ext', 'x', True)


@with_tempdir
def test_errors_warnings(dir):
    # test the error for syntax errors in the config file
    (dir / 'conf.py').write_text(u'project = \n', encoding='ascii')
    raises_msg(ConfigError, 'conf.py', Config, dir, 'conf.py', {}, None)

    # test the automatic conversion of 2.x only code in configs
    (dir / 'conf.py').write_text(
        u'# -*- coding: utf-8\n\nproject = u"Jägermeister"\n',
        encoding='utf-8')
    cfg = Config(dir, 'conf.py', {}, None)
    cfg.init_values(lambda warning: 1/0)
    assert cfg.project == u'Jägermeister'

    # test the warning for bytestrings with non-ascii content
    # bytestrings with non-ascii content are a syntax error in python3 so we
    # skip the test there
    if PY3:
        return
    (dir / 'conf.py').write_text(
        u'# -*- coding: latin-1\nproject = "fooä"\n', encoding='latin-1')
    cfg = Config(dir, 'conf.py', {}, None)
    warned = [False]

    def warn(msg):
        warned[0] = True

    cfg.check_unicode(warn)
    assert warned[0]


@with_tempdir
def test_errors_if_setup_is_not_callable(dir):
    # test the error to call setup() in the config file
    (dir / 'conf.py').write_text(u'setup = 1')
    raises_msg(ConfigError, 'callable', TestApp, srcdir=dir)


@mock.patch.object(sphinx, '__display_version__', '1.3.4')
def test_needs_sphinx():
    # micro version
    app = TestApp(confoverrides={'needs_sphinx': '1.3.3'})  # OK: less
    app.cleanup()
    app = TestApp(confoverrides={'needs_sphinx': '1.3.4'})  # OK: equals
    app.cleanup()
    raises(VersionRequirementError, TestApp,
           confoverrides={'needs_sphinx': '1.3.5'})  # NG: greater

    # minor version
    app = TestApp(confoverrides={'needs_sphinx': '1.2'})  # OK: less
    app.cleanup()
    app = TestApp(confoverrides={'needs_sphinx': '1.3'})  # OK: equals
    app.cleanup()
    raises(VersionRequirementError, TestApp,
           confoverrides={'needs_sphinx': '1.4'})  # NG: greater

    # major version
    app = TestApp(confoverrides={'needs_sphinx': '0'})  # OK: less
    app.cleanup()
    app = TestApp(confoverrides={'needs_sphinx': '1'})  # OK: equals
    app.cleanup()
    raises(VersionRequirementError, TestApp,
           confoverrides={'needs_sphinx': '2'})  # NG: greater


@with_tempdir
def test_config_eol(tmpdir):
    # test config file's eol patterns: LF, CRLF
    configfile = tmpdir / 'conf.py'
    for eol in (b'\n', b'\r\n'):
        configfile.write_bytes(b'project = "spam"' + eol)
        cfg = Config(tmpdir, 'conf.py', {}, None)
        cfg.init_values(lambda warning: 1/0)
        assert cfg.project == u'spam'


@with_app(confoverrides={'master_doc': 123,
                         'language': 'foo',
                         'primary_domain': None})
def test_builtin_conf(app, status, warning):
    warnings = warning.getvalue()
    assert_in('master_doc', warnings,
              'override on builtin "master_doc" should raise a type warning')
    assert_not_in('language', warnings, 'explicitly permitted '
                  'override on builtin "language" should NOT raise a type warning')
    assert_not_in('primary_domain', warnings, 'override to None on builtin '
                  '"primary_domain" should NOT raise a type warning')


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
    'value11': True,
    'value12': False,
    'value13': False,
    'value14': False,
    'value15': False,
    'value16': False,
}


@gen_with_app(testroot='config')
def test_gen_check_types(app, status, warning):
    if PY3:
        TYPECHECK_WARNINGS['value11'] = False

    for key, should in iteritems(TYPECHECK_WARNINGS):
        yield assert_in if should else assert_not_in, key, warning.getvalue(), (
            'override on "%s" should%s raise a type warning' %
            (key, '' if should else ' NOT')
        )


@with_app(testroot='config')
def test_check_enum(app, status, warning):
    assert "The config value `value17` has to be a one of ('default', 'one', 'two'), " \
           not in warning.getvalue()


@with_app(testroot='config', confoverrides={'value17': 'invalid'})
def test_check_enum_failed(app, status, warning):
    assert "The config value `value17` has to be a one of ('default', 'one', 'two'), " \
           "but `invalid` is given." in warning.getvalue()
