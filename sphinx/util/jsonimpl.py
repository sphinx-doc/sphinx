"""
    sphinx.util.jsonimpl
    ~~~~~~~~~~~~~~~~~~~~

    JSON serializer implementation wrapper.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import json
import warnings
from collections import UserString
from typing import IO, Any

from sphinx.deprecation import RemovedInSphinx40Warning

warnings.warn('sphinx.util.jsonimpl is deprecated',
              RemovedInSphinx40Warning, stacklevel=2)


class SphinxJSONEncoder(json.JSONEncoder):
    """JSONEncoder subclass that forces translation proxies."""
    def default(self, obj: Any) -> str:
        if isinstance(obj, UserString):
            return str(obj)
        return super().default(obj)


def dump(obj: Any, fp: IO, *args: Any, **kwargs: Any) -> None:
    kwargs['cls'] = SphinxJSONEncoder
    json.dump(obj, fp, *args, **kwargs)


def dumps(obj: Any, *args: Any, **kwargs: Any) -> str:
    kwargs['cls'] = SphinxJSONEncoder
    return json.dumps(obj, *args, **kwargs)


def load(*args: Any, **kwargs: Any) -> Any:
    return json.load(*args, **kwargs)


def loads(*args: Any, **kwargs: Any) -> Any:
    return json.loads(*args, **kwargs)
