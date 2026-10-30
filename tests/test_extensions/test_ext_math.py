"""Test math extensions."""

from __future__ import annotations

import re
import shutil
import subprocess
import warnings
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from docutils import nodes
from docutils.utils import new_document

from sphinx.ext import imgmath as imgmath_mod
from sphinx.ext.mathjax import MATHJAX_URL
from sphinx.testing.util import assert_node
from sphinx.util._pathlib import _StrPath

from tests.utils import extract_node

if TYPE_CHECKING:
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp

FAKE_MATHJAX_URL = 'https://example.org/fake-mathjax.js'


def has_binary(binary: str) -> bool:
    try:
        subprocess.check_output([binary])
    except FileNotFoundError:
        return False
    except OSError:
        pass
    return True


def _mock_imgmath_config(**overrides: object) -> MagicMock:
    config = MagicMock()
    config.imgmath_font_size = 12
    config.imgmath_latex_preamble = ''
    config.imgmath_use_preview = False
    config.imgmath_image_format = 'png'
    config.imgmath_batch_size = 2
    config.imgmath_latex = 'latex'
    config.imgmath_latex_args = []
    config.imgmath_dvipng = 'dvipng'
    config.imgmath_dvipng_args = []
    config.imgmath_dvisvgm = 'dvisvgm'
    config.imgmath_dvisvgm_args = []
    config.templates_path = []
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


def test_imgmath_build_batch_document_png() -> None:
    config = _mock_imgmath_config()
    doc = imgmath_mod._build_batch_document(
        ['$a$', '$b$'], config=config, image_format='png'
    )
    assert doc.count(r'\clearpage') == 1
    assert r'\begin{document}' in doc
    assert '$a$' in doc
    assert '$b$' in doc
    # png uses tightpage='' so no dvips option
    assert 'preview' not in doc
    # single equation has no separator
    single = imgmath_mod._build_batch_document(
        ['$a$'], config=config, image_format='png'
    )
    assert r'\clearpage' not in single


def test_imgmath_build_batch_document_svg_preview() -> None:
    config = _mock_imgmath_config(imgmath_use_preview=True)
    doc = imgmath_mod._build_batch_document(
        ['$a$', '$b$'], config=config, image_format='svg'
    )
    assert r'\usepackage[active,dvips,tightpage]{preview}' in doc
    assert doc.count(r'\begin{preview}') == 2
    assert doc.count(r'\end{preview}') == 2
    assert r'\usepackage{amsmath}' in doc


def test_imgmath_has_custom_template(tmp_path: Path) -> None:
    confdir = _StrPath(tmp_path)
    config = _mock_imgmath_config()
    assert imgmath_mod._has_custom_template(config, confdir) is False
    template_dir = tmp_path / '_templates'
    template_dir.mkdir()
    config.templates_path = ['_templates']
    assert imgmath_mod._has_custom_template(config, confdir) is False
    (template_dir / 'template.tex.jinja').write_text('custom', encoding='utf-8')
    assert imgmath_mod._has_custom_template(config, confdir) is True
    # absolute templates_path is honoured
    config.templates_path = [str(template_dir)]
    assert imgmath_mod._has_custom_template(config, confdir) is True


def test_imgmath_collect_math_expressions_dedupes() -> None:
    doc1 = new_document('<test>')
    doc1 += nodes.math('', 'E=mc^2')
    doc1 += nodes.math_block('', 'a^2', number=None)
    doc2 = new_document('<test>')
    doc2 += nodes.math('', 'E=mc^2')  # duplicate inline
    env = MagicMock()
    env.all_docs = {'index': 0, 'other': 0}
    env.get_doctree.side_effect = [doc1, doc2]
    maths = imgmath_mod._collect_math_expressions(env)
    assert maths[0] == '$E=mc^2$'
    assert len(maths) == 2  # duplicate removed
    # unreadable doctree is skipped, not fatal
    env.get_doctree.side_effect = Exception('boom')
    env.all_docs = {'broken': 0}
    assert imgmath_mod._collect_math_expressions(env) == []


