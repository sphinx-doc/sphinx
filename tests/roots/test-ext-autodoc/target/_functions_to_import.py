from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sphinx.application import Sphinx


def function_to_be_imported(app: Optional['Sphinx']) -> str:
    """docstring"""
