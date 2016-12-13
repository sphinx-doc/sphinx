# -*- coding: utf-8 -*-
"""
    sphinx.util.compat
    ~~~~~~~~~~~~~~~~~~

    Stuff for docutils compatibility.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import absolute_import

import sys
import warnings

from docutils import nodes
from docutils.parsers.rst import Directive  # noqa

from docutils.parsers.rst import Directive  # noqa
from docutils import __version__ as _du_version

from sphinx.deprecation import RemovedInSphinx17Warning

docutils_version = tuple(int(x) for x in _du_version.split('.')[:2])


def make_admonition(node_class, name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    warnings.warn('make_admonition is deprecated, use '
                  'docutils.parsers.rst.directives.admonitions.BaseAdmonition '
                  'instead', DeprecationWarning, stacklevel=2)
    text = '\n'.join(content)
    admonition_node = node_class(text)
    if arguments:
        title_text = arguments[0]
        textnodes, messages = state.inline_text(title_text, lineno)
        admonition_node += nodes.title(title_text, '', *textnodes)
        admonition_node += messages
        if 'class' in options:
            classes = options['class']
        else:
            classes = ['admonition-' + nodes.make_id(title_text)]
        admonition_node['classes'] += classes
    state.nested_parse(content, content_offset, admonition_node)
    return [admonition_node]


class _DeprecationWrapper(object):
    def __init__(self, mod, deprecated):
        # type: (Any, Dict) -> None
        self._mod = mod
        self._deprecated = deprecated

    def __getattr__(self, attr):
        if attr in self._deprecated:
            warnings.warn("sphinx.util.compat.%s is deprecated and will be "
                          "removed in Sphinx 1.7, please use the standard "
                          "library version instead." % attr,
                          RemovedInSphinx17Warning, stacklevel=2)
            return self._deprecated[attr]
        return getattr(self._mod, attr)


sys.modules[__name__] = _DeprecationWrapper(sys.modules[__name__], dict(  # type: ignore
    docutils_version = docutils_version,
    Directive = Directive,
))
