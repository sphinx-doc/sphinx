# -*- coding: utf-8 -*-
"""
    sphinx.web.feed
    ~~~~~~~~~~~~~~~

    Nifty module that generates RSS feeds.

    :copyright: 2007-2008 by Armin Ronacher.
    :license: BSD.
"""
import time
from datetime import datetime
from xml.dom.minidom import Document
from email.Utils import formatdate


def format_rss_date(date):
    """
    Pass it a datetime object to receive the string representation
    for RSS date fields.
    """
    return formatdate(time.mktime(date.timetuple()) + date.microsecond / 1e6)


class Feed(object):
    """
    Abstract feed creation class. To generate feeds use one of
    the subclasses `RssFeed` or `AtomFeed`.
    """

    def __init__(self, req, title, description, link):
        self.req = req
        self.title = title
        self.description = description
        self.link = req.make_external_url(link)
        self.items = []
        self._last_update = None

    def add_item(self, title, author, link, description, pub_date):
        if self._last_update is None or pub_date > self._last_update:
            self._last_update = pub_date
        date = pub_date or datetime.utcnow()
        self.items.append({
            'title':        title,
            'author':       author,
            'link':         self.req.make_external_url(link),
            'description':  description,
            'pub_date':     date
        })

    def generate(self):
        return self.generate_document().toxml('utf-8')

    def generate_document(self):
        doc = Document()
        Element = doc.createElement
        Text = doc.createTextNode

        rss = doc.appendChild(Element('rss'))
        rss.setAttribute('version', '2.0')

        channel = rss.appendChild(Element('channel'))
        for key in ('title', 'description', 'link'):
            value = getattr(self, key)
            channel.appendChild(Element(key)).appendChild(Text(value))
        date = format_rss_date(self._last_update or datetime.utcnow())
        channel.appendChild(Element('pubDate')).appendChild(Text(date))

        for item in self.items:
            d = Element('item')
            for key in ('title', 'author', 'link', 'description'):
                d.appendChild(Element(key)).appendChild(Text(item[key]))
            pub_date = format_rss_date(item['pub_date'])
            d.appendChild(Element('pubDate')).appendChild(Text(pub_date))
            d.appendChild(Element('guid')).appendChild(Text(item['link']))
            channel.appendChild(d)

        return doc
