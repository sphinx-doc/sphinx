"""modules for backward compatibility"""

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from sphinx.application import Sphinx


def setup(app: "Sphinx") -> Dict[str, Any]:
    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
