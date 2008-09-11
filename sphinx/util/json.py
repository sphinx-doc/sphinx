# -*- coding: utf-8 -*-
"""
    sphinx.util.json
    ~~~~~~~~~~~~~~~~

    This module imports JSON functions from various locations.

    :copyright: 2008 by Armin Ronacher.
    :license: BSD.
"""

# if no simplejson is available this module can not load json files.
can_load = True

# unset __name__ for a moment so that the import goes straight into
# the stdlib for python 2.4.
_old_name = __name__
del __name__

try:
    from simplejson import dumps, dump, loads, load
except ImportError:
    try:
        from json import dumps, dump, loads, load
    except ImportError:
        from sphinx.util._json import dumps, dump
        def _dummy(x):
            raise NotImplementedError('simplejson unavailable, can\'t load')
        load = loads = _dummy
        can_load = False
        del _dummy

__name__ = _old_name
del _old_name
