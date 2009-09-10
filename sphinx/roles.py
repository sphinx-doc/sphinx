# -*- coding: utf-8 -*-
"""
    sphinx.roles
    ~~~~~~~~~~~~

    Handlers for additional ReST roles.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import warnings

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
    'program' : nodes.strong,  # XXX should be an x-ref
    'regexp' : nodes.literal,
}

for rolename, nodeclass in generic_docroles.iteritems():
    role = roles.GenericRole(rolename, nodeclass)
    roles.register_local_role(rolename, role)


# -- generic cross-reference role ----------------------------------------------

class XRefRole(object):
    """XXX add docstrings"""

    nodeclass = addnodes.pending_xref
    innernodeclass = nodes.literal

    def __init__(self, fix_parens=False, lowercase=False,
                 nodeclass=None, innernodeclass=None):
        self.fix_parens = fix_parens
        self.lowercase = lowercase
        if nodeclass is not None:
            self.nodeclass = nodeclass
        if innernodeclass is not None:
            self.innernodeclass = innernodeclass

    def _fix_parens(self, env, has_explicit_title, title, target):
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
        if ':' not in typ:
            domain, role = '', typ
        else:
            domain, role = typ.split(':', 1)
        text = utils.unescape(text)
        # if the first character is a bang, don't cross-reference at all
        if text[0:1] == '!':
            if self.fix_parens:
                text, _ = self._fix_parens(env, False, text[1:], "")
            innernode = self.innernodeclass(rawtext, text, classes=['xref'])
            return self.result_nodes(inliner.document, env, innernode,
                                     is_ref=False)
        # split title and target in role content
        has_explicit_title, title, target = split_explicit_title(text)
        # fix-up title and target
        if self.lowercase:
            target = target.lower()
        if self.fix_parens:
            title, target = self._fix_parens(
                env, has_explicit_title, title, target)
        # create the reference node
        refnode = self.nodeclass(rawtext, reftype=role, refdomain=domain,
                                 refexplicit=has_explicit_title)
        # we may need the line number for warnings
        refnode.line = lineno
        title, target = self.process_link(
            env, refnode, has_explicit_title, title, target)
        # now that the target and title are finally determined, set them
        refnode['reftarget'] = target
        refnode += self.innernodeclass(rawtext, title, classes=['xref'])
        # result_nodes allow further modification of return values
        return self.result_nodes(inliner.document, env, refnode, is_ref=True)

    # methods that can be overwritten

    def process_link(self, env, refnode, has_explicit_title, title, target):
        return title, ws_re.sub(' ', target)

    def result_nodes(self, document, env, node, is_ref):
        return [node], []


def indexmarkup_role(typ, rawtext, etext, lineno, inliner,
                     options={}, content=[]):
    env = inliner.document.settings.env
    if not typ:
        typ = env.config.default_role
    else:
        typ = typ.lower()
    text = utils.unescape(etext)
    targetid = 'index-%s' % env.new_serialno('index')
    indexnode = addnodes.index()
    targetnode = nodes.target('', '', ids=[targetid])
    inliner.document.note_explicit_target(targetnode)
    if typ == 'pep':
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


specific_docroles = {
    # links to download references
    'download': XRefRole(nodeclass=addnodes.download_reference),
    # links to headings or arbitrary labels
    'ref': XRefRole(lowercase=True, innernodeclass=nodes.emphasis),
    # links to documents
    'doc': XRefRole(),
    # links to labels, without a different title
    'keyword': XRefRole(),

    'pep': indexmarkup_role,
    'rfc': indexmarkup_role,
    'menuselection': menusel_role,
    'file': emph_literal_role,
    'samp': emph_literal_role,
    'abbr': abbr_role,
}

for rolename, func in specific_docroles.iteritems():
    roles.register_local_role(rolename, func)


# backwards compatibility alias
def xfileref_role(*args, **kwds):
    warnings.warn('xfileref_role is deprecated, use XRefRole',
                  DeprecationWarning, stacklevel=2)
    return XRefRole()(*args, **kwds)
