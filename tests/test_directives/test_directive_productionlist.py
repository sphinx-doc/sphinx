"""Tests the productionlist directive."""

from __future__ import annotations

import pytest
from docutils import nodes

from sphinx.addnodes import pending_xref
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node, etree_parse


@pytest.mark.sphinx('html', testroot='productionlist')
def test_productionlist(app):
    app.build(force_all=True)

    warnings = app.warning.getvalue().split('\n')
    assert len(warnings) == 2
    assert warnings[-1] == ''
    assert (
        'Dup2.rst:4: WARNING: duplicate token description of Dup, other instance in Dup1'
        in warnings[0]
    )

    etree = etree_parse(app.outdir / 'index.html')
    nodes = list(etree.iter('ul'))
    assert len(nodes) >= 3

    ul = nodes[2]
    cases = []
    for li in list(ul):
        li_list = list(li)
        assert len(li_list) == 1
        p = li_list[0]
        assert p.tag == 'p'
        text = str(p.text).strip(' :')
        p_list = list(p)
        assert len(p_list) == 1
        a = p_list[0]
        assert a.tag == 'a'
        link = a.get('href')
        a_list = list(a)
        assert len(a_list) == 1
        code = a_list[0]
        assert code.tag == 'code'
        code_list = list(code)
        assert len(code_list) == 1
        span = code_list[0]
        assert span.tag == 'span'
        link_text = span.text.strip()
        cases.append((text, link, link_text))
    assert cases == [
        ('A', 'Bare.html#grammar-token-A', 'A'),
        ('B', 'Bare.html#grammar-token-B', 'B'),
        ('P1:A', 'P1.html#grammar-token-P1-A', 'P1:A'),
        ('P1:B', 'P1.html#grammar-token-P1-B', 'P1:B'),
        ('P2:A', 'P1.html#grammar-token-P1-A', 'P1:A'),
        ('P2:B', 'P2.html#grammar-token-P2-B', 'P2:B'),
        ('Explicit title A, plain', 'Bare.html#grammar-token-A', 'MyTitle'),
        ('Explicit title A, colon', 'Bare.html#grammar-token-A', 'My:Title'),
        ('Explicit title P1:A, plain', 'P1.html#grammar-token-P1-A', 'MyTitle'),
        ('Explicit title P1:A, colon', 'P1.html#grammar-token-P1-A', 'My:Title'),
        ('Tilde A', 'Bare.html#grammar-token-A', 'A'),
        ('Tilde P1:A', 'P1.html#grammar-token-P1-A', 'A'),
        ('Tilde explicit title P1:A', 'P1.html#grammar-token-P1-A', '~MyTitle'),
        ('Tilde, explicit title P1:A', 'P1.html#grammar-token-P1-A', 'MyTitle'),
        ('Dup', 'Dup2.html#grammar-token-Dup', 'Dup'),
        ('FirstLine', 'firstLineRule.html#grammar-token-FirstLine', 'FirstLine'),
        ('SecondLine', 'firstLineRule.html#grammar-token-SecondLine', 'SecondLine'),
    ]

    text = (app.outdir / 'LineContinuation.html').read_text(encoding='utf8')
    assert 'A</strong> ::=  B C D    E F G' in text


@pytest.mark.sphinx('html', testroot='root')
def test_productionlist_xref(app):
    text = """\
.. productionlist:: P2
   A: `:A` `A`
   B: `P1:B` `~P1:B`
"""
    doctree = restructuredtext.parse(app, text)
    refnodes = list(doctree.findall(pending_xref))
    assert_node(refnodes[0], pending_xref, reftarget='A')
    assert_node(refnodes[1], pending_xref, reftarget='P2:A')
    assert_node(refnodes[2], pending_xref, reftarget='P1:B')
    assert_node(refnodes[3], pending_xref, reftarget='P1:B')
    assert_node(refnodes[0], [pending_xref, nodes.literal, 'A'])
    assert_node(refnodes[1], [pending_xref, nodes.literal, 'A'])
    assert_node(refnodes[2], [pending_xref, nodes.literal, 'P1:B'])
    assert_node(refnodes[3], [pending_xref, nodes.literal, 'B'])
