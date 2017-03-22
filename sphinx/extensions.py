# -*- coding: utf-8 -*-
"""
    sphinx.extensions
    ~~~~~~~~~~~~~~~~~

    Utilities for Sphinx extensions.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import traceback

from six import iteritems

from sphinx.errors import ExtensionError, VersionRequirementError
from sphinx.locale import _
from sphinx.util import logging

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from sphinx.application import Sphinx  # NOQA


logger = logging.getLogger(__name__)


# list of deprecated extensions. Keys are extension name.
# Values are Sphinx version that merge the extension.
EXTENSION_BLACKLIST = {
    "sphinxjp.themecore": "1.2"
}  # type: Dict[unicode, unicode]


class Extension(object):
    def __init__(self, name, module, **kwargs):
        self.name = name
        self.module = module
        self.version = kwargs.pop('version', 'unknown version')
        self.parallel_read_safe = kwargs.pop('parallel_read_safe', None)
        self.parallel_write_safe = kwargs.pop('parallel_read_safe', True)
        self.metadata = kwargs


def load(app, extname):
    # type: (Sphinx, unicode) -> None
    """Load a Sphinx extension."""
    if extname in app.extensions:  # alread loaded
        return
    if extname in EXTENSION_BLACKLIST:
        logger.warning(_('the extension %r was already merged with Sphinx since '
                         'version %s; this extension is ignored.'),
                       extname, EXTENSION_BLACKLIST[extname])
        return

    # update loading context
    app._setting_up_extension.append(extname)

    try:
        mod = __import__(extname, None, None, ['setup'])
    except ImportError as err:
        logger.verbose(_('Original exception:\n') + traceback.format_exc())
        raise ExtensionError(_('Could not import extension %s') % extname, err)

    if not hasattr(mod, 'setup'):
        logger.warning(_('extension %r has no setup() function; is it really '
                         'a Sphinx extension module?'), extname)
        metadata = {}  # type: Dict[unicode, Any]
    else:
        try:
            metadata = mod.setup(app)
        except VersionRequirementError as err:
            # add the extension name to the version required
            raise VersionRequirementError(
                _('The %s extension used by this project needs at least '
                  'Sphinx v%s; it therefore cannot be built with this '
                  'version.') % (extname, err)
            )

    if metadata is None:
        metadata = {}
        if extname == 'rst2pdf.pdfbuilder':
            metadata['parallel_read_safe'] = True
    elif not isinstance(metadata, dict):
        logger.warning(_('extension %r returned an unsupported object from '
                         'its setup() function; it should return None or a '
                         'metadata dictionary'), extname)

    app.extensions[extname] = Extension(extname, mod, **metadata)
    app._setting_up_extension.pop()


def confirm(app, requirements):
    # type: (Sphinx, Dict[unicode, unicode]) -> None
    """Confirm the expected Sphinx extensions are loaded."""
    if requirements is None:
        return

    for extname, reqversion in iteritems(requirements):
        extension = app.extensions.get(extname)
        if extension is None:
            logger.warning(_('needs_extensions config value specifies a '
                             'version requirement for extension %s, but it is '
                             'not loaded'), extname)
            continue

        if extension.version == 'unknown version' or reqversion > extension.version:
            raise VersionRequirementError(_('This project needs the extension %s at least in '
                                            'version %s and therefore cannot be built with '
                                            'the loaded version (%s).') %
                                          (extname, reqversion, extension.version))
