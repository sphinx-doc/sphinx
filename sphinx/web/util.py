# -*- coding: utf-8 -*-
"""
    sphinx.web.util
    ~~~~~~~~~~~~~~~

    Miscellaneous utilities.

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""
from __future__ import with_statement

import re
from os import path

from ..util import relative_uri
from .._jinja import Environment, FileSystemLoader


def get_target_uri(source_filename):
    """Get the web-URI for a given reST file name."""
    if source_filename == 'index.rst':
        return ''
    if source_filename.endswith('/index.rst'):
        return source_filename[:-9] # up to /
    return source_filename[:-4] + '/'


# ------------------------------------------------------------------------------
# Setup the templating environment

templates_path = path.join(path.dirname(__file__), '..', 'templates')
jinja_env = Environment(loader=FileSystemLoader(templates_path,
                                                use_memcache=True),
                        friendly_traceback=True)

def do_datetime_format():
    def wrapped(env, ctx, value):
        return value.strftime('%a, %d %b %Y %H:%M')
    return wrapped

jinja_env.filters['datetimeformat'] = do_datetime_format


_striptags_re = re.compile(r'(<!--.*?-->|<[^>]+>)')

def striptags(text):
    return ' '.join(_striptags_re.sub('', text).split())


def render_template(req, template_name, *contexts):
    context = {}
    for ctx in contexts:
        context.update(ctx)
    tmpl = jinja_env.get_template(template_name)

    path = req.path.lstrip('/')
    if not path[-1:] == '/':
        path += '/'
    def relative_path_to(otheruri, resource=False):
        if not resource:
            otheruri = get_target_uri(otheruri)
        return relative_uri(path, otheruri)
    context['pathto'] = relative_path_to

    # add it here a second time for templates that don't
    # get the builder information from the environment (such as search)
    context['builder'] = 'web'
    context['req'] = req

    return tmpl.render(context)


def render_simple_template(template_name, context):
    tmpl = jinja_env.get_template(template_name)
    return tmpl.render(context)


class lazy_property(object):
    """
    Descriptor implementing a "lazy property", i.e. the function
    calculating the property value is called only once.
    """

    def __init__(self, func, name=None, doc=None):
        self._func = func
        self._name = name or func.func_name
        self.__doc__ = doc or func.__doc__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = self._func(obj)
        setattr(obj, self._name, value)
        return value


class blackhole_dict(dict):
    def __setitem__(self, key, value):
        pass
