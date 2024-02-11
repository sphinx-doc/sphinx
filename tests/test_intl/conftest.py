#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from _pytest.config import Config
    from _pytest.main import Session
    from _pytest.nodes import Item


def pytest_collection_modifyitems(
    session: Session, config: Config, items: Sequence[Item]
) -> None:
    for item in items:
        if (
            'tests/test_intl/test_intl.py' in str(item.path)
            and not item.get_closest_marker('parallel')
        ):
            # force serial execution of items in 'test_intl'
            item.add_marker('serial')

