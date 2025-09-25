from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING

from docutils import nodes

from sphinx import addnodes
from sphinx.domains.cpp._ids import (
    _id_shorthands_v1,
)
from sphinx.util.cfamily import (
    NoOldIdError,
    verify_description_mode,
)

if TYPE_CHECKING:
    from typing import Any

    from docutils.nodes import TextElement

    from sphinx.addnodes import desc_signature
    from sphinx.domains.cpp._symbol import Symbol
    from sphinx.domains.cpp.ast_base import ASTBase
    from sphinx.domains.cpp.ast_operators import ASTOperator
    from sphinx.domains.cpp.ast_templates import ASTTemplateArgs
    from sphinx.environment import BuildEnvironment
    from sphinx.util.cfamily import StringifyTransform


class ASTIdentifier(ASTBase):
    """Represents an identifier in the AST."""

    def __init__(self, name: str) -> None:
        if not isinstance(name, str) or len(name) == 0:
            raise AssertionError
        self.name = sys.intern(name)
        self.is_anonymous = name[0] == '@'

    # ASTBaseBase already implements this method,
    # but specialising it here improves performance
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTIdentifier):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def _stringify(self, transform: StringifyTransform) -> str:
        return transform(self.name)

    def is_anon(self) -> bool:
        return self.is_anonymous

    def get_id(self, version: int) -> str:
        if self.is_anonymous and version < 3:
            raise NoOldIdError
        if version == 1:
            if self.name == 'size_t':
                return 's'
            else:
                return self.name
        if self.name == 'std':
            return 'St'
        elif self.name[0] == '~':
            # a destructor, just use an arbitrary version of dtors
            return 'D0'
        else:
            if self.is_anonymous:
                return 'Ut%d_%s' % (len(self.name) - 1, self.name[1:])
            else:
                return str(len(self.name)) + self.name

    # and this is where we finally make a difference between __str__ and the display string

    def __str__(self) -> str:
        return self.name

    def get_display_string(self) -> str:
        return '[anonymous]' if self.is_anonymous else self.name

    def describe_signature(
        self,
        signode: TextElement,
        mode: str,
        env: BuildEnvironment,
        prefix: str,
        templateArgs: str,
        symbol: Symbol,
    ) -> None:
        verify_description_mode(mode)
        if self.is_anonymous:
            node = addnodes.desc_sig_name(text='[anonymous]')
        else:
            node = addnodes.desc_sig_name(self.name, self.name)
        if mode == 'markType':
            target_text = prefix + self.name + templateArgs
            pnode = addnodes.pending_xref(
                '',
                refdomain='cpp',
                reftype='identifier',
                reftarget=target_text,
                modname=None,
                classname=None,
            )
            pnode['cpp:parent_key'] = symbol.get_lookup_key()
            pnode += node
            signode += pnode
        elif mode == 'lastIsName':
            name_node = addnodes.desc_name()
            name_node += node
            signode += name_node
        elif mode == 'noneIsName':
            signode += node
        elif mode == 'param':
            node['classes'].append('sig-param')
            signode += node
        elif mode == 'udl':
            # the target is 'operator""id' instead of just 'id'
            assert len(prefix) == 0
            assert len(templateArgs) == 0
            assert not self.is_anonymous
            target_text = 'operator""' + self.name
            pnode = addnodes.pending_xref(
                '',
                refdomain='cpp',
                reftype='identifier',
                reftarget=target_text,
                modname=None,
                classname=None,
            )
            pnode['cpp:parent_key'] = symbol.get_lookup_key()
            pnode += node
            signode += pnode
        else:
            raise Exception('Unknown description mode: %s' % mode)

    @property
    def identifier(self) -> str:
        warnings.warn(
            '`ASTIdentifier.identifier` is deprecated, use `ASTIdentifier.name` instead',
            DeprecationWarning,
            stacklevel=2,
        )
        return self.name


class ASTNestedNameElement(ASTBase):
    """Represents an element in a nested name."""

    def __init__(
        self,
        identOrOp: ASTIdentifier | ASTOperator,
        templateArgs: ASTTemplateArgs | None,
    ) -> None:
        self.identOrOp = identOrOp
        self.templateArgs = templateArgs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTNestedNameElement):
            return NotImplemented
        return (
            self.identOrOp == other.identOrOp
            and self.templateArgs == other.templateArgs
        )

    def __hash__(self) -> int:
        return hash((self.identOrOp, self.templateArgs))

    def is_operator(self) -> bool:
        return False

    def get_id(self, version: int) -> str:
        res = self.identOrOp.get_id(version)
        if self.templateArgs:
            res += self.templateArgs.get_id(version)
        return res

    def _stringify(self, transform: StringifyTransform) -> str:
        res = transform(self.identOrOp)
        if self.templateArgs:
            res += transform(self.templateArgs)
        return res


