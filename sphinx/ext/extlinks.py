# -*- coding: utf-8 -*-
"""
    sphinx.ext.extlinks
    ~~~~~~~~~~~~~~~~~~~

    Extension to save typing and prevent hard-coding of base URLs in the reST
    files.

    This adds a new config value called ``extlinks`` that is created like this::

       extlinks = {'exmpl': ('http://example.com/', prefix), ...}

    Now you can use e.g. :exmpl:`foo` in your documents.  This will create a
    link to ``http://example.com/foo``.  The link caption depends on the
    *prefix* value given:

    - If it is ``None``, the caption will be the full URL.
    - If it is a string (empty or not), the caption will be the prefix prepended
      to the role content.

    You can also give an explicit caption, e.g. :exmpl:`Foo <foo>`.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes, utils

from sphinx.util import split_explicit_title


def make_link_role(base_url, prefix):
    def role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
        text = utils.unescape(text)
        has_explicit_title, title, url = split_explicit_title(text)
        # NOTE: not using urlparse.urljoin() here, to allow something like
        # base_url = 'bugs.python.org/issue'  and  url = '1024'
        full_url = base_url + url
        if not has_explicit_title:
            if prefix is None:
                title = full_url
            else:
                title = prefix + url
        pnode = nodes.reference(title, title, refuri=full_url)
        return [pnode], []
    return role

def setup_link_roles(app):
    for name, (base_url, prefix) in app.config.extlinks.iteritems():
        app.add_role(name, make_link_role(base_url, prefix))

def setup(app):
    app.add_config_value('extlinks', {}, 'env')
    app.connect('builder-inited', setup_link_roles)
