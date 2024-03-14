"""Hooks to register when the ``xdist`` plugin is active.

Wen ``xdist`` is active, the controller node automatically loads
this module through :func:`sphinx.testing.plugin.pytest_addhooks`.
"""

from __future__ import annotations

__all__ = ()

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest
    from xdist.workermanage import NodeManager, WorkerController


def pytest_configure_node(node: WorkerController) -> None:
    node_config: pytest.Config = node.config
    # the node's config is not the same as the controller's config
    assert node_config.pluginmanager.has_plugin('xdist'), 'xdist is not loaded'

    manager: NodeManager = node.nodemanager
    config: pytest.Config = manager.config
    assert config.pluginmanager.has_plugin('xdist'), 'xdist is not loaded'

    # worker nodes do not inherit the 'config.option.dist' value
    # when used by pytester, so we simply copy it from the main
    # controller to the worker node
    node.workerinput['sphinx_xdist_policy'] = config.option.dist
