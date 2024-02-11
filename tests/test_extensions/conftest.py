#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _unload(rollback_sysmodules):
    """Ensure that autodoc-related modules are clean-up."""


