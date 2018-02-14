# -*- coding: utf-8 -*-
"""
    sphinx.util.compat
    ~~~~~~~~~~~~~~~~~~

    modules for backward compatibility

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings

from six import string_types, iteritems

from sphinx.deprecation import RemovedInSphinx30Warning
from sphinx.util import import_object

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.config import Config  # NOQA


def deprecate_source_parsers(app, config):
    # type: (Sphinx, Config) -> None
    if config.source_parsers:
        warnings.warn('The config variable "source_parsers" is deprecated. '
                      'Please use app.add_source_parser() API instead.',
                      RemovedInSphinx30Warning)
        for suffix, parser in iteritems(config.source_parsers):
            if isinstance(parser, string_types):
                parser = import_object(parser, 'source parser')  # type: ignore
            app.add_source_parser(suffix, parser)


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.connect('config-inited', deprecate_source_parsers)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
