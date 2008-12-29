# -*- coding: utf-8 -*-
"""
    sphinx.pycode
    ~~~~~~~~~~~~~

    Utilities parsing and analyzing Python code.

    :copyright: 2008 by Georg Brandl.
    :license: BSD, see LICENSE for details.
"""

import sys
import time
from os import path

from sphinx.pycode import pytree
from sphinx.pycode.pgen2 import driver, token


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


def prepare_commentdoc(s):
    result = []
    lines = [line.strip() for line in s.expandtabs().splitlines()]
    for line in lines:
        if line.startswith('#: '):
            result.append(line[3:])
    if result and result[-1]:
        result.append('')
    return '\n'.join(result)


_eq = pytree.Leaf(token.EQUAL, '=')


class ClassAttrVisitor(pytree.NodeVisitor):
    def init(self, scope):
        self.scope = scope
        self.namespace = []
        self.collected = []

    def visit_classdef(self, node):
        self.namespace.append(node[1].value)
        self.generic_visit(node)
        self.namespace.pop()

    def visit_expr_stmt(self, node):
        if _eq not in node.children:
            # not an assignment (we don't care for augmented assignments)
            return
        prefix = node[0].get_prefix()
        if not prefix:
            # if this assignment is the first thing in a class block,
            # the comment will be the prefix of the preceding INDENT token
            prev = node[0].get_prev_leaf()
            if prev and prev.type == token.INDENT:
                prefix = prev.prefix
        doc = prepare_commentdoc(prefix)
        if doc:
            name = '.'.join(self.namespace + [node[0].compact()])
            if name.startswith(self.scope):
                self.collected.append((name, doc))

    def visit_funcdef(self, node):
        # don't descend into functions -- nothing interesting there
        return


class ModuleAnalyzer(object):

    def __init__(self, tree, modname, srcname):
        self.tree = tree
        self.modname = modname
        self.srcname = srcname

    @classmethod
    def for_string(cls, string, modname, srcname='<string>'):
        return cls(pydriver.parse_string(string), modname, srcname)

    @classmethod
    def for_file(cls, filename, modname):
        # XXX if raises
        fileobj = open(filename, 'r')
        try:
            return cls(pydriver.parse_stream(fileobj), modname, filename)
        finally:
            fileobj.close()

    @classmethod
    def for_module(cls, modname):
        if modname not in sys.modules:
            # XXX
            __import__(modname)
        mod = sys.modules[modname]
        if hasattr(mod, '__loader__'):
            # XXX raises
            source = mod.__loader__.get_source(modname)
            return cls.for_string(source, modname)
        filename = getattr(mod, '__file__', None)
        if filename is None:
            # XXX
            raise RuntimeError('no source found')
        if filename.lower().endswith('.pyo') or \
           filename.lower().endswith('.pyc'):
            filename = filename[:-1]
        elif not filename.lower().endswith('.py'):
            raise RuntimeError('not a .py file')
        if not path.isfile(filename):
            # XXX
            raise RuntimeError('source not present')
        return cls.for_file(filename, modname)

    def find_defs(self):
        attr_visitor = ClassAttrVisitor(number2name, '')
        attr_visitor.visit(self.tree)
        for name, doc in attr_visitor.collected:
            print '>>', name
            print doc


x0 = time.time()
ma = ModuleAnalyzer.for_module('sphinx.builders.html')
x1 = time.time()
ma.find_defs()
x2 = time.time()
print "parsing %.4f, finding %.4f" % (x1-x0, x2-x1)