def test_imgmath_pre_render_batch_disabled() -> None:
    app = MagicMock()
    app.config.imgmath_batch_size = 1
    imgmath_mod.pre_render_batch(app, MagicMock())
    app.builder.assert_not_called()
    # invalid image format is ignored
    app.config.imgmath_batch_size = 10
    app.config.imgmath_image_format = 'bogus'
    app.builder.format = 'html'
    imgmath_mod.pre_render_batch(app, MagicMock())
    # non-html builders are ignored
    app.config.imgmath_image_format = 'png'
    app.builder.format = 'latex'
    imgmath_mod.pre_render_batch(app, MagicMock())


def test_imgmath_render_batch_chunk_skips_cached(tmp_path: Path) -> None:
    cached = tmp_path / 'cached.png'
    cached.write_bytes(b'x')
    config = _mock_imgmath_config()
    builder = MagicMock()
    with patch.object(imgmath_mod, '_compile_batch_document') as compile_batch:
        imgmath_mod._render_batch_chunk(
            ['$a$'],
            [cached],
            config=config,
            confdir=_StrPath(tmp_path),
            builder=builder,
            image_format='png',
        )
    compile_batch.assert_not_called()


def test_imgmath_render_batch_chunk_falls_back_to_single(tmp_path: Path) -> None:
    from sphinx.ext.imgmath import MathExtError

    out = tmp_path / 'out.png'
    config = _mock_imgmath_config()
    builder = MagicMock()
    with (
        patch.object(
            imgmath_mod,
            '_compile_batch_document',
            side_effect=MathExtError('latex boom'),
        ),
        patch.object(imgmath_mod, '_compile_single_math') as single,
    ):
        imgmath_mod._render_batch_chunk(
            ['$a$'],
            [out],
            config=config,
            confdir=_StrPath(tmp_path),
            builder=builder,
            image_format='png',
        )
    single.assert_called_once()


