"""
    test_transforms_post_transforms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the post_transforms

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
from docutils import nodes


@pytest.mark.sphinx('html', testroot='transforms-post_transforms-missing-reference')
def test_nitpicky_warning(app, status, warning):
    app.build()
    assert ('index.rst:4: WARNING: py:class reference target '
            'not found: io.StringIO' in warning.getvalue())

    content = (app.outdir / 'index.html').read_text()
    assert ('<p><code class="xref py py-class docutils literal notranslate"><span class="pre">'
            'io.StringIO</span></code></p>' in content)


@pytest.mark.sphinx('html', testroot='transforms-post_transforms-missing-reference',
                    freshenv=True)
def test_missing_reference(app, status, warning):
    def missing_reference(app, env, node, contnode):
        assert app is app
        assert env is app.env
        assert node['reftarget'] == 'io.StringIO'
        assert contnode.astext() == 'io.StringIO'

        return nodes.inline('', 'missing-reference.StringIO')

    warning.truncate(0)
    app.connect('missing-reference', missing_reference)
    app.build()
    assert warning.getvalue() == ''

    content = (app.outdir / 'index.html').read_text()
    assert '<p><span>missing-reference.StringIO</span></p>' in content


@pytest.mark.sphinx('html', testroot='domain-py-python_use_unqualified_type_names',
                    freshenv=True)
def test_missing_reference_conditional_pending_xref(app, status, warning):
    def missing_reference(app, env, node, contnode):
        return contnode

    warning.truncate(0)
    app.connect('missing-reference', missing_reference)
    app.build()
    assert warning.getvalue() == ''

    content = (app.outdir / 'index.html').read_text()
    assert '<span class="n"><span class="pre">Age</span></span>' in content
