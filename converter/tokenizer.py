# -*- coding: utf-8 -*-
"""
    Python documentation LaTeX file tokenizer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    For more documentation, look into the ``restwriter.py`` file.

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""

import re

from .scanner import Scanner

class Tokenizer(Scanner):
    """ Lex a Python doc LaTeX document. """

    specials = {
        '{': 'bgroup',
        '}': 'egroup',
        '[': 'boptional',
        ']': 'eoptional',
        '~': 'tilde',
        '$': 'mathmode',
    }

    @property
    def mtext(self):
        return self.match.group()

    def tokenize(self):
        return TokenStream(self._tokenize())

    def _tokenize(self):
        lineno = 1
        while not self.eos:
            if self.scan(r'\\verb([^a-zA-Z])(.*?)(\1)'):
                # specialcase \verb here
                yield lineno, 'command', 'verb', '\\verb'
                yield lineno, 'text', self.match.group(1), self.match.group(1)
                yield lineno, 'text', self.match.group(2), self.match.group(2)
                yield lineno, 'text', self.match.group(3), self.match.group(3)
            elif self.scan(r'\\([a-zA-Z]+\*?)[ \t]*'):
                yield lineno, 'command', self.match.group(1), self.mtext
            elif self.scan(r'\\.'):
                yield lineno, 'command', self.mtext[1], self.mtext
            elif self.scan(r'\\\n'):
                yield lineno, 'text', self.mtext, self.mtext
                lineno += 1
            elif self.scan(r'%(.*)\n[ \t]*'):
                yield lineno, 'comment', self.match.group(1), self.mtext
                lineno += 1
            elif self.scan(r'[{}\[\]~$]'):
                yield lineno, self.specials[self.mtext], self.mtext, self.mtext
            elif self.scan(r'(\n[ \t]*){2,}'):
                lines = self.mtext.count('\n')
                yield lineno, 'parasep', '\n' * lines, self.mtext
                lineno += lines
            elif self.scan(r'\n[ \t]*'):
                yield lineno, 'text', ' ', self.mtext
                lineno += 1
            elif self.scan(r'[^\\%}{\[\]~\n]+'):
                yield lineno, 'text', self.mtext, self.mtext
            else:
                raise RuntimeError('unexpected text on line %d: %r' %
                                   (lineno, self.data[self.pos:self.pos+100]))


class TokenStream(object):
    """
    A token stream works like a normal generator just that
    it supports peeking and pushing tokens back to the stream.
    """

    def __init__(self, generator):
        self._generator = generator
        self._pushed = []
        self.last = (1, 'initial', '')

    def __iter__(self):
        return self

    def __nonzero__(self):
        """ Are we at the end of the tokenstream? """
        if self._pushed:
            return True
        try:
            self.push(self.next())
        except StopIteration:
            return False
        return True

    def pop(self):
        """ Return the next token from the stream. """
        if self._pushed:
            rv = self._pushed.pop()
        else:
            rv = self._generator.next()
        self.last = rv
        return rv

    next = pop

    def popmany(self, num=1):
        """ Pop a list of tokens. """
        return [self.next() for i in range(num)]

    def peek(self):
        """ Pop and push a token, return it. """
        token = self.next()
        self.push(token)
        return token

    def peekmany(self, num=1):
        """ Pop and push a list of tokens. """
        tokens = self.popmany(num)
        for tok in tokens:
            self.push(tok)
        return tokens

    def push(self, item):
        """ Push a token back to the stream. """
        self._pushed.append(item)