@pytest.mark.skipif(
    not has_binary('dvipng'),
    reason='Requires dvipng" binary',
)
@pytest.mark.sphinx(
    'html',
    testroot='ext-math-simple',
    confoverrides={'extensions': ['sphinx.ext.imgmath']},
)
def test_imgmath_png(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    if "LaTeX command 'latex' cannot be run" in app.warning.getvalue():
        msg = 'LaTeX command "latex" is not available'
        raise pytest.skip.Exception(msg)
    if "dvipng command 'dvipng' cannot be run" in app.warning.getvalue():
        msg = 'dvipng command "dvipng" is not available'
        raise pytest.skip.Exception(msg)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    shutil.rmtree(app.outdir)
    html = (
        r'<div class="math">\s*<p>\s*<img src="_images/math/\w+.png"'
        r'\s*alt="a\^2\+b\^2=c\^2"/>\s*</p>\s*</div>'
    )
    assert re.search(html, content, re.DOTALL)


@pytest.mark.skipif(
    not has_binary('dvisvgm'),
    reason='Requires dvisvgm" binary',
)
@pytest.mark.sphinx(
    'html',
    testroot='ext-math-simple',
    confoverrides={'extensions': ['sphinx.ext.imgmath'], 'imgmath_image_format': 'svg'},
)
def test_imgmath_svg(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    if "LaTeX command 'latex' cannot be run" in app.warning.getvalue():
        msg = 'LaTeX command "latex" is not available'
        raise pytest.skip.Exception(msg)
    if "dvisvgm command 'dvisvgm' cannot be run" in app.warning.getvalue():
        msg = 'dvisvgm command "dvisvgm" is not available'
        raise pytest.skip.Exception(msg)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    shutil.rmtree(app.outdir)
    html = (
        r'<div class="math">\s*<p>\s*<img src="_images/math/\w+.svg"'
        r'\s*alt="a\^2\+b\^2=c\^2"/>\s*</p>\s*</div>'
    )
    assert re.search(html, content, re.DOTALL)


@pytest.mark.skipif(
    not has_binary('dvipng'),
    reason='Requires dvipng" binary',
)
@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.imgmath'],
        'imgmath_batch_size': 2,
    },
)
def test_imgmath_batch_png(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    if "LaTeX command 'latex' cannot be run" in app.warning.getvalue():
        msg = 'LaTeX command "latex" is not available'
        raise pytest.skip.Exception(msg)
    if "dvipng command 'dvipng' cannot be run" in app.warning.getvalue():
        msg = 'dvipng command "dvipng" is not available'
        raise pytest.skip.Exception(msg)
    warning = app.warning.getvalue()
    assert 'latex exited with error' not in warning
    assert 'Batch LaTeX compilation failed' not in warning

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    math_images = list((app.outdir / '_images' / 'math').glob('*.png'))
    try:
        # inline and display math are both rendered
        assert re.search(
            r'<img class="math" src="_images/math/[0-9a-f]{40}\.png"', content
        )
        assert '<div class="math">' in content
        # all images are non-empty and deterministically named (sha1)
        assert len(math_images) >= 2
        assert all(p.stat().st_size > 0 for p in math_images)
    finally:
        shutil.rmtree(app.outdir)


@pytest.mark.skipif(
    not has_binary('dvisvgm'),
    reason='Requires dvisvgm" binary',
)
@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.imgmath'],
        'imgmath_image_format': 'svg',
        'imgmath_batch_size': 2,
    },
)
def test_imgmath_batch_svg(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    if "LaTeX command 'latex' cannot be run" in app.warning.getvalue():
        msg = 'LaTeX command "latex" is not available'
        raise pytest.skip.Exception(msg)
    if "dvisvgm command 'dvisvgm' cannot be run" in app.warning.getvalue():
        msg = 'dvisvgm command "dvisvgm" is not available'
        raise pytest.skip.Exception(msg)
    warning = app.warning.getvalue()
    assert 'latex exited with error' not in warning
    assert 'Batch LaTeX compilation failed' not in warning

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    math_images = list((app.outdir / '_images' / 'math').glob('*.svg'))
    try:
        assert re.search(
            r'<img class="math" src="_images/math/[0-9a-f]{40}\.svg"', content
        )
        assert '<div class="math">' in content
        assert len(math_images) >= 2
        assert all(p.stat().st_size > 0 for p in math_images)
    finally:
        shutil.rmtree(app.outdir)


@pytest.mark.skipif(
    not has_binary('dvisvgm'),
    reason='Requires dvisvgm" binary',
)
@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.imgmath'],
        'imgmath_image_format': 'svg',
        'imgmath_embed': True,
        'imgmath_batch_size': 2,
    },
)
def test_imgmath_batch_svg_embed(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    if "LaTeX command 'latex' cannot be run" in app.warning.getvalue():
        msg = 'LaTeX command "latex" is not available'
        raise pytest.skip.Exception(msg)
    if "dvisvgm command 'dvisvgm' cannot be run" in app.warning.getvalue():
        msg = 'dvisvgm command "dvisvgm" is not available'
        raise pytest.skip.Exception(msg)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    try:
        # embed mode renders inline + display math without separate files
        assert re.search(r'<img src="data:image/svg\+xml;base64,[\w+/=]+"', content)
        assert re.search(r'<img class="math" src="data:image/svg\+xml;base64,', content)
    finally:
        shutil.rmtree(app.outdir)


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.imgmath'],
        'imgmath_image_format': 'svg',
        'imgmath_batch_size': 100,
    },
)
def test_imgmath_batch_single_latex_invocation(app: SphinxTestApp) -> None:
    """Batching compiles N equations with fewer LaTeX processes (mocked)."""
    from pathlib import Path as _Path

    latex_calls = 0
    convert_calls = 0

    real_build = imgmath_mod._build_batch_document

    def fake_compile_batch(_combined: str, *, config: object) -> _Path:
        nonlocal latex_calls
        latex_calls += 1
        assert r'\clearpage' in _combined or _combined.count('$') >= 2
        return _Path('/nonexistent/math.dvi')

    def fake_convert_dvi_to_svg(
        _dvipath: _Path, out_path: _Path, *, config: object, page: int | None = None
    ) -> None:
        nonlocal convert_calls
        convert_calls += 1
        assert page is not None
        assert page >= 1
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b'<svg></svg>')

    with (
        patch.object(imgmath_mod, '_compile_batch_document', fake_compile_batch),
        patch.object(imgmath_mod, '_build_batch_document', real_build),
        patch.object(imgmath_mod, 'convert_dvi_to_svg', fake_convert_dvi_to_svg),
    ):
        app.build(force_all=True)

    maths = imgmath_mod._collect_math_expressions(app.env)
    assert len(maths) >= 2
    # one LaTeX call for the whole batch, one convert per equation
    assert latex_calls == 1
    assert convert_calls == len(maths)
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    shutil.rmtree(app.outdir)
    assert re.search(r'<img class="math" src="_images/math/\w+\.svg"', content)


