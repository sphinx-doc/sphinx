"""Render math in HTML via dvipng or dvisvgm."""

from __future__ import annotations

__all__ = ()

import base64
import contextlib
import os
import os.path
import re
import shutil
import subprocess
import tempfile
from hashlib import sha1
from pathlib import Path
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

from docutils import nodes

import sphinx
from sphinx import package_dir
from sphinx.errors import SphinxError
from sphinx.locale import _, __
from sphinx.util import logging
from sphinx.util.math import get_node_equation_number, wrap_displaymath
from sphinx.util.png import read_png_depth, write_png_depth
from sphinx.util.template import LaTeXRenderer

if TYPE_CHECKING:
    from typing import Any

    from docutils.nodes import Element

    from sphinx.application import Sphinx
    from sphinx.config import Config
    from sphinx.util._pathlib import _StrPath
    from sphinx.util.typing import ExtensionMetadata
    from sphinx.writers.html5 import HTML5Translator

logger = logging.getLogger(__name__)

templates_path = package_dir.joinpath('templates', 'imgmath')


class MathExtError(SphinxError):
    category = 'Math extension error'

    def __init__(
        self, msg: str, stderr: str | None = None, stdout: str | None = None
    ) -> None:
        if stderr:
            msg += '\n[stderr]\n' + stderr
        if stdout:
            msg += '\n[stdout]\n' + stdout
        super().__init__(msg)


class InvokeError(SphinxError):
    """errors on invoking converters."""


SUPPORT_FORMAT = ('png', 'svg')

depth_re = re.compile(r'\[\d+ depth=(-?\d+)\]')
depthsvg_re = re.compile(r'.*, depth=(.*)pt')
depthsvgcomment_re = re.compile(r'<!-- DEPTH=(-?\d+) -->')


def read_svg_depth(filename: str | os.PathLike[str]) -> int | None:
    """Read the depth from comment at last line of SVG file"""
    with open(filename, encoding='utf-8') as f:
        for line in f:  # NoQA: B007
            pass
        # Only last line is checked
        matched = depthsvgcomment_re.match(line)
        if matched:
            return int(matched.group(1))
        return None


def write_svg_depth(filename: Path, depth: int) -> None:
    """Write the depth to SVG file as a comment at end of file"""
    with open(filename, 'a', encoding='utf-8') as f:
        f.write('\n<!-- DEPTH=%s -->' % depth)


def generate_latex_macro(
    image_format: str,
    math: str,
    config: Config,
    confdir: _StrPath,
) -> str:
    """Generate LaTeX macro."""
    variables = {
        'fontsize': config.imgmath_font_size,
        'baselineskip': round(config.imgmath_font_size * 1.2),
        'preamble': config.imgmath_latex_preamble,
        # the dvips option is important when imgmath_latex in {"xelatex", "tectonic"},
        # it has no impact when imgmath_latex="latex"
        'tightpage': '' if image_format == 'png' else ',dvips,tightpage',
        'math': math,
    }

    if config.imgmath_use_preview:
        template_name = 'preview.tex'
    else:
        template_name = 'template.tex'

    for template_dir in config.templates_path:
        for template_suffix in ('.jinja', '_t'):
            template = confdir / template_dir / (template_name + template_suffix)
            if template.exists():
                return LaTeXRenderer().render(template, variables)

    return LaTeXRenderer([templates_path]).render(template_name + '.jinja', variables)


def compile_math(latex: str, *, config: Config) -> Path:
    """Compile LaTeX macros for math to DVI."""
    tempdir = Path(tempfile.mkdtemp(suffix='-sphinx-imgmath'))
    filename = tempdir / 'math.tex'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(latex)

    imgmath_latex_name = os.path.basename(config.imgmath_latex)

    # build latex command; old versions of latex don't have the
    # --output-directory option, so we have to manually chdir to the
    # temp dir to run it.
    command = [config.imgmath_latex]
    if imgmath_latex_name != 'tectonic':
        command.append('--interaction=nonstopmode')
    # add custom args from the config file
    command.extend(config.imgmath_latex_args)
    command.append('math.tex')

    try:
        subprocess.run(
            command, capture_output=True, cwd=tempdir, check=True, encoding='ascii'
        )
        if imgmath_latex_name in {'xelatex', 'tectonic'}:
            return tempdir / 'math.xdv'
        else:
            return tempdir / 'math.dvi'
    except OSError as exc:
        logger.warning(
            __(
                'LaTeX command %r cannot be run (needed for math '
                'display), check the imgmath_latex setting'
            ),
            config.imgmath_latex,
        )
        raise InvokeError from exc
    except CalledProcessError as exc:
        msg = 'latex exited with error'
        raise MathExtError(msg, exc.stderr, exc.stdout) from exc


