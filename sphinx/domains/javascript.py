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
from sphinx.roles import XRefRole

js_sig_re = re.compile(
    r'''([^ .]+\.)? # object name
        ([^ .]+\s*) # name
        \((.*)\)$ # arguments
''', re.VERBOSE)

class JSObject(ObjectDescription):
    """
    Description of a JavaScript object.
    """
    has_arguments = False

    def handle_signature(self, sig, signode):
        match = js_sig_re.match(sig)
        if match is None:
            raise ValueError()
        nameprefix, name, arglist = match.groups()

        objectname = self.env.temp_data.get('js:object')
        if objectname and nameprefix:
            # someone documenting the method of an attribute of the current
            # object? shouldn't happen but who knows...
            fullname = objectname + '.' + nameprefix + name
        elif objectname:
            fullname = objectname + '.' + name
        elif nameprefix:
            fullname = nameprefix + '.' + name
        else:
            # just a function or constructor
            objectname = ''
            fullname = ''

        signode['object'] = objectname
        signode['fullname'] = fullname

        signode += addnodes.desc_name(name, name)
        if self.has_arguments:
            signode += addnodes.desc_parameterlist()
        if not arglist:
            return fullname, nameprefix

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
        return fullname, nameprefix

class JSCallable(JSObject):
    """Description of a JavaScript function, method or constructor."""
    has_arguments = True

class JavaScriptDomain(Domain):
    """JavaScript language domain."""
    name = 'js'
    label= 'JavaScript'
    object_types = {
        'function'  : ObjType(l_('js function'), 'func'),
        'data'      : ObjType(l_('js data'), 'data'),
        'attribute' : ObjType(l_('js attribute'), 'attr'),
    }
    directives = {
        'function'  : JSCallable,
        'data'      : JSObject,
        'attribute' : JSObject,
    }
    roles = {
        'func': XRefRole(fix_parens=True),
        'data': XRefRole(),
        'attr': XRefRole()
    }
