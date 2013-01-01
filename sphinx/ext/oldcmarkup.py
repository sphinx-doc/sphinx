# -*- coding: utf-8 -*-
"""
    sphinx.ext.oldcmarkup
    ~~~~~~~~~~~~~~~~~~~~~

    Extension for compatibility with old C markup (directives and roles).

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils.parsers.rst import directives

from sphinx.util.compat import Directive

_warned_oldcmarkup = False
WARNING_MSG = 'using old C markup; please migrate to new-style markup ' \
              '(e.g. c:function instead of cfunction), see ' \
              'http://sphinx-doc.org/domains.html'


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
        if not env.app._oldcmarkup_warned:
            self.state_machine.reporter.warning(WARNING_MSG, line=self.lineno)
            env.app._oldcmarkup_warned = True
        newname = 'c:' + self.name[1:]
        newdir = env.lookup_domain_element('directive', newname)[0]
        return newdir(newname, self.arguments, self.options,
                      self.content, self.lineno, self.content_offset,
                      self.block_text, self.state, self.state_machine).run()


def old_crole(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    env = inliner.document.settings.env
    if not typ:
        typ = env.config.default_role
    if not env.app._oldcmarkup_warned:
        inliner.reporter.warning(WARNING_MSG, line=lineno)
        env.app._oldcmarkup_warned = True
    newtyp = 'c:' + typ[1:]
    newrole = env.lookup_domain_element('role', newtyp)[0]
    return newrole(newtyp, rawtext, text, lineno, inliner, options, content)


def setup(app):
    app._oldcmarkup_warned = False
    app.add_directive('cfunction', OldCDirective)
    app.add_directive('cmember', OldCDirective)
    app.add_directive('cmacro', OldCDirective)
    app.add_directive('ctype', OldCDirective)
    app.add_directive('cvar', OldCDirective)
    app.add_role('cdata', old_crole)
    app.add_role('cfunc', old_crole)
    app.add_role('cmacro', old_crole)
    app.add_role('ctype', old_crole)
    app.add_role('cmember', old_crole)
