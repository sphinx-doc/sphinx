# -*- coding: utf-8 -*-
"""
    Python documentation LaTeX parser - document nodes
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""


class DocNode(object):
    """ A node in the document tree. """
    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def __str__(self):
        raise RuntimeError('cannot stringify docnodes')

    def walk(self):
        return []


class CommentNode(DocNode):
    """ A comment. """
    def __init__(self, comment):
        assert isinstance(comment, basestring)
        self.comment = comment

    def __repr__(self):
        return 'CommentNode(%r)' % self.comment


class RootNode(DocNode):
    """ A whole document. """
    def __init__(self, filename, children):
        self.filename = filename
        self.children = children
        self.params = {}
        self.labels = {}

    def __repr__(self):
        return 'RootNode(%r, %r)' % (self.filename, self.children)

    def walk(self):
        return self.children

    def transform(self):
        """ Do restructurings not possible during parsing. """
        def do_descenvs(node):
            r""" Make \xxxlines an attribute of the parent xxxdesc node. """
            for subnode in node.walk():
                do_descenvs(subnode)
            if isinstance(node, DescEnvironmentNode):
                for subnode in node.content.walk():
                    if isinstance(subnode, DescLineCommandNode):
                        node.additional.append((subnode.cmdname, subnode.args))

        do_descenvs(self)


class NodeList(DocNode, list):
    """ A list of subnodes. """
    def __init__(self, children=None):
        list.__init__(self, children or [])

    def __repr__(self):
        return 'NL%s' % list.__repr__(self)

    def walk(self):
        return self

    def append(self, node):
        assert isinstance(node, DocNode)
        if type(node) is EmptyNode:
            return
        elif self and isinstance(node, TextNode) and \
                 type(self[-1]) is TextNode:
            self[-1].text += node.text
        elif type(node) is NodeList:
            list.extend(self, node)
        elif type(node) is VerbatimNode and self and \
                 isinstance(self[-1], ParaSepNode):
            # don't allow a ParaSepNode before VerbatimNode
            # because this breaks ReST's '::'
            self[-1] = node
        else:
            list.append(self, node)

    def flatten(self):
        if len(self) > 1:
            return self
        elif len(self) == 1:
            return self[0]
        else:
            return EmptyNode()


class ParaSepNode(DocNode):
    """ A node for paragraph separator. """
    def __repr__(self):
        return 'Para'


class TextNode(DocNode):
    """ A node containing text. """
    def __init__(self, text):
        assert isinstance(text, basestring)
        self.text = text

    def __repr__(self):
        if type(self) is TextNode:
            return 'T%r' % self.text
        else:
            return '%s(%r)' % (self.__class__.__name__, self.text)


class EmptyNode(TextNode):
    """ An empty node. """
    def __init__(self, *args):
        self.text = ''


class NbspNode(TextNode):
    """ A non-breaking space. """
    def __init__(self, *args):
        # this breaks ReST markup (!)
        #self.text = u'\N{NO-BREAK SPACE}'
        self.text = ' '

    def __repr__(self):
        return 'NBSP'


simplecmd_mapping = {
    'ldots': u'...',
    'moreargs': '...',
    'unspecified': '...',
    'ASCII': 'ASCII',
    'UNIX': 'Unix',
    'Unix': 'Unix',
    'POSIX': 'POSIX',
    'LaTeX': 'LaTeX',
    'EOF': 'EOF',
    'Cpp': 'C++',
    'C': 'C',
    'sub': u'--> ',
    'textbackslash': '\\\\',
    'textunderscore': '_',
    'texteuro': u'\N{EURO SIGN}',
    'textasciicircum': u'^',
    'textasciitilde': u'~',
    'textgreater': '>',
    'textless': '<',
    'textbar': '|',
    'backslash': '\\\\',
    'tilde': '~',
    'copyright': u'\N{COPYRIGHT SIGN}',
    # \e is mostly inside \code and therefore not escaped.
    'e': '\\',
    'infinity': u'\N{INFINITY}',
    'plusminus': u'\N{PLUS-MINUS SIGN}',
    'leq': u'\N{LESS-THAN OR EQUAL TO}',
    'geq': u'\N{GREATER-THAN OR EQUAL TO}',
    'pi': u'\N{GREEK SMALL LETTER PI}',
    'AA': u'\N{LATIN CAPITAL LETTER A WITH RING ABOVE}',
}

class SimpleCmdNode(TextNode):
    """ A command resulting in simple text. """
    def __init__(self, cmdname, args):
        self.text = simplecmd_mapping[cmdname]


class BreakNode(DocNode):
    """ A line break. """
    def __repr__(self):
        return 'BR'


class CommandNode(DocNode):
    """ A general command. """
    def __init__(self, cmdname, args):
        self.cmdname = cmdname
        self.args = args

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.cmdname, self.args)

    def walk(self):
        return self.args


class DescLineCommandNode(CommandNode):
    """ A \\xxxline command. """


class InlineNode(CommandNode):
    """ A node with inline markup. """
    def walk(self):
        return []


class IndexNode(InlineNode):
    """ An index-generating command. """
    def __init__(self, cmdname, args):
        self.cmdname = cmdname
        # tricky -- this is to make this silent in paragraphs
        # while still generating index entries for textonly()
        self.args = []
        self.indexargs = args


class SectioningNode(CommandNode):
    """ A heading node. """


class EnvironmentNode(DocNode):
    """ An environment. """
    def __init__(self, envname, args, content):
        self.envname = envname
        self.args = args
        self.content = content

    def __repr__(self):
        return 'EnvironmentNode(%r, %r, %r)' % (self.envname,
                                                self.args, self.content)

    def walk(self):
        return [self.content]


class DescEnvironmentNode(EnvironmentNode):
    """ An xxxdesc environment. """
    def __init__(self, envname, args, content):
        self.envname = envname
        self.args = args
        self.additional = []
        self.content = content

    def __repr__(self):
        return 'DescEnvironmentNode(%r, %r, %r)' % (self.envname,
                                                    self.args, self.content)


class TableNode(EnvironmentNode):
    def __init__(self, numcols, headings, lines):
        self.numcols = numcols
        self.headings = headings
        self.lines = lines

    def __repr__(self):
        return 'TableNode(%r, %r, %r)' % (self.numcols,
                                          self.headings, self.lines)

    def walk(self):
        return []


class VerbatimNode(DocNode):
    """ A verbatim code block. """
    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return 'VerbatimNode(%r)' % self.content


class ListNode(DocNode):
    """ A list. """
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.items)

    def walk(self):
        return [item[1] for item in self.items]


class ItemizeNode(ListNode):
    """ An enumeration with bullets. """


class EnumerateNode(ListNode):
    """ An enumeration with numbers. """


class DescriptionNode(ListNode):
    """ A description list. """


class DefinitionsNode(ListNode):
    """ A definition list. """


class ProductionListNode(ListNode):
    """ A grammar production list. """
