# -*- coding: utf-8 -*-
"""
    sphinx.web.userdb
    ~~~~~~~~~~~~~~~~~

    A module that provides pythonic access to the `docusers` file
    that stores users and their passwords so that they can gain access
    to the administration system.

    :copyright: 2007 by Armin Ronacher.
    :license: Python license.
"""
from __future__ import with_statement
from os import path
from hashlib import sha1
from random import choice, randrange
from collections import defaultdict


def gen_password(length=8, add_numbers=True, mix_case=True,
                 add_special_char=True):
    """
    Generate a pronounceable password.
    """
    if length <= 0:
        raise ValueError('requested password of length <= 0')
    consonants = 'bcdfghjklmnprstvwz'
    vowels = 'aeiou'
    if mix_case:
        consonants = consonants * 2 + consonants.upper()
        vowels = vowels * 2 + vowels.upper()
    pw =  ''.join([choice(consonants) +
                   choice(vowels) +
                   choice(consonants + vowels) for _
                   in xrange(length // 3 + 1)])[:length]
    if add_numbers:
        n = length // 3
        if n > 0:
            pw = pw[:-n]
            for _ in xrange(n):
                pw += choice('0123456789')
    if add_special_char:
        tmp = randrange(0, len(pw))
        l1 = pw[:tmp]
        l2 = pw[tmp:]
        if max(len(l1), len(l2)) == len(l1):
            l1 = l1[:-1]
        else:
            l2 = l2[:-1]
        return l1 + choice('#$&%?!') + l2
    return pw


class UserDatabase(object):

    def __init__(self, filename):
        self.filename = filename
        self.users = {}
        self.privileges = defaultdict(set)
        if path.exists(filename):
            with file(filename) as f:
                for line in f:
                    line = line.strip()
                    if line and line[0] != '#':
                        parts = line.split(':')
                        self.users[parts[0]] = parts[1]
                        self.privileges[parts[0]].update(x for x in
                                                         parts[2].split(',')
                                                         if x)

    def set_password(self, user, password):
        """Encode the password for a user (also adds users)."""
        self.users[user] = sha1('%s|%s' % (user, password)).hexdigest()

    def add_user(self, user):
        """Add a new user and return the generated password."""
        pw = gen_password(8, add_special_char=False)
        self.set_password(user, pw)
        self.privileges[user].clear()
        return pw

    def check_password(self, user, password):
        return user in self.users and \
            self.users[user] == sha1('%s|%s' % (user, password)).hexdigest()

    def save(self):
        with file(self.filename, 'w') as f:
            for username, password in self.users.iteritems():
                privileges = ','.join(self.privileges.get(username, ()))
                f.write('%s:%s:%s\n' % (username, password, privileges))
