from __future__ import annotations

import re
from typing import TYPE_CHECKING
from xml.etree.ElementTree import tostring

if TYPE_CHECKING:
    import os
    from collections.abc import Callable, Sequence
    from xml.etree.ElementTree import Element


def _gettext(node: Element) -> str:
    if node.text is not None:
        # the node has only one text
        return node.text

    # the node has tags and text; gather texts just under the node
    return ''.join(n.tail or '' for n in node)


def check_xpath(
    root: Element,
    filename: str | os.PathLike[str],
    xpath: str,
    check: str | re.Pattern[str] | Callable[[Sequence[Element]], None] | None,
    be_found: bool = True,
) -> None:
    nodes = root.findall(xpath)
    assert isinstance(nodes, list)

    if check is None:
        # check for an empty list
        assert nodes == [], f'found any nodes matching xpath {xpath!r} in file {filename}'
        return

    assert nodes, 'did not find any node matching xpath {xpath!r} in file {filename}'
    if not check:
        # only check for node presence
        return

    if callable(check):
        check(nodes)
        return

    rex = re.compile(check)
    if be_found:
        if any(rex.search(_gettext(node)) for node in nodes):
            return
    else:
        if all(not rex.search(_gettext(node)) for node in nodes):
            return

    ctx: list[bytes] = [tostring(node, encoding='utf-8') for node in nodes]
    msg = f'{check!r} not found in any node matching {xpath!r} in file {filename}: {ctx}'
    raise AssertionError(msg)