def compile_math_batch(latex_bodies: list[str], *, config: Config) -> Path:
    r"""Compile a batch of math expressions into a single multi-page DVI.

    Each entry in *latex_bodies* is the body content for one equation
    (e.g. ``\\fontsize{12}{14}\\selectfont E=mc^2``).
    They are compiled into one document with each equation separated by
    ``\\clearpage``, producing a multi-page DVI where each page
    corresponds to one equation.
    """
    tempdir = Path(tempfile.mkdtemp(suffix='-sphinx-imgmath-batch'))

    combined = '\\documentclass[12pt]{article}\n'
    combined += '\\usepackage[utf8]{inputenc}\n'
    combined += '\\usepackage{amsmath, amsthm, amssymb, amsfonts, anyfontsize, bm}\n'
    combined += '\\pagestyle{empty}\n'
    if config.imgmath_latex_preamble:
        combined += config.imgmath_latex_preamble + '\n'
    combined += '\\begin{document}\n'
    for i, body in enumerate(latex_bodies):
        combined += body
        combined += '\n'
        if i < len(latex_bodies) - 1:
            combined += '\\clearpage\n'
    combined += '\\end{document}\n'

    filename = tempdir / 'math.tex'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(combined)

    imgmath_latex_name = os.path.basename(config.imgmath_latex)
    command = [config.imgmath_latex]
    if imgmath_latex_name != 'tectonic':
        command.append('--interaction=nonstopmode')
    command.extend(config.imgmath_latex_args)
    command.append('math.tex')

    try:
        subprocess.run(
            command, capture_output=True, cwd=tempdir, check=True, encoding='ascii'
        )
        if imgmath_latex_name in {'xelatex', 'tectonic'}:
            return tempdir / 'math.xdv'
        else:
            return tempdir / 'math.dvi'
    except OSError as exc:
        logger.warning(
            __(
                'LaTeX command %r cannot be run (needed for math '
                'display), check the imgmath_latex setting'
            ),
            config.imgmath_latex,
        )
        raise InvokeError from exc
    except CalledProcessError as exc:
        msg = 'latex exited with error'
        raise MathExtError(msg, exc.stderr, exc.stdout) from exc


def convert_dvi_to_image(command: list[str], name: str) -> tuple[str, str]:
    """Convert DVI file to specific image format."""
    try:
        ret = subprocess.run(command, capture_output=True, check=True, encoding='ascii')
        return ret.stdout, ret.stderr
    except OSError as exc:
        logger.warning(
            __(
                '%s command %r cannot be run (needed for math '
                'display), check the imgmath_%s setting'
            ),
            name,
            command[0],
            name,
        )
        raise InvokeError from exc
    except CalledProcessError as exc:
        msg = f'{name} exited with error'
        raise MathExtError(msg, exc.stderr, exc.stdout) from exc


def convert_dvi_to_png(
    dvipath: Path,
    out_path: Path,
    *,
    config: Config,
    page: int | None = None,
) -> int | None:
    """Convert DVI file to PNG image."""
    name = 'dvipng'
    command = [config.imgmath_dvipng, '-o', out_path, '-T', 'tight', '-z9']
    command.extend(config.imgmath_dvipng_args)
    if page is not None:
        command.extend(['-page', str(page)])
    if config.imgmath_use_preview:
        command.append('--depth')
    command.append(dvipath)

    stdout, _stderr = convert_dvi_to_image(command, name)

    depth = None
    if config.imgmath_use_preview:
        for line in stdout.splitlines():
            matched = depth_re.match(line)
            if matched:
                depth = int(matched.group(1))
                write_png_depth(out_path, depth)
                break

    return depth


