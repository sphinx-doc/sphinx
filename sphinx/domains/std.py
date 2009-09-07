# -*- coding: utf-8 -*-
"""
    sphinx.domains.std
    ~~~~~~~~~~~~~~~~~~

    The standard domain.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.roles import XRefRole
from sphinx.locale import l_
from sphinx.domains import Domain, ObjType
from sphinx.directives import ObjectDescription
from sphinx.util import make_refnode, ws_re
from sphinx.util.compat import Directive


# RE for option descriptions
option_desc_re = re.compile(
    r'((?:/|-|--)[-_a-zA-Z0-9]+)(\s*.*?)(?=,\s+(?:/|-|--)|$)')


class GenericObject(ObjectDescription):
    """
    A generic x-ref directive registered with Sphinx.add_description_unit().
    """
    indextemplate = ''
    parse_node = None

    def parse_signature(self, sig, signode):
        if self.parse_node:
            name = self.parse_node(self.env, sig, signode)
        else:
            signode.clear()
            signode += addnodes.desc_name(sig, sig)
            # normalize whitespace like XRefRole does
            name = ws_re.sub('', sig)
        return name

    def add_target_and_index(self, name, sig, signode):
        targetname = '%s-%s' % (self.objtype, name)
        signode['ids'].append(targetname)
        self.state.document.note_explicit_target(signode)
        if self.indextemplate:
            colon = self.indextemplate.find(':')
            if colon != -1:
                indextype = self.indextemplate[:colon].strip()
                indexentry = self.indextemplate[colon+1:].strip() % (name,)
            else:
                indextype = 'single'
                indexentry = self.indextemplate % (name,)
            self.indexnode['entries'].append((indextype, indexentry,
                                              targetname, targetname))
        self.env.domaindata['std']['objects'][self.objtype, name] = \
            self.env.docname, targetname


class EnvVar(GenericObject):
    indextemplate = l_('environment variable; %s')


class Target(Directive):
    """
    Generic target for user-defined cross-reference types.
    """
    indextemplate = ''

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        # normalize whitespace in fullname like XRefRole does
        fullname = ws_re.sub('', self.arguments[0].strip())
        targetname = '%s-%s' % (self.name, fullname)
        node = nodes.target('', '', ids=[targetname])
        self.state.document.note_explicit_target(node)
        ret = [node]
        if self.indextemplate:
            indexentry = self.indextemplate % (fullname,)
            indextype = 'single'
            colon = indexentry.find(':')
            if colon != -1:
                indextype = indexentry[:colon].strip()
                indexentry = indexentry[colon+1:].strip()
            inode = addnodes.index(entries=[(indextype, indexentry,
                                             targetname, targetname)])
            ret.insert(0, inode)
        env.domaindata['std']['objects'][self.name, fullname] = \
            env.docname, targetname
        return ret


class Cmdoption(ObjectDescription):
    """
    Description of a command-line option (.. cmdoption).
    """

    def parse_signature(self, sig, signode):
        """Transform an option description into RST nodes."""
        count = 0
        firstname = ''
        for m in option_desc_re.finditer(sig):
            optname, args = m.groups()
            if count:
                signode += addnodes.desc_addname(', ', ', ')
            signode += addnodes.desc_name(optname, optname)
            signode += addnodes.desc_addname(args, args)
            if not count:
                firstname = optname
            count += 1
        if not firstname:
            raise ValueError
        return firstname

    def add_target_and_index(self, name, sig, signode):
        targetname = name.replace('/', '-')
        currprogram = self.env.doc_read_data.get('std_program')
        if currprogram:
            targetname = '-' + currprogram + targetname
        targetname = 'cmdoption' + targetname
        signode['ids'].append(targetname)
        self.state.document.note_explicit_target(signode)
        self.indexnode['entries'].append(
            ('pair', _('%scommand line option; %s') %
             ((currprogram and currprogram + ' ' or ''), sig),
             targetname, targetname))
        self.env.domaindata['std']['progoptions'][currprogram, name] = \
            self.env.docname, targetname


class Program(Directive):
    """
    Directive to name the program for which options are documented.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        program = ws_re.sub('-', self.arguments[0].strip())
        if program == 'None':
            env.doc_read_data['std_program'] = None
        else:
            env.doc_read_data['std_program'] = program
        return []


class OptionXRefRole(XRefRole):
    innernodeclass = addnodes.literal_emphasis

    def process_link(self, env, pnode, has_explicit_title, title, target):
        program = env.doc_read_data.get('std_program')
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


