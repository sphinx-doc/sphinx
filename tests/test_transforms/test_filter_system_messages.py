from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from docutils import nodes

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.parametrize('keep_warnings', [False, True])
@pytest.mark.parametrize(
    'content',
    ['An unmatched *asterisk.', '`link<address`_', 'Unknown |substitution|.'],
)
def test_problematic_system_message_links(
    make_app: Callable[..., SphinxTestApp],
    tmp_path: Path,
    content: str,
    keep_warnings: bool,
) -> None:
    tmp_path.joinpath('conf.py').touch()
    tmp_path.joinpath('index.rst').write_text(content, encoding='utf-8')
    app = make_app(
        srcdir=tmp_path,
        buildername='html',
        confoverrides={'keep_warnings': keep_warnings},
    )
    app.build()
    doctree = app.env.get_doctree('index')
    problematic = list(doctree.findall(nodes.problematic))
    messages = list(doctree.findall(nodes.system_message))
    html = app.outdir.joinpath('index.html').read_text(encoding='utf-8')

    assert app.warning.getvalue()
    assert next(doctree.findall(nodes.paragraph)).astext() == content
    if keep_warnings:
        assert problematic
        assert messages
        for node in problematic:
            target = doctree.ids[node['refid']]
            assert isinstance(target, nodes.system_message)
            assert target in messages
            assert f'href="#{node["refid"]}"' in html
            assert f'id="{node["refid"]}"' in html
    else:
        assert not problematic
        assert not messages
        assert not any(
            isinstance(node, nodes.system_message | nodes.problematic)
            for node in doctree.ids.values()
        )
        assert 'class="problematic"' not in html
