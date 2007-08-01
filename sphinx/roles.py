# -*- coding: utf-8 -*-
"""
    sphinx.roles
    ~~~~~~~~~~~~

    Handlers for additional ReST roles.

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""

import re

from docutils import nodes, utils
from docutils.parsers.rst import roles

from . import addnodes

ws_re = re.compile(r'\s+')

generic_docroles = {
    'command' : nodes.strong,
    'dfn' : nodes.emphasis,
    'guilabel' : nodes.strong,
    'kbd' : nodes.literal,
    'keyword' : nodes.literal,
    'mailheader' : nodes.emphasis,
    'makevar' : nodes.Text,
    'manpage' : nodes.emphasis,
    'mimetype' : nodes.emphasis,
    'newsgroup' : nodes.emphasis,
    'option' : nodes.emphasis,
    'program' : nodes.strong,
    'regexp' : nodes.literal,
}

for rolename, nodeclass in generic_docroles.iteritems():
    roles.register_generic_role(rolename, nodeclass)


def indexmarkup_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    env = inliner.document.settings.env
    text = utils.unescape(text)
    targetid = 'index-%s' % env.index_num
    env.index_num += 1
    targetnode = nodes.target('', '', ids=[targetid])
    inliner.document.note_explicit_target(targetnode)
    if typ == 'envvar':
        env.note_index_entry('single', '%s' % text,
                             targetid, text)
        env.note_index_entry('single', 'environment variables!%s' % text,
                             targetid, text)
        textnode = nodes.strong(text, text)
        return [targetnode, textnode], []
    elif typ == 'pep':
        env.note_index_entry('single', 'Python Enhancement Proposals!PEP %s' % text,
                             targetid, 'PEP %s' % text)
        try:
            pepnum = int(text)
        except ValueError:
            msg = inliner.reporter.error('invalid PEP number %s' % text, line=lineno)
            prb = inliner.problematic(rawtext, rawtext, msg)
            return [prb], [msg]
        ref = inliner.document.settings.pep_base_url + 'pep-%04d' % pepnum
        sn = nodes.strong('PEP '+text, 'PEP '+text)
        rn = nodes.reference('', '', refuri=ref)
        rn += sn
        return [targetnode, rn], []
    elif typ == 'rfc':
        env.note_index_entry('single', 'RFC!RFC %s' % text,
                             targetid, 'RFC %s' % text)
        try:
            rfcnum = int(text)
        except ValueError:
            msg = inliner.reporter.error('invalid RFC number %s' % text, line=lineno)
            prb = inliner.problematic(rawtext, rawtext, msg)
            return [prb], [msg]
        ref = inliner.document.settings.rfc_base_url + inliner.rfc_url % rfcnum
        sn = nodes.strong('RFC '+text, 'RFC '+text)
        rn = nodes.reference('', '', refuri=ref)
        rn += sn
        return [targetnode, rn], []

roles.register_canonical_role('envvar', indexmarkup_role)
roles.register_local_role('pep', indexmarkup_role)
roles.register_local_role('rfc', indexmarkup_role)


# default is `literal`
innernodetypes = {
    'ref': nodes.emphasis,
    'token': nodes.strong,
}

def xfileref_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    env = inliner.document.settings.env
    text = utils.unescape(text)
    # 'token' is the default role inside 'productionlist' directives
    if typ == '':
        typ = 'token'
    if env.config.get('strip_trailing_parentheses', False):
        if text[-2:] == '()':
            text = text[:-2]
    pnode = addnodes.pending_xref(rawtext)
    pnode['reftype'] = typ
    pnode['reftarget'] = ws_re.sub('', text)
    pnode['modname'] = env.currmodule
    pnode['classname'] = env.currclass
    pnode += innernodetypes.get(typ, nodes.literal)(rawtext, text, classes=['xref'])
    return [pnode], []


def menusel_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    return [nodes.emphasis(
        rawtext, utils.unescape(text).replace('-->', u'\N{TRIANGULAR BULLET}'))], []


_filevar_re = re.compile('{([^}]+)}')

def file_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    text = utils.unescape(text)
    retnodes = []
    pos = 0
    for m in _filevar_re.finditer(text):
        if m.start() > pos:
            txt = text[pos:m.start()]
            retnodes.append(nodes.literal(txt, txt))
        retnodes.append(nodes.emphasis('', '', nodes.literal(m.group(1), m.group(1))))
        pos = m.end()
    if pos < len(text):
        retnodes.append(nodes.literal(text[pos:], text[pos:]))
    return retnodes, []


specific_docroles = {
    'data': xfileref_role,
    'exc': xfileref_role,
    'func': xfileref_role,
    'class': xfileref_role,
    'const': xfileref_role,
    'attr': xfileref_role,
    'meth': xfileref_role,

    'cfunc' : xfileref_role,
    'cdata' : xfileref_role,
    'ctype' : xfileref_role,
    'cmacro' : xfileref_role,

    'mod' : xfileref_role,

    'ref': xfileref_role,
    'token' : xfileref_role,

    'menuselection' : menusel_role,
    'file' : file_role,
}

for rolename, func in specific_docroles.iteritems():
    roles.register_canonical_role(rolename, func)
