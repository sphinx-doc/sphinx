import os
import re
import sys

import pytest

from sphinx.testing.util import strip_escseq

ENV_WARNINGS = """\
{root}/autodoc_fodder.py:docstring of autodoc_fodder.MarkupError:\\d+: \
WARNING: Explicit markup ends without a blank line; unexpected unindent.
{root}/index.rst:\\d+: WARNING: Encoding 'utf-8-sig' used for reading included \
file '{root}/wrongenc.inc' seems to be wrong, try giving an :encoding: option
{root}/index.rst:\\d+: WARNING: invalid single index entry ''
{root}/index.rst:\\d+: WARNING: image file not readable: foo.png
{root}/index.rst:\\d+: WARNING: download file not readable: {root}/nonexisting.png
{root}/undecodable.rst:\\d+: WARNING: undecodable source characters, replacing \
with "\\?": b?'here: >>>(\\\\|/)xbb<<<((\\\\|/)r)?'
"""

HTML_WARNINGS = ENV_WARNINGS + """\
{root}/index.rst:\\d+: WARNING: unknown option: '&option'
{root}/index.rst:\\d+: WARNING: citation not found: missing
{root}/index.rst:\\d+: WARNING: a suitable image for html builder not found: foo.\\*
{root}/index.rst:\\d+: WARNING: Lexing literal_block ".*" as "c" resulted in an error at token: ".*". Retrying in relaxed mode.
"""

LATEX_WARNINGS = ENV_WARNINGS + """\
{root}/index.rst:\\d+: WARNING: unknown option: '&option'
{root}/index.rst:\\d+: WARNING: citation not found: missing
{root}/index.rst:\\d+: WARNING: a suitable image for latex builder not found: foo.\\*
{root}/index.rst:\\d+: WARNING: Lexing literal_block ".*" as "c" resulted in an error at token: ".*". Retrying in relaxed mode.
"""

TEXINFO_WARNINGS = ENV_WARNINGS + """\
{root}/index.rst:\\d+: WARNING: unknown option: '&option'
{root}/index.rst:\\d+: WARNING: citation not found: missing
{root}/index.rst:\\d+: WARNING: a suitable image for texinfo builder not found: foo.\\*
{root}/index.rst:\\d+: WARNING: a suitable image for texinfo builder not found: \
\\['application/pdf', 'image/svg\\+xml'\\] \\(svgimg.\\*\\)
"""


def _check_warnings(expected_warnings: str, warning: str) -> None:
    warnings = strip_escseq(re.sub(re.escape(os.sep) + '{1,2}', '/', warning))
    assert re.match(f'{expected_warnings}$', warnings), (
        "Warnings don't match:\n"
        + f'--- Expected (regex):\n{expected_warnings}\n'
        + f'--- Got:\n{warnings}'
    )
    sys.modules.pop('autodoc_fodder', None)


@pytest.mark.sphinx('html', testroot='warnings', freshenv=True)
def test_html_warnings(app, warning):
    app.build(force_all=True)
    warnings_exp = HTML_WARNINGS.format(root=re.escape(app.srcdir.as_posix()))
    _check_warnings(warnings_exp, warning.getvalue())


@pytest.mark.sphinx('latex', testroot='warnings', freshenv=True)
def test_latex_warnings(app, warning):
    app.build(force_all=True)
    warnings_exp = LATEX_WARNINGS.format(root=re.escape(app.srcdir.as_posix()))
    _check_warnings(warnings_exp, warning.getvalue())


@pytest.mark.sphinx('texinfo', testroot='warnings', freshenv=True)
def test_texinfo_warnings(app, warning):
    app.build(force_all=True)
    warnings_exp = TEXINFO_WARNINGS.format(root=re.escape(app.srcdir.as_posix()))
    _check_warnings(warnings_exp, warning.getvalue())
