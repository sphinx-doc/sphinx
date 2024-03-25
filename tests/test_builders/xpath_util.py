from __future__ import annotations

import re
import textwrap
from typing import TYPE_CHECKING
from xml.etree.ElementTree import tostring

if TYPE_CHECKING:
    import os
    from collections.abc import Callable, Iterable, Sequence
    from xml.etree.ElementTree import Element, ElementTree


def _get_text(node: Element) -> str:
    if node.text is not None:
        # the node has only one text
        return node.text

    # the node has tags and text; gather texts just under the node
    return ''.join(n.tail or '' for n in node)


def _prettify(nodes: Iterable[Element]) -> str:
    def pformat(node: Element) -> str:
        return tostring(node, encoding='unicode', method='html')

    return ''.join(f'(i={index}) {pformat(node)}\n' for index, node in enumerate(nodes))


def check_xpath(
    etree: ElementTree,
    filename: str | os.PathLike[str],
    xpath: str,
    check: str | re.Pattern[str] | Callable[[Sequence[Element]], None] | None,
    be_found: bool = True,
    *,
    min_count: int = 1,
) -> None:
    """Check that one or more nodes satisfy a predicate.

    :param etree: The element tree.
    :param filename: The element tree source name (for errors only).
    :param xpath: An XPath expression to use.
    :param check: Optional regular expression or a predicate the nodes must validate.
    :param be_found: If false, negate the predicate.
    :param min_count: Minimum number of nodes expected to satisfy the predicate.

    * If *check* is empty (``''``), only the minimum count is checked.
    * If *check* is ``None``, no node should satisfy the XPath expression.
    """
    nodes = etree.findall(xpath)
    assert isinstance(nodes, list)

    if check is None:
        # use == to have a nice pytest diff
        assert nodes == [], f'found nodes matching xpath {xpath!r} in file {filename}'
        return

    assert len(nodes) >= min_count, (f'expecting at least {min_count} node(s) '
                                     f'to satisfy {xpath!r} in file {filename}')

    if check == '':
        return

    if callable(check):
        check(nodes)
        return

    rex = re.compile(check)
    if be_found:
        if any(rex.search(_get_text(node)) for node in nodes):
            return
    else:
        if all(not rex.search(_get_text(node)) for node in nodes):
            return

    ctx = textwrap.indent(_prettify(nodes), ' ' * 2)
    msg = f'{check!r} not found in any node matching {xpath!r} in file {filename}:\n{ctx}'
    raise AssertionError(msg)