@pytest.mark.skipif(
    not has_binary('dvisvgm'),
    reason='Requires dvisvgm" binary',
)
@pytest.mark.sphinx(
    'html',
    testroot='ext-math-simple',
    confoverrides={
        'extensions': ['sphinx.ext.imgmath'],
        'imgmath_image_format': 'svg',
        'imgmath_embed': True,
    },
)
def test_imgmath_svg_embed(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    if "LaTeX command 'latex' cannot be run" in app.warning.getvalue():
        msg = 'LaTeX command "latex" is not available'
        raise pytest.skip.Exception(msg)
    if "dvisvgm command 'dvisvgm' cannot be run" in app.warning.getvalue():
        msg = 'dvisvgm command "dvisvgm" is not available'
        raise pytest.skip.Exception(msg)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    shutil.rmtree(app.outdir)
    html = r'<img src="data:image/svg\+xml;base64,[\w\+/=]+"'
    assert re.search(html, content, re.DOTALL)


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'mathjax_options': {'integrity': 'sha384-0123456789'},
    },
)
def test_mathjax_options(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    shutil.rmtree(app.outdir)
    assert (
        '<script defer="defer" integrity="sha384-0123456789" '
        f'src="{MATHJAX_URL}">'
        '</script>'
    ) in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_mathjax_align(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    shutil.rmtree(app.outdir)
    html = (
        r'<div class="math notranslate nohighlight">\s*'
        r'\\\[ \\begin\{align\}\\begin\{aligned\}S \&amp;= \\pi r\^2\\\\'
        r'V \&amp;= \\frac\{4\}\{3\} \\pi r\^3\\end\{aligned\}\\end\{align\} \\\]</div>'
    )
    assert re.search(html, content, re.DOTALL)


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={'math_number_all': True, 'extensions': ['sphinx.ext.mathjax']},
)
def test_math_number_all_mathjax(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    html = (
        r'<div class="math notranslate nohighlight" id="equation-index-0">\s*'
        r'<span class="eqno">\(1\)<a .*>\xb6</a></span>\\\[a\^2\+b\^2=c\^2\\\]</div>'
    )
    assert re.search(html, content, re.DOTALL)


@pytest.mark.sphinx(
    'latex',
    testroot='ext-math',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_math_number_all_latex(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')
    macro = (
        r'\\begin{equation\*}\s*'
        r'\\begin{split}a\^2\+b\^2=c\^2\\end{split}\s*'
        r'\\end{equation\*}'
    )
    assert re.search(macro, content, re.DOTALL)

    macro = r'Inline \\\(E=mc\^2\\\)'
    assert re.search(macro, content, re.DOTALL)

    macro = (
        r'\\begin{equation\*}\s*'
        r'\\begin{split}e\^{i\\pi}\+1=0\\end{split}\s+'
        r'\\end{equation\*}'
    )
    assert re.search(macro, content, re.DOTALL)

    macro = (
        r'\\begin{align\*}\\!\\begin{aligned}\s*'
        r'S &= \\pi r\^2\\\\\s*'
        r'V &= \\frac\{4}\{3} \\pi r\^3\\\\\s*'
        r'\\end{aligned}\\end{align\*}'
    )
    assert re.search(macro, content, re.DOTALL)

    macro = r'Referencing equation \\eqref{equation:math:foo}.'
    assert re.search(macro, content, re.DOTALL)


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'math_eqref_format': 'Eq.{number}',
    },
)
def test_math_eqref_format_html(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'math.html').read_text(encoding='utf8')
    html = (
        '<p>Referencing equation <a class="reference internal" '
        'href="#equation-foo">Eq.1</a> and <a class="reference internal" '
        'href="#equation-foo">Eq.1</a>.</p>'
    )
    assert html in content


@pytest.mark.sphinx(
    'latex',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'math_eqref_format': 'Eq.{number}',
    },
)
def test_math_eqref_format_latex(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')
    macro = (
        r'Referencing equation Eq.\\ref{equation:math:foo} and '
        r'Eq.\\ref{equation:math:foo}.'
    )
    assert re.search(macro, content, re.DOTALL)


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'numfig': True,
        'math_numfig': True,
    },
)
def test_mathjax_numfig_html(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'math.html').read_text(encoding='utf8')
    html = (
        '<div class="math notranslate nohighlight" id="equation-math-0">\n'
        '<span class="eqno">(1.2)'
    )
    assert html in content
    html = (
        '<p>Referencing equation <a class="reference internal" '
        'href="#equation-foo">(1.1)</a> and '
        '<a class="reference internal" href="#equation-foo">(1.1)</a>.</p>'
    )
    assert html in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'numfig': True,
        'math_numfig': True,
        'math_numsep': '-',
    },
)
def test_mathjax_numsep_html(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'math.html').read_text(encoding='utf8')
    html = (
        '<div class="math notranslate nohighlight" id="equation-math-0">\n'
        '<span class="eqno">(1-2)'
    )
    assert html in content
    html = (
        '<p>Referencing equation <a class="reference internal" '
        'href="#equation-foo">(1-1)</a> and '
        '<a class="reference internal" href="#equation-foo">(1-1)</a>.</p>'
    )
    assert html in content


