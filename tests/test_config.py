# -*- coding: utf-8 -*-
"""
    test_config
    ~~~~~~~~~~~

    Test the sphinx.config.Config class and its handling in the
    Application class.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

from util import *

from sphinx.application import ExtensionError


@with_testapp(confoverrides={'master_doc': 'master', 'nonexisting_value': 'True'})
def test_core_config(app):
    cfg = app.config

    # simple values
    assert 'project' in cfg.__dict__
    assert cfg.project == 'Sphinx Tests'
    assert cfg.templates_path == ['_templates']

    # overrides
    assert cfg.master_doc == 'master'

    # simple default values
    assert 'exclude_dirs' not in cfg.__dict__
    assert cfg.exclude_dirs == []
    assert cfg.show_authors == False

    # complex default values
    assert 'html_title' not in cfg.__dict__
    assert cfg.html_title == 'Sphinx Tests v0.4alpha1 documentation'

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


@with_testapp()
def test_extension_values(app):
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
