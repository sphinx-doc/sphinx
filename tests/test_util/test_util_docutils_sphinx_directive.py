from __future__ import annotations

from types import SimpleNamespace

from docutils import nodes
from docutils.parsers.rst.languages import en as english
from docutils.parsers.rst.states import (
    Inliner,
    RSTState,
    RSTStateMachine,
    state_classes,
)
from docutils.statemachine import StringList
from docutils.utils import Reporter

from sphinx.util.docutils import SphinxDirective, new_document


def make_directive(
    *, env: SimpleNamespace, input_lines: StringList | None = None
) -> SphinxDirective:
    _, directive = make_directive_and_state(env=env, input_lines=input_lines)
    return directive


def make_directive_and_state(
    *, env: SimpleNamespace, input_lines: StringList | None = None
) -> tuple[RSTState, SphinxDirective]:
    sm = RSTStateMachine(state_classes, initial_state='Body')
    sm.reporter = Reporter(source='<tests>', report_level=0, halt_level=0)
    if input_lines is not None:
        sm.input_lines = input_lines
    state = RSTState(sm)
    document = state.document = new_document('<tests>')
    document.settings.env = env
    document.settings.tab_width = 4
    document.settings.pep_references = None
    document.settings.rfc_references = None
    inliner = Inliner()
    inliner.init_customizations(document.settings)
    state.inliner = inliner
    state.parent = document
    state.memo = SimpleNamespace(
        document=document,
        reporter=document.reporter,
        language=english,
        title_styles=[],
        section_level=0,
        section_bubble_up_kludge=False,
        inliner=inliner,
    )
    directive = SphinxDirective(
        name='test_directive',
        arguments=[],
        options={},
        content=StringList(),
        lineno=0,
        content_offset=0,
        block_text='',
        state=state,
        state_machine=sm,
    )
    return state, directive


def test_sphinx_directive_env() -> None:
    state, directive = make_directive_and_state(env=SimpleNamespace())

    assert hasattr(directive, 'env')
    assert directive.env is state.document.settings.env


def test_sphinx_directive_config() -> None:
    env = SimpleNamespace(config=object())
    state, directive = make_directive_and_state(env=env)

    assert hasattr(directive, 'config')
    assert directive.config is directive.env.config
    assert directive.config is state.document.settings.env.config


def test_sphinx_directive_get_source_info() -> None:
    env = SimpleNamespace()
    input_lines = StringList(['spam'], source='<source>')
    directive = make_directive(env=env, input_lines=input_lines)

    assert directive.get_source_info() == ('<source>', 1)


def test_sphinx_directive_set_source_info() -> None:
    env = SimpleNamespace()
    input_lines = StringList(['spam'], source='<source>')
    directive = make_directive(env=env, input_lines=input_lines)

    node = nodes.Element()
    directive.set_source_info(node)
    assert node.source == '<source>'
    assert node.line == 1


def test_sphinx_directive_get_location() -> None:
    env = SimpleNamespace()
    input_lines = StringList(['spam'], source='<source>')
    directive = make_directive(env=env, input_lines=input_lines)

    assert directive.get_location() == '<source>:1'


def test_sphinx_directive_parse_content_to_nodes() -> None:
    directive = make_directive(env=SimpleNamespace())
    content = 'spam\n====\n\nEggs! *Lobster thermidor.*'
    directive.content = StringList(content.split('\n'), source='<source>')

    parsed = directive.parse_content_to_nodes(allow_section_headings=True)
    assert len(parsed) == 1
    node = parsed[0]
    assert isinstance(node, nodes.section)
    assert len(node.children) == 2
    assert isinstance(node.children[0], nodes.title)
    assert node.children[0].astext() == 'spam'
    assert isinstance(node.children[1], nodes.paragraph)
    assert node.children[1].astext() == 'Eggs! Lobster thermidor.'


def test_sphinx_directive_parse_text_to_nodes() -> None:
    directive = make_directive(env=SimpleNamespace())
    content = 'spam\n====\n\nEggs! *Lobster thermidor.*'

    parsed = directive.parse_text_to_nodes(content, allow_section_headings=True)
    assert len(parsed) == 1
    node = parsed[0]
    assert isinstance(node, nodes.section)
    assert len(node.children) == 2
    assert isinstance(node.children[0], nodes.title)
    assert node.children[0].astext() == 'spam'
    assert isinstance(node.children[1], nodes.paragraph)
    assert node.children[1].astext() == 'Eggs! Lobster thermidor.'


def test_sphinx_directive_parse_inline() -> None:
    directive = make_directive(env=SimpleNamespace())
    content = 'Eggs! *Lobster thermidor.*'

    parsed, messages = directive.parse_inline(content)
    assert len(parsed) == 2
    assert messages == []
    assert parsed[0] == nodes.Text('Eggs! ')
    assert isinstance(parsed[1], nodes.emphasis)
    assert parsed[1].rawsource == '*Lobster thermidor.*'
    assert parsed[1][0] == nodes.Text('Lobster thermidor.')
