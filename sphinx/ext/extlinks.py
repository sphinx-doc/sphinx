"""
    sphinx.ext.extlinks
    ~~~~~~~~~~~~~~~~~~~

    Extension to save typing and prevent hard-coding of base URLs in the reST
    files.

    This adds a new config value called ``extlinks`` that is created like this::

       extlinks = {'exmpl': ('https://example.invalid/%s.html', prefix), ...}

    Now you can use e.g. :exmpl:`foo` in your documents.  This will create a
    link to ``https://example.invalid/foo.html``.  The link caption depends on
    the *prefix* value given:

    - If it is ``None``, the caption will be the full URL.
    - If it is a string (empty or not), the caption will be the prefix prepended
      to the role content.

    You can also give an explicit caption, e.g. :exmpl:`Foo <foo>`.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import Any, Dict, List, Tuple

from docutils import nodes, utils
from docutils.nodes import Node, system_message
from docutils.parsers.rst.states import Inliner

import sphinx
from sphinx.application import Sphinx
from sphinx.util.nodes import split_explicit_title
from sphinx.util.typing import RoleFunction


def make_link_role(base_url: str, prefix: str) -> RoleFunction:
    def role(typ: str, rawtext: str, text: str, lineno: int,
             inliner: Inliner, options: Dict = {}, content: List[str] = []
             ) -> Tuple[List[Node], List[system_message]]:
        text = utils.unescape(text)
        has_explicit_title, title, part = split_explicit_title(text)
        try:
            full_url = base_url % part
        except (TypeError, ValueError):
            inliner.reporter.warning(
                'unable to expand %s extlink with base URL %r, please make '
                'sure the base contains \'%%s\' exactly once'
                % (typ, base_url), line=lineno)
            full_url = base_url + part
        if not has_explicit_title:
            if prefix is None:
                title = full_url
            else:
                title = prefix + part
        pnode = nodes.reference(title, title, internal=False, refuri=full_url)
        return [pnode], []
    return role


def setup_link_roles(app: Sphinx) -> None:
    for name, (base_url, prefix) in app.config.extlinks.items():
        app.add_role(name, make_link_role(base_url, prefix))


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_config_value('extlinks', {}, 'env')
    app.connect('builder-inited', setup_link_roles)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
