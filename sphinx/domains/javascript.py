# -*- coding: utf-8 -*-
"""
    sphinx.domains.javascript
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    The JavaScript domain.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import re

from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.locale import l_, _
from sphinx.directives import ObjectDescription
from sphinx.domains.python import py_paramlist_re as js_paramlist_re

js_sig_re = re.compile(r'(\w+)\s*\((.*)\)')

class JSFunction(ObjectDescription):
    """
    Description of a JavaScript function.
    """
    def handle_signature(self, sig, signode):
        match = js_sig_re.match(sig)
        if match is None:
            raise ValueError()
        name, arglist = match.groups()

        signode += addnodes.desc_name(name, name)
        if not arglist:
            signode += addnodes.desc_parameterlist()
            return name

        stack = [signode[-1]]
        for token in js_paramlist_re.split(arglist):
            if token == '[':
                opt = addnodes.desc_optional()
                stack[-1] += opt
                stack.append(opt)
            elif token == ']':
                try:
                    stack.pop()
                except IndexError:
                    raise ValueError()
            elif not token or token == ',' or token.isspace():
                pass
            else:
                token = token.strip()
                stack[-1] += addnodes.desc_parameter(token, token)
        if len(stack) != 1:
            raise ValueError()
        return name

class JavaScriptDomain(Domain):
    """JavaScript language domain."""
    name = "js"
    label= "JavaScript"
    object_types = {
        "function": ObjType(l_("js function"), "func"),
    }
    directives = {
        "function": JSFunction,
    }