class Glossary(Directive):
    """
    Directive to create a glossary with cross-reference targets
    for :term: roles.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'sorted': directives.flag,
    }

    def run(self):
        env = self.state.document.settings.env
        objects = env.domaindata['std']['objects']
        gloss_entries = env.doc_read_data.setdefault('gloss_entries', set())
        node = addnodes.glossary()
        node.document = self.state.document
        self.state.nested_parse(self.content, self.content_offset, node)

        # the content should be definition lists
        dls = [child for child in node
               if isinstance(child, nodes.definition_list)]
        # now, extract definition terms to enable cross-reference creation
        new_dl = nodes.definition_list()
        new_dl['classes'].append('glossary')
        items = []
        for dl in dls:
            for li in dl.children:
                if not li.children or not isinstance(li[0], nodes.term):
                    continue
                termtext = li.children[0].astext()
                new_id = 'term-' + nodes.make_id(termtext)
                if new_id in gloss_entries:
                    new_id = 'term-' + str(len(gloss_entries))
                gloss_entries.add(new_id)
                li[0]['names'].append(new_id)
                li[0]['ids'].append(new_id)
                objects['term', termtext.lower()] = env.docname, new_id
                # add an index entry too
                indexnode = addnodes.index()
                indexnode['entries'] = [('single', termtext, new_id, termtext)]
                li.insert(0, indexnode)
                items.append((termtext, li))
        if 'sorted' in self.options:
            items.sort(key=lambda x: x[0].lower())
        new_dl.extend(item[1] for item in items)
        node.children = [new_dl]
        return [node]


token_re = re.compile('`([a-z_][a-z0-9_]*)`')

def token_xrefs(text):
    retnodes = []
    pos = 0
    for m in token_re.finditer(text):
        if m.start() > pos:
            txt = text[pos:m.start()]
            retnodes.append(nodes.Text(txt, txt))
        refnode = addnodes.pending_xref(
            m.group(1), reftype='token', refdomain='std', reftarget=m.group(1))
        refnode += nodes.literal(m.group(1), m.group(1), classes=['xref'])
        retnodes.append(refnode)
        pos = m.end()
    if pos < len(text):
        retnodes.append(nodes.Text(text[pos:], text[pos:]))
    return retnodes


class ProductionList(Directive):
    """
    Directive to list grammar productions.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        objects = env.domaindata['std']['objects']
        node = addnodes.productionlist()
        messages = []
        i = 0

        for rule in self.arguments[0].split('\n'):
            if i == 0 and ':' not in rule:
                # production group
                continue
            i += 1
            try:
                name, tokens = rule.split(':', 1)
            except ValueError:
                break
            subnode = addnodes.production()
            subnode['tokenname'] = name.strip()
            if subnode['tokenname']:
                idname = 'grammar-token-%s' % subnode['tokenname']
                if idname not in self.state.document.ids:
                    subnode['ids'].append(idname)
                self.state.document.note_implicit_target(subnode, subnode)
                objects['token', subnode['tokenname']] = env.docname, idname
            subnode.extend(token_xrefs(tokens))
            node.append(subnode)
        return [node] + messages


class StandardDomain(Domain):
    """
    Domain for all objects that don't fit into another domain or are added
    via the application interface.
    """

    name = 'std'
    label = 'Default'

    object_types = {
        'term': ObjType(l_('glossary term'), 'term', searchprio=-1),
        'token': ObjType(l_('grammar token'), 'token', searchprio=-1),
        'envvar': ObjType(l_('environment variable'), 'envvar'),
        'cmdoption': ObjType(l_('program option'), 'option'),
    }

    directives = {
        'program': Program,
        'cmdoption': Cmdoption,
        'envvar': EnvVar,
        'glossary': Glossary,
        'productionlist': ProductionList,
    }
    roles = {
        'option': OptionXRefRole(innernodeclass=addnodes.literal_emphasis),
        'envvar': XRefRole(),  # XXX add index entries
        'token':  XRefRole(),
        'term':   XRefRole(lowercase=True, innernodeclass=nodes.emphasis),
    }

    initial_data = {
        'progoptions': {},  # (program, name) -> docname, labelid
        'objects': {},      # (type, name) -> docname, labelid
    }

    def clear_doc(self, docname):
        for key, (fn, _) in self.data['progoptions'].items():
            if fn == docname:
                del self.data['progoptions'][key]
        for key, (fn, _) in self.data['objects'].items():
            if fn == docname:
                del self.data['objects'][key]

    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):
        if typ == 'option':
            progname = node['refprogram']
            docname, labelid = self.data['progoptions'].get((progname, target),
                                                            ('', ''))
            if not docname:
                return None
            else:
                return make_refnode(builder, fromdocname, docname,
                                    labelid, contnode)
        else:
            docname, labelid = self.data['objects'].get((typ, target),
                                                        ('', ''))
            if not docname:
                if typ == 'term':
                    env.warn(fromdocname, 'term not in glossary: %s' % target,
                             node.line)
                return None
            else:
                return make_refnode(builder, fromdocname, docname,
                                    labelid, contnode)

    def get_objects(self):
        for (prog, option), info in self.data['progoptions'].iteritems():
            yield (option, 'option', info[0], info[1], 1)
        for (type, name), info in self.data['objects'].iteritems():
            yield (name, type, info[0], info[1],
                   self.object_types[type].attrs['searchprio'])
