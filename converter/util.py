# -*- coding: utf-8 -*-
"""
    Python documentation conversion utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""

import re

from docutils.nodes import make_id

from .docnodes import TextNode, EmptyNode, NodeList


def umlaut(cmd, c):
    try:
        if cmd == '"':
            return {'o': u'ö',
                    'a': u'ä',
                    'u': u'ü',
                    'i': u'ï',
                    'O': u'Ö',
                    'A': u'Ä',
                    'U': u'Ü'}[c]
        elif cmd == "'":
            return {'a': u'á',
                    'e': u'é'}[c]
        elif cmd == '~':
            return {'n': u'ñ'}[c]
        elif cmd == 'c':
            return {'c': u'ç'}[c]
        elif cmd == '`':
            return {'o': u'ò'}[c]
        else:
            from .latexparser import ParserError
            raise ParserError('invalid umlaut \\%s' % cmd, 0)
    except KeyError:
        from .latexparser import ParserError
        raise ParserError('unsupported umlaut \\%s%s' % (cmd, c), 0)

def fixup_text(text):
    return text.replace('``', '"').replace("''", '"').replace('`', "'").\
           replace('|', '\\|').replace('*', '\\*')

def empty(node):
    return (type(node) is EmptyNode)

def text(node):
    """ Return the text for a TextNode or raise an error. """
    if isinstance(node, TextNode):
        return node.text
    elif isinstance(node, NodeList):
        restext = ''
        for subnode in node:
            restext += text(subnode)
        return restext
    from .restwriter import WriterError
    raise WriterError('text() failed for %r' % node)

markup_re = re.compile(r'(:[a-zA-Z0-9_-]+:)?`(.*?)`')

def my_make_id(name):
    """ Like make_id(), but strip roles first. """
    return make_id(markup_re.sub(r'\2', name))

alphanum = u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
wordchars_s = alphanum + u'_.-'
wordchars_e = alphanum + u'+`(-'
bad_markup_re = re.compile(r'(:[a-zA-Z0-9_-]+:)?(`{1,2})[ ]*(.+?)[ ]*(\2)')
quoted_code_re = re.compile(r'\\`(``.+?``)\'')

def repair_bad_inline_markup(text):
    # remove quoting from `\code{x}'
    xtext = quoted_code_re.sub(r'\1', text)

    # special: the literal backslash
    xtext = xtext.replace('``\\``', '\x03')
    # special: literal backquotes
    xtext = xtext.replace('``````', '\x02')

    ntext = []
    lasti = 0
    l = len(xtext)
    for m in bad_markup_re.finditer(xtext):
        ntext.append(xtext[lasti:m.start()])
        s, e = m.start(), m.end()
        if s != 0 and xtext[s-1:s] in wordchars_s:
            ntext.append('\\ ')
        ntext.append((m.group(1) or '') + m.group(2) + m.group(3) + m.group(4))
        if e != l and xtext[e:e+1] in wordchars_e:
            ntext.append('\\ ')
        lasti = m.end()
    ntext.append(xtext[lasti:])
    return ''.join(ntext).replace('\x02', '``````').replace('\x03', '``\\``')
