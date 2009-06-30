# -*- coding: utf-8 -*-
"""
    sphinx.roles
    ~~~~~~~~~~~~

    Handlers for additional ReST roles.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from docutils import nodes, utils
from docutils.parsers.rst import roles

from sphinx import addnodes
from sphinx.util import ws_re, split_explicit_title


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


def make_xref_role(link_func, nodeclass=None, innernodeclass=None):
    if nodeclass is None:
        nodeclass = addnodes.pending_xref
    if innernodeclass is None:
        innernodeclass = nodes.literal

    def func(typ, rawtext, text, lineno, inliner, options={}, content=[]):
        env = inliner.document.settings.env
        if not typ:
            typ = env.config.default_role
        else:
            typ = typ.lower()
        text = utils.unescape(text)
        # if the first character is a bang, don't cross-reference at all
        if text[0:1] == '!':
            text = _fix_parens(typ, text[1:], env)
            return [innernodeclass(rawtext, text, classes=['xref'])], []
        # we want a cross-reference, create the reference node
        pnode = nodeclass(rawtext, reftype=typ, refcaption=False,
                          modname=env.currmodule, classname=env.currclass)
        # we may need the line number for warnings
        pnode.line = lineno
        has_explicit_title, title, target = split_explicit_title(text)
        target, title = link_func(env, pnode, has_explicit_title, title, target)
        pnode['reftarget'] = target
        pnode += innernodeclass(rawtext, title, classes=['xref'])
        return [pnode], []
    return func


def menusel_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    return [nodes.emphasis(
        rawtext,
        utils.unescape(text).replace('-->', u'\N{TRIANGULAR BULLET}'))], []
    return role


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


def normalize_func_parens(env, has_explicit_title, target, title):
    if has_explicit_title:
        if title.endswith('()'):
            # remove parentheses
            title = title[:-2]
        if env.config.add_function_parentheses:
            # add them back to all occurrences if configured
            title += '()'
    # remove parentheses from the target too
    if target.endswith('()'):
        target = target[:-2]
    return target, title


def generic_link_func(env, pnode, has_explicit_title, title, target):
    if has_explicit_title:
        pnode['refcaption'] = True
    return target, title


def pyref_link_func(env, pnode, has_explicit_title, title, target):
    if has_explicit_title:
        pnode['refcaption'] = True
    # fix-up parentheses in link title
    else:
        title = title.lstrip('.')   # only has a meaning for the target
        target = target.lstrip('~') # only has a meaning for the title
        # if the first character is a tilde, don't display the module/class
        # parts of the contents
        if title[0:1] == '~':
            title = title[1:]
            dot = title.rfind('.')
            if dot != -1:
                title = title[dot+1:]
    # if the first character is a dot, search more specific namespaces first
    # else search builtins first
    if target[0:1] == '.':
        target = target[1:]
        pnode['refspecific'] = True
    return target, title


def pyref_callable_link_func(env, pnode, has_explicit_title, title, target):
    target, title = pyref_link_func(env, pnode, has_explicit_title, title, target)
    target, title = normalize_func_parens(env, has_explicit_title, target, title)
    return target, title


def option_link_func(env, pnode, has_explicit_title, title, target):
    program = env.currprogram
    if not has_explicit_title:
        if ' ' in title and not (title.startswith('/') or
                                 title.startswith('-')):
            program, target = re.split(' (?=-|--|/)', title, 1)
            program = ws_re.sub('-', program)
            target = target.strip()
    elif ' ' in target:
        program, target = re.split(' (?=-|--|/)', target, 1)
        program = ws_re.sub('-', program)
    pnode['refprogram'] = program
    return target, title


def simple_link_func(env, pnode, has_explicit_title, title, target):
    # normalize all whitespace to avoid referencing problems
    target = ws_re.sub(' ', target)
    return target, title


def lowercase_link_func(env, pnode, has_explicit_title, title, target):
    target, title = simple_link_func(env, pnode, has_explicit_title, title, target)
    return target.lower(), title


def cfunc_link_func(env, pnode, has_explicit_title, title, target):
    return normalize_func_parens(env, has_explicit_title, target, title)


generic_pyref_role = make_xref_role(pyref_link_func)
callable_pyref_role = make_xref_role(pyref_callable_link_func)
simple_xref_role = make_xref_role(simple_link_func)

specific_docroles = {
    'data': generic_pyref_role,
    'exc': generic_pyref_role,
    'func': callable_pyref_role,
    'class': generic_pyref_role,
    'const': generic_pyref_role,
    'attr': generic_pyref_role,
    'meth': callable_pyref_role,
    'mod': generic_pyref_role,
    'obj': generic_pyref_role,

    'keyword': simple_xref_role,
    'ref': make_xref_role(lowercase_link_func, None, nodes.emphasis),
    'token': simple_xref_role,
    'term': make_xref_role(lowercase_link_func, None, nodes.emphasis),
    'option': make_xref_role(option_link_func, None, addnodes.literal_emphasis),
    'doc': simple_xref_role,
    'download': make_xref_role(simple_link_func, addnodes.download_reference),

    'cmember': simple_xref_role,
    'cmacro': simple_xref_role,
    'cfunc' : make_xref_role(cfunc_link_func),
    'cdata': simple_xref_role,
    'ctype': simple_xref_role,

    'menuselection': menusel_role,
    'file': emph_literal_role,
    'samp': emph_literal_role,
    'abbr': abbr_role,
}

for rolename, func in specific_docroles.iteritems():
    roles.register_local_role(rolename, func)
