"""
    sphinx.directives
    ~~~~~~~~~~~~~~~~~

    Handlers for additional ReST directives.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
from typing import List, cast

from docutils import nodes
from docutils.parsers.rst import directives, roles

from sphinx import addnodes
from sphinx.deprecation import RemovedInSphinx40Warning, deprecated_alias
from sphinx.util import docutils
from sphinx.util.docfields import DocFieldTransformer, TypedField
from sphinx.util.docutils import SphinxDirective

if False:
    # For type annotation
    from typing import Any, Dict, Tuple  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.util.docfields import Field  # NOQA
    from sphinx.util.typing import DirectiveOption  # NOQA


# RE to strip backslash escapes
nl_escape_re = re.compile(r'\\\n')
strip_backslash_re = re.compile(r'\\(.)')


def optional_int(argument):
    """
    Check for an integer argument or None value; raise ``ValueError`` if not.
    """
    if argument is None:
        return None
    else:
        value = int(argument)
        if value < 0:
            raise ValueError('negative value; must be positive or zero')
        return value


class ObjectDescription(SphinxDirective):
    """
    Directive to describe a class, function or similar object.  Not used
    directly, but subclassed (in domain-specific directives) to add custom
    behavior.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'noindex': directives.flag,
    }  # type: Dict[str, DirectiveOption]

    # types of doc fields that this directive handles, see sphinx.util.docfields
    doc_field_types = []    # type: List[Field]
    domain = None           # type: str
    objtype = None          # type: str
    indexnode = None        # type: addnodes.index

    # Warning: this might be removed in future version. Don't touch this from extensions.
    _doc_field_type_map = {}  # type: Dict[str, Tuple[Field, bool]]

    def get_field_type_map(self):
        # type: () -> Dict[str, Tuple[Field, bool]]
        if self._doc_field_type_map == {}:
            self._doc_field_type_map = {}
            for field in self.doc_field_types:
                for name in field.names:
                    self._doc_field_type_map[name] = (field, False)

                if field.is_typed:
                    typed_field = cast(TypedField, field)
                    for name in typed_field.typenames:
                        self._doc_field_type_map[name] = (field, True)

        return self._doc_field_type_map

    def get_signatures(self):
        # type: () -> List[str]
        """
        Retrieve the signatures to document from the directive arguments.  By
        default, signatures are given as arguments, one per line.

        Backslash-escaping of newlines is supported.
        """
        lines = nl_escape_re.sub('', self.arguments[0]).split('\n')
        # remove backslashes to support (dummy) escapes; helps Vim highlighting
        return [strip_backslash_re.sub(r'\1', line.strip()) for line in lines]

    def handle_signature(self, sig, signode):
        # type: (str, addnodes.desc_signature) -> Any
        """
        Parse the signature *sig* into individual nodes and append them to
        *signode*. If ValueError is raised, parsing is aborted and the whole
        *sig* is put into a single desc_name node.

        The return value should be a value that identifies the object.  It is
        passed to :meth:`add_target_and_index()` unchanged, and otherwise only
        used to skip duplicates.
        """
        raise ValueError

    def add_target_and_index(self, name, sig, signode):
        # type: (Any, str, addnodes.desc_signature) -> None
        """
        Add cross-reference IDs and entries to self.indexnode, if applicable.

        *name* is whatever :meth:`handle_signature()` returned.
        """
        return  # do nothing by default

    def before_content(self):
        # type: () -> None
        """
        Called before parsing content. Used to set information about the current
        directive context on the build environment.
        """
        pass

    def after_content(self):
        # type: () -> None
        """
        Called after parsing content. Used to reset information about the
        current directive context on the build environment.
        """
        pass

    def run(self):
        # type: () -> List[nodes.Node]
        """
        Main directive entry function, called by docutils upon encountering the
        directive.

        This directive is meant to be quite easily subclassable, so it delegates
        to several additional methods.  What it does:

        * find out if called as a domain-specific directive, set self.domain
        * create a `desc` node to fit all description inside
        * parse standard options, currently `noindex`
        * create an index node if needed as self.indexnode
        * parse all given signatures (as returned by self.get_signatures())
          using self.handle_signature(), which should either return a name
          or raise ValueError
        * add index entries using self.add_target_and_index()
        * parse the content and handle doc fields in it
        """
        if ':' in self.name:
            self.domain, self.objtype = self.name.split(':', 1)
        else:
            self.domain, self.objtype = '', self.name
        self.indexnode = addnodes.index(entries=[])

        node = addnodes.desc()
        node.document = self.state.document
        node['domain'] = self.domain
        # 'desctype' is a backwards compatible attribute
        node['objtype'] = node['desctype'] = self.objtype
        node['noindex'] = noindex = ('noindex' in self.options)

        self.names = []  # type: List[Any]
        signatures = self.get_signatures()
        for i, sig in enumerate(signatures):
            # add a signature node for each signature in the current unit
            # and add a reference target for it
            signode = addnodes.desc_signature(sig, '')
            signode['first'] = False
            node.append(signode)
            try:
                # name can also be a tuple, e.g. (classname, objname);
                # this is strictly domain-specific (i.e. no assumptions may
                # be made in this base class)
                name = self.handle_signature(sig, signode)
            except ValueError:
                # signature parsing failed
                signode.clear()
                signode += addnodes.desc_name(sig, sig)
                continue  # we don't want an index entry here
            if name not in self.names:
                self.names.append(name)
                if not noindex:
                    # only add target and index entry if this is the first
                    # description of the object with this name in this desc block
                    self.add_target_and_index(name, sig, signode)

        contentnode = addnodes.desc_content()
        node.append(contentnode)
        if self.names:
            # needed for association of version{added,changed} directives
            self.env.temp_data['object'] = self.names[0]
        self.before_content()
        self.state.nested_parse(self.content, self.content_offset, contentnode)
        DocFieldTransformer(self).transform_all(contentnode)
        self.env.temp_data['object'] = None
        self.after_content()
        return [self.indexnode, node]


