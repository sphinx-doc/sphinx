from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

import lxml.etree
from lxml.etree import _Element as ElementLXML
from lxml.etree import _ElementTree as ElementTreeLXML

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


def _get_text(node: ElementLXML) -> str:
    if node.text is not None:
        # the node has only one text
        return node.text

    # the node has tags and text; gather texts just under the node
    return ''.join(n.tail or '' for n in node)


def check_xpath(
    etree: ElementTreeLXML,
    fname: str | os.PathLike[str],
    xpath: str,
    check: str | re.Pattern[str] | Callable[[Sequence[ElementLXML]], None] | None,
    be_found: bool = True,
) -> None:
    assert isinstance(etree, ElementTreeLXML)

    nodes = list(etree.findall(xpath))
    assert all(isinstance(node, ElementLXML) for node in nodes)

    if check is None:
        assert nodes == [], ('found any nodes matching xpath '
                             f'{xpath!r} in file {os.fsdecode(fname)}')
        return
    else:
        assert nodes != [], ('did not find any node matching xpath '
                             f'{xpath!r} in file {os.fsdecode(fname)}')
    if callable(check):
        check(nodes)
    elif not check:
        # only check for node presence
        pass
    else:
        rex = re.compile(check)
        if be_found:
            if any(rex.search(_get_text(node)) for node in nodes):
                return
        else:
            if all(not rex.search(_get_text(node)) for node in nodes):
                return

        context = list(map(lxml.etree.tostring, nodes))
        msg = (f'{check!r} not found in any node matching '
               f'{xpath!r} in file {os.fsdecode(fname)}: {context}')
        raise AssertionError(msg)
