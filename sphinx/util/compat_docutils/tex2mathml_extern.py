# -*- coding: utf-8 -*-
"""
    sphinx.util.compat_docutils.tex2mathml_extern
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Wrappers for TeX->MathML conversion by external tools.

    This code is copied from Docutils trunk.
    Original author is Günter Milde <milde@users.sf.net>.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import subprocess

document_template = r"""\documentclass{article}
\usepackage{amsmath}
\begin{document}
%s
\end{document}
"""


def latexml(math_code, reporter=None):
    """Convert LaTeX math code to MathML with LaTeXML_

    .. _LaTeXML: http://dlmf.nist.gov/LaTeXML/
    """
    p = subprocess.Popen(
        [
            'latexml',
            '-',  # read from stdin
            # '--preload=amsmath',
            '--inputencoding=utf8',
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)
    p.stdin.write((document_template % math_code).encode('utf8'))
    p.stdin.close()
    latexml_code = p.stdout.read()
    latexml_err = p.stderr.read().decode('utf8')
    if reporter and latexml_err.find('Error') >= 0 or not latexml_code:
        reporter.error(latexml_err)

    post_p = subprocess.Popen(
        [
            'latexmlpost',
            '-',
            '--nonumbersections',
            '--format=xhtml',
            # '--linelength=78', # experimental
            '--'
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)
    post_p.stdin.write(latexml_code)
    post_p.stdin.close()
    result = post_p.stdout.read().decode('utf8')
    post_p_err = post_p.stderr.read().decode('utf8')
    if reporter and post_p_err.find('Error') >= 0 or not result:
        reporter.error(post_p_err)

    # extract MathML code:
    start, end = result.find('<math'), result.find('</math>')+7
    result = result[start:end]
    if 'class="ltx_ERROR' in result:
        raise SyntaxError(result)
    return result


def ttm(math_code, reporter=None):
    """Convert LaTeX math code to MathML with TtM_

    .. _TtM: http://hutchinson.belmont.ma.us/tth/mml/
    """
    p = subprocess.Popen(
        [
            'ttm',
            # '-i', # italic font for equations. Default roman.
            '-u',  # unicode character encoding. (Default iso-8859-1).
            '-r',  # output raw MathML (no preamble or  postlude)
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)
    p.stdin.write((document_template % math_code).encode('utf8'))
    p.stdin.close()
    result = p.stdout.read()
    err = p.stderr.read().decode('utf8')
    if err.find('**** Unknown') >= 0:
        msg = '\n'.join([line for line in err.splitlines() if line.startswith('****')])
        raise SyntaxError('\nMessage from external converter TtM:\n' + msg)
    if reporter and err.find('**** Error') >= 0 or not result:
        reporter.error(err)
    start, end = result.find('<math'), result.find('</math>') + 7
    result = result[start:end]
    return result


def blahtexml(math_code, inline=True, reporter=None):
    """Convert LaTeX math code to MathML with blahtexml_

    .. _blahtexml: http://gva.noekeon.org/blahtexml/
    """
    options = [
        '--mathml',
        '--indented',
        '--spacing', 'moderate',
        '--mathml-encoding', 'raw',
        '--other-encoding', 'raw',
        '--doctype-xhtml+mathml',
        '--annotate-TeX',
    ]
    if inline:
        mathmode_arg = ''
    else:
        mathmode_arg = 'mode="display"'
        options.append('--displaymath')

    p = subprocess.Popen(
        ['blahtexml'] + options,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)
    p.stdin.write(math_code.encode('utf8'))
    p.stdin.close()
    result = p.stdout.read().decode('utf8')
    err = p.stderr.read().decode('utf8')

    if result.find('<error>') >= 0:
        msg = result[result.find('<message>') + 9:result.find('</message>')]
        raise SyntaxError('\nMessage from external converter blahtexml:\n' + msg)
    if reporter and (err.find('**** Error') >= 0 or not result):
        reporter.error(err)
    start, end = result.find('<markup>') + 9, result.find('</markup>')
    result = ('<math xmlns="http://www.w3.org/1998/Math/MathML"%s>\n'
              '%s</math>\n') % (mathmode_arg, result[start:end])
    return result

# self-test

if __name__ == "__main__":
    example = u'\frac{\partial \sin^2(\alpha)}{\partial \vec r} \varpi \, \text{Grüße}'
    # print(latexml(example).encode('utf8'))
    # print(ttm(example)#.encode('utf8'))
    print(blahtexml(example).encode('utf8'))