@pytest.mark.usefixtures('_http_teapot')
@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.imgmath'],
        'numfig': True,
        'numfig_secnum_depth': 0,
        'math_numfig': True,
    },
)
def test_imgmath_numfig_html(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'page.html').read_text(encoding='utf8')
    html = '<span class="eqno">(3)<a class="headerlink" href="#equation-bar"'
    assert html in content
    html = (
        '<p>Referencing equations <a class="reference internal" '
        'href="math.html#equation-foo">(1)</a> and '
        '<a class="reference internal" href="#equation-bar">(3)</a>.</p>'
    )
    assert html in content


@pytest.mark.sphinx('dummy', testroot='ext-math-compat')
def test_math_compat(app: SphinxTestApp) -> None:
    with warnings.catch_warnings(record=True):
        app.build(force_all=True)
        doctree = app.env.get_and_resolve_doctree('index', app.builder, tags=app.tags)
        assert_node(
            doctree,
            [
                nodes.document,
                nodes.section,
                (
                    nodes.title,
                    [nodes.section, (nodes.title, nodes.paragraph)],
                    nodes.section,
                ),
            ],
        )
        assert_node(
            extract_node(doctree, 0, 1, 1),
            (
                'Inline: ',
                [nodes.math, 'E=mc^2'],
                '\nInline my math: ',
                [nodes.math, 'E = mc^2'],
            ),
        )
        assert_node(
            extract_node(doctree, 0, 2),
            (
                [nodes.title, 'block'],
                [nodes.math_block, 'a^2+b^2=c^2\n\n'],
                [nodes.paragraph, 'Second math'],
                [nodes.math_block, 'e^{i\\pi}+1=0\n\n'],
                [nodes.paragraph, 'Multi math equations'],
                [nodes.math_block, 'E = mc^2'],
            ),
        )


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'mathjax4_config': {'extensions': ['tex2jax.js']},
    },
)
def test_mathjax4_config(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content
    assert '<script defer="defer" src="%s">' % MATHJAX_URL in content
    assert '<script>window.MathJax = {"extensions": ["tex2jax.js"]}</script>' in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'mathjax3_config': {'extensions': ['tex2jax.js']},
        'mathjax_path': FAKE_MATHJAX_URL,
    },
)
def test_mathjax3_config(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert FAKE_MATHJAX_URL in content
    assert f'<script defer="defer" src="{FAKE_MATHJAX_URL}">' in content
    assert '<script>window.MathJax = {"extensions": ["tex2jax.js"]}</script>' in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'mathjax_config_path': '_static/custom_mathjax_config.js',
    },
)
def test_mathjax_config_path_config(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content
    assert f'<script defer="defer" src="{MATHJAX_URL}">' in content
    assert (
        '<script>window.MathJax = {"extensions": ["tex2jax.js"]}\n</script>'
    ) in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'mathjax2_config': {'extensions': ['tex2jax.js']},
        'mathjax_path': FAKE_MATHJAX_URL,
    },
)
def test_mathjax2_config(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert f'<script async="async" src="{FAKE_MATHJAX_URL}">' in content
    assert (
        '<script type="text/x-mathjax-config">'
        'MathJax.Hub.Config({"extensions": ["tex2jax.js"]})'
        '</script>'
    ) in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'mathjax_options': {'async': 'async'},
        'mathjax4_config': {'extensions': ['tex2jax.js']},
    },
)
def test_mathjax_options_async_for_mathjax4(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content
    assert '<script async="async" src="%s">' % MATHJAX_URL in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'mathjax_options': {'defer': 'defer'},
        'mathjax2_config': {'extensions': ['tex2jax.js']},
    },
)
def test_mathjax_options_defer_for_mathjax2(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<script defer="defer" src="%s">' % MATHJAX_URL in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'mathjax_path': 'MathJax.js',
    },
)
def test_mathjax_path(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<script defer="defer" src="_static/MathJax.js"></script>' in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={
        'extensions': ['sphinx.ext.mathjax'],
        'mathjax_path': 'MathJax.js?config=scipy-mathjax',
    },
)
def test_mathjax_path_config(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<script defer="defer" src="_static/MathJax.js?config=scipy-mathjax"></script>'
    ) in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_mathjax_is_installed_only_if_document_having_math(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content

    content = (app.outdir / 'nomath.html').read_text(encoding='utf8')
    assert MATHJAX_URL not in content


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_mathjax_is_not_installed_if_no_equations(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert 'MathJax.js' not in content
    assert MATHJAX_URL not in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_mathjax_is_installed_if_no_equations_when_forced(app: SphinxTestApp) -> None:
    app.set_html_assets_policy('always')
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content

    content = (app.outdir / 'nomath.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math-include',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_mathjax_is_installed_if_included_file_has_equations(
    app: SphinxTestApp,
) -> None:
    app.build(force_all=True)

    # no real equations at the rst level, but includes "included"
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content

    # no real equations at the rst level, but includes "math.rst"
    content = (app.outdir / 'included.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content

    content = (app.outdir / 'math.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content


@pytest.mark.sphinx(
    'singlehtml',
    testroot='ext-math',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_mathjax_is_installed_only_if_document_having_math_singlehtml(
    app: SphinxTestApp,
) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content


@pytest.mark.sphinx(
    'singlehtml',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_mathjax_is_not_installed_if_no_equations_singlehtml(
    app: SphinxTestApp,
) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert 'MathJax.js' not in content
    assert MATHJAX_URL not in content


@pytest.mark.sphinx(
    'singlehtml',
    testroot='ext-math-include',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_mathjax_is_installed_if_included_file_has_equations_singlehtml(
    app: SphinxTestApp,
) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert MATHJAX_URL in content


@pytest.mark.sphinx(
    'html',
    testroot='ext-math-duplicate-label',
    confoverrides={'extensions': ['sphinx.ext.mathjax'], 'show_warning_types': True},
)
def test_duplicate_equation_label_warning_type(app: SphinxTestApp) -> None:
    """Test that duplicate equation labels emit warnings with type ref.equation."""
    app.build(force_all=True)

    from sphinx._cli.util.errors import strip_escape_sequences

    warnings = strip_escape_sequences(app.warning.getvalue())
    assert 'WARNING: duplicate label of equation duplicated' in warnings
    assert '[ref.equation]' in warnings
