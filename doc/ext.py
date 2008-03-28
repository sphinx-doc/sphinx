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

def parse_directive(env, sig, signode):
    if not sig.startswith('.'):
        dec_sig = '.. %s::' % sig
        signode += addnodes.desc_name(dec_sig, dec_sig)
        return sig
    m = dir_sig_re.match(sig)
    if not m:
        signode += addnodes.desc_name(sig, sig)
        return sig
    name, args = m.groups()
    dec_name = '.. %s::' % name
    signode += addnodes.desc_name(dec_name, dec_name)
    signode += addnodes.desc_classname(args, args)
    return name


def parse_role(env, sig, signode):
    signode += addnodes.desc_name(':%s:' % sig, ':%s:' % sig)
    return sig


def setup(app):
    app.add_description_unit('directive', 'dir', 'pair: %s; directive', parse_directive)
    app.add_description_unit('role', 'role', 'pair: %s; role', parse_role)
    app.add_description_unit('confval', 'confval', 'pair: %s; configuration value')
