"""Test math extensions."""

from __future__ import annotations

import re
import shutil
import subprocess
import warnings
from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx.ext.mathjax import MATHJAX_URL
from sphinx.testing.util import assert_node

from tests.utils import extract_node

if TYPE_CHECKING:
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
