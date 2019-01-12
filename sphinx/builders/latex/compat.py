"""
    sphinx.builders.latex.compat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Compatibility module for LaTeX writer.
    This module will be removed after deprecation period.
    Don't use components in this modules directly.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.builders.latex.transforms import URI_SCHEMES, ShowUrlsTransform
from sphinx.builders.latex.util import ExtBabel
from sphinx.deprecation import (
    RemovedInSphinx30Warning, RemovedInSphinx40Warning, deprecated_alias
)


deprecated_alias('sphinx.writers.latex',
                 {
                     'ShowUrlsTransform': ShowUrlsTransform,
                     'URI_SCHEMES': URI_SCHEMES,
                 },
                 RemovedInSphinx30Warning)

deprecated_alias('sphinx.writers.latex',
                 {
                     'ExtBabel': ExtBabel,
                 },
                 RemovedInSphinx40Warning)