class DefaultRole(SphinxDirective):
    """
    Set the default interpreted text role.  Overridden from docutils.
    """

    optional_arguments = 1
    final_argument_whitespace = False

    def run(self):
        # type: () -> List[nodes.Node]
        if not self.arguments:
            docutils.unregister_role('')
            return []
        role_name = self.arguments[0]
        role, messages = roles.role(role_name, self.state_machine.language,
                                    self.lineno, self.state.reporter)
        if role:
            docutils.register_role('', role)
            self.env.temp_data['default_role'] = role_name
        else:
            literal_block = nodes.literal_block(self.block_text, self.block_text)
            reporter = self.state.reporter
            error = reporter.error('Unknown interpreted text role "%s".' % role_name,
                                   literal_block, line=self.lineno)
            messages += [error]

        return cast(List[nodes.Node], messages)


class DefaultDomain(SphinxDirective):
    """
    Directive to (re-)set the default domain for this source file.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}  # type: Dict

    def run(self):
        # type: () -> List[nodes.Node]
        domain_name = self.arguments[0].lower()
        # if domain_name not in env.domains:
        #     # try searching by label
        #     for domain in env.domains.values():
        #         if domain.label.lower() == domain_name:
        #             domain_name = domain.name
        #             break
        self.env.temp_data['default_domain'] = self.env.domains.get(domain_name)
        return []

from sphinx.directives.code import (  # noqa
    Highlight, CodeBlock, LiteralInclude
)
from sphinx.directives.other import (  # noqa
    TocTree, Author, Index, VersionChange, SeeAlso,
    TabularColumns, Centered, Acks, HList, Only, Include, Class
)
from sphinx.directives.patches import (  # noqa
    Figure, Meta
)

deprecated_alias('sphinx.directives',
                 {
                     'Highlight': Highlight,
                     'CodeBlock': CodeBlock,
                     'LiteralInclude': LiteralInclude,
                     'TocTree': TocTree,
                     'Author': Author,
                     'Index': Index,
                     'VersionChange': VersionChange,
                     'SeeAlso': SeeAlso,
                     'TabularColumns': TabularColumns,
                     'Centered': Centered,
                     'Acks': Acks,
                     'HList': HList,
                     'Only': Only,
                     'Include': Include,
                     'Class': Class,
                     'Figure': Figure,
                     'Meta': Meta,
                 },
                 RemovedInSphinx40Warning)


# backwards compatible old name (will be marked deprecated in 3.0)
DescDirective = ObjectDescription


def setup(app):
    # type: (Sphinx) -> Dict[str, Any]
    directives.register_directive('default-role', DefaultRole)
    directives.register_directive('default-domain', DefaultDomain)
    directives.register_directive('describe', ObjectDescription)
    # new, more consistent, name
    directives.register_directive('object', ObjectDescription)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
