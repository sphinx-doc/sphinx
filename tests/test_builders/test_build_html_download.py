import hashlib
import re

import pytest


@pytest.mark.sphinx('html')
@pytest.mark.test_params(shared_result='test_build_html_output')
def test_html_download(app):
    app.build()

    # subdir/includes.html
    result = (app.outdir / 'subdir' / 'includes.html').read_text(encoding='utf8')
    pattern = ('<a class="reference download internal" download="" '
               'href="../(_downloads/.*/img.png)">')
    matched = re.search(pattern, result)
    assert matched
    assert (app.outdir / matched.group(1)).exists()
    filename = matched.group(1)

    # includes.html
    result = (app.outdir / 'includes.html').read_text(encoding='utf8')
    pattern = ('<a class="reference download internal" download="" '
               'href="(_downloads/.*/img.png)">')
    matched = re.search(pattern, result)
    assert matched
    assert (app.outdir / matched.group(1)).exists()
    assert matched.group(1) == filename

    pattern = ('<a class="reference download internal" download="" '
               'href="(_downloads/.*/)(file_with_special_%23_chars.xyz)">')
    matched = re.search(pattern, result)
    assert matched
    assert (app.outdir / matched.group(1) / "file_with_special_#_chars.xyz").exists()


@pytest.mark.sphinx('html', testroot='roles-download')
def test_html_download_role(app, status, warning):
    app.build()
    digest = hashlib.md5(b'dummy.dat', usedforsecurity=False).hexdigest()
    assert (app.outdir / '_downloads' / digest / 'dummy.dat').exists()
    digest_another = hashlib.md5(b'another/dummy.dat', usedforsecurity=False).hexdigest()
    assert (app.outdir / '_downloads' / digest_another / 'dummy.dat').exists()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (('<li><p><a class="reference download internal" download="" '
             'href="_downloads/%s/dummy.dat">'
             '<code class="xref download docutils literal notranslate">'
             '<span class="pre">dummy.dat</span></code></a></p></li>' % digest)
            in content)
    assert (('<li><p><a class="reference download internal" download="" '
             'href="_downloads/%s/dummy.dat">'
             '<code class="xref download docutils literal notranslate">'
             '<span class="pre">another/dummy.dat</span></code></a></p></li>' %
             digest_another) in content)
    assert ('<li><p><code class="xref download docutils literal notranslate">'
            '<span class="pre">not_found.dat</span></code></p></li>' in content)
    assert ('<li><p><a class="reference download external" download="" '
            'href="https://www.sphinx-doc.org/en/master/_static/sphinx-logo.svg">'
            '<code class="xref download docutils literal notranslate">'
            '<span class="pre">Sphinx</span> <span class="pre">logo</span>'
            '</code></a></p></li>' in content)
