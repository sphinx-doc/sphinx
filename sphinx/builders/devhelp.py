"""
    sphinx.builders.devhelp
    ~~~~~~~~~~~~~~~~~~~~~~~

    Build HTML documentation and Devhelp_ support files.

    .. _Devhelp: https://wiki.gnome.org/Apps/Devhelp

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings
from typing import Any, Dict

from sphinxcontrib.devhelp import DevhelpBuilder

from sphinx.application import Sphinx
from sphinx.deprecation import RemovedInSphinx40Warning, deprecated_alias

deprecated_alias('sphinx.builders.devhelp',
                 {
                     'DevhelpBuilder': DevhelpBuilder,
                 },
                 RemovedInSphinx40Warning,
                 {
                     'DevhelpBuilder': 'sphinxcontrib.devhelp.DevhelpBuilder'
                 })


def setup(app: Sphinx) -> Dict[str, Any]:
    warnings.warn('sphinx.builders.devhelp has been moved to sphinxcontrib-devhelp.',
                  RemovedInSphinx40Warning)
    app.setup_extension('sphinxcontrib.devhelp')

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
