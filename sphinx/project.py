# -*- coding: utf-8 -*-
"""
    sphinx.project
    ~~~~~~~~~~~~~~

    Utility function and classes for Sphinx projects.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from typing import TYPE_CHECKING

from sphinx.locale import __
from sphinx.util import get_matching_files
from sphinx.util import logging
from sphinx.util.matching import compile_matchers

if TYPE_CHECKING:
    from typing import Dict, List, Set  # NOQA

logger = logging.getLogger(__name__)
EXCLUDE_PATHS = ['**/_sources', '.#*', '**/.#*', '*.lproj/**']  # type: List[unicode]


class Project(object):
    """A project is source code set of Sphinx document."""

    def __init__(self, srcdir, source_suffix):
        # type: (unicode, Dict[unicode, unicode]) -> None
        #: Source directory.
        self.srcdir = srcdir

        #: source_suffix. Same as :confval:`source_suffix`.
        self.source_suffix = source_suffix

        #: The name of documents belongs to this project.
        self.docnames = set()  # type: Set[unicode]

    def restore(self, other):
        # type: (Project) -> None
        """Take over a result of last build."""
        self.docnames = other.docnames

    def discovery(self, exclude_paths=[]):
        # type: (List[unicode]) -> Set[unicode]
        """Find all document files in the source directory and put them in
        :attr:`docnames`.
        """
        self.docnames = set()
        excludes = compile_matchers(exclude_paths + EXCLUDE_PATHS)
        for filename in get_matching_files(self.srcdir, excludes):  # type: ignore
            for suffix in self.source_suffix:
                if filename.endswith(suffix):
                    docname = filename[:-len(suffix)]
                    if os.access(os.path.join(self.srcdir, filename), os.R_OK):
                        self.docnames.add(docname)
                    else:
                        logger.warning(__("document not readable. Ignored."), location=docname)

        return self.docnames
