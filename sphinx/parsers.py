# -*- coding: utf-8 -*-
"""
    sphinx.parsers
    ~~~~~~~~~~~~~~

    A Base class for additional parsers.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import docutils.parsers


class Parser(docutils.parsers.Parser):
    """
    A base class of parsers.
    """

    def set_application(self, app):
        """set_application will be called from Sphinx to set app and other instance variables

        :param sphinx.application.Sphinx app: Sphinx application object
        """
        self.app = app
        self.config = app.config
        self.env = app.env
        self.warn = app.warn
        self.info = app.info
