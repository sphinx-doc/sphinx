from __future__ import annotations

import os
import warnings
from base64 import b64encode
from collections import defaultdict
from hashlib import sha256
from typing import TYPE_CHECKING, Any, NoReturn

from sphinx.deprecation import RemovedInSphinx90Warning
from sphinx.errors import ThemeError

if TYPE_CHECKING:
    from pathlib import Path


class _CascadingStyleSheet:
    filename: str | os.PathLike[str]
    priority: int
    attributes: dict[str, str]

    def __init__(
        self,
        filename: str | os.PathLike[str], /, *,
        priority: int = 500,
        rel: str = 'stylesheet',
        type: str = 'text/css',
        **attributes: str,
    ) -> None:
        object.__setattr__(self, 'filename', filename)
        object.__setattr__(self, 'priority', priority)
        object.__setattr__(self, 'attributes', {'rel': rel, 'type': type} | attributes)

    def __str__(self) -> str:
        attr = ', '.join(f'{k}={v!r}' for k, v in self.attributes.items())
        return (f'{self.__class__.__name__}({self.filename!r}, '
                f'priority={self.priority}, '
                f'{attr})')

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            warnings.warn('The str interface for _CascadingStyleSheet objects is deprecated. '
                          'Use css.filename instead.', RemovedInSphinx90Warning, stacklevel=2)
            return self.filename == other
        if not isinstance(other, _CascadingStyleSheet):
            return NotImplemented
        return (self.filename == other.filename
                and self.priority == other.priority
                and self.attributes == other.attributes)

    def __hash__(self) -> int:
        return hash((self.filename, self.priority, *sorted(self.attributes.items())))

    def __setattr__(self, key: str, value: Any) -> NoReturn:
        msg = f'{self.__class__.__name__} is immutable'
        raise AttributeError(msg)

    def __delattr__(self, key: str) -> NoReturn:
        msg = f'{self.__class__.__name__} is immutable'
        raise AttributeError(msg)

    def __getattr__(self, key: str) -> str:
        warnings.warn('The str interface for _CascadingStyleSheet objects is deprecated. '
                      'Use css.filename instead.', RemovedInSphinx90Warning, stacklevel=2)
        return getattr(os.fspath(self.filename), key)

    def __getitem__(self, key: int | slice) -> str:
        warnings.warn('The str interface for _CascadingStyleSheet objects is deprecated. '
                      'Use css.filename instead.', RemovedInSphinx90Warning, stacklevel=2)
        return os.fspath(self.filename)[key]


class _JavaScript:
    filename: str | os.PathLike[str]
    priority: int
    attributes: dict[str, str]

    def __init__(
        self,
        filename: str | os.PathLike[str], /, *,
        priority: int = 500,
        **attributes: str,
    ) -> None:
        object.__setattr__(self, 'filename', filename)
        object.__setattr__(self, 'priority', priority)
        object.__setattr__(self, 'attributes', attributes)

    def __str__(self) -> str:
        attr = ''
        if self.attributes:
            attr = ', ' + ', '.join(f'{k}={v!r}' for k, v in self.attributes.items())
        return (f'{self.__class__.__name__}({self.filename!r}, '
                f'priority={self.priority}'
                f'{attr})')

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            warnings.warn('The str interface for _JavaScript objects is deprecated. '
                          'Use js.filename instead.', RemovedInSphinx90Warning, stacklevel=2)
            return self.filename == other
        if not isinstance(other, _JavaScript):
            return NotImplemented
        return (self.filename == other.filename
                and self.priority == other.priority
                and self.attributes == other.attributes)

    def __hash__(self) -> int:
        return hash((self.filename, self.priority, *sorted(self.attributes.items())))

    def __setattr__(self, key: str, value: Any) -> NoReturn:
        msg = f'{self.__class__.__name__} is immutable'
        raise AttributeError(msg)

    def __delattr__(self, key: str) -> NoReturn:
        msg = f'{self.__class__.__name__} is immutable'
        raise AttributeError(msg)

    def __getattr__(self, key: str) -> str:
        warnings.warn('The str interface for _JavaScript objects is deprecated. '
                      'Use js.filename instead.', RemovedInSphinx90Warning, stacklevel=2)
        return getattr(os.fspath(self.filename), key)

    def __getitem__(self, key: int | slice) -> str:
        warnings.warn('The str interface for _JavaScript objects is deprecated. '
                      'Use js.filename instead.', RemovedInSphinx90Warning, stacklevel=2)
        return os.fspath(self.filename)[key]


def _file_integrity(outdir: Path, filename: str | os.PathLike[str]) -> str:
    """Generate SubResource Integrity checksums for local Cascading StyleSheet
    and JavaScript files included within a Sphinx project built for publication
    in HTML format.

    The ordering of algorithms is significant; please refer to the W3C SRI
    specification for details.

    Ref: https://www.w3.org/TR/2016/REC-SRI-20160623/
    """
    filename = os.fspath(filename)
    # Don't generate checksums for HTTP URIs
    if '://' in filename:
        return ''
    # Some themes and extensions have used query strings
    # for a similar asset checksum feature.
    # As we cannot safely strip the query string,
    # raise an error to the user.
    if '?' in filename:
        msg = f'Local asset file paths must not contain query strings: {filename!r}'
        raise ThemeError(msg)
    algorithms = {
        'sha256': sha256,
    }
    checksums = []
    try:
        content = outdir.joinpath(filename).read_bytes()
        for prefix, hasher in algorithms.items():
            checksum: bytes = hasher(content).digest()
            checksum_base64: str = b64encode(checksum).decode('ascii')
            checksums.append(f"{prefix}-{checksum_base64}")
    except FileNotFoundError:
        return ''
    return ' '.join(checksums)


def _integrity_concordance(integrity_a: str, integrity_b: str) -> bool:
    """Determines whether two W3C SubResource Integrity values could
    possibly agree on the content that they both refer to.  This requires
    that they share at least one common hash value for each algorithm that
    they both contain a checksum for.
    """

    def _hashes_by_algorithm(integrity: str) -> dict[str, set[str]]:
        hashes = defaultdict(set)
        for checksum in integrity.split():
            algorithm, _ = checksum.split("-")
            hashes[algorithm].add(checksum)
        return hashes

    hashes_a, hashes_b = (
        _hashes_by_algorithm(integrity_a),
        _hashes_by_algorithm(integrity_b),
    )
    for algorithm in hashes_a.keys() & hashes_b.keys():
        if not hashes_a[algorithm] & hashes_b[algorithm]:
            return False
    return True
