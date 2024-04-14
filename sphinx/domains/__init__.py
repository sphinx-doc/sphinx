"""Support for domains.

Domains are groupings of description directives
and roles describing e.g. constructs of one programming language.
"""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional, cast

from docutils.nodes import Element, Node, system_message

from sphinx.errors import SphinxError
from sphinx.locale import _

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from typing import ClassVar

    from docutils import nodes
    from docutils.parsers.rst import Directive
    from docutils.parsers.rst.states import Inliner

    from sphinx.addnodes import pending_xref
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
    from sphinx.roles import XRefRole
    from sphinx.util.typing import RoleFunction


class ObjType:
    """
    An ObjType is the description for a type of object that a domain can
    document.  In the object_types attribute of Domain subclasses, object type
    names are mapped to instances of this class.

    Constructor arguments:

    - *lname*: localized name of the type (do not include domain name)
    - *roles*: all the roles that can refer to an object of this type
    - *attrs*: object attributes -- currently only "searchprio" is known,
      which defines the object's priority in the full-text search index,
      see :meth:`Domain.get_objects()`.
    """

    known_attrs = {
        'searchprio': 1,
    }

    def __init__(self, lname: str, *roles: Any, **attrs: Any) -> None:
        self.lname = lname
        self.roles: tuple = roles
        self.attrs: dict = self.known_attrs.copy()
        self.attrs.update(attrs)


class IndexEntry(NamedTuple):
    name: str
    subtype: int
    docname: str
    anchor: str
    extra: str
    qualifier: str
    descr: str


class Index(ABC):
    """
    An Index is the description for a domain-specific index.  To add an index to
    a domain, subclass Index, overriding the three name attributes:

    * `name` is an identifier used for generating file names.
      It is also used for a hyperlink target for the index. Therefore, users can
      refer the index page using ``ref`` role and a string which is combined
      domain name and ``name`` attribute (ex. ``:ref:`py-modindex```).
    * `localname` is the section title for the index.
    * `shortname` is a short name for the index, for use in the relation bar in
      HTML output.  Can be empty to disable entries in the relation bar.

    and providing a :meth:`generate()` method.  Then, add the index class to
    your domain's `indices` list.  Extensions can add indices to existing
    domains using :meth:`~sphinx.application.Sphinx.add_index_to_domain()`.

    .. versionchanged:: 3.0

       Index pages can be referred by domain name and index name via
       :rst:role:`ref` role.
    """

    name: str
    localname: str
    shortname: str | None = None

    def __init__(self, domain: Domain) -> None:
        if not self.name or self.localname is None:
            raise SphinxError('Index subclass %s has no valid name or localname'
                              % self.__class__.__name__)
        self.domain = domain

    @abstractmethod
    def generate(self, docnames: Iterable[str] | None = None,
                 ) -> tuple[list[tuple[str, list[IndexEntry]]], bool]:
        """Get entries for the index.

        If ``docnames`` is given, restrict to entries referring to these
        docnames.

        The return value is a tuple of ``(content, collapse)``:

        ``collapse``
          A boolean that determines if sub-entries should start collapsed (for
          output formats that support collapsing sub-entries).

        ``content``:
          A sequence of ``(letter, entries)`` tuples, where ``letter`` is the
          "heading" for the given ``entries``, usually the starting letter, and
          ``entries`` is a sequence of single entries. Each entry is a sequence
          ``[name, subtype, docname, anchor, extra, qualifier, descr]``. The
          items in this sequence have the following meaning:

          ``name``
            The name of the index entry to be displayed.

          ``subtype``
            The sub-entry related type. One of:

            ``0``
              A normal entry.
            ``1``
              An entry with sub-entries.
            ``2``
              A sub-entry.

          ``docname``
            *docname* where the entry is located.

          ``anchor``
            Anchor for the entry within ``docname``

          ``extra``
            Extra info for the entry.

          ``qualifier``
            Qualifier for the description.

          ``descr``
            Description for the entry.

        Qualifier and description are not rendered for some output formats such
        as LaTeX.
        """
        raise NotImplementedError


TitleGetter = Callable[[Node], Optional[str]]


