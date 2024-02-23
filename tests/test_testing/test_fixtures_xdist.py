from __future__ import annotations

import uuid

import pytest

UNIQUE_ID = uuid.uuid4().hex


@pytest.mark.xdist_group('group-1')
@pytest.mark.sphinx('dummy')
@pytest.mark.test_params(shared_result=UNIQUE_ID)
def test_group_1a(app, shared_result):
    app.build()


@pytest.mark.xdist_group('group-1')
@pytest.mark.sphinx('dummy')
@pytest.mark.test_params(shared_result=UNIQUE_ID)
def test_group_1b(app, shared_result):
    app.build()
