# -*- coding: utf-8 -*-
"""
    sphinx.roles
    ~~~~~~~~~~~~

    Handlers for additional ReST roles.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from docutils import nodes, utils
from docutils.parsers.rst import roles

from sphinx import addnodes
from sphinx.util import ws_re, caption_ref_re


generic_docroles = {
    'command' : nodes.strong,
    'dfn' : nodes.emphasis,
    'guilabel' : nodes.strong,
    'kbd' : nodes.literal,
    'mailheader' : addnodes.literal_emphasis,
    'makevar' : nodes.strong,
    'manpage' : addnodes.literal_emphasis,
    'mimetype' : addnodes.literal_emphasis,
    'newsgroup' : addnodes.literal_emphasis,
    'program' : nodes.strong,
    'regexp' : nodes.literal,
}

for rolename, nodeclass in generic_docroles.iteritems():
    role = roles.GenericRole(rolename, nodeclass)
    roles.register_local_role(rolename, role)


def indexmarkup_role(typ, rawtext, etext, lineno, inliner,
                     options={}, content=[]):
    env = inliner.document.settings.env
    if not typ:
        typ = env.config.default_role
    else:
        typ = typ.lower()
    text = utils.unescape(etext)
    targetid = 'index-%s' % env.index_num
    env.index_num += 1
    indexnode = addnodes.index()
    targetnode = nodes.target('', '', ids=[targetid])
    inliner.document.note_explicit_target(targetnode)
    if typ == 'envvar':
        indexnode['entries'] = [('single', text, targetid, text),
                                ('single', _('environment variable; %s') % text,
                                 targetid, text)]
        xref_nodes = xfileref_role(typ, rawtext, etext, lineno, inliner,
                                   options, content)[0]
        return [indexnode, targetnode] + xref_nodes, []
    elif typ == 'pep':
        indexnode['entries'] = [
            ('single', _('Python Enhancement Proposals!PEP %s') % text,
             targetid, 'PEP %s' % text)]
        try:
            pepnum = int(text)
        except ValueError:
            msg = inliner.reporter.error('invalid PEP number %s' % text,
                                         line=lineno)
            prb = inliner.problematic(rawtext, rawtext, msg)
            return [prb], [msg]
        ref = inliner.document.settings.pep_base_url + 'pep-%04d' % pepnum
        sn = nodes.strong('PEP '+text, 'PEP '+text)
        rn = nodes.reference('', '', refuri=ref)
        rn += sn
        return [indexnode, targetnode, rn], []
    elif typ == 'rfc':
        indexnode['entries'] = [('single', 'RFC; RFC %s' % text,
                                 targetid, 'RFC %s' % text)]
        try:
            rfcnum = int(text)
        except ValueError:
            msg = inliner.reporter.error('invalid RFC number %s' % text,
                                         line=lineno)
            prb = inliner.problematic(rawtext, rawtext, msg)
            return [prb], [msg]
        ref = inliner.document.settings.rfc_base_url + inliner.rfc_url % rfcnum
        sn = nodes.strong('RFC '+text, 'RFC '+text)
        rn = nodes.reference('', '', refuri=ref)
        rn += sn
        return [indexnode, targetnode, rn], []

roles.register_local_role('envvar', indexmarkup_role)
roles.register_local_role('pep', indexmarkup_role)
roles.register_local_role('rfc', indexmarkup_role)


# default is `literal`
innernodetypes = {
    'ref': nodes.emphasis,
    'term': nodes.emphasis,
    'token': nodes.strong,
    'envvar': nodes.strong,
    'download': nodes.strong,
    'option': addnodes.literal_emphasis,
}

def _fix_parens(typ, text, env):
    if typ in ('func', 'meth', 'cfunc'):
        if text.endswith('()'):
            # remove parentheses
            text = text[:-2]
        if env.config.add_function_parentheses:
            # add them back to all occurrences if configured
            text += '()'
    return text

def xfileref_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    env = inliner.document.settings.env
    if not typ:
        typ = env.config.default_role
    else:
        typ = typ.lower()
    text = utils.unescape(text)
    # if the first character is a bang, don't cross-reference at all
    if text[0:1] == '!':
        text = _fix_parens(typ, text[1:], env)
        return [innernodetypes.get(typ, nodes.literal)(
            rawtext, text, classes=['xref'])], []
    # we want a cross-reference, create the reference node
    nodeclass = (typ == 'download') and addnodes.download_reference or \
                addnodes.pending_xref
    pnode = nodeclass(rawtext, reftype=typ, refcaption=False,
                      modname=env.currmodule, classname=env.currclass)
    # we may need the line number for warnings
    pnode.line = lineno
    # the link title may differ from the target, but by default
    # they are the same
    title = target = text
    titleistarget = True
    # look if explicit title and target are given with `foo <bar>` syntax
    brace = text.find('<')
    if brace != -1:
        titleistarget = False
        pnode['refcaption'] = True
        m = caption_ref_re.match(text)
        if m:
            target = m.group(2)
            title = m.group(1)
        else:
            # fallback: everything after '<' is the target
            target = text[brace+1:]
            title = text[:brace]
    # special target for Python object cross-references
    if typ in ('data', 'exc', 'func', 'class', 'const', 'attr',
               'meth', 'mod', 'obj'):
        # fix-up parentheses in link title
        if titleistarget:
            title = title.lstrip('.')   # only has a meaning for the target
            target = target.lstrip('~') # only has a meaning for the title
            title = _fix_parens(typ, title, env)
            # if the first character is a tilde, don't display the module/class
            # parts of the contents
            if title[0:1] == '~':
                title = title[1:]
                dot = title.rfind('.')
                if dot != -1:
                    title = title[dot+1:]
        # remove parentheses from the target too
        if target.endswith('()'):
            target = target[:-2]
        # if the first character is a dot, search more specific namespaces first
        # else search builtins first
        if target[0:1] == '.':
            target = target[1:]
            pnode['refspecific'] = True
    # some other special cases for the target
    elif typ == 'option':
        program = env.currprogram
        if titleistarget:
            if ' ' in title and not (title.startswith('/') or
                                     title.startswith('-')):
                program, target = re.split(' (?=-|--|/)', title, 1)
                program = ws_re.sub('-', program)
                target = target.strip()
        elif ' ' in target:
            program, target = re.split(' (?=-|--|/)', target, 1)
            program = ws_re.sub('-', program)
        pnode['refprogram'] = program
    elif typ == 'term':
        # normalize whitespace in definition terms (if the term reference is
        # broken over a line, a newline will be in target)
        target = ws_re.sub(' ', target).lower()
    elif typ == 'ref':
        # reST label names are always lowercased
        target = ws_re.sub('', target).lower()
    elif typ == 'cfunc':
        # fix-up parens for C functions too
        if titleistarget:
            title = _fix_parens(typ, title, env)
        # remove parentheses from the target too
        if target.endswith('()'):
            target = target[:-2]
    else:
        # remove all whitespace to avoid referencing problems
        target = ws_re.sub('', target)
    pnode['refdoc'] = env.docname
    pnode['reftarget'] = target
    pnode += innernodetypes.get(typ, nodes.literal)(rawtext, title,
                                                    classes=['xref'])
    return [pnode], []


def menusel_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    return [nodes.emphasis(
        rawtext,
        utils.unescape(text).replace('-->', u'\N{TRIANGULAR BULLET}'))], []


_litvar_re = re.compile('{([^}]+)}')

def emph_literal_role(typ, rawtext, text, lineno, inliner,
                      options={}, content=[]):
    text = utils.unescape(text)
    pos = 0
    retnode = nodes.literal(role=typ.lower())
    for m in _litvar_re.finditer(text):
        if m.start() > pos:
            txt = text[pos:m.start()]
            retnode += nodes.Text(txt, txt)
        retnode += nodes.emphasis(m.group(1), m.group(1))
        pos = m.end()
    if pos < len(text):
        retnode += nodes.Text(text[pos:], text[pos:])
    return [retnode], []


_abbr_re = re.compile('\((.*)\)$')

def abbr_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    text = utils.unescape(text)
    m = _abbr_re.search(text)
    if m is None:
        return [addnodes.abbreviation(text, text)], []
    abbr = text[:m.start()].strip()
    expl = m.group(1)
    return [addnodes.abbreviation(abbr, abbr, explanation=expl)], []


specific_docroles = {
    'data': xfileref_role,
    'exc': xfileref_role,
    'func': xfileref_role,
    'class': xfileref_role,
    'const': xfileref_role,
    'attr': xfileref_role,
    'meth': xfileref_role,
    'obj': xfileref_role,
    'cfunc' : xfileref_role,
    'cmember': xfileref_role,
    'cdata': xfileref_role,
    'ctype': xfileref_role,
    'cmacro': xfileref_role,

    'mod': xfileref_role,

    'keyword': xfileref_role,
    'ref': xfileref_role,
    'token': xfileref_role,
    'term': xfileref_role,
    'option': xfileref_role,
    'doc': xfileref_role,
    'download': xfileref_role,

    'menuselection': menusel_role,
    'file': emph_literal_role,
    'samp': emph_literal_role,
    'abbr': abbr_role,
}

for rolename, func in specific_docroles.iteritems():
    roles.register_local_role(rolename, func)
