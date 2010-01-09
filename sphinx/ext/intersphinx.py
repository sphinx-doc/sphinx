# -*- coding: utf-8 -*-
"""
    sphinx.ext.intersphinx
    ~~~~~~~~~~~~~~~~~~~~~~

    Insert links to Python objects documented in remote Sphinx documentation.

    This works as follows:

    * Each Sphinx HTML build creates a file named "objects.inv" that contains
      a mapping from Python identifiers to URIs relative to the HTML set's root.

    * Projects using the Intersphinx extension can specify links to such mapping
      files in the `intersphinx_mapping` config value.  The mapping will then be
      used to resolve otherwise missing references to Python objects into links
      to the other documentation.

    * By default, the mapping file is assumed to be at the same location as the
      rest of the documentation; however, the location of the mapping file can
      also be specified individually, e.g. if the docs should be buildable
      without Internet access.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import time
import urllib2
import posixpath
from os import path

from docutils import nodes

from sphinx.builders.html import INVENTORY_FILENAME

handlers = [urllib2.ProxyHandler(), urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler()]
if hasattr(urllib2, 'HTTPSHandler'):
    handlers.append(urllib2.HTTPSHandler)

urllib2.install_opener(urllib2.build_opener(*handlers))


def fetch_inventory(app, uri, inv):
    """Fetch, parse and return an intersphinx inventory file."""
    invdata = {}
    # both *uri* (base URI of the links to generate) and *inv* (actual
    # location of the inventory file) can be local or remote URIs
    localuri = uri.find('://') == -1
    try:
        if inv.find('://') != -1:
            f = urllib2.urlopen(inv)
        else:
            f = open(path.join(app.srcdir, inv))
    except Exception, err:
        app.warn('intersphinx inventory %r not fetchable due to '
                 '%s: %s' % (inv, err.__class__, err))
        return
    try:
        line = f.next()
        if line.rstrip() != '# Sphinx inventory version 1':
            raise ValueError('unknown or unsupported inventory version')
        line = f.next()
        projname = line.rstrip()[11:].decode('utf-8')
        line = f.next()
        version = line.rstrip()[11:]
        for line in f:
            name, type, location = line.rstrip().split(None, 2)
            if localuri:
                location = path.join(uri, location)
            else:
                location = posixpath.join(uri, location)
            invdata[name] = (type, projname, version, location)
        f.close()
    except Exception, err:
        app.warn('intersphinx inventory %r not readable due to '
                 '%s: %s' % (inv, err.__class__, err))
    else:
        return invdata


def load_mappings(app):
    """Load all intersphinx mappings into the environment."""
    now = int(time.time())
    cache_time = now - app.config.intersphinx_cache_limit * 86400
    env = app.builder.env
    if not hasattr(env, 'intersphinx_cache'):
        env.intersphinx_cache = {}
    cache = env.intersphinx_cache
    update = False
    for uri, inv in app.config.intersphinx_mapping.iteritems():
        # we can safely assume that the uri<->inv mapping is not changed
        # during partial rebuilds since a changed intersphinx_mapping
        # setting will cause a full environment reread
        if not inv:
            inv = posixpath.join(uri, INVENTORY_FILENAME)
        # decide whether the inventory must be read: always read local
        # files; remote ones only if the cache time is expired
        if '://' not in inv or uri not in cache \
               or cache[uri][0] < cache_time:
            invdata = fetch_inventory(app, uri, inv)
            cache[uri] = (now, invdata)
            update = True
    if update:
        env.intersphinx_inventory = {}
        for _, invdata in cache.itervalues():
            if invdata:
                env.intersphinx_inventory.update(invdata)


def missing_reference(app, env, node, contnode):
    """Attempt to resolve a missing reference via intersphinx references."""
    type = node['reftype']
    target = node['reftarget']
    if type == 'mod':
        type, proj, version, uri = env.intersphinx_inventory.get(target,
                                                                 ('','','',''))
        if type != 'mod':
            return None
        target = 'module-' + target   # for link anchor
    else:
        if target[-2:] == '()':
            target = target[:-2]
        target = target.rstrip(' *')
        # special case: exceptions and object methods
        if type == 'exc' and '.' not in target and \
           'exceptions.' + target in env.intersphinx_inventory:
            target = 'exceptions.' + target
        elif type in ('func', 'meth') and '.' not in target and \
           'object.' + target in env.intersphinx_inventory:
            target = 'object.' + target
        if target not in env.intersphinx_inventory:
            return None
        type, proj, version, uri = env.intersphinx_inventory[target]
    # print "Intersphinx hit:", target, uri
    newnode = nodes.reference('', '')
    newnode['refuri'] = uri + '#' + target
    newnode['reftitle'] = '(in %s v%s)' % (proj, version)
    newnode['class'] = 'external-xref'
    newnode.append(contnode)
    return newnode


def setup(app):
    app.add_config_value('intersphinx_mapping', {}, True)
    app.add_config_value('intersphinx_cache_limit', 5, False)
    app.connect('missing-reference', missing_reference)
    app.connect('builder-inited', load_mappings)
