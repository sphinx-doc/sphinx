# -*- coding: utf-8 -*-
"""
    sphinx.domains.download
    ~~~~~~~~~~~~~~~~~~~~~~~

    The download files domain.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from hashlib import md5

from six.moves import reduce

from sphinx import addnodes
from sphinx.domains import Domain
from sphinx.locale import __
from sphinx.util import logging

if False:
    # For type annotation
    from typing import Any, Dict, Iterable, Set  # NOQA
    from docutils import nodes  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA

logger = logging.getLogger(__name__)


class DownloadDomain(Domain):
    """Download files domain."""
    name = 'download'
    label = 'download'

    initial_data = {
        'objects': {},  # docname -> set of filenames
    }  # type: Dict[unicode, Dict[unicode, Set[unicode]]]

    def clear_doc(self, docname):
        # type: (unicode) -> None
        self.data['objects'].pop(docname, None)

    def merge_domaindata(self, docnames, otherdata):
        # type: (Iterable[unicode], Dict) -> None
        for docname in docnames:
            if docname in otherdata:
                self.data['objects'][docname] = otherdata[docname]

    def process_doc(self, env, docname, document):
        # type: (BuildEnvironment, unicode, nodes.Node) -> None
        downloads = self.data['objects'].setdefault(docname, set())
        for node in document.traverse(addnodes.download_reference):
            rel_filename, filename = env.relfn2path(node['reftarget'], docname)
            env.note_dependency(rel_filename)

            if not os.access(filename, os.R_OK):
                logger.warning(__('download file not readable: %s') % filename,
                               location=node, type='download', subtype='not_readable')
                node['invalid'] = True
                continue

            downloads.add(filename)
            node['reftarget'] = self.get_destination_filename(filename)

    def get_download_files(self):
        # type: () -> Set[unicode]
        return reduce(lambda x, y: x | y, self.data['objects'].values(), set())

    def get_destination_filename(self, filename):
        # type: (unicode) -> unicode
        digest = md5(filename.encode('utf-8')).hexdigest()
        return '%s/%s' % (digest, os.path.basename(filename))


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_domain(DownloadDomain)

    return {
        'version': 'builtin',
        'env_version': 1,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