def convert_dvi_to_svg(
    dvipath: Path,
    out_path: Path,
    *,
    config: Config,
    page: int | None = None,
) -> int | None:
    """Convert DVI file to SVG image."""
    name = 'dvisvgm'
    command = [config.imgmath_dvisvgm, '-o', out_path]
    command.extend(config.imgmath_dvisvgm_args)
    if page is not None:
        command.append(f'--page={page}')
    command.append(dvipath)

    _stdout, stderr = convert_dvi_to_image(command, name)

    depth = None
    if config.imgmath_use_preview:
        for line in stderr.splitlines():  # not stdout !
            matched = depthsvg_re.match(line)
            if matched:
                depth = round(float(matched.group(1)) * 100 / 72.27)  # assume 100ppi
                write_svg_depth(out_path, depth)
                break

    return depth


def render_math(
    self: HTML5Translator, math: str, *, config: Config
) -> tuple[_StrPath | None, int | None]:
    """Render the LaTeX math expression *math* using latex and dvipng or
    dvisvgm.

    Return the image absolute filename and the "depth",
    that is, the distance of image bottom and baseline in pixels, if the
    option to use preview_latex is switched on.

    Error handling may seem strange, but follows a pattern: if LaTeX or dvipng
    (dvisvgm) aren't available, only a warning is generated (since that enables
    people on machines without these programs to at least build the rest of the
    docs successfully).  If the programs are there, however, they may not fail
    since that indicates a problem in the math source.
    """
    image_format = config.imgmath_image_format.lower()
    if image_format not in SUPPORT_FORMAT:
        unsupported_format_msg = 'imgmath_image_format must be either "png" or "svg"'
        raise MathExtError(unsupported_format_msg)

    body_latex = (
        f'\\fontsize{config.imgmath_font_size}'
        f'{{{round(config.imgmath_font_size * 1.2)}}}\\selectfont {math}'
    )
    filename = (
        f'{sha1(body_latex.encode(), usedforsecurity=False).hexdigest()}.{image_format}'
    )
    generated_path = self.builder.outdir / self.builder.imagedir / 'math' / filename
    generated_path.parent.mkdir(parents=True, exist_ok=True)
    if generated_path.is_file():
        if image_format == 'png':
            depth = read_png_depth(generated_path)
        elif image_format == 'svg':
            depth = read_svg_depth(generated_path)
        return generated_path, depth

    # if latex or dvipng (dvisvgm) has failed once, don't bother to try again
    latex_failed = hasattr(self.builder, '_imgmath_warned_latex')
    trans_failed = hasattr(self.builder, '_imgmath_warned_image_translator')
    if latex_failed or trans_failed:
        return None, None

    batch_size = config.imgmath_batch_size

    if batch_size > 1:
        # Batch accumulation mode
        if not hasattr(self.builder, '_imgmath_batch'):
            self.builder._imgmath_batch = []  # type: ignore[attr-defined]
            self.builder._imgmath_batch_results = {}  # type: ignore[attr-defined]
            self.builder._imgmath_translator = self  # type: ignore[attr-defined]

        batch: list[str] = self.builder._imgmath_batch  # type: ignore[attr-defined]
        results: dict[str, tuple[_StrPath, int | None]] = (
            self.builder._imgmath_batch_results  # type: ignore[attr-defined]
        )

        if math in results:
            return results[math]

        batch.append(math)

        if len(batch) >= batch_size:
            _process_batch(self.builder, batch, results, config)
            batch.clear()

        if math in results:
            return results[math]
        return None, None

    # Single-equation mode (batch_size == 1)
    latex = generate_latex_macro(image_format, math, config, self.builder.confdir)

    # .tex -> .dvi
    try:
        dvipath = compile_math(latex, config=config)
    except InvokeError:
        self.builder._imgmath_warned_latex = True  # type: ignore[attr-defined]
        return None, None

    # .dvi -> .png/.svg
    try:
        if image_format == 'png':
            depth = convert_dvi_to_png(dvipath, generated_path, config=config)
        elif image_format == 'svg':
            depth = convert_dvi_to_svg(dvipath, generated_path, config=config)
    except InvokeError:
        self.builder._imgmath_warned_image_translator = True  # type: ignore[attr-defined]
        return None, None

    return generated_path, depth


