# -*- coding: utf-8 -*-
"""
    sphinx.domains
    ~~~~~~~~~~~~~~

    Support for domains, which are groupings of description directives
    and roles describing e.g. constructs of one programming language.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""


class ObjType(object):
    """
    XXX add docstring
    """

    known_attrs = {
        'search': True,
    }

    def __init__(self, lname, *roles, **attrs):
        self.lname = lname
        self.roles = roles
        self.attrs = self.known_attrs.copy()
        self.attrs.update(attrs)


class Domain(object):
    """
    A Domain is meant to be a group of "object" description directives for
    objects of a similar nature, and corresponding roles to create references to
    them.  Examples would be Python modules, classes, functions etc., elements
    of a templating language, Sphinx roles and directives, etc.

    Each domain has a separate storage for information about existing objects
    and how to reference them in `data`, which must be a dictionary.  It also
    must implement several functions that expose the object information in a
    uniform way to parts of Sphinx that allow the user to reference or search
    for objects in a domain-agnostic way.

    About `self.data`: since all object and cross-referencing information is
    stored on a BuildEnvironment instance, the `domain.data` object is also
    stored in the `env.domaindata` dict under the key `domain.name`.  Before the
    build process starts, every active domain is instantiated and given the
    environment object; the `domaindata` dict must then either be nonexistent or
    a dictionary whose 'version' key is equal to the domain class'
    `data_version` attribute.  Otherwise, `IOError` is raised and the pickled
    environment is discarded.
    """

    #: domain name: should be short, but unique
    name = ''
    #: domain label: longer, more descriptive (used in messages)
    label = ''
    #: type (usually directive) name -> ObjType instance
    object_types = {}
    #: directive name -> directive class
    directives = {}
    #: role name -> role callable
    roles = {}

    #: data value for a fresh environment
    initial_data = {}
    #: data version
    data_version = 0

    def __init__(self, env):
        self.env = env
        if self.name not in env.domaindata:
            assert isinstance(self.initial_data, dict)
            new_data = self.initial_data.copy()
            new_data['version'] = self.data_version
            self.data = env.domaindata[self.name] = new_data
        else:
            self.data = env.domaindata[self.name]
            if self.data['version'] != self.data_version:
                raise IOError('data of %r domain out of date' % self.label)
        self._role_cache = {}
        self._directive_cache = {}
        self._role2type = {}
        for name, obj in self.object_types.iteritems():
            for rolename in obj.roles:
                self._role2type[rolename] = name
        self.object_type = self._role2type.get  # XXX necessary?

    def role(self, name):
        """
        Return a role adapter function that always gives the registered
        role its full name ('domain:name') as the first argument.
        """
        if name in self._role_cache:
            return self._role_cache[name]
        if name not in self.roles:
            return None
        fullname = '%s:%s' % (self.name, name)
        def role_adapter(typ, rawtext, text, lineno, inliner,
                         options={}, content=[]):
            return self.roles[name](fullname, rawtext, text, lineno,
                                    inliner, options, content)
        self._role_cache[name] = role_adapter
        return role_adapter

    def directive(self, name):
        """
        Return a directive adapter class that always gives the registered
        directive its full name ('domain:name') as ``self.name``.
        """
        if name in self._directive_cache:
            return self._directive_cache[name]
        if name not in self.directives:
            return None
        fullname = '%s:%s' % (self.name, name)
        # XXX what about function-style directives?
        BaseDirective = self.directives[name]
        class DirectiveAdapter(BaseDirective):
            def run(self):
                self.name = fullname
                return BaseDirective.run(self)
        self._directive_cache[name] = DirectiveAdapter
        return DirectiveAdapter

    # methods that should be overwritten

    def clear_doc(self, docname):
        """
        Remove traces of a document in the domain-specific inventories.
        """
        pass

    # XXX way for individual docs to override methods in an existing domain?

    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):
        """
        Resolve the ``pending_xref`` *node* with the given *typ* and *target*.

        This method should return a new node, to replace the xref node,
        containing the *contnode* which is the markup content of the
        cross-reference.

        If no resolution can be found, None can be returned; the xref node will
        then given to the 'missing-reference' event, and if that yields no
        resolution, replaced by *contnode*.

        The method can also raise `sphinx.environment.NoUri` to suppress the
        'missing-reference' event being emitted.
        """
        pass

    def get_objects(self):
        """
        Return an iterable of "object descriptions", which are tuples with
        five items:

        * `name`     -- fully qualified name
        * `type`     -- object type, a key in ``self.object_types``
        * `docname`  -- the document where it is to be found
        * `anchor`   -- the anchor name for the object
        * `priority` -- how "important" the object is; an integer
                        (XXX assign meanings)
        """
        return []


from sphinx.domains.c import CDomain
from sphinx.domains.std import StandardDomain
from sphinx.domains.python import PythonDomain

# this contains all registered domains
all_domains = {
    'std': StandardDomain,
    'py': PythonDomain,
    'c': CDomain,
}
