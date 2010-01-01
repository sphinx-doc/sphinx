# -*- coding: utf-8 -*-
"""
    sphinx.pycode
    ~~~~~~~~~~~~~

    Utilities parsing and analyzing Python code.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
from os import path
from cStringIO import StringIO

from sphinx.pycode import nodes
from sphinx.pycode.pgen2 import driver, token, tokenize, parse, literals
from sphinx.util.docstrings import prepare_docstring, prepare_commentdoc


# load the Python grammar
_grammarfile = path.join(path.dirname(__file__), 'Grammar.txt')
pygrammar = driver.load_grammar(_grammarfile)
pydriver = driver.Driver(pygrammar, convert=nodes.convert)

# an object with attributes corresponding to token and symbol names
class sym: pass
for k, v in pygrammar.symbol2number.iteritems():
    setattr(sym, k, v)
for k, v in token.tok_name.iteritems():
    setattr(sym, v, k)

# a dict mapping terminal and nonterminal numbers to their names
number2name = pygrammar.number2symbol.copy()
number2name.update(token.tok_name)


# a regex to recognize coding cookies
_coding_re = re.compile(r'coding[:=]\s*([-\w.]+)')

_eq = nodes.Leaf(token.EQUAL, '=')


class AttrDocVisitor(nodes.NodeVisitor):
    """
    Visitor that collects docstrings for attribute assignments on toplevel and
    in classes.

    The docstrings can either be in special '#:' comments before the assignment
    or in a docstring after it.
    """
    def init(self, scope, encoding):
        self.scope = scope
        self.encoding = encoding
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
        prefix = prefix.decode(self.encoding)
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
            # need to "eval" the string because it's returned in its
            # original form
            docstring = literals.evalString(node[0].value, self.encoding)
            docstring = prepare_docstring(docstring)
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
    # cache for analyzer objects -- caches both by module and file name
    cache = {}

    @classmethod
    def for_string(cls, string, modname, srcname='<string>'):
        return cls(StringIO(string), modname, srcname)

    @classmethod
    def for_file(cls, filename, modname):
        if ('file', filename) in cls.cache:
            return cls.cache['file', filename]
        try:
            fileobj = open(filename, 'r')
        except Exception, err:
            raise PycodeError('error opening %r' % filename, err)
        obj = cls(fileobj, modname, filename)
        cls.cache['file', filename] = obj
        return obj

    @classmethod
    def for_module(cls, modname):
        if ('module', modname) in cls.cache:
            entry = cls.cache['module', modname]
            if isinstance(entry, PycodeError):
                raise entry
            return entry

        try:
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
                    raise PycodeError('error getting source for %r' % modname,
                                      err)
                obj = cls.for_string(source, modname)
                cls.cache['module', modname] = obj
                return obj
            filename = getattr(mod, '__file__', None)
            if filename is None:
                raise PycodeError('no source found for module %r' % modname)
            filename = path.normpath(path.abspath(filename))
            lfilename = filename.lower()
            if lfilename.endswith('.pyo') or lfilename.endswith('.pyc'):
                filename = filename[:-1]
            elif not lfilename.endswith('.py'):
                raise PycodeError('source is not a .py file: %r' % filename)
            if not path.isfile(filename):
                raise PycodeError('source file is not present: %r' % filename)
            obj = cls.for_file(filename, modname)
        except PycodeError, err:
            cls.cache['module', modname] = err
            raise
        cls.cache['module', modname] = obj
        return obj

    def __init__(self, source, modname, srcname):
        # name of the module
        self.modname = modname
        # name of the source file
        self.srcname = srcname
        # file-like object yielding source lines
        self.source = source

        # will be filled by tokenize()
        self.tokens = None
        # will be filled by parse()
        self.parsetree = None
        # will be filled by find_attr_docs()
        self.attr_docs = None
        # will be filled by find_tags()
        self.tags = None

    def tokenize(self):
        """Generate tokens from the source."""
        if self.tokens is not None:
            return
        self.tokens = list(tokenize.generate_tokens(self.source.readline))
        self.source.close()

    def parse(self):
        """Parse the generated source tokens."""
        if self.parsetree is not None:
            return
        self.tokenize()
        try:
            self.parsetree = pydriver.parse_tokens(self.tokens)
        except parse.ParseError, err:
            raise PycodeError('parsing failed', err)
        # find the source code encoding
        encoding = sys.getdefaultencoding()
        comments = self.parsetree.get_prefix()
        for line in comments.splitlines()[:2]:
            match = _coding_re.search(line)
            if match is not None:
                encoding = match.group(1)
                break
        self.encoding = encoding

    def find_attr_docs(self, scope=''):
        """Find class and module-level attributes and their documentation."""
        if self.attr_docs is not None:
            return self.attr_docs
        self.parse()
        attr_visitor = AttrDocVisitor(number2name, scope, self.encoding)
        attr_visitor.visit(self.parsetree)
        self.attr_docs = attr_visitor.collected
        # now that we found everything we could in the tree, throw it away
        # (it takes quite a bit of memory for large modules)
        self.parsetree = None
        return attr_visitor.collected

    def find_tags(self):
        """Find class, function and method definitions and their location."""
        if self.tags is not None:
            return self.tags
        self.tokenize()
        result = {}
        namespace = []
        stack = []
        indent = 0
        defline = False
        expect_indent = False
        def tokeniter(ignore = (token.COMMENT, token.NL)):
            for tokentup in self.tokens:
                if tokentup[0] not in ignore:
                    yield tokentup
        tokeniter = tokeniter()
        for type, tok, spos, epos, line in tokeniter:
            if expect_indent:
                if type != token.INDENT:
                    # no suite -- one-line definition
                    assert stack
                    dtype, fullname, startline, _ = stack.pop()
                    endline = epos[0]
                    namespace.pop()
                    result[fullname] = (dtype, startline, endline)
                expect_indent = False
            if tok in ('def', 'class'):
                name = tokeniter.next()[1]
                namespace.append(name)
                fullname = '.'.join(namespace)
                stack.append((tok, fullname, spos[0], indent))
                defline = True
            elif type == token.INDENT:
                expect_indent = False
                indent += 1
            elif type == token.DEDENT:
                indent -= 1
                # if the stacklevel is the same as it was before the last
                # def/class block, this dedent closes that block
                if stack and indent == stack[-1][3]:
                    dtype, fullname, startline, _ = stack.pop()
                    endline = spos[0]
                    namespace.pop()
                    result[fullname] = (dtype, startline, endline)
            elif type == token.NEWLINE:
                # if this line contained a definition, expect an INDENT
                # to start the suite; if there is no such INDENT
                # it's a one-line definition
                if defline:
                    defline = False
                    expect_indent = True
        self.tags = result
        return result


if __name__ == '__main__':
    import time, pprint
    x0 = time.time()
    #ma = ModuleAnalyzer.for_file(__file__.rstrip('c'), 'sphinx.builders.html')
    ma = ModuleAnalyzer.for_file('sphinx/builders/html.py',
                                 'sphinx.builders.html')
    ma.tokenize()
    x1 = time.time()
    ma.parse()
    x2 = time.time()
    #for (ns, name), doc in ma.find_attr_docs().iteritems():
    #    print '>>', ns, name
    #    print '\n'.join(doc)
    pprint.pprint(ma.find_tags())
    x3 = time.time()
    #print nodes.nice_repr(ma.parsetree, number2name)
    print "tokenizing %.4f, parsing %.4f, finding %.4f" % (x1-x0, x2-x1, x3-x2)