def _suppress_unlink(path: Path) -> None:
    with contextlib.suppress(OSError):
        path.unlink()


def _populate_from_file(
    math: str,
    path: Path,
    image_format: str,
    results: dict[str, tuple[_StrPath, int | None]],
) -> None:
    """Read depth from an already-compiled image file and store in *results*."""
    if image_format == 'png':
        depth = read_png_depth(path)
    else:
        depth = read_svg_depth(path)
    results[math] = (path, depth)  # type: ignore[assignment]


def _compile_single(
    math: str,
    path: Path,
    image_format: str,
    config: Config,
    confdir: _StrPath,
    results: dict[str, tuple[_StrPath, int | None]],
) -> None:
    """Compile a single equation and store the result in *results*."""
    latex = generate_latex_macro(image_format, math, config, confdir)
    dvipath = compile_math(latex, config=config)
    if image_format == 'png':
        depth = convert_dvi_to_png(dvipath, path, config=config)
    else:
        depth = convert_dvi_to_svg(dvipath, path, config=config)
    results[math] = (path, depth)  # type: ignore[assignment]
    _suppress_unlink(path.with_suffix(f'.{image_format}.pending'))


def _process_batch(
    builder: Any,
    batch: list[str],
    results: dict[str, tuple[_StrPath, int | None]],
    config: Config,
) -> None:
    """Compile a batch of math expressions in one LaTeX invocation."""
    image_format = config.imgmath_image_format.lower()

    out_paths = []
    for math in batch:
        body = (
            f'\\fontsize{config.imgmath_font_size}'
            f'{{{round(config.imgmath_font_size * 1.2)}}}\\selectfont {math}'
        )
        filename = (
            f'{sha1(body.encode(), usedforsecurity=False).hexdigest()}.{image_format}'
        )
        path = builder.outdir / builder.imagedir / 'math' / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        out_paths.append(path)

    # All cached?
    all_cached = all(p.is_file() for p in out_paths)
    if all_cached:
        for math, p in zip(batch, out_paths, strict=True):
            if image_format == 'png':
                depth = read_png_depth(p)
            else:
                depth = read_svg_depth(p)
            results[math] = (p, depth)
        return

    # Build per-equation body LaTeX
    bodies = []
    for math in batch:
        body = (
            f'\\fontsize{config.imgmath_font_size}'
            f'{{{round(config.imgmath_font_size * 1.2)}}}\\selectfont {math}'
        )
        bodies.append(body)

    try:
        dvipath = compile_math_batch(bodies, config=config)
    except (InvokeError, MathExtError) as exc:
        if isinstance(exc, InvokeError):
            builder._imgmath_warned_latex = True
        logger.warning(
            __(
                'Batch LaTeX compilation failed, falling back to '
                'per-equation compilation'
            )
        )
        logger.info(str(exc))
        for math_entry, path in zip(batch, out_paths, strict=True):
            if path.is_file():
                _populate_from_file(math_entry, path, image_format, results)
                _suppress_unlink(path.with_suffix(f'.{image_format}.pending'))
                continue
            try:
                _compile_single(
                    math_entry,
                    path,
                    image_format,
                    config,
                    getattr(builder, 'confdir', None),  # type: ignore[arg-type]
                    results,
                )
            except (InvokeError, MathExtError):
                results[math_entry] = (None, None)  # type: ignore[assignment]
        return

    # Extract each page from the multi-page DVI
    for idx, (math, path) in enumerate(zip(batch, out_paths, strict=True)):
        if path.is_file():
            if image_format == 'png':
                depth = read_png_depth(path)
            else:
                depth = read_svg_depth(path)
            results[math] = (path, depth)
            _suppress_unlink(path.with_suffix(f'.{image_format}.pending'))
            continue

        try:
            if image_format == 'png':
                depth = convert_dvi_to_png(dvipath, path, config=config, page=idx + 1)
            else:
                depth = convert_dvi_to_svg(dvipath, path, config=config, page=idx + 1)
            results[math] = (path, depth)
        except InvokeError:
            logger.warning(
                __('Failed to convert batch page %d to %s'), idx + 1, image_format
            )
            results[math] = (None, None)  # type: ignore[assignment]
        else:
            _suppress_unlink(path.with_suffix(f'.{image_format}.pending'))


