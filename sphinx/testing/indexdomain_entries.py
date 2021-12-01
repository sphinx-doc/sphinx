"""
    this module for the follow code of indexentries.py:

    .. code-block: python

        55         domain = cast(IndexDomain, self.env.get_domain('index'))
        56         for fn, entries in domain.entries.items():

    This was prepared to set the test data that self.env.get_domain('index').entries has.
"""
class _Domain(object):
    def __init__(self, entries):
        self.entries = entries


class _Environment(object):
    def __init__(self, entries):
        self.domain = {}
        self.domain['index'] = _Domain(entries)
    def get_domain(self, domain_type):
        return self.domain[domain_type]


class _Configuration(object):
    def __init__(self):
        self.parameter_name = 'value'


class Builder(object):
    def __init__(self, entries):
        self.env = _Environment(entries)
        self.get_domain = self.env.get_domain
        self.config = _Configuration()
    def get_relative_uri(self, uri_type, file_name):
        return file_name + '.html'
