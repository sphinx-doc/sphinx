from __future__ import annotations

from typing import TYPE_CHECKING

import pygments
import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx(
    'html',
    testroot='reST-code-block',
    confoverrides={'html_codeblock_linenos_style': 'table'},
)
def test_html_codeblock_linenos_style_table(app: SphinxTestApp) -> None:
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert (
        '<div class="linenodiv"><pre><span class="normal">1</span>\n'
        '<span class="normal">2</span>\n'
        '<span class="normal">3</span>\n'
        '<span class="normal">4</span></pre></div>'
    ) in content


@pytest.mark.sphinx(
    'html',
    testroot='reST-code-block',
    confoverrides={'html_codeblock_linenos_style': 'inline'},
)
def test_html_codeblock_linenos_style_inline(app: SphinxTestApp) -> None:
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert '<span class="linenos">1</span>' in content


@pytest.mark.sphinx('html', testroot='reST-code-role')
def test_html_code_role(app: SphinxTestApp) -> None:
    if tuple(map(int, pygments.__version__.split('.')[:2])) >= (2, 19):
        sp = '<span class="w"> </span>'
    else:
        sp = ' '

    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    common_content = (
        f'<span class="k">def</span>{sp}<span class="nf">foo</span>'
        '<span class="p">(</span>'
        '<span class="mi">1</span> '
        '<span class="o">+</span> '
        '<span class="mi">2</span> '
        '<span class="o">+</span> '
        '<span class="kc">None</span> '
        '<span class="o">+</span> '
        '<span class="s2">&quot;abc&quot;</span>'
        '<span class="p">):</span> '
        '<span class="k">pass</span>'
    )
    assert (
        '<p>Inline <code class="code highlight python docutils literal highlight-python">'
        + common_content
        + '</code> code block</p>'
    ) in content
    assert (
        '<div class="highlight-python notranslate">'
        '<div class="highlight"><pre><span></span>' + common_content
    ) in content