class Domain:
    """
    A Domain is meant to be a group of "object" description directives for
    objects of a similar nature, and corresponding roles to create references to
    them.  Examples would be Python modules, classes, functions etc., elements
    of a templating language, Sphinx roles and directives, etc.

    Each domain has a separate storage for information about existing objects
    and how to reference them in `self.data`, which must be a dictionary.  It
    also must implement several functions that expose the object information in
    a uniform way to parts of Sphinx that allow the user to reference or search
    for objects in a domain-agnostic way.

    About `self.data`: since all object and cross-referencing information is
    stored on a BuildEnvironment instance, the `domain.data` object is also
    stored in the `env.domaindata` dict under the key `domain.name`.  Before the
    build process starts, every active domain is instantiated and given the
    environment object; the `domaindata` dict must then either be nonexistent or
    a dictionary whose 'version' key is equal to the domain class'
    :attr:`data_version` attribute.  Otherwise, `OSError` is raised and the
    pickled environment is discarded.
    """

    #: domain name: should be short, but unique
    name = ''
    #: domain label: longer, more descriptive (used in messages)
    label = ''
    #: type (usually directive) name -> ObjType instance
    object_types: dict[str, ObjType] = {}
    #: directive name -> directive class
    directives: dict[str, type[Directive]] = {}
    #: role name -> role callable
    roles: dict[str, RoleFunction | XRefRole] = {}
    #: a list of Index subclasses
    indices: list[type[Index]] = []
    #: role name -> a warning message if reference is missing
    dangling_warnings: dict[str, str] = {}
    #: node_class -> (enum_node_type, title_getter)
    enumerable_nodes: dict[type[Node], tuple[str, TitleGetter | None]] = {}
    #: data value for a fresh environment
    initial_data: dict = {}
    #: data value
    data: dict
    #: data version, bump this when the format of `self.data` changes
    data_version = 0
    #: Value for an empty inventory of objects for this domain.
    #: It must be copy.deepcopy-able.
    #: If this value is overridden, then the various intersphinx methods in the domain should
    #: probably also be overridden.
    #: Intersphinx is not inspecting this dictionary, so the domain has complete freedom in
    #: the key and value type.
    initial_intersphinx_inventory: ClassVar[dict] = {}

    def __init__(self, env: BuildEnvironment) -> None:
        self.env: BuildEnvironment = env
        self._role_cache: dict[str, Callable] = {}
        self._directive_cache: dict[str, Callable] = {}
        self._role2type: dict[str, list[str]] = {}
        self._type2role: dict[str, str] = {}

        # convert class variables to instance one (to enhance through API)
        self.object_types = dict(self.object_types)
        self.directives = dict(self.directives)
        self.roles = dict(self.roles)
        self.indices = list(self.indices)

        if self.name not in env.domaindata:
            assert isinstance(self.initial_data, dict)
            new_data = copy.deepcopy(self.initial_data)
            new_data['version'] = self.data_version
            self.data = env.domaindata[self.name] = new_data
        else:
            self.data = env.domaindata[self.name]
            if self.data['version'] != self.data_version:
                raise OSError('data of %r domain out of date' % self.label)
        for name, obj in self.object_types.items():
            for rolename in obj.roles:
                self._role2type.setdefault(rolename, []).append(name)
            self._type2role[name] = obj.roles[0] if obj.roles else ''
        self.objtypes_for_role = self._role2type.get
        self.role_for_objtype = self._type2role.get

    def setup(self) -> None:
        """Set up domain object."""
        from sphinx.domains.std import StandardDomain

        # Add special hyperlink target for index pages (ex. py-modindex)
        std = cast(StandardDomain, self.env.get_domain('std'))
        for index in self.indices:
            if index.name and index.localname:
                docname = f"{self.name}-{index.name}"
                std.note_hyperlink_target(docname, docname, '', index.localname)

    def add_object_type(self, name: str, objtype: ObjType) -> None:
        """Add an object type."""
        self.object_types[name] = objtype
        if objtype.roles:
            self._type2role[name] = objtype.roles[0]
        else:
            self._type2role[name] = ''

        for role in objtype.roles:
            self._role2type.setdefault(role, []).append(name)

    def role(self, name: str) -> RoleFunction | None:
        """Return a role adapter function that always gives the registered
        role its full name ('domain:name') as the first argument.
        """
        if name in self._role_cache:
            return self._role_cache[name]
        if name not in self.roles:
            return None
        fullname = f'{self.name}:{name}'

        def role_adapter(typ: str, rawtext: str, text: str, lineno: int,
                         inliner: Inliner, options: dict | None = None,
                         content: Sequence[str] = (),
                         ) -> tuple[list[Node], list[system_message]]:
            return self.roles[name](fullname, rawtext, text, lineno,
                                    inliner, options or {}, content)
        self._role_cache[name] = role_adapter
        return role_adapter

    def directive(self, name: str) -> Callable | None:
        """Return a directive adapter class that always gives the registered
        directive its full name ('domain:name') as ``self.name``.
        """
        if name in self._directive_cache:
            return self._directive_cache[name]
        if name not in self.directives:
            return None
        fullname = f'{self.name}:{name}'
        BaseDirective = self.directives[name]

        class DirectiveAdapter(BaseDirective):  # type: ignore[valid-type,misc]
            def run(self) -> list[Node]:
                self.name = fullname
                return super().run()
        self._directive_cache[name] = DirectiveAdapter
        return DirectiveAdapter

    # methods that should be overwritten

    def clear_doc(self, docname: str) -> None:
        """Remove traces of a document in the domain-specific inventories."""
        pass

    def merge_domaindata(self, docnames: list[str], otherdata: dict[str, Any]) -> None:
        """Merge in data regarding *docnames* from a different domaindata
        inventory (coming from a subprocess in parallel builds).
        """
        raise NotImplementedError('merge_domaindata must be implemented in %s '
                                  'to be able to do parallel builds!' %
                                  self.__class__)

    def process_doc(self, env: BuildEnvironment, docname: str,
                    document: nodes.document) -> None:
        """Process a document after it is read by the environment."""
        pass

    def check_consistency(self) -> None:
        """Do consistency checks (**experimental**)."""
        pass

    def process_field_xref(self, pnode: pending_xref) -> None:
        """Process a pending xref created in a doc field.
        For example, attach information about the current scope.
        """
        pass

    def resolve_xref(self, env: BuildEnvironment, fromdocname: str, builder: Builder,
                     typ: str, target: str, node: pending_xref, contnode: Element,
                     ) -> Element | None:
        """Resolve the pending_xref *node* with the given *typ* and *target*.

        This method should return a new node, to replace the xref node,
        containing the *contnode* which is the markup content of the
        cross-reference.

        If no resolution can be found, None can be returned; the xref node will
        then given to the :event:`missing-reference` event, and if that yields no
        resolution, replaced by *contnode*.

        The method can also raise :exc:`sphinx.environment.NoUri` to suppress
        the :event:`missing-reference` event being emitted.
        """
        pass

    def resolve_any_xref(self, env: BuildEnvironment, fromdocname: str, builder: Builder,
                         target: str, node: pending_xref, contnode: Element,
                         ) -> list[tuple[str, Element]]:
        """Resolve the pending_xref *node* with the given *target*.

        The reference comes from an "any" or similar role, which means that we
        don't know the type.  Otherwise, the arguments are the same as for
        :meth:`resolve_xref`.

        The method must return a list (potentially empty) of tuples
        ``('domain:role', newnode)``, where ``'domain:role'`` is the name of a
        role that could have created the same reference, e.g. ``'py:func'``.
        ``newnode`` is what :meth:`resolve_xref` would return.

        .. versionadded:: 1.3
        """
        raise NotImplementedError

    def get_objects(self) -> Iterable[tuple[str, str, str, str, str, int]]:
        """Return an iterable of "object descriptions".

        Object descriptions are tuples with six items:

        ``name``
          Fully qualified name.

        ``dispname``
          Name to display when searching/linking.

        ``type``
          Object type, a key in ``self.object_types``.

        ``docname``
          The document where it is to be found.

        ``anchor``
          The anchor name for the object.

        ``priority``
          How "important" the object is (determines placement in search
          results). One of:

          ``1``
            Default priority (placed before full-text matches).
          ``0``
            Object is important (placed before default-priority objects).
          ``2``
            Object is unimportant (placed after full-text matches).
          ``-1``
            Object should not show up in search at all.
        """
        return []

    def get_type_name(self, type: ObjType, primary: bool = False) -> str:
        """Return full name for given ObjType."""
        if primary:
            return type.lname
        return _('%s %s') % (self.label, type.lname)

    def get_enumerable_node_type(self, node: Node) -> str | None:
        """Get type of enumerable nodes (experimental)."""
        enum_node_type, _ = self.enumerable_nodes.get(node.__class__, (None, None))
        return enum_node_type

    def get_full_qualified_name(self, node: Element) -> str | None:
        """Return full qualified name for given node."""
        pass

    def intersphinx_add_entries_v2(self, store: Any,
                                   data: dict[str, dict[str, Any]]) -> None:
        """Store the given *data* for later intersphinx reference resolution.

        This method is called at most once with all data loaded from inventories in
        v1 and v2 format.

        The *data* is a dictionary indexed by **object type**, i.e, a key from
        :attr:`object_types`. The value is a dictionary indexed by **object name**,
        i.e., the **name** part of each tuple returned by :meth:`get_objects`.
        The value of those inner dictionaries are objects with intersphinx data,
        that should not be inspected by the domain, but merely returned as a result
        of reference resolution.

        For example, for Python the data could look like the following.

        .. code-block:: python

            data = {
                'class': {'pkg.mod.Foo': SomeIntersphinxData(...)},
                'method': {'pkg.mod.Foo.bar': SomeIntersphinxData(...)},
            }

        The domain must store the given inner intersphinx data in the given *store*,
        in whichever way makes sense for later reference resolution.
        This *store* was initially a copy of :attr:`initial_intersphinx_inventory`.

        Later in :meth:`intersphinx_resolve_xref` during intersphinx reference resolution,
        the domain is again given the *store* object to perform the resolution.

        .. versionadded:: 8.0
        """
        store = cast(dict[str, dict[str, Any]], store)
        assert len(store) == 0  # the method is called at most once
        store.update(data)  # update so the object is changed in-place

    def _intersphinx_adjust_object_types(self, env: BuildEnvironment,
                                         store: Any,
                                         typ: str, target: str,
                                         disabled_object_types: list[str],
                                         node: pending_xref, contnode: Element,
                                         objtypes: list[str]) -> None:
        """For implementing backwards compatibility.

        This method is an internal implementation detail used in the std and python domains,
        for implementing backwards compatibility.

        The given *objtypes* is the list of object types computed based on the *typ*,
        which will be used for lookup.
        By overriding this method this list can be manipulated, e.g., adding types
        that were removed in earlier Sphinx versions.
        After this method returns, the types in *disabled_object_types* are removed
        from *objtypes*. This final list is given to the lookup method.
        """
        # for std and py to overwrite for their backwards compatibility
        # we adjust the object types for backwards compatibility
        if self.name == 'std' and 'cmdoption' in objtypes:
            # until Sphinx-1.6, cmdoptions are stored as std:option
            objtypes.append('option')
        if self.name == 'py' and 'attribute' in objtypes:
            # Since Sphinx-2.1, properties are stored as py:method
            objtypes.append('method')

    def _intersphinx_resolve_xref_lookup(self, store: dict[str, dict[str, Any]],
                                         target: str, objtypes: list[str]
                                         ) -> Any | None:
        for objtype in objtypes:
            if objtype not in store:
                # Continue if there's nothing of this kind in the inventory
                continue

            if target in store[objtype]:
                # Case-sensitive match, use it
                return store[objtype][target]
            elif self.name == 'std' and objtype in ('label', 'term'):
                # Some types require case-insensitive matches:
                # * 'term': https://github.com/sphinx-doc/sphinx/issues/9291
                # * 'label': https://github.com/sphinx-doc/sphinx/issues/12008
                target_lower = target.lower()
                insensitive_matches = list(filter(lambda k: k.lower() == target_lower,
                                                  store[objtype].keys()))
                if insensitive_matches:
                    return store[objtype][insensitive_matches[0]]
                else:
                    # No case-insensitive match either, continue to the next candidate
                    continue
            else:
                # Could reach here if we're not a term but have a case insensitive match.
                # This is a fix for terms specifically, but potentially should apply to
                # other types.
                continue
        return None

    def intersphinx_resolve_xref(self, env: BuildEnvironment,
                                 store: Any,
                                 typ: str, target: str,
                                 disabled_object_types: list[str],
                                 node: pending_xref, contnode: Element
                                 ) -> Any | None:
        """Resolve the pending_xref *node* with the given *target* via intersphinx.

        This method should perform lookup of the pending cross-reference
        in the given *store*, but otherwise behave very similarly to :meth:`resolve_xref`.

        The *typ* may be ``any`` if the cross-references comes from an any-role.

        The *store* was created through a previous call to :meth:`intersphinx_add_entries_v2`.

        The *disabled_object_types* is a list of object types that the reference may not
        resolve to, per user request through :confval:`intersphinx_disabled_reftypes`.
        These disabled object types are just the names of the types, without a domain prefix.

        If a candidate is found in the store, the associated object must be returned.

        If no candidates can be found, *None* can be returned; and subsequent event
        handlers will be given a chance to resolve the reference.
        The method can also raise :exc:`sphinx.environment.NoUri` to suppress
        any subsequent resolution of this reference.

        .. versionadded:: 8.0
        """
        if typ == 'any':
            objtypes = list(self.object_types)
        else:
            for_role = self.objtypes_for_role(typ)
            if not for_role:
                return None
            objtypes = for_role

        self._intersphinx_adjust_object_types(
            env, store, typ, target, disabled_object_types, node, contnode, objtypes)
        objtypes = [o for o in objtypes if o not in disabled_object_types]

        typed_store = cast(dict[str, dict[str, Any]], store)
        # we try the target either as is, or with full qualification based on the scope of node
        res = self._intersphinx_resolve_xref_lookup(typed_store, target, objtypes)
        if res is not None:
            return res
        # try with qualification of the current scope instead
        full_qualified_name = self.get_full_qualified_name(node)
        if full_qualified_name:
            return self._intersphinx_resolve_xref_lookup(
                typed_store, full_qualified_name, objtypes)
        else:
            return None
