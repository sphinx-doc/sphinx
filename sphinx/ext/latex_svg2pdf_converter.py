# -*- coding: utf-8 -*-
"""
    sphinx.ext.latex_svg2pdf_converter
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    SVG to PDF converter extension for LaTeX builder

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import subprocess

from sphinx.errors import ExtensionError
from sphinx.locale import __
from sphinx.transforms.post_transforms.images import ImageConverter
from sphinx.util import logging
from sphinx.util.osutil import ENOENT, EPIPE, EINVAL

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from sphinx.application import Sphinx  # NOQA


logger = logging.getLogger(__name__)


class InkscapeConverter(ImageConverter):
    conversion_rules = [
        ('image/svg+xml', 'application/pdf'),
    ]

    def is_available(self):
        # type: () -> bool
        """Confirms the converter is available or not."""
        try:
            args = [self.config.latex_svg2pdf_converter, '--version']
            logger.debug('Invoking %r ...', args)
            ret = subprocess.call(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            if ret == 0:
                return True
            else:
                return False
        except (OSError, IOError):
            logger.warning(__('convert command %r cannot be run.'
                              'check the image_converter setting'),
                           self.latex_svg2pdf_converter)
            return False

    def convert(self, _from, _to):
        # type: (unicode, unicode) -> bool
        """Converts the image to expected one."""
        if self.app.builder.name != 'latex':
            return

        try:
            args = ([self.config.latex_svg2pdf_converter] +
                    self.config.latex_svg2pdf_converter_args +
                    ['--export-pdf=' + _to, _from])
            logger.debug('Invoking %r ...', args)
            p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        except OSError as err:
            if err.errno != ENOENT:  # No such file or directory
                raise
            logger.warning(__('convert command %r cannot be run.'
                              'check the image_converter setting'),
                           self.config.latex_svg2pdf_converter)
            return False

        try:
            stdout, stderr = p.communicate()
        except (OSError, IOError) as err:
            if err.errno not in (EPIPE, EINVAL):
                raise
            stdout, stderr = p.stdout.read(), p.stderr.read()
            p.wait()
        if p.returncode != 0:
            raise ExtensionError(__('convert exited with error:\n'
                                    '[stderr]\n%s\n[stdout]\n%s') %
                                 (stderr, stdout))

        return True


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_post_transform(InkscapeConverter)
    app.add_config_value('latex_svg2pdf_converter', 'inkscape', 'env')
    app.add_config_value('latex_svg2pdf_converter_args',
            ['--export-area-drawing'], 'env')

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
