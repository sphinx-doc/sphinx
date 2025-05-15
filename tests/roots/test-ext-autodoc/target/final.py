from __future__ import annotations

import typing
from typing import final

import typing_extensions
from typing_extensions import final as final_ext  # noqa: UP035


@typing.final
class Class:
    """docstring"""

    @final
    def meth1(self):
        """docstring"""

    def meth2(self):
        """docstring"""

    @final_ext
    def meth3(self):
        """docstring"""

    @typing_extensions.final
    def meth4(self):
        """docstring"""
