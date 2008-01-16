# -*- coding: utf-8 -*-
"""
    sphinx.web.antispam
    ~~~~~~~~~~~~~~~~~~~

    Small module that performs anti spam tests based on the bad content
    regex list provided by moin moin.

    :copyright: 2007-2008 by Armin Ronacher.
    :license: BSD.
"""

import re
import urllib
import time
from os import path

DOWNLOAD_URL = 'http://moinmaster.wikiwikiweb.de/BadContent?action=raw'
UPDATE_INTERVAL = 60 * 60 * 24 * 7


class AntiSpam(object):
    """
    Class that reads a bad content database (flat file that is automatically
    updated from the moin moin server) and checks strings against it.
    """

    def __init__(self, bad_content_file):
        self.bad_content_file = bad_content_file
        lines = None

        if not path.exists(self.bad_content_file):
            last_change = 0
        else:
            last_change = path.getmtime(self.bad_content_file)

        if last_change + UPDATE_INTERVAL < time.time():
            try:
                f = urllib.urlopen(DOWNLOAD_URL)
                data = f.read()
            except:
                pass
            else:
                lines = [l.strip() for l in data.splitlines()
                              if not l.startswith('#')]
                f = open(bad_content_file, 'w')
                try:
                    f.write('\n'.join(lines))
                finally:
                    f.close()
                last_change = int(time.time())

        if lines is None:
            try:
                f = open(bad_content_file)
                try:
                    lines = [l.strip() for l in f]
                finally:
                    f.close()
            except:
                lines = []
        self.rules = [re.compile(rule) for rule in lines if rule]

    def is_spam(self, fields):
        for regex in self.rules:
            for field in fields:
                if regex.search(field) is not None:
                    return True
        return False
