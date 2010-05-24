# -*- coding: utf-8 -*-
"""
    sphinx.ext.oldcmarkup
    ~~~~~~~~~~~~~~~~~~~~~

    Extension for compatibility with old C markup (directives and roles).

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils.parsers.rst import directives

from sphinx.util.compat import Directive


class OldCDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'noindex': directives.flag,
        'module': directives.unchanged,
    }

    def run(self):
        env = self.state.document.settings.env
        newname = 'c:' + self.name[1:]
        newdir = env.lookup_domain_element('directive', newname)[0]
        return newdir(newname, self.arguments, self.options,
                      self.content, self.lineno, self.content_offset,
                      self.block_text, self.state, self.state_machine).run()


def old_crole(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    env = inliner.document.settings.env
    newtyp = 'c:' + typ[1:]
    newrole = env.lookup_domain_element('role', newtyp)[0]
    return newrole(newtyp, rawtext, text, lineno, inliner, options, content)


def setup(app):
    app.add_directive('cfunction', OldCDirective)
    app.add_directive('cmember', OldCDirective)
    app.add_directive('cmacro', OldCDirective)
    app.add_directive('ctype', OldCDirective)
    app.add_directive('cvar', OldCDirective)
    app.add_role('cdata', old_crole)
    app.add_role('cfunc', old_crole)
    app.add_role('cmacro', old_crole)
    app.add_role('ctype', old_crole)
