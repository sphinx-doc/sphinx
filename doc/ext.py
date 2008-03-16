# -*- coding: utf-8 -*-
"""
    ext.py -- Sphinx extension for the Sphinx documentation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

import re

from sphinx import addnodes

dir_sig_re = re.compile(r'\.\. ([^:]+)::(.*)$')

def parse_directive(sig, signode):
    if not sig.startswith('.'):
        sig = '.. %s::' % sig
        signode += addnodes.desc_name(sig, sig)
        return
    m = dir_sig_re.match(sig)
    if not m:
        signode += addnodes.desc_name(sig, sig)
        return
    name, args = m.groups()
    name = '.. %s::' % name
    signode += addnodes.desc_name(name, name)
    signode += addnodes.desc_classname(args, args)


def parse_role(sig, signode):
    signode += addnodes.desc_name(':%s:' % sig, ':%s:' % sig)


def setup(app):
    app.add_description_unit('directive', 'dir', 'directive', parse_directive)
    app.add_description_unit('role', 'role', 'role', parse_role)
    app.add_description_unit('confval', 'confval', 'configuration value')
