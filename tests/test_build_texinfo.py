"""
    test_build_texinfo
    ~~~~~~~~~~~~~~~~~~

    Test the build process with Texinfo builder with the test root.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import subprocess
from subprocess import PIPE, CalledProcessError
from unittest.mock import Mock

import pytest

from sphinx.builders.texinfo import default_texinfo_documents
from sphinx.config import Config
from sphinx.testing.util import strip_escseq
from sphinx.util.docutils import new_document
from sphinx.writers.texinfo import TexinfoTranslator

from .test_build_html import ENV_WARNINGS

TEXINFO_WARNINGS = ENV_WARNINGS + """\
%(root)s/index.rst:\\d+: WARNING: unknown option: &option
%(root)s/index.rst:\\d+: WARNING: citation not found: missing
%(root)s/index.rst:\\d+: WARNING: a suitable image for texinfo builder not found: foo.\\*
%(root)s/index.rst:\\d+: WARNING: a suitable image for texinfo builder not found: \
\\['application/pdf', 'image/svg\\+xml'\\] \\(svgimg.\\*\\)
"""


@pytest.mark.sphinx('texinfo', testroot='warnings', freshenv=True)
def test_texinfo_warnings(app, status, warning):
    app.builder.build_all()
    warnings = strip_escseq(re.sub(re.escape(os.sep) + '{1,2}', '/', warning.getvalue()))
    warnings_exp = TEXINFO_WARNINGS % {
        'root': re.escape(app.srcdir.replace(os.sep, '/'))}
    assert re.match(warnings_exp + '$', warnings), \
        'Warnings don\'t match:\n' + \
        '--- Expected (regex):\n' + warnings_exp + \
        '--- Got:\n' + warnings


@pytest.mark.sphinx('texinfo')
def test_texinfo(app, status, warning):
    TexinfoTranslator.ignore_missing_images = True
    app.builder.build_all()
    result = (app.outdir / 'sphinxtests.texi').read_text()
    assert ('@anchor{markup doc}@anchor{11}'
            '@anchor{markup id1}@anchor{12}'
            '@anchor{markup testing-various-markup}@anchor{13}' in result)
    assert 'Footnotes' not in result
    # now, try to run makeinfo over it
    try:
        args = ['makeinfo', '--no-split', 'sphinxtests.texi']
        subprocess.run(args, stdout=PIPE, stderr=PIPE, cwd=app.outdir, check=True)
    except OSError as exc:
        raise pytest.skip.Exception from exc  # most likely makeinfo was not found
    except CalledProcessError as exc:
        print(exc.stdout)
        print(exc.stderr)
        assert False, 'makeinfo exited with return code %s' % exc.retcode


@pytest.mark.sphinx('texinfo', testroot='markup-rubric')
def test_texinfo_rubric(app, status, warning):
    app.build()

    output = (app.outdir / 'python.texi').read_text()
    assert '@heading This is a rubric' in output
    assert '@heading This is a multiline rubric' in output


@pytest.mark.sphinx('texinfo', testroot='markup-citation')
def test_texinfo_citation(app, status, warning):
    app.builder.build_all()

    output = (app.outdir / 'python.texi').read_text()
    assert 'This is a citation ref; @ref{1,,[CITE1]} and @ref{2,,[CITE2]}.' in output
    assert ('@anchor{index cite1}@anchor{1}@w{(CITE1)} \n'
            'This is a citation\n') in output
    assert ('@anchor{index cite2}@anchor{2}@w{(CITE2)} \n'
            'This is a multiline citation\n') in output


def test_default_texinfo_documents():
    config = Config({'project': 'STASI™ Documentation',
                     'author': "Wolfgang Schäuble & G'Beckstein"})
    config.init_values()
    expected = [('index', 'stasi', 'STASI™ Documentation',
                 "Wolfgang Schäuble & G'Beckstein", 'stasi',
                 'One line description of project', 'Miscellaneous')]
    assert default_texinfo_documents(config) == expected


@pytest.mark.sphinx('texinfo')
def test_texinfo_escape_id(app, status, warning):
    settings = Mock(title='',
                    texinfo_dir_entry='',
                    texinfo_elements={})
    document = new_document('', settings)
    translator = app.builder.create_translator(document, app.builder)

    assert translator.escape_id('Hello world') == 'Hello world'
    assert translator.escape_id('Hello    world') == 'Hello world'
    assert translator.escape_id('Hello   Sphinx   world') == 'Hello Sphinx world'
    assert translator.escape_id('Hello:world') == 'Hello world'
    assert translator.escape_id('Hello(world)') == 'Hello world'
    assert translator.escape_id('Hello world.') == 'Hello world'
    assert translator.escape_id('.') == '.'
