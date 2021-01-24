"""
    sphinx.ext.jsmath
    ~~~~~~~~~~~~~~~~~

    Set up everything for use of JSMath to display math in HTML
    via JavaScript.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings
from typing import Any, Dict

from sphinxcontrib.jsmath import (html_visit_displaymath, html_visit_math,  # NOQA
                                  install_jsmath)

import sphinx
from sphinx.application import Sphinx
from sphinx.deprecation import RemovedInSphinx40Warning


def setup(app: Sphinx) -> Dict[str, Any]:
    warnings.warn('sphinx.ext.jsmath has been moved to sphinxcontrib-jsmath.',
                  RemovedInSphinx40Warning)

    app.setup_extension('sphinxcontrib.jsmath')

    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
