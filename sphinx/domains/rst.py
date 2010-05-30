# -*- coding: utf-8 -*-
"""
    sphinx.domains.rst
    ~~~~~~~~~~~~~~~~~~

    The reStructuredText domain.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.locale import l_, _
from sphinx.directives import ObjectDescription
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode


dir_sig_re = re.compile(r'\.\. (.+?)::(.*)$')


class ReSTMarkup(ObjectDescription):
    """
    Description of generic reST markup.
    """

    def add_target_and_index(self, name, sig, signode):
        if name not in self.state.document.ids:
            signode['names'].append(name)
            signode['ids'].append(name)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)

            objects = self.env.domaindata['rst']['objects']
            if (self.objtype, name) in objects:
                self.env.warn(self.env.docname,
                              'duplicate description of %s %s, ' %
                              (self.objtype, name) +
                              'other instance in ' +
                              self.env.doc2path(objects[name][0]),
                              self.lineno)
            objects[self.objtype, name] = self.env.docname
        indextext = self.get_index_text(self.objtype, name)
        if indextext:
            self.indexnode['entries'].append(('single', indextext,
                                              name, name))

    def get_index_text(self, objectname, name):
        if self.objtype == 'directive':
            return _('%s (directive)') % name
        elif self.objtype == 'role':
            return _('%s (role)') % name
        return ''


def parse_directive(d):
    """
    Parses a directive signature. Returns (directive, arguments) string tuple.
    if no arguments are given, returns (directive, '').
    """
    dir = d.strip()
    if not dir.startswith('.'):
        # Assume it is a directive without syntax
        return (dir, '')
    m = dir_sig_re.match(dir)
    if not m:
        return (dir, '')
    parsed_dir, parsed_args = m.groups()
    return (parsed_dir.strip(), ' ' + parsed_args.strip())


class ReSTDirective(ReSTMarkup):
    """
    Description of a reST directive.
    """
    def handle_signature(self, sig, signode):
        name, args = parse_directive(sig)
        desc_name = '.. %s::' % name
        signode += addnodes.desc_name(desc_name, desc_name)
        if len(args) > 0:
            signode += addnodes.desc_addname(args, args)
        return name


class ReSTRole(ReSTMarkup):
    """
    Description of a reST role.
    """
    def handle_signature(self, sig, signode):
        signode += addnodes.desc_name(':%s:' % sig, ':%s:' % sig)
        return sig


class ReSTDomain(Domain):
    """ReStructuredText domain."""
    name = 'rst'
    label = 'reStructuredText'

    object_types = {
        'directive': ObjType(l_('directive'), 'dir'),
        'role':      ObjType(l_('role'),      'role'),
    }
    directives = {
        'directive': ReSTDirective,
        'role':      ReSTRole,
    }
    roles = {
        'dir':  XRefRole(),
        'role': XRefRole(),
    }
    initial_data = {
        'objects': {},  # fullname -> docname, objtype
    }

    def clear_doc(self, docname):
        for (typ, name), doc in self.data['objects'].items():
            if doc == docname:
                del self.data['objects'][typ, name]

    def resolve_xref(self, env, fromdocname, builder, typ, target, node,
                     contnode):
        objects = self.data['objects']

        if not (typ, target) in objects:
            return None
        return make_refnode(builder, fromdocname, objects[typ, target][0],
                            target, contnode, target)

    def get_objects(self):
        for (typ, name), docname in self.data['objects'].iteritems():
            yield name, name, typ, docname, name, 1
