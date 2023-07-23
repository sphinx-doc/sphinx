"""Simple requests package loader"""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from typing import Any, Iterator
from urllib.parse import urlsplit

import requests
from urllib3.exceptions import InsecureRequestWarning

import sphinx

_USER_AGENT = (f'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0 '
               f'Sphinx/{sphinx.__version__}')


@contextmanager
def ignore_insecure_warning(verify: bool) -> Iterator[None]:
    with warnings.catch_warnings():
        if not verify:
            # ignore InsecureRequestWarning if verify=False
            warnings.filterwarnings("ignore", category=InsecureRequestWarning)
        yield


def _get_tls_cacert(url: str, certs: str | dict[str, str] | None) -> str | bool:
    """Get additional CA cert for a specific URL."""
    if not certs:
        return True
    elif isinstance(certs, (str, tuple)):
        return certs
    else:
        hostname = urlsplit(url).netloc
        if '@' in hostname:
            _, hostname = hostname.split('@', 1)

        return certs.get(hostname, True)


def get(url: str,
        _user_agent: str = '',
        _tls_info: tuple[bool, str | dict[str, str] | None] = (),  # type: ignore[assignment]
        **kwargs: Any) -> requests.Response:
    """Sends a HEAD request like requests.head().

    This sets up User-Agent header and TLS verification automatically."""
    headers = kwargs.setdefault('headers', {})
    headers.setdefault('User-Agent', _user_agent or _USER_AGENT)
    if _tls_info:
        tls_verify, tls_cacerts = _tls_info
        verify = bool(kwargs.get('verify', tls_verify))
        kwargs.setdefault('verify', verify and _get_tls_cacert(url, tls_cacerts))
    else:
        verify = kwargs.get('verify', True)

    with ignore_insecure_warning(verify):
        return requests.get(url, **kwargs)


def head(url: str,
         _user_agent: str = '',
         _tls_info: tuple[bool, str | dict[str, str] | None] = (),  # type: ignore[assignment]
         **kwargs: Any) -> requests.Response:
    """Sends a HEAD request like requests.head().

    This sets up User-Agent header and TLS verification automatically."""
    headers = kwargs.setdefault('headers', {})
    headers.setdefault('User-Agent', _user_agent or _USER_AGENT)
    if _tls_info:
        tls_verify, tls_cacerts = _tls_info
        verify = bool(kwargs.get('verify', tls_verify))
        kwargs.setdefault('verify', verify and _get_tls_cacert(url, tls_cacerts))
    else:
        verify = kwargs.get('verify', True)

    with ignore_insecure_warning(verify):
        return requests.head(url, **kwargs)


class _Session(requests.Session):

    def get(self, url: str, **kwargs: Any) -> requests.Response:  # type: ignore[override]
        """Sends a GET request like requests.get().

        This sets up User-Agent header and TLS verification automatically."""
        headers = kwargs.setdefault('headers', {})
        headers.setdefault('User-Agent', kwargs.pop('_user_agent', _USER_AGENT))
        if '_tls_info' in kwargs:
            tls_verify, tls_cacerts = kwargs.pop('_tls_info')
            verify = bool(kwargs.get('verify', tls_verify))
            kwargs.setdefault('verify', verify and _get_tls_cacert(url, tls_cacerts))
        else:
            verify = kwargs.get('verify', True)

        with ignore_insecure_warning(verify):
            return super().get(url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> requests.Response:  # type: ignore[override]
        """Sends a HEAD request like requests.head().

        This sets up User-Agent header and TLS verification automatically."""
        headers = kwargs.setdefault('headers', {})
        headers.setdefault('User-Agent', kwargs.pop('_user_agent', _USER_AGENT))
        if '_tls_info' in kwargs:
            tls_verify, tls_cacerts = kwargs.pop('_tls_info')
            verify = bool(kwargs.get('verify', tls_verify))
            kwargs.setdefault('verify', verify and _get_tls_cacert(url, tls_cacerts))
        else:
            verify = kwargs.get('verify', True)

        with ignore_insecure_warning(verify):
            return super().head(url, **kwargs)
