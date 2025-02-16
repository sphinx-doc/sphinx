"""Tests the Python Domain"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx import addnodes
from sphinx.addnodes import (
    desc,
    desc_addname,
    desc_annotation,
    desc_content,
    desc_name,
    desc_sig_keyword,
    desc_sig_space,
    desc_signature,
)
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx(
    'html',
    testroot='domain-py',
    freshenv=True,
)
def test_domain_py_canonical(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'canonical.html').read_text(encoding='utf8')
    assert (
        '<a class="reference internal" href="#canonical.Foo" title="canonical.Foo">'
        '<code class="xref py py-class docutils literal notranslate">'
        '<span class="pre">Foo</span></code></a>'
    ) in content
    assert app.warning.getvalue() == ''


@pytest.mark.sphinx('html', testroot='_blank')
def test_canonical(app: SphinxTestApp) -> None:
    text = '.. py:class:: io.StringIO\n   :canonical: _io.StringIO'
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_addname, 'io.'],
                            [desc_name, 'StringIO'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert 'io.StringIO' in domain.objects
    assert domain.objects['io.StringIO'] == ('index', 'io.StringIO', 'class', False)
    assert domain.objects['_io.StringIO'] == ('index', 'io.StringIO', 'class', True)


@pytest.mark.sphinx('html', testroot='_blank')
def test_canonical_definition_overrides(app: SphinxTestApp) -> None:
    text = (
        '.. py:class:: io.StringIO\n'
        '   :canonical: _io.StringIO\n'
        '.. py:class:: _io.StringIO\n'
    )
    restructuredtext.parse(app, text)
    assert app.warning.getvalue() == ''

    domain = app.env.domains.python_domain
    assert domain.objects['_io.StringIO'] == ('index', 'id0', 'class', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_canonical_definition_skip(app: SphinxTestApp) -> None:
    text = (
        '.. py:class:: _io.StringIO\n'
        '.. py:class:: io.StringIO\n'
        '   :canonical: _io.StringIO\n'
    )

    restructuredtext.parse(app, text)
    assert app.warning.getvalue() == ''

    domain = app.env.domains.python_domain
    assert domain.objects['_io.StringIO'] == ('index', 'io.StringIO', 'class', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_canonical_duplicated(app: SphinxTestApp) -> None:
    text = (
        '.. py:class:: mypackage.StringIO\n'
        '   :canonical: _io.StringIO\n'
        '.. py:class:: io.StringIO\n'
        '   :canonical: _io.StringIO\n'
    )

    restructuredtext.parse(app, text)
    assert app.warning.getvalue() != ''
