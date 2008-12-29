# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Python parse tree definitions.

This is a very concrete parse tree; we need to keep every token and
even the comments and whitespace between tokens.

Adapted for read-only nodes from pytree.py in Python's 2to3 tool, and
added a few bits.
"""

__author__ = "Guido van Rossum <guido@python.org>"


class Base(object):

    """Abstract base class for Node and Leaf.

    This provides some default functionality and boilerplate using the
    template pattern.

    A node may be a subnode of at most one parent.
    """

    # Default values for instance variables
    type = None    # int: token number (< 256) or symbol number (>= 256)
    parent = None  # Parent node pointer, or None
    children = ()  # Tuple of subnodes
    was_changed = False

    def __new__(cls, *args, **kwds):
        """Constructor that prevents Base from being instantiated."""
        assert cls is not Base, "Cannot instantiate Base"
        return object.__new__(cls)

    def __eq__(self, other):
        """Compares two nodes for equality.

        This calls the method _eq().
        """
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self._eq(other)

    def __ne__(self, other):
        """Compares two nodes for inequality.

        This calls the method _eq().
        """
        if self.__class__ is not other.__class__:
            return NotImplemented
        return not self._eq(other)

    def _eq(self, other):
        """Compares two nodes for equality.

        This is called by __eq__ and __ne__.  It is only called if the
        two nodes have the same type.  This must be implemented by the
        concrete subclass.  Nodes should be considered equal if they
        have the same structure, ignoring the prefix string and other
        context information.
        """
        raise NotImplementedError

    def get_lineno(self):
        """Returns the line number which generated the invocant node."""
        node = self
        while not isinstance(node, Leaf):
            if not node.children:
                return
            node = node.children[0]
        return node.lineno

    def get_next_sibling(self):
        """Return the node immediately following the invocant in their
        parent's children list. If the invocant does not have a next
        sibling, return None."""
        if self.parent is None:
            return None

        # Can't use index(); we need to test by identity
        for i, child in enumerate(self.parent.children):
            if child is self:
                try:
                    return self.parent.children[i+1]
                except IndexError:
                    return None

    def get_prev_sibling(self):
        """Return the node immediately preceding the invocant in their
        parent's children list. If the invocant does not have a previous
        sibling, return None."""
        if self.parent is None:
            return None

        # Can't use index(); we need to test by identity
        for i, child in enumerate(self.parent.children):
            if child is self:
                if i == 0:
                    return None
                return self.parent.children[i-1]

    def get_prev_leaf(self):
        """Return the leaf node that precedes this node in the parse tree."""
        def last_child(node):
            if isinstance(node, Leaf):
                return node
            elif not node.children:
                return None
            else:
                return last_child(node.children[-1])
        if self.parent is None:
            return None
        prev = self.get_prev_sibling()
        if isinstance(prev, Leaf):
            return prev
        elif prev is not None:
            return last_child(prev)
        return self.parent.get_prev_leaf()

    def get_suffix(self):
        """Return the string immediately following the invocant node. This
        is effectively equivalent to node.get_next_sibling().get_prefix()"""
        next_sib = self.get_next_sibling()
        if next_sib is None:
            return ""
        return next_sib.get_prefix()


class Node(Base):

    """Concrete implementation for interior nodes."""

    def __init__(self, type, children, context=None, prefix=None):
        """Initializer.

        Takes a type constant (a symbol number >= 256), a sequence of
        child nodes, and an optional context keyword argument.

        As a side effect, the parent pointers of the children are updated.
        """
        assert type >= 256, type
        self.type = type
        self.children = list(children)
        for ch in self.children:
            assert ch.parent is None, repr(ch)
            ch.parent = self
        if prefix is not None:
            self.set_prefix(prefix)

    def __repr__(self):
        return "%s(%s, %r)" % (self.__class__.__name__,
                               self.type, self.children)

    def __str__(self):
        """This reproduces the input source exactly."""
        return "".join(map(str, self.children))

    def compact(self):
        return ''.join(child.compact() for child in self.children)

    def __getitem__(self, index):
        return self.children[index]

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def _eq(self, other):
        """Compares two nodes for equality."""
        return (self.type, self.children) == (other.type, other.children)

    def post_order(self):
        """Returns a post-order iterator for the tree."""
        for child in self.children:
            for node in child.post_order():
                yield node
        yield self

    def pre_order(self):
        """Returns a pre-order iterator for the tree."""
        yield self
        for child in self.children:
            for node in child.post_order():
                yield node

    def get_prefix(self):
        """Returns the prefix for the node.

        This passes the call on to the first child.
        """
        if not self.children:
            return ""
        return self.children[0].get_prefix()


class Leaf(Base):

    """Concrete implementation for leaf nodes."""

    # Default values for instance variables
    prefix = ""  # Whitespace and comments preceding this token in the input
    lineno = 0   # Line where this token starts in the input
    column = 0   # Column where this token tarts in the input

    def __init__(self, type, value, context=None, prefix=None):
        """Initializer.

        Takes a type constant (a token number < 256), a string value,
        and an optional context keyword argument.
        """
        assert 0 <= type < 256, type
        if context is not None:
            self.prefix, (self.lineno, self.column) = context
        self.type = type
        self.value = value
        if prefix is not None:
            self.prefix = prefix

    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__,
                                   self.type, self.value, self.prefix)

    def __str__(self):
        """This reproduces the input source exactly."""
        return self.prefix + str(self.value)

    def compact(self):
        return str(self.value)

    def _eq(self, other):
        """Compares two nodes for equality."""
        return (self.type, self.value) == (other.type, other.value)

    def post_order(self):
        """Returns a post-order iterator for the tree."""
        yield self

    def pre_order(self):
        """Returns a pre-order iterator for the tree."""
        yield self

    def get_prefix(self):
        """Returns the prefix for the node."""
        return self.prefix


def convert(grammar, raw_node):
    """Convert raw node to a Node or Leaf instance."""
    type, value, context, children = raw_node
    if children or type in grammar.number2symbol:
        # If there's exactly one child, return that child instead of
        # creating a new node.
        if len(children) == 1:
            return children[0]
        return Node(type, children, context=context)
    else:
        return Leaf(type, value, context=context)


def nice_repr(node, number2name, prefix=False):
    def _repr(node):
        if isinstance(node, Leaf):
            return "%s(%r)" % (number2name[node.type], node.value)
        else:
            return "%s(%s)" % (number2name[node.type],
                               ', '.join(map(_repr, node.children)))
    def _prepr(node):
        if isinstance(node, Leaf):
            return "%s(%r, %r)" % (number2name[node.type], node.prefix, node.value)
        else:
            return "%s(%s)" % (number2name[node.type],
                               ', '.join(map(_prepr, node.children)))
    return (prefix and _prepr or _repr)(node)


class NodeVisitor(object):
    def __init__(self, number2name, *args):
        self.number2name = number2name
        self.init(*args)

    def init(self, *args):
        pass

    def visit(self, node):
        """Visit a node."""
        method = 'visit_' + self.number2name[node.type]
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        if isinstance(node, Node):
            for child in node:
                self.visit(child)
