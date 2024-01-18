import pytest


@pytest.mark.sphinx('html', testroot='root',
                    confoverrides={'option_emphasise_placeholders': True})
def test_option_emphasise_placeholders(app, status, warning):
    app.build()
    content = (app.outdir / 'objects.html').read_text(encoding='utf8')
    assert '<em><span class="pre">TYPE</span></em>' in content
    assert '{TYPE}' not in content
    assert ('<em><span class="pre">WHERE</span></em>'
            '<span class="pre">-</span>'
            '<em><span class="pre">COUNT</span></em>' in content)
    assert '<span class="pre">{{value}}</span>' in content
    assert ('<span class="pre">--plugin.option</span></span>'
            '<a class="headerlink" href="#cmdoption-perl-plugin.option" title="Link to this definition">¶</a></dt>') in content


@pytest.mark.sphinx('html', testroot='root')
def test_option_emphasise_placeholders_default(app, status, warning):
    app.build()
    content = (app.outdir / 'objects.html').read_text(encoding='utf8')
    assert '<span class="pre">={TYPE}</span>' in content
    assert '<span class="pre">={WHERE}-{COUNT}</span></span>' in content
    assert '<span class="pre">{client_name}</span>' in content
    assert ('<span class="pre">--plugin.option</span></span>'
            '<span class="sig-prename descclassname"></span>'
            '<a class="headerlink" href="#cmdoption-perl-plugin.option" title="Link to this definition">¶</a></dt>') in content


@pytest.mark.sphinx('html', testroot='root')
def test_option_reference_with_value(app, status, warning):
    app.build()
    content = (app.outdir / 'objects.html').read_text(encoding='utf-8')
    assert ('<span class="pre">-mapi</span></span><span class="sig-prename descclassname">'
            '</span><a class="headerlink" href="#cmdoption-git-commit-mapi"') in content
    assert 'first option <a class="reference internal" href="#cmdoption-git-commit-mapi">' in content
    assert ('<a class="reference internal" href="#cmdoption-git-commit-mapi">'
            '<code class="xref std std-option docutils literal notranslate"><span class="pre">-mapi[=xxx]</span></code></a>') in content
    assert '<span class="pre">-mapi</span> <span class="pre">with_space</span>' in content
