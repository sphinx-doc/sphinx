# -*- coding: utf-8 -*-
"""
    test_writer_latex
    ~~~~~~~~~~~~~~~~

    Test the LaTeX writer

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function
from sphinx.writers.latex import rstdim_to_latexdim


def test_rstdim_to_latexdim():
    # Length units docutils supported
    # http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#length-units
    assert rstdim_to_latexdim('160em') == '160em'
    assert rstdim_to_latexdim('160px') == '160.000\\sphinxpxdimen'
    assert rstdim_to_latexdim('160in') == '160in'
    assert rstdim_to_latexdim('160cm') == '160cm'
    assert rstdim_to_latexdim('160mm') == '160mm'
    assert rstdim_to_latexdim('160pt') == '160bp'
    assert rstdim_to_latexdim('160pc') == '160pc'
    assert rstdim_to_latexdim('30%') == '0.300\\linewidth'
    assert rstdim_to_latexdim('160') is None

    assert rstdim_to_latexdim('160.0em') == '160.0em'