def render_maths_to_base64(image_format: str, generated_path: Path) -> str:
    with open(generated_path, 'rb') as f:
        content = f.read()
    encoded = base64.b64encode(content).decode(encoding='utf-8')
    if image_format == 'png':
        return f'data:image/png;base64,{encoded}'
    if image_format == 'svg':
        return f'data:image/svg+xml;base64,{encoded}'
    unsupported_format_msg = 'imgmath_image_format must be either "png" or "svg"'
    raise MathExtError(unsupported_format_msg)


def clean_up_files(app: Sphinx, exc: Exception) -> None:
    if exc:
        return

    # Flush any remaining equations in the batch
    builder = app.builder
    remaining_batch = getattr(builder, '_imgmath_batch', None)
    if remaining_batch:
        _process_batch(
            builder,
            remaining_batch,
            getattr(builder, '_imgmath_batch_results', {}),
            builder.config,
        )
        remaining_batch.clear()

    # Remove .pending placeholder files left by batch visitors
    math_dir = builder.outdir / builder.imagedir / 'math'
    if math_dir.is_dir():
        for p in math_dir.glob('*.pending'):
            _suppress_unlink(p)

    if app.config.imgmath_embed and app.config.imgmath_batch_size <= 1:
        # in embed mode, the images are still generated in the math output dir
        # to be shared across workers, but are not useful to the final document
        with contextlib.suppress(Exception):
            shutil.rmtree(math_dir)


def get_tooltip(self: HTML5Translator, node: Element, *, config: Config) -> str:
    if config.imgmath_add_tooltips:
        return f' alt="{self.encode(node.astext()).strip()}"'
    return ''


def html_visit_math(self: HTML5Translator, node: nodes.math) -> None:
    config = self.builder.config
    try:
        rendered_path, depth = render_math(
            self, '$' + node.astext() + '$', config=config
        )
    except MathExtError as exc:
        msg = str(exc)
        sm = nodes.system_message(
            msg, type='WARNING', level=2, backrefs=[], source=node.astext()
        )
        sm.walkabout(self)
        logger.warning(__('display latex %r: %s'), node.astext(), msg)
        raise nodes.SkipNode from exc

    if rendered_path is None:
        if config.imgmath_batch_size > 1:
            # Batch mode: compute the image path and write a placeholder
            # so the HTML references the correct final filename.
            math_str = '$' + node.astext() + '$'
            body_latex = (
                f'\\fontsize{config.imgmath_font_size}'
                f'{{{round(config.imgmath_font_size * 1.2)}}}'
                f'\\selectfont {math_str}'
            )
            filename = (
                f'{sha1(body_latex.encode(), usedforsecurity=False).hexdigest()}'
                f'.{config.imgmath_image_format.lower()}'
            )
            math_dir = self.builder.outdir / self.builder.imagedir / 'math'
            math_dir.mkdir(parents=True, exist_ok=True)
            placeholder = math_dir / (filename + '.pending')
            placeholder.touch()
            if config.imgmath_embed:
                img_src = (Path(self.builder.imgpath) / 'math' / filename).as_posix()
            else:
                relative_path = Path(self.builder.imgpath, 'math', filename)
                img_src = relative_path.as_posix()
            tooltip = get_tooltip(self, node, config=config)
            self.body.append(f'<img class="math" src="{img_src}"{tooltip}/>')
        else:
            # something failed -- use text-only as a bad substitute
            self.body.append(
                f'<span class="math">{self.encode(node.astext()).strip()}</span>'
            )
    else:
        if config.imgmath_embed:
            image_format = config.imgmath_image_format.lower()
            img_src = render_maths_to_base64(image_format, rendered_path)
        else:
            bname = os.path.basename(rendered_path)
            relative_path = Path(self.builder.imgpath, 'math', bname)
            img_src = relative_path.as_posix()
        align = f' style="vertical-align: {-depth:d}px"' if depth is not None else ''
        tooltip = get_tooltip(self, node, config=config)
        self.body.append(f'<img class="math" src="{img_src}"{tooltip}{align}/>')
    raise nodes.SkipNode


