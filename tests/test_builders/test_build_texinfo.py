"""Test the build process with Texinfo builder with the test root."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from subprocess import CalledProcessError
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from sphinx.builders.texinfo import default_texinfo_documents
from sphinx.config import Config
from sphinx.util.docutils import new_document
from sphinx.writers.texinfo import TexinfoTranslator

if TYPE_CHECKING:
    from collections.abc import Callable

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.parametrize('directive', ['admonition:: Virtual modules', 'note::'])
@pytest.mark.parametrize('nested', [False, True])
def test_texinfo_toctree_in_admonition(
    make_app_with_empty_project: Callable[..., SphinxTestApp],
    tmp_path: Path,
    directive: str,
    nested: bool,
) -> None:
    content = (
        f'.. {directive}\n\n'
        '   Before the tree.\n\n'
        '   .. toctree::\n\n'
        '      child\n\n'
        '   After the tree.\n'
    )
    if nested:
        content = '.. warning::\n\n' + ''.join(
            f'   {line}\n' for line in content.splitlines()
        )
    (tmp_path / 'index.rst').write_text('Root\n====\n\n' + content, encoding='utf8')
    (tmp_path / 'child.rst').write_text(
        'Child\n=====\n\n.. note::\n\n   Child note.\n', encoding='utf8'
    )
    app = make_app_with_empty_project(buildername='texinfo')
    app.build()
    output = (app.outdir / 'projectnamenotset.texi').read_text(encoding='utf8')
    assert 'Before the tree.' in output
    assert 'After the tree.' in output
    assert 'Child note.' in output
    assert output.count('@cartouche\n') == 2 + nested
    assert '@quotation Note \nChild note.\n@end quotation\n@end cartouche' in output
    # Texinfo section nodes and menus cannot occur inside an admonition.
    blocks = []
    for line in output.splitlines():
        if line.startswith(('@cartouche', '@quotation')):
            blocks.append(line.split()[0][1:])
        elif line.startswith(('@end cartouche', '@end quotation')):
            assert blocks.pop() == line.split()[1]
        elif line.startswith(('@node ', '@menu')):
            assert not blocks
    assert not blocks
    if makeinfo := shutil.which('makeinfo'):
        subprocess.run(
            [makeinfo, '--no-split', 'projectnamenotset.texi'],
            cwd=app.outdir,
            capture_output=True,
            check=True,
        )


@pytest.mark.sphinx('texinfo', testroot='root')
def test_texinfo(app: SphinxTestApp) -> None:
    TexinfoTranslator.ignore_missing_images = True
    app.build(force_all=True)
    result = (app.outdir / 'sphinxtests.texi').read_text(encoding='utf8')
    assert (
        '@anchor{markup doc}@anchor{11}'
        '@anchor{markup id1}@anchor{12}'
        '@anchor{markup testing-various-markup}@anchor{13}'
    ) in result
    assert 'Footnotes' not in result
    # now, try to run makeinfo over it
    try:
        args = ['makeinfo', '--no-split', 'sphinxtests.texi']
        subprocess.run(args, capture_output=True, cwd=app.outdir, check=True)
    except OSError as exc:
        raise pytest.skip.Exception from exc  # most likely makeinfo was not found
    except CalledProcessError as exc:
        print(exc.stdout)
        print(exc.stderr)
        msg = f'makeinfo exited with return code {exc.returncode}'
        raise AssertionError(msg) from exc


@pytest.mark.sphinx('texinfo', testroot='markup-rubric')
def test_texinfo_rubric(app: SphinxTestApp) -> None:
    app.build()

    output = (app.outdir / 'projectnamenotset.texi').read_text(encoding='utf8')
    assert '@heading This is a rubric' in output
    assert '@heading This is a multiline rubric' in output
    assert '@heading A rubric with a heading level' in output


@pytest.mark.sphinx('texinfo', testroot='markup-citation')
def test_texinfo_citation(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    output = (app.outdir / 'projectnamenotset.texi').read_text(encoding='utf8')
    assert 'This is a citation ref; @ref{1,,[CITE1]} and @ref{2,,[CITE2]}.' in output
    assert (
        '@anchor{index cite1}@anchor{1}@w{(CITE1)} \nThis is a citation\n'
    ) in output
    assert (
        '@anchor{index cite2}@anchor{2}@w{(CITE2)} \nThis is a multiline citation\n'
    ) in output


def test_default_texinfo_documents() -> None:
    config = Config({
        'project': 'STASI™ Documentation',
        'author': "Wolfgang Schäuble & G'Beckstein",
    })
    expected = [
        (
            'index',
            'stasi',
            'STASI™ Documentation',
            "Wolfgang Schäuble & G'Beckstein",
            'stasi',
            'One line description of project',
            'Miscellaneous',
        )
    ]
    assert default_texinfo_documents(config) == expected


@pytest.mark.sphinx('texinfo', testroot='root')
def test_texinfo_escape_id(app: SphinxTestApp) -> None:
    settings = Mock(title='', texinfo_dir_entry='', texinfo_elements={})
    document = new_document('', settings)
    translator = app.builder.create_translator(document, app.builder)
    assert isinstance(translator, TexinfoTranslator)  # type-checking

    assert translator.escape_id('Hello world') == 'Hello world'
    assert translator.escape_id('Hello    world') == 'Hello world'
    assert translator.escape_id('Hello   Sphinx   world') == 'Hello Sphinx world'
    assert translator.escape_id('Hello:world') == 'Hello world'
    assert translator.escape_id('Hello(world)') == 'Hello world'
    assert translator.escape_id('Hello world.') == 'Hello world'
    assert translator.escape_id('.') == '.'


@pytest.mark.sphinx('texinfo', testroot='footnotes')
def test_texinfo_footnote(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    output = (app.outdir / 'projectnamenotset.texi').read_text(encoding='utf8')
    assert 'First footnote: @footnote{\nFirst\n}' in output


@pytest.mark.sphinx('texinfo', testroot='root')
def test_texinfo_xrefs(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    output = (app.outdir / 'sphinxtests.texi').read_text(encoding='utf8')
    assert re.search(r'@ref{\w+,,--plugin\.option}', output)

    # Now rebuild it without xrefs
    app.config.texinfo_cross_references = False
    app.build(force_all=True)
    output = (app.outdir / 'sphinxtests.texi').read_text(encoding='utf8')
    assert not re.search(r'@ref{\w+,,--plugin\.option}', output)
    assert (
        'Link to perl +p, --ObjC++, --plugin.option, create-auth-token, arg and -j'
    ) in output


@pytest.mark.sphinx('texinfo', testroot='root')
def test_texinfo_samp_with_variable(app: SphinxTestApp) -> None:
    app.build()

    output = (app.outdir / 'sphinxtests.texi').read_text(encoding='utf8')

    assert '@code{@var{variable_only}}' in output
    assert '@code{@var{variable} and text}' in output
    assert '@code{Show @var{variable} in the middle}' in output


@pytest.mark.usefixtures('_http_teapot')
@pytest.mark.sphinx('texinfo', testroot='images')
def test_copy_images(app: SphinxTestApp) -> None:
    app.build()

    images_dir = Path(app.outdir) / 'projectnamenotset-figures'
    images = {image.name for image in images_dir.rglob('*')}
    images.discard('python-logo.png')
    assert images == {
        'ba30773957c3fe046897111afd65a80b81cad089.png',  # texinfo: image from data:image/png URI in source
        'img.png',
        'rimg.png',
        'testimäge.png',
    }  # fmt: skip
