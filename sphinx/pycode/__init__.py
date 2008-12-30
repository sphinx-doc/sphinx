# -*- coding: utf-8 -*-
"""
    sphinx.pycode
    ~~~~~~~~~~~~~

    Utilities parsing and analyzing Python code.

    :copyright: 2008 by Georg Brandl.
    :license: BSD, see LICENSE for details.
"""

import sys
from os import path

from sphinx.pycode import pytree
from sphinx.pycode.pgen2 import driver, token, parse, literals
from sphinx.util.docstrings import prepare_docstring, prepare_commentdoc


# load the Python grammar
_grammarfile = path.join(path.dirname(__file__), 'Grammar.txt')
pygrammar = driver.load_grammar(_grammarfile)
pydriver = driver.Driver(pygrammar, convert=pytree.convert)

class sym: pass
for k, v in pygrammar.symbol2number.iteritems():
    setattr(sym, k, v)

# a dict mapping terminal and nonterminal numbers to their names
number2name = pygrammar.number2symbol.copy()
number2name.update(token.tok_name)


_eq = pytree.Leaf(token.EQUAL, '=')


class AttrDocVisitor(pytree.NodeVisitor):
    """
    Visitor that collects docstrings for attribute assignments on toplevel and
    in classes.

    The docstrings can either be in special '#:' comments before the assignment
    or in a docstring after it.
    """
    def init(self, scope):
        self.scope = scope
        self.namespace = []
        self.collected = {}

    def visit_classdef(self, node):
        self.namespace.append(node[1].value)
        self.generic_visit(node)
        self.namespace.pop()

    def visit_expr_stmt(self, node):
        """Visit an assignment which may have a special comment before it."""
        if _eq not in node.children:
            # not an assignment (we don't care for augmented assignments)
            return
        pnode = node[0]
        prefix = pnode.get_prefix()
        # if the assignment is the first statement on a new indentation
        # level, its preceding whitespace and comments are not assigned
        # to that token, but the first INDENT or DEDENT token
        while not prefix:
            pnode = pnode.get_prev_leaf()
            if not pnode or pnode.type not in (token.INDENT, token.DEDENT):
                break
            prefix = pnode.get_prefix()
        docstring = prepare_commentdoc(prefix)
        if docstring:
            self.add_docstring(node, docstring)

    def visit_simple_stmt(self, node):
        """Visit a docstring statement which may have an assignment before."""
        if node[0].type != token.STRING:
            # not a docstring; but still need to visit children
            return self.generic_visit(node)
        prev = node.get_prev_sibling()
        if not prev:
            return
        if prev.type == sym.simple_stmt and \
               prev[0].type == sym.expr_stmt and _eq in prev[0].children:
            # need to "eval" the string because it's returned in its original form
            docstring = prepare_docstring(literals.evalString(node[0].value))
            self.add_docstring(prev[0], docstring)

    def visit_funcdef(self, node):
        # don't descend into functions -- nothing interesting there
        return

    def add_docstring(self, node, docstring):
        # add an item for each assignment target
        for i in range(0, len(node) - 1, 2):
            target = node[i]
            if target.type != token.NAME:
                # don't care about complex targets
                continue
            namespace = '.'.join(self.namespace)
            if namespace.startswith(self.scope):
                self.collected[namespace, target.value] = docstring


class PycodeError(Exception):
    def __str__(self):
        res = self.args[0]
        if len(self.args) > 1:
            res += ' (exception was: %r)' % self.args[1]
        return res


class ModuleAnalyzer(object):
    # cache for analyzer objects
    cache = {}

    def __init__(self, tree, modname, srcname):
        self.tree = tree
        self.modname = modname
        self.srcname = srcname

    @classmethod
    def for_string(cls, string, modname, srcname='<string>'):
        return cls(pydriver.parse_string(string), modname, srcname)

    @classmethod
    def for_file(cls, filename, modname):
        try:
            fileobj = open(filename, 'r')
        except Exception, err:
            raise PycodeError('error opening %r' % filename, err)
        try:
            try:
                return cls(pydriver.parse_stream(fileobj), modname, filename)
            except parse.ParseError, err:
                raise PycodeError('error parsing %r' % filename, err)
        finally:
            fileobj.close()

    @classmethod
    def for_module(cls, modname):
        if modname in cls.cache:
            return cls.cache[modname]
        if modname not in sys.modules:
            try:
                __import__(modname)
            except ImportError, err:
                raise PycodeError('error importing %r' % modname, err)
        mod = sys.modules[modname]
        if hasattr(mod, '__loader__'):
            try:
                source = mod.__loader__.get_source(modname)
            except Exception, err:
                raise PycodeError('error getting source for %r' % modname, err)
            obj = cls.for_string(source, modname)
            cls.cache[modname] = obj
            return obj
        filename = getattr(mod, '__file__', None)
        if filename is None:
            raise PycodeError('no source found for module %r' % modname)
        if filename.lower().endswith('.pyo') or \
           filename.lower().endswith('.pyc'):
            filename = filename[:-1]
        elif not filename.lower().endswith('.py'):
            raise PycodeError('source is not a .py file: %r' % filename)
        if not path.isfile(filename):
            raise PycodeError('source file is not present: %r' % filename)
        obj = cls.for_file(filename, modname)
        cls.cache[modname] = obj
        return obj

    def find_attr_docs(self, scope=''):
        attr_visitor = AttrDocVisitor(number2name, scope)
        attr_visitor.visit(self.tree)
        return attr_visitor.collected


if __name__ == '__main__':
    import time
    x0 = time.time()
    ma = ModuleAnalyzer.for_file('sphinx/builders/html.py', 'sphinx.builders.html')
    #ma = ModuleAnalyzer.for_file(__file__.rstrip('c'), 'sphinx.builders.html')
    x1 = time.time()
    for (ns, name), doc in ma.find_attr_docs().iteritems():
        print '>>', ns, name
        print '\n'.join(doc)
    x2 = time.time()
    #print pytree.nice_repr(ma.tree, number2name)
    print "parsing %.4f, finding %.4f" % (x1-x0, x2-x1)
