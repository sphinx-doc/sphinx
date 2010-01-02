# -*- coding: utf-8 -*-
"""
    sphinx.directives
    ~~~~~~~~~~~~~~~~~

    Handlers for additional ReST directives.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.directives import images

from sphinx import addnodes
from sphinx.locale import l_

# import and register directives
from sphinx.directives.code import *
from sphinx.directives.other import *


# allow units for the figure's "figwidth"
try:
    images.Figure.option_spec['figwidth'] = \
        directives.length_or_percentage_or_unitless
except AttributeError:
    images.figure.options['figwidth'] = \
        directives.length_or_percentage_or_unitless


def _is_only_paragraph(node):
    """True if the node only contains one paragraph (and system messages)."""
    if len(node) == 0:
        return False
    elif len(node) > 1:
        for subnode in node[1:]:
            if not isinstance(subnode, nodes.system_message):
                return False
    if isinstance(node[0], nodes.paragraph):
        return True
    return False


# RE to strip backslash escapes
strip_backslash_re = re.compile(r'\\(?=[^\\])')


class ObjectDescription(Directive):
    """
    Directive to describe a class, function or similar object.  Not used
    directly, but subclassed to add custom behavior.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'noindex': directives.flag,
        'module': directives.unchanged,
    }

    # XXX make this more domain specific

    doc_fields_with_arg = {
        'param': '%param',
        'parameter': '%param',
        'arg': '%param',
        'argument': '%param',
        'keyword': '%param',
        'kwarg': '%param',
        'kwparam': '%param',
        'type': '%type',
        'raises': l_('Raises'),
        'raise': l_('Raises'),
        'exception': l_('Raises'),
        'except': l_('Raises'),
        'var': l_('Variable'),
        'ivar': l_('Variable'),
        'cvar': l_('Variable'),
        'returns': l_('Returns'),
        'return': l_('Returns'),
    }

    doc_fields_with_linked_arg = ('raises', 'raise', 'exception', 'except')

    doc_fields_without_arg = {
        'returns': l_('Returns'),
        'return': l_('Returns'),
        'rtype': l_('Return type'),
    }

    def handle_doc_fields(self, node):
        """
        Convert field lists with known keys inside the description content into
        better-looking equivalents.
        """
        # don't traverse, only handle field lists that are immediate children
        for child in node.children:
            if not isinstance(child, nodes.field_list):
                continue
            params = []
            pfield = None
            param_nodes = {}
            param_types = {}
            new_list = nodes.field_list()
            for field in child:
                fname, fbody = field
                try:
                    typ, obj = fname.astext().split(None, 1)
                    typdesc = self.doc_fields_with_arg[typ]
                    if _is_only_paragraph(fbody):
                        children = fbody.children[0].children
                    else:
                        children = fbody.children
                    if typdesc == '%param':
                        if not params:
                            # add the field that later gets all the parameters
                            pfield = nodes.field()
                            new_list += pfield
                        dlitem = nodes.list_item()
                        dlpar = nodes.paragraph()
                        dlpar += nodes.emphasis(obj, obj)
                        dlpar += nodes.Text(' -- ', ' -- ')
                        dlpar += children
                        param_nodes[obj] = dlpar
                        dlitem += dlpar
                        params.append(dlitem)
                    elif typdesc == '%type':
                        typenodes = fbody.children
                        if _is_only_paragraph(fbody):
                            typenodes = ([nodes.Text(' (')] +
                                         typenodes[0].children +
                                         [nodes.Text(')')])
                        param_types[obj] = typenodes
                    else:
                        fieldname = typdesc + ' '
                        nfield = nodes.field()
                        nfieldname = nodes.field_name(fieldname, fieldname)
                        nfield += nfieldname
                        node = nfieldname
                        if typ in self.doc_fields_with_linked_arg:
                            # XXX currmodule/currclass
                            node = addnodes.pending_xref(
                                obj, reftype='obj', refexplicit=False,
                                reftarget=obj)
                            #, modname=self.env.currmodule
                            #, classname=self.env.currclass
                            nfieldname += node
                        node += nodes.Text(obj, obj)
                        nfield += nodes.field_body()
                        nfield[1] += fbody.children
                        new_list += nfield
                except (KeyError, ValueError):
                    fnametext = fname.astext()
                    try:
                        typ = self.doc_fields_without_arg[fnametext]
                    except KeyError:
                        # at least capitalize the field name
                        typ = fnametext.capitalize()
                    fname[0] = nodes.Text(typ)
                    new_list += field
            if params:
                if len(params) == 1:
                    pfield += nodes.field_name('', _('Parameter'))
                    pfield += nodes.field_body()
                    pfield[1] += params[0][0]
                else:
                    pfield += nodes.field_name('', _('Parameters'))
                    pfield += nodes.field_body()
                    pfield[1] += nodes.bullet_list()
                    pfield[1][0].extend(params)

            for param, type in param_types.iteritems():
                if param in param_nodes:
                    param_nodes[param][1:1] = type
            child.replace_self(new_list)

    def get_signatures(self):
        """
        Retrieve the signatures to document from the directive arguments.
        """
        # remove backslashes to support (dummy) escapes; helps Vim highlighting
        return [strip_backslash_re.sub('', sig.strip())
                for sig in self.arguments[0].split('\n')]

    def parse_signature(self, sig, signode):
        """
        Parse the signature *sig* into individual nodes and append them to
        *signode*. If ValueError is raised, parsing is aborted and the whole
        *sig* is put into a single desc_name node.
        """
        raise ValueError

    def add_target_and_index(self, name, sig, signode):
        """
        Add cross-reference IDs and entries to self.indexnode, if applicable.
        """
        return  # do nothing by default

    def before_content(self):
        """
        Called before parsing content. Used to set information about the current
        directive context on the build environment.
        """
        pass

    def after_content(self):
        """
        Called after parsing content. Used to reset information about the
        current directive context on the build environment.
        """
        pass

    def run(self):
        if ':' in self.name:
            self.domain, self.objtype = self.name.split(':', 1)
        else:
            self.domain, self.objtype = '', self.name
        self.env = self.state.document.settings.env
        self.indexnode = addnodes.index(entries=[])

        node = addnodes.desc()
        node.document = self.state.document
        node['domain'] = self.domain
        # 'desctype' is a backwards compatible attribute
        node['objtype'] = node['desctype'] = self.objtype
        node['noindex'] = noindex = ('noindex' in self.options)

        self.names = []
        signatures = self.get_signatures()
        for i, sig in enumerate(signatures):
            # add a signature node for each signature in the current unit
            # and add a reference target for it
            signode = addnodes.desc_signature(sig, '')
            signode['first'] = False
            node.append(signode)
            try:
                # name can also be a tuple, e.g. (classname, objname)
                name = self.parse_signature(sig, signode)
            except ValueError, err:
                # signature parsing failed
                signode.clear()
                signode += addnodes.desc_name(sig, sig)
                continue  # we don't want an index entry here
            if not noindex and name not in self.names:
                # only add target and index entry if this is the first
                # description of the object with this name in this desc block
                self.names.append(name)
                self.add_target_and_index(name, sig, signode)

        contentnode = addnodes.desc_content()
        node.append(contentnode)
        if self.names:
            # needed for association of version{added,changed} directives
            self.env.doc_read_data['object'] = self.names[0]
        self.before_content()
        self.state.nested_parse(self.content, self.content_offset, contentnode)
        self.handle_doc_fields(contentnode)
        self.env.doc_read_data['object'] = None
        self.after_content()
        return [self.indexnode, node]

# backwards compatible old name
DescDirective = ObjectDescription


class DefaultDomain(Directive):
    """
    Directive to (re-)set the default domain for this source file.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        domain_name = arguments[0]
        env.doc_read_data['default_domain'] = env.domains.get(domain_name)


directives.register_directive('default-domain', DefaultDomain)
directives.register_directive('describe', ObjectDescription)
# new, more consistent, name
directives.register_directive('object', ObjectDescription)
