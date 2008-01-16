# -*- coding: utf-8 -*-
"""
    sphinx.web.markup
    ~~~~~~~~~~~~~~~~~

    Awfully simple markup used in comments. Syntax:

    `this is some <code>`
        like <tt> in HTML

    ``this is like ` just that i can contain backticks``
        like <tt> in HTML

    *emphasized*
        translates to <em class="important">

    **strong**
        translates to <strong>

    !!!very important message!!!
        use this to mark important or dangerous things.
        Translates to <em class="dangerous">

    [[http://www.google.com/]]
        Simple link with the link target as caption. If the
        URL is relative the provided callback is called to get
        the full URL.

    [[http://www.google.com/ go to google]]
        Link with "go to google" as caption.

    <code>preformatted code that could by python code</code>
        Python code (most of the time), otherwise preformatted.

    <quote>cite someone</quote>
        Like <blockquote> in HTML.

    :copyright: 2007-2008 by Armin Ronacher.
    :license: BSD.
"""
import cgi
import re
from urlparse import urlparse

from sphinx.highlighting import highlight_block


inline_formatting = {
    'escaped_code': ('``',        '``'),
    'code':         ('`',         '`'),
    'strong':       ('**',        '**'),
    'emphasized':   ('*',         '*'),
    'important':    ('!!!',       '!!!'),
    'link':         ('[[',        ']]'),
    'quote':        ('<quote>',   '</quote>'),
    'code_block':   ('<code>',    '</code>'),
    'paragraph':    (r'\n{2,}',   None),
    'newline':      (r'\\$',      None)
}

simple_formattings = {
    'strong_begin':                 '<strong>',
    'strong_end':                   '</strong>',
    'emphasized_begin':             '<em>',
    'emphasized_end':               '</em>',
    'important_begin':              '<em class="important">',
    'important_end':                '</em>',
    'quote_begin':                  '<blockquote>',
    'quote_end':                    '</blockquote>'
}

raw_formatting = set(['link', 'code', 'escaped_code', 'code_block'])

formatting_start_re = re.compile('|'.join(
    '(?P<%s>%s)' % (name, end is not None and re.escape(start) or start)
    for name, (start, end)
    in sorted(inline_formatting.items(), key=lambda x: -len(x[1][0]))
), re.S | re.M)

formatting_end_res = dict(
    (name, re.compile(re.escape(end))) for name, (start, end)
    in inline_formatting.iteritems() if end is not None
)

without_end_tag = set(name for name, (_, end) in inline_formatting.iteritems()
                      if end is None)



class StreamProcessor(object):

    def __init__(self, stream):
        self._pushed = []
        self._stream = stream

    def __iter__(self):
        return self

    def next(self):
        if self._pushed:
            return self._pushed.pop()
        return self._stream.next()

    def push(self, token, data):
        self._pushed.append((token, data))

    def get_data(self, drop_needle=False):
        result = []
        try:
            while True:
                token, data = self.next()
                if token != 'text':
                    if not drop_needle:
                        self.push(token, data)
                    break
                result.append(data)
        except StopIteration:
            pass
        return ''.join(result)


class MarkupParser(object):

    def __init__(self, make_rel_url):
        self.make_rel_url = make_rel_url

    def tokenize(self, text):
        text = '\n'.join(text.splitlines())
        last_pos = 0
        pos = 0
        end = len(text)
        stack = []
        text_buffer = []

        while pos < end:
            if stack:
                m = formatting_end_res[stack[-1]].match(text, pos)
                if m is not None:
                    if text_buffer:
                        yield 'text', ''.join(text_buffer)
                        del text_buffer[:]
                    yield stack[-1] + '_end', None
                    stack.pop()
                    pos = m.end()
                    continue

            m = formatting_start_re.match(text, pos)
            if m is not None:
                if text_buffer:
                    yield 'text', ''.join(text_buffer)
                    del text_buffer[:]

                for key, value in m.groupdict().iteritems():
                    if value is not None:
                        if key in without_end_tag:
                            yield key, None
                        else:
                            if key in raw_formatting:
                                regex = formatting_end_res[key]
                                m2 = regex.search(text, m.end())
                                if m2 is None:
                                    yield key, text[m.end():]
                                else:
                                    yield key, text[m.end():m2.start()]
                                m = m2
                            else:
                                yield key + '_begin', None
                                stack.append(key)
                        break

                if m is None:
                    break
                else:
                    pos = m.end()
                    continue

            text_buffer.append(text[pos])
            pos += 1

        yield 'text', ''.join(text_buffer)
        for token in reversed(stack):
            yield token + '_end', None

    def stream_to_html(self, text):
        stream = StreamProcessor(self.tokenize(text))
        paragraph = []
        result = []

        def new_paragraph():
            result.append(paragraph[:])
            del paragraph[:]

        for token, data in stream:
            if token in simple_formattings:
                paragraph.append(simple_formattings[token])
            elif token in ('text', 'escaped_code', 'code'):
                if data:
                    data = cgi.escape(data)
                    if token in ('escaped_code', 'code'):
                        data = '<tt>%s</tt>' % data
                    paragraph.append(data)
            elif token == 'link':
                if ' ' in data:
                    href, caption = data.split(' ', 1)
                else:
                    href = caption = data
                protocol = urlparse(href)[0]
                nofollow = True
                if not protocol:
                    href = self.make_rel_url(href)
                    nofollow = False
                elif protocol == 'javascript':
                    href = href[11:]
                paragraph.append('<a href="%s"%s>%s</a>' % (cgi.escape(href),
                                 nofollow and ' rel="nofollow"' or '',
                                 cgi.escape(caption)))
            elif token == 'code_block':
                result.append(highlight_block(data, 'python'))
                new_paragraph()
            elif token == 'paragraph':
                new_paragraph()
            elif token == 'newline':
                paragraph.append('<br>')

        if paragraph:
            result.append(paragraph)
        for item in result:
            if isinstance(item, list):
                if item:
                    yield '<p>%s</p>' % ''.join(item)
            else:
                yield item

    def to_html(self, text):
        return ''.join(self.stream_to_html(text))


def markup(text, make_rel_url=lambda x: './' + x):
    return MarkupParser(make_rel_url).to_html(text)