class ASTNestedName(ASTBase):
    """Represents a nested name (e.g., std::vector)."""

    def __init__(
        self, names: list[ASTNestedNameElement], templates: list[bool], rooted: bool
    ) -> None:
        assert len(names) > 0
        self.names = names
        self.templates = templates
        assert len(self.names) == len(self.templates)
        self.rooted = rooted

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTNestedName):
            return NotImplemented
        return (
            self.names == other.names
            and self.templates == other.templates
            and self.rooted == other.rooted
        )

    def __hash__(self) -> int:
        return hash((self.names, self.templates, self.rooted))

    @property
    def name(self) -> ASTNestedName:
        return self

    def num_templates(self) -> int:
        count = 0
        for n in self.names:
            if n.is_operator():
                continue
            if n.templateArgs:
                count += 1
        return count

    def get_id(self, version: int, modifiers: str = '') -> str:
        if version == 1:
            tt = str(self)
            if tt in _id_shorthands_v1:
                return _id_shorthands_v1[tt]
            else:
                return '::'.join(n.get_id(version) for n in self.names)

        res = []
        if len(self.names) > 1 or len(modifiers) > 0:
            res.append('N')
        res.append(modifiers)
        res.extend(n.get_id(version) for n in self.names)
        if len(self.names) > 1 or len(modifiers) > 0:
            res.append('E')
        return ''.join(res)

    def _stringify(self, transform: StringifyTransform) -> str:
        res = []
        if self.rooted:
            res.append('')
        for i in range(len(self.names)):
            n = self.names[i]
            if self.templates[i]:
                res.append('template ' + transform(n))
            else:
                res.append(transform(n))
        return '::'.join(res)

    def describe_signature(
        self, signode: TextElement, mode: str, env: BuildEnvironment, symbol: Symbol
    ) -> None:
        verify_description_mode(mode)
        # just print the name part, with template args, not template params
        if mode == 'noneIsName':
            if self.rooted:
                unreachable = 'Can this happen?'
                raise AssertionError(unreachable)  # TODO: Can this happen?
                signode += nodes.Text('::')
            for i in range(len(self.names)):
                if i != 0:
                    unreachable = 'Can this happen?'
                    raise AssertionError(unreachable)  # TODO: Can this happen?
                    signode += nodes.Text('::blah')
                n = self.names[i]
                if self.templates[i]:
                    unreachable = 'Can this happen?'
                    raise AssertionError(unreachable)  # TODO: Can this happen?
                    signode += nodes.Text('template')
                    signode += nodes.Text(' ')
                n.describe_signature(signode, mode, env, '', symbol)
        elif mode == 'param':
            assert not self.rooted, str(self)
            assert len(self.names) == 1
            assert not self.templates[0]
            self.names[0].describe_signature(signode, 'param', env, '', symbol)
        elif mode in {'markType', 'lastIsName', 'markName'}:
            # Each element should be a pending xref targeting the complete
            # prefix. however, only the identifier part should be a link, such
            # that template args can be a link as well.
            # For 'lastIsName' we should also prepend template parameter lists.
            template_params: list[Any] = []
            if mode == 'lastIsName':
                assert symbol is not None
                if symbol.declaration.templatePrefix is not None:
                    template_params = symbol.declaration.templatePrefix.templates
            i_template_params = 0
            template_params_prefix = ''
            prefix = ''
            first = True
            names = self.names[:-1] if mode == 'lastIsName' else self.names
            # If lastIsName, then wrap all of the prefix in a desc_addname,
            # else append directly to signode.
            # NOTE: Breathe previously relied on the prefix being in the desc_addname node,
            #       so it can remove it in inner declarations.
            dest = signode
            if mode == 'lastIsName':
                dest = addnodes.desc_addname()
            if self.rooted:
                prefix += '::'
                if mode == 'lastIsName' and len(names) == 0:
                    signode += addnodes.desc_sig_punctuation('::', '::')
                else:
                    dest += addnodes.desc_sig_punctuation('::', '::')
            for i in range(len(names)):
                nne = names[i]
                template = self.templates[i]
                if not first:
                    dest += addnodes.desc_sig_punctuation('::', '::')
                    prefix += '::'
                if template:
                    dest += addnodes.desc_sig_keyword('template', 'template')
                    dest += addnodes.desc_sig_space()
                first = False
                txt_nne = str(nne)
                if txt_nne:
                    if nne.templateArgs and i_template_params < len(template_params):
                        template_params_prefix += str(
                            template_params[i_template_params]
                        )
                        i_template_params += 1
                    nne.describe_signature(
                        dest, 'markType', env, template_params_prefix + prefix, symbol
                    )
                prefix += txt_nne
            if mode == 'lastIsName':
                if len(self.names) > 1:
                    dest += addnodes.desc_sig_punctuation('::', '::')
                    signode += dest
                if self.templates[-1]:
                    signode += addnodes.desc_sig_keyword('template', 'template')
                    signode += addnodes.desc_sig_space()
                self.names[-1].describe_signature(signode, mode, env, '', symbol)
        else:
            raise Exception('Unknown description mode: %s' % mode)


# Define __all__ for this module
__all__ = [
    'ASTIdentifier',
    'ASTNestedNameElement',
    'ASTNestedName',
]
