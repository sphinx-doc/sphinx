"""Simple requests package loader"""

from __future__ import annotations

import sys
import warnings
from contextlib import contextmanager
from typing import Any, Generator
from urllib.parse import urlsplit

import requests
from urllib3.exceptions import InsecureRequestWarning

import sphinx

useragent_header = [('User-Agent',
                     'Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0')]


@contextmanager
def ignore_insecure_warning(**kwargs: Any) -> Generator[None, None, None]:
    with warnings.catch_warnings():
        if not kwargs.get('verify'):
            # ignore InsecureRequestWarning if verify=False
            warnings.filterwarnings("ignore", category=InsecureRequestWarning)
        yield


def _get_tls_cacert(url: str, tls_verify: bool,
                    certs: str | dict | None) -> str | bool:
    """Get additional CA cert for a specific URL.

    This also returns ``False`` if verification is disabled.
    And returns ``True`` if additional CA cert not found.
    """
    if not tls_verify:
        return False

    if not certs:
        return True
    elif isinstance(certs, (str, tuple)):
        return certs  # type: ignore
    else:
        hostname = urlsplit(url).netloc
        if '@' in hostname:
            hostname = hostname.split('@')[1]

        return certs.get(hostname, True)


def _get_user_agent(user_agent: str | None) -> str:
    if user_agent:
        return user_agent
    else:
        return ' '.join([
            f'Sphinx/{sphinx.__version__}',
            f'requests/{requests.__version__}',
            'python/%s' % '.'.join(map(str, sys.version_info[:3])),
        ])


def get(url: str, **kwargs: Any) -> requests.Response:
    """Sends a GET request like requests.get().

    This sets up User-Agent header and TLS verification automatically."""
    headers = kwargs.setdefault('headers', {})
    config = kwargs.pop('config', None)
    if config:
        certs = getattr(config, 'tls_cacerts', None)

        kwargs.setdefault('verify', _get_tls_cacert(url, config.tls_verify, certs))
        headers.setdefault('User-Agent', _get_user_agent(config.user_agent))
    else:
        headers.setdefault('User-Agent', useragent_header[0][1])

    with ignore_insecure_warning(**kwargs):
        return requests.get(url, **kwargs)


def head(url: str, **kwargs: Any) -> requests.Response:
    """Sends a HEAD request like requests.head().

    This sets up User-Agent header and TLS verification automatically."""
    headers = kwargs.setdefault('headers', {})
    config = kwargs.pop('config', None)
    if config:
        certs = getattr(config, 'tls_cacerts', None)

        kwargs.setdefault('verify', _get_tls_cacert(url, config.tls_verify, certs))
        headers.setdefault('User-Agent', _get_user_agent(config.user_agent))
    else:
        headers.setdefault('User-Agent', useragent_header[0][1])

    with ignore_insecure_warning(**kwargs):
        return requests.head(url, **kwargs)
