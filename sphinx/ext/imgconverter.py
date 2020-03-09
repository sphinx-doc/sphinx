"""
    sphinx.ext.imgconverter
    ~~~~~~~~~~~~~~~~~~~~~~~

    Image converter extension for Sphinx

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import subprocess
from subprocess import CalledProcessError, PIPE
from typing import Any, Dict

from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.locale import __
from sphinx.transforms.post_transforms.images import ImageConverter
from sphinx.util import logging


logger = logging.getLogger(__name__)


class ImagemagickConverter(ImageConverter):
    conversion_rules = [
        ('image/svg+xml', 'image/png'),
        ('image/gif', 'image/png'),
        ('application/pdf', 'image/png'),
        ('application/illustrator', 'image/png'),
    ]

    def is_available(self) -> bool:
        """Confirms the converter is available or not."""
        try:
            args = [self.config.image_converter, '-version']
            logger.debug('Invoking %r ...', args)
            subprocess.run(args, stdout=PIPE, stderr=PIPE, check=True)
            return True
        except OSError:
            logger.warning(__('convert command %r cannot be run, '
                              'check the image_converter setting'),
                           self.config.image_converter)
            return False
        except CalledProcessError as exc:
            logger.warning(__('convert exited with error:\n'
                              '[stderr]\n%r\n[stdout]\n%r'),
                           exc.stderr, exc.stdout)
            return False

    def convert(self, _from: str, _to: str) -> bool:
        """Converts the image to expected one."""
        try:
            # append an index 0 to source filename to pick up the first frame
            # (or first page) of image (ex. Animation GIF, PDF)
            _from += '[0]'

            args = ([self.config.image_converter] +
                    self.config.image_converter_args +
                    [_from, _to])
            logger.debug('Invoking %r ...', args)
            subprocess.run(args, stdout=PIPE, stderr=PIPE, check=True)
            return True
        except OSError:
            logger.warning(__('convert command %r cannot be run, '
                              'check the image_converter setting'),
                           self.config.image_converter)
            return False
        except CalledProcessError as exc:
            raise ExtensionError(__('convert exited with error:\n'
                                    '[stderr]\n%r\n[stdout]\n%r') %
                                 (exc.stderr, exc.stdout))


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_post_transform(ImagemagickConverter)
    app.add_config_value('image_converter', 'convert', 'env')
    app.add_config_value('image_converter_args', [], 'env')

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
