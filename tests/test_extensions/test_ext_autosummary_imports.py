"""Test autosummary for import cycles."""

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.ext.autosummary import autosummary_table
from sphinx.testing.util import assert_node


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-import_cycle')
@pytest.mark.usefixtures('rollback_sysmodules')
def test_autosummary_import_cycle(app):
    app.build()

    doctree = app.env.get_doctree('index')
    app.env.apply_post_transforms(doctree, 'index')

    assert len(list(doctree.findall(nodes.reference))) == 1

    assert_node(
        doctree,
        (
            addnodes.index,  # [0]
            nodes.target,  # [1]
            nodes.paragraph,  # [2]
            addnodes.tabular_col_spec,  # [3]
            [
                autosummary_table,
                nodes.table,
                nodes.tgroup,
                (
                    nodes.colspec,  # [4][0][0][0]
                    nodes.colspec,  # [4][0][0][1]
                    [nodes.tbody, nodes.row],  # [4][0][0][2][1]
                ),
            ],
            addnodes.index,  # [5]
            addnodes.desc,  # [6]
        ),
    )
    assert_node(
        doctree[4][0][0][2][0],
        ([nodes.entry, nodes.paragraph, (nodes.reference, nodes.Text)], nodes.entry),
    )
    assert_node(
        doctree[4][0][0][2][0][0][0][0],
        nodes.reference,
        refid='spam.eggs.Ham',
        reftitle='spam.eggs.Ham',
    )

    expected = (
        'Summarised items should not include the current module. '
        "Replace 'spam.eggs.Ham' with 'Ham'."
    )
    assert expected in app.warning.getvalue()


@pytest.mark.sphinx('dummy', testroot='ext-autosummary-module_prefix')
@pytest.mark.usefixtures('rollback_sysmodules')
def test_autosummary_generate_prefixes(app):
    app.build()
    warnings = app.warning.getvalue()
    assert 'Summarised items should not include the current module.' not in warnings
    assert warnings == ''