def html_visit_displaymath(self: HTML5Translator, node: nodes.math_block) -> None:
    config = self.builder.config
    if node.get('no-wrap', node.get('nowrap', False)):
        latex = node.astext()
    else:
        latex = wrap_displaymath(node.astext(), None, False)
    try:
        rendered_path, _depth = render_math(self, latex, config=config)
    except MathExtError as exc:
        msg = str(exc)
        sm = nodes.system_message(
            msg, type='WARNING', level=2, backrefs=[], source=node.astext()
        )
        sm.walkabout(self)
        logger.warning(__('inline latex %r: %s'), node.astext(), msg)
        raise nodes.SkipNode from exc
    self.body.append(self.starttag(node, 'div', CLASS='math'))
    self.body.append('<p>')
    if node['number']:
        number = get_node_equation_number(self, node)
        self.body.append('<span class="eqno">(%s)' % number)
        self.add_permalink_ref(node, _('Link to this equation'))
        self.body.append('</span>')

    if rendered_path is None:
        if config.imgmath_batch_size > 1:
            # Batch mode: compute the image path and write a placeholder
            body_latex = (
                f'\\fontsize{config.imgmath_font_size}'
                f'{{{round(config.imgmath_font_size * 1.2)}}}'
                f'\\selectfont {latex}'
            )
            filename = (
                f'{sha1(body_latex.encode(), usedforsecurity=False).hexdigest()}'
                f'.{config.imgmath_image_format.lower()}'
            )
            math_dir = self.builder.outdir / self.builder.imagedir / 'math'
            math_dir.mkdir(parents=True, exist_ok=True)
            placeholder = math_dir / (filename + '.pending')
            placeholder.touch()
            if config.imgmath_embed:
                img_src = (Path(self.builder.imgpath) / 'math' / filename).as_posix()
            else:
                relative_path = Path(self.builder.imgpath, 'math', filename)
                img_src = relative_path.as_posix()
            tooltip = get_tooltip(self, node, config=config)
            self.body.append(f'<img src="{img_src}"{tooltip}/></p>\n</div>')
        else:
            # something failed -- use text-only as a bad substitute
            text = self.encode(node.astext()).strip()
            self.body.append(f'<span class="math">{text}</span></p>\n</div>')
    else:
        if config.imgmath_embed:
            image_format = config.imgmath_image_format.lower()
            img_src = render_maths_to_base64(image_format, rendered_path)
        else:
            bname = os.path.basename(rendered_path)
            relative_path = Path(self.builder.imgpath, 'math', bname)
            img_src = relative_path.as_posix()
        tooltip = get_tooltip(self, node, config=config)
        self.body.append(f'<img src="{img_src}"{tooltip}/></p>\n</div>')
    raise nodes.SkipNode


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_html_math_renderer(
        'imgmath',
        inline_renderers=(html_visit_math, None),
        block_renderers=(html_visit_displaymath, None),
    )

    app.add_config_value('imgmath_image_format', 'png', 'html', types=frozenset({str}))
    app.add_config_value('imgmath_dvipng', 'dvipng', 'html', types=frozenset({str}))
    app.add_config_value('imgmath_dvisvgm', 'dvisvgm', 'html', types=frozenset({str}))
    app.add_config_value('imgmath_latex', 'latex', 'html', types=frozenset({str}))
    app.add_config_value('imgmath_use_preview', False, 'html', types=frozenset({bool}))
    app.add_config_value(
        'imgmath_dvipng_args',
        ['-gamma', '1.5', '-D', '110', '-bg', 'Transparent'],
        'html',
        types=frozenset({list}),
    )
    app.add_config_value(
        'imgmath_dvisvgm_args', ['--no-fonts'], 'html', types=frozenset({list, tuple})
    )
    app.add_config_value(
        'imgmath_latex_args', [], 'html', types=frozenset({list, tuple})
    )
    app.add_config_value('imgmath_latex_preamble', '', 'html', types=frozenset({str}))
    app.add_config_value('imgmath_add_tooltips', True, 'html', types=frozenset({bool}))
    app.add_config_value('imgmath_font_size', 12, 'html', types=frozenset({int}))
    app.add_config_value('imgmath_embed', False, 'html', types=frozenset({bool}))
    app.add_config_value('imgmath_batch_size', 1, 'html', types=frozenset({int}))
    app.connect('build-finished', clean_up_files)
    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
    }
