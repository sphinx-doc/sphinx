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


# -- generic cross-reference roles ---------------------------------------------

class XRefRole(object):
    nodeclass = addnodes.pending_xref
    innernodeclass = nodes.literal

    def __init__(self, domain_name, fix_parens=False, lowercase=False,
                 nodeclass=None, innernodeclass=None):
        self.domain_name = domain_name
        self.fix_parens = fix_parens
        if nodeclass is not None:
            self.nodeclass = nodeclass
        if innernodeclass is not None:
            self.innernodeclass = innernodeclass

    def process_link(self, env, pnode, has_explicit_title, title, target):
        return title, ws_re.sub(' ', target)

    def normalize_func_parens(self, env, has_explicit_title, title, target):
        if not has_explicit_title:
            if title.endswith('()'):
                # remove parentheses
                title = title[:-2]
            if env.config.add_function_parentheses:
                # add them back to all occurrences if configured
                title += '()'
        # remove parentheses from the target too
        if target.endswith('()'):
            target = target[:-2]
        return title, target

    def __call__(self, typ, rawtext, text, lineno, inliner,
                 options={}, content=[]):
        env = inliner.document.settings.env
        if not typ:
            typ = env.config.default_role
        else:
            typ = typ.lower()
        if ":" in typ:
            domain, role = typ.split(":", 1)
        else:
            domain, role = self.domain_name, typ
        text = utils.unescape(text)
        # if the first character is a bang, don't cross-reference at all
        if text[0:1] == '!':
            if self.fix_parens:
                text, _ = self.normalize_func_parens(env, False, text[1:], "")
            return [self.innernodeclass(rawtext, text, classes=['xref'])], []
        # split title and target in role content
        has_explicit_title, title, target = split_explicit_title(text)
        # we want a cross-reference, create the reference node
        pnode = self.nodeclass(rawtext, reftype=role, refdomain=domain,
                               refcaption=has_explicit_title)
        # we may need the line number for warnings
        pnode.line = lineno
        title, target = self.process_link(env, pnode,
                                          has_explicit_title, title, target)
        pnode['reftarget'] = target
        pnode += self.innernodeclass(rawtext, title, classes=['xref'])
        return [pnode], []


class OptionXRefRole(XRefRole):
    innernodeclass = addnodes.literal_emphasis

    def process_link(self, env, pnode, has_explicit_title, title, target):
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
        return title, target


specific_docroles = {
    'keyword': XRefRole(''),
    'ref': XRefRole('', lowercase=True, innernodeclass=nodes.emphasis),
    'token': XRefRole(''),
    'term': XRefRole('', lowercase=True, innernodeclass=nodes.emphasis),
    'option': OptionXRefRole('', innernodeclass=addnodes.literal_emphasis),
    'doc': XRefRole(''),
    'download': XRefRole('', nodeclass=addnodes.download_reference),

    'menuselection': menusel_role,
    'file': emph_literal_role,
    'samp': emph_literal_role,
    'abbr': abbr_role,
}

for rolename, func in specific_docroles.iteritems():
    roles.register_local_role(rolename, func)


