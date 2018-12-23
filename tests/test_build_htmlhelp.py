"""
    test_build_htmlhelp
    ~~~~~~~~~~~~~~~~~~~
    Test the HTML Help builder and check output against XPath.
    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os.path
import re
import sys
from subprocess import Popen, PIPE

import pytest

from sphinx.util.osutil import cd


@pytest.mark.skipif(sys.platform != "win32",
                    reason="hhc.exe only available on Windows.")
@pytest.mark.sphinx('htmlhelp', testroot='build-htmlhelp')
def test_chm():
    # run make.bat
    with cd(r".\roots\test-build-htmlhelp"):
        try:
            p = Popen(['make.bat'],
                      stdout=PIPE, stderr=PIPE)
        except:
            raise
        else:
            p.communicate()

    # check .hhk file
    this_path = os.path.dirname(os.path.abspath(__file__))
    hhk_file = os.path.join(this_path, 'roots', 'test-build-htmlhelp',
                            'build', 'htmlhelp', 'test.hhk')
    if not os.path.isfile(hhk_file):
        print(".chm build failed, please install HTML Help Workshop.")
        return

    with open(hhk_file, 'rb') as f:
        data = f.read()
    m = re.search(br'&#[xX][0-9a-fA-F]+;', data)
    assert m == None, 'Hex escaping exists in .hhk file: ' + str(m.group(0))

