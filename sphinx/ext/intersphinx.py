# -*- coding: utf-8 -*-
"""
    sphinx.ext.intersphinx
    ~~~~~~~~~~~~~~~~~~~~~~

    Insert links to objects documented in remote Sphinx documentation.

    This works as follows:

    * Each Sphinx HTML build creates a file named "objects.inv" that contains a
      mapping from object names to URIs relative to the HTML set's root.

    * Projects using the Intersphinx extension can specify links to such mapping
      files in the `intersphinx_mapping` config value.  The mapping will then be
      used to resolve otherwise missing references to objects into links to the
      other documentation.

    * By default, the mapping file is assumed to be at the same location as the
      rest of the documentation; however, the location of the mapping file can
      also be specified individually, e.g. if the docs should be buildable
      without Internet access.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import time
import zlib
import codecs
import urllib2
import posixpath
from os import path
import re

from docutils import nodes
from docutils.utils import relative_path

from sphinx.locale import _
from sphinx.builders.html import INVENTORY_FILENAME
from sphinx.util.pycompat import b


handlers = [urllib2.ProxyHandler(), urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler()]
try:
    handlers.append(urllib2.HTTPSHandler)
except AttributeError:
    pass

urllib2.install_opener(urllib2.build_opener(*handlers))

UTF8StreamReader = codecs.lookup('utf-8')[2]


def read_inventory_v1(f, uri, join):
    f = UTF8StreamReader(f)
    invdata = {}
    line = f.next()
    projname = line.rstrip()[11:]
    line = f.next()
    version = line.rstrip()[11:]
    for line in f:
        name, type, location = line.rstrip().split(None, 2)
        location = join(uri, location)
        # version 1 did not add anchors to the location
        if type == 'mod':
            type = 'py:module'
            location += '#module-' + name
        else:
            type = 'py:' + type
            location += '#' + name
        invdata.setdefault(type, {})[name] = (projname, version, location, '-')
    return invdata


def read_inventory_v2(f, uri, join, bufsize=16*1024):
    invdata = {}
    line = f.readline()
    projname = line.rstrip()[11:].decode('utf-8')
    line = f.readline()
    version = line.rstrip()[11:].decode('utf-8')
    line = f.readline().decode('utf-8')
    if 'zlib' not in line:
        raise ValueError

    def read_chunks():
        decompressor = zlib.decompressobj()
        for chunk in iter(lambda: f.read(bufsize), b('')):
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def split_lines(iter):
        buf = b('')
        for chunk in iter:
            buf += chunk
            lineend = buf.find(b('\n'))
            while lineend != -1:
                yield buf[:lineend].decode('utf-8')
                buf = buf[lineend+1:]
                lineend = buf.find(b('\n'))
        assert not buf

    for line in split_lines(read_chunks()):
        # be careful to handle names with embedded spaces correctly
        m = re.match(r'(?x)(.+?)\s+(\S*:\S*)\s+(\S+)\s+(\S+)\s+(.*)',
                     line.rstrip())
        if not m:
            continue
        name, type, prio, location, dispname = m.groups()
        if type == 'py:module' and type in invdata and \
            name in invdata[type]:  # due to a bug in 1.1 and below,
                                    # two inventory entries are created
                                    # for Python modules, and the first
                                    # one is correct
            continue
        if location.endswith(u'$'):
            location = location[:-1] + name
        location = join(uri, location)
        invdata.setdefault(type, {})[name] = (projname, version,
                                              location, dispname)
    return invdata


def fetch_inventory(app, uri, inv):
    """Fetch, parse and return an intersphinx inventory file."""
    # both *uri* (base URI of the links to generate) and *inv* (actual
    # location of the inventory file) can be local or remote URIs
    localuri = uri.find('://') == -1
    join = localuri and path.join or posixpath.join
    try:
        if inv.find('://') != -1:
            f = urllib2.urlopen(inv)
        else:
            f = open(path.join(app.srcdir, inv), 'rb')
    except Exception, err:
        app.warn('intersphinx inventory %r not fetchable due to '
                 '%s: %s' % (inv, err.__class__, err))
        return
    try:
        line = f.readline().rstrip().decode('utf-8')
        try:
            if line == '# Sphinx inventory version 1':
                invdata = read_inventory_v1(f, uri, join)
            elif line == '# Sphinx inventory version 2':
                invdata = read_inventory_v2(f, uri, join)
            else:
                raise ValueError
            f.close()
        except ValueError:
            f.close()
            raise ValueError('unknown or unsupported inventory version')
    except Exception, err:
        app.warn('intersphinx inventory %r not readable due to '
                 '%s: %s' % (inv, err.__class__.__name__, err))
    else:
        return invdata


def load_mappings(app):
    """Load all intersphinx mappings into the environment."""
    now = int(time.time())
    cache_time = now - app.config.intersphinx_cache_limit * 86400
    env = app.builder.env
    if not hasattr(env, 'intersphinx_cache'):
        env.intersphinx_cache = {}
        env.intersphinx_inventory = {}
        env.intersphinx_named_inventory = {}
    cache = env.intersphinx_cache
    update = False
    for key, value in app.config.intersphinx_mapping.iteritems():
        if isinstance(value, tuple):
            # new format
            name, (uri, inv) = key, value
            if not name.isalnum():
                app.warn('intersphinx identifier %r is not alphanumeric' % name)
        else:
            # old format, no name
            name, uri, inv = None, key, value
        # we can safely assume that the uri<->inv mapping is not changed
        # during partial rebuilds since a changed intersphinx_mapping
        # setting will cause a full environment reread
        if not inv:
            inv = posixpath.join(uri, INVENTORY_FILENAME)
        # decide whether the inventory must be read: always read local
        # files; remote ones only if the cache time is expired
        if '://' not in inv or uri not in cache \
               or cache[uri][1] < cache_time:
            app.info('loading intersphinx inventory from %s...' % inv)
            invdata = fetch_inventory(app, uri, inv)
            if invdata:
                cache[uri] = (name, now, invdata)
            else:
                cache.pop(uri, None)
            update = True
    if update:
        env.intersphinx_inventory = {}
        env.intersphinx_named_inventory = {}
        # Duplicate values in different inventories will shadow each
        # other; which one will override which can vary between builds
        # since they are specified using an unordered dict.  To make
        # it more consistent, we sort the named inventories and then
        # add the unnamed inventories last.  This means that the
        # unnamed inventories will shadow the named ones but the named
        # ones can still be accessed when the name is specified.
        cached_vals = list(cache.itervalues())
        named_vals = sorted(v for v in cached_vals if v[0])
        unnamed_vals = [v for v in cached_vals if not v[0]]
        for name, _, invdata in named_vals + unnamed_vals:
            if name:
                env.intersphinx_named_inventory[name] = invdata
            for type, objects in invdata.iteritems():
                env.intersphinx_inventory.setdefault(
                    type, {}).update(objects)


def missing_reference(app, env, node, contnode):
    """Attempt to resolve a missing reference via intersphinx references."""
    domain = node.get('refdomain')
    if not domain:
        # only objects in domains are in the inventory
        return
    target = node['reftarget']
    objtypes = env.domains[domain].objtypes_for_role(node['reftype'])
    if not objtypes:
        return
    objtypes = ['%s:%s' % (domain, objtype) for objtype in objtypes]
    to_try = [(env.intersphinx_inventory, target)]
    in_set = None
    if ':' in target:
        # first part may be the foreign doc set name
        setname, newtarget = target.split(':', 1)
        if setname in env.intersphinx_named_inventory:
            in_set = setname
            to_try.append((env.intersphinx_named_inventory[setname], newtarget))
    for inventory, target in to_try:
        for objtype in objtypes:
            if objtype not in inventory or target not in inventory[objtype]:
                continue
            proj, version, uri, dispname = inventory[objtype][target]
            if '://' not in uri and node.get('refdoc'):
                # get correct path in case of subdirectories
                uri = path.join(relative_path(node['refdoc'], env.srcdir), uri)
            newnode = nodes.reference('', '', internal=False, refuri=uri,
                          reftitle=_('(in %s v%s)') % (proj, version))
            if node.get('refexplicit'):
                # use whatever title was given
                newnode.append(contnode)
            elif dispname == '-' or \
                    (domain == 'std' and node['reftype'] == 'keyword'):
                # use whatever title was given, but strip prefix
                title = contnode.astext()
                if in_set and title.startswith(in_set+':'):
                    newnode.append(contnode.__class__(title[len(in_set)+1:],
                                                      title[len(in_set)+1:]))
                else:
                    newnode.append(contnode)
            else:
                # else use the given display name (used for :ref:)
                newnode.append(contnode.__class__(dispname, dispname))
            return newnode
    # at least get rid of the ':' in the target if no explicit title given
    if in_set is not None and not node.get('refexplicit', True):
        if len(contnode) and isinstance(contnode[0], nodes.Text):
            contnode[0] = nodes.Text(newtarget, contnode[0].rawsource)


def setup(app):
    app.add_config_value('intersphinx_mapping', {}, True)
    app.add_config_value('intersphinx_cache_limit', 5, False)
    app.connect('missing-reference', missing_reference)
    app.connect('builder-inited', load_mappings)
