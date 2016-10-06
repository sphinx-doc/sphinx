# -*- coding: utf-8 -*-
"""
    sphinx.util.requests
    ~~~~~~~~~~~~~~~~~~~~

    Simple requests package loader

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from __future__ import absolute_import

import requests
import warnings
import pkg_resources
from requests.packages.urllib3.exceptions import SSLError

# try to load requests[security]
try:
    pkg_resources.require(['requests[security]'])
except pkg_resources.DistributionNotFound:
    import ssl
    if not getattr(ssl, 'HAS_SNI', False):
        # don't complain on each url processed about the SSL issue
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecurePlatformWarning)
        warnings.warn(
            'Some links may return broken results due to being unable to '
            'check the Server Name Indication (SNI) in the returned SSL cert '
            'against the hostname in the url requested. Recommended to '
            'install "requests[security]" as a dependency or upgrade to '
            'a python version with SNI support (Python 3 and Python 2.7.9+).'
        )
except pkg_resources.UnknownExtra:
    warnings.warn(
        'Some links may return broken results due to being unable to '
        'check the Server Name Indication (SNI) in the returned SSL cert '
        'against the hostname in the url requested. Recommended to '
        'install requests-2.4.1+.'
    )

useragent_header = [('User-Agent',
                     'Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0')]


def is_ssl_error(exc):
    if isinstance(exc, SSLError):
        return True
    else:
        args = getattr(exc, 'args', [])
        if args and isinstance(args[0], SSLError):
            return True
        else:
            return False
