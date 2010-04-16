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
            if name in objects:
                self.env.warn(
                    self.env.docname,
                    'duplicate object description of %s, ' % name +
                    'other instance in ' +
                    self.env.doc2path(objects[name][0]),
                    self.lineno)
            objects[name] = self.env.docname, self.objtype
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
    Parses a directive. Returns (directive, arguments) string tuple. 
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
    return (parsed_dir.strip(), parsed_args.strip())

class ReSTDirective(ReSTMarkup):
    """
    Description of reST directive.
    """
    def handle_signature(self, sig, signode):
        name, args = parse_directive(sig)
        dec_name = '.. %s::' % name
        signode += addnodes.desc_name(dec_name, dec_name)
        if len(args) > 0:
            signode += addnodes.desc_addname(args, args)
        return name

class ReSTRole(ReSTMarkup):
    """
    Description of reST role.
    """
    def handle_signature(self, sig, signode):
        signode += addnodes.desc_name(':%s:' % sig, ':%s:' % sig)
        return sig
    
class ReSTDomain(Domain):
    """ReStructuredText domain."""
    name = 'rst'
    label = 'reStructuredText'
    
    object_types = {
        'directive': ObjType(l_('reStructuredText directive'), 'dir'),
        'role':      ObjType(l_('reStructuredText role'),      'role'),
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
        for name, (doc, _) in self.data['objects'].items():
            if doc == docname:
                del self.data['objects'][name]
    
    def resolve_xref(self, env, fromdocname, builder, typ, target, node,
                     contnode):
        objects = self.data['objects']
        
        if not target in objects:
            return None
        return make_refnode(builder, fromdocname, objects[target][0], target,
               contnode, target)
    
    def get_objects(self):
        for name, (docname, type) in self.data['objects'].iteritems():
            yield name, type, docname, name, 1


