"""Private utilities for the `pytest-xdist`_ plugin.

.. _pytest-xdist: https://pytest-xdist.readthedocs.io

All functions in this module have an undefined behaviour if they are
called before the ``pytest_cmdline_main`` hook.
"""

from __future__ import annotations

__all__ = ()

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import pytest

#: Scheduling policy for :mod:`xdist` specified by :option:`!--dist`.
Policy = Literal['no', 'each', 'load', 'loadscope', 'loadfile', 'loadgroup', 'worksteal']


def get_xdist_policy(config: pytest.Config) -> Policy:
    """Get the ``config.option.dist`` value even if :mod:`!xdist` is absent.

    Use ``get_xdist_policy(config) != 'no'`` to determine whether the plugin
    is active and loaded or not.
    """
    # On systems without the :mod:`!xdist` module, the ``dist`` option does
    # not even exist in the first place and thus using ``config.option.dist``
    # would raise an :exc:`AttributeError`.
    if config.pluginmanager.has_plugin('xdist'):
        # worker nodes do not inherit the 'config.option.dist' value
        # when used by pytester, but since we have a hook that adds
        # them as a worker input, we can retrieve it correctly even
        # if we are not in the controller node
        if hasattr(config, 'workerinput'):
            # this requires our custom xdist hooks
            return config.workerinput['sphinx_xdist_policy']
        return config.option.dist
    return 'no'


def is_pytest_xdist_enabled(config: pytest.Config) -> bool:
    """Check that the :mod:`!xdist` plugin is loaded and active.

    :param config: A pytest configuration object.
    """
    return get_xdist_policy(config) != 'no'


def is_pytest_xdist_controller(config: pytest.Config) -> bool:
    """Check if the configuration is attached to the xdist controller.

    If the :mod:`!xdist` plugin is not active, this returns ``False``.

    .. important::

       This function differs from :func:`xdist.is_xdist_worker` in the
       sense that it works even if the :mod:`xdist` plugin is inactive.
    """
    return is_pytest_xdist_enabled(config) and not is_pytest_xdist_worker(config)


def is_pytest_xdist_worker(config: pytest.Config) -> bool:
    """Check if the configuration is attached to a xdist worker.

    If the :mod:`!xdist` plugin is not active, this returns ``False``.

    .. important::

       This function differs from :func:`xdist.is_xdist_controller` in the
       sense that it works even if the :mod:`xdist` plugin is inactive.
    """
    return is_pytest_xdist_enabled(config) and hasattr(config, 'workerinput')
