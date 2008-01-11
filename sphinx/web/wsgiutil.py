# -*- coding: utf-8 -*-
"""
    sphinx.web.wsgiutil
    ~~~~~~~~~~~~~~~~~~~

    To avoid further dependencies this module collects some of the
    classes werkzeug provides and use in other views.

    :copyright: 2007-2008 by Armin Ronacher.
    :license: BSD.
"""
from __future__ import with_statement

import cgi
import urllib
import cPickle as pickle
import tempfile
from os import path
from time import gmtime, time, asctime
from random import random
from Cookie import SimpleCookie
from hashlib import sha1
from datetime import datetime
from cStringIO import StringIO

from .util import lazy_property
from ..util.json import dump_json


HTTP_STATUS_CODES = {
    100:    'CONTINUE',
    101:    'SWITCHING PROTOCOLS',
    102:    'PROCESSING',
    200:    'OK',
    201:    'CREATED',
    202:    'ACCEPTED',
    203:    'NON-AUTHORITATIVE INFORMATION',
    204:    'NO CONTENT',
    205:    'RESET CONTENT',
    206:    'PARTIAL CONTENT',
    207:    'MULTI STATUS',
    300:    'MULTIPLE CHOICES',
    301:    'MOVED PERMANENTLY',
    302:    'FOUND',
    303:    'SEE OTHER',
    304:    'NOT MODIFIED',
    305:    'USE PROXY',
    306:    'RESERVED',
    307:    'TEMPORARY REDIRECT',
    400:    'BAD REQUEST',
    401:    'UNAUTHORIZED',
    402:    'PAYMENT REQUIRED',
    403:    'FORBIDDEN',
    404:    'NOT FOUND',
    405:    'METHOD NOT ALLOWED',
    406:    'NOT ACCEPTABLE',
    407:    'PROXY AUTHENTICATION REQUIRED',
    408:    'REQUEST TIMEOUT',
    409:    'CONFLICT',
    410:    'GONE',
    411:    'LENGTH REQUIRED',
    412:    'PRECONDITION FAILED',
    413:    'REQUEST ENTITY TOO LARGE',
    414:    'REQUEST-URI TOO LONG',
    415:    'UNSUPPORTED MEDIA TYPE',
    416:    'REQUESTED RANGE NOT SATISFIABLE',
    417:    'EXPECTATION FAILED',
    500:    'INTERNAL SERVER ERROR',
    501:    'NOT IMPLEMENTED',
    502:    'BAD GATEWAY',
    503:    'SERVICE UNAVAILABLE',
    504:    'GATEWAY TIMEOUT',
    505:    'HTTP VERSION NOT SUPPORTED',
    506:    'VARIANT ALSO VARIES',
    507:    'INSUFFICIENT STORAGE',
    510:    'NOT EXTENDED'
}

SID_COOKIE_NAME = 'python_doc_sid'


# ------------------------------------------------------------------------------
# Support for HTTP parameter parsing, requests and responses


class _StorageHelper(cgi.FieldStorage):
    """
    Helper class used by `Request` to parse submitted file and
    form data. Don't use this class directly.
    """

    FieldStorageClass = cgi.FieldStorage

    def __init__(self, environ, get_stream):
        cgi.FieldStorage.__init__(self,
            fp=environ['wsgi.input'],
            environ={
                'REQUEST_METHOD':   environ['REQUEST_METHOD'],
                'CONTENT_TYPE':     environ['CONTENT_TYPE'],
                'CONTENT_LENGTH':   environ['CONTENT_LENGTH']
            },
            keep_blank_values=True
        )
        self.get_stream = get_stream

    def make_file(self, binary=None):
        return self.get_stream()


class MultiDict(dict):
    """
    A dict that takes a list of multiple values as only argument
    in order to store multiple values per key.
    """

    def __init__(self, mapping=()):
        if isinstance(mapping, MultiDict):
            dict.__init__(self, mapping.lists())
        elif isinstance(mapping, dict):
            tmp = {}
            for key, value in mapping:
                tmp[key] = [value]
            dict.__init__(self, tmp)
        else:
            tmp = {}
            for key, value in mapping:
                tmp.setdefault(key, []).append(value)
            dict.__init__(self, tmp)

    def __getitem__(self, key):
        """
        Return the first data value for this key;
        raises KeyError if not found.
        """
        return dict.__getitem__(self, key)[0]

    def __setitem__(self, key, value):
        """Set an item as list."""
        dict.__setitem__(self, key, [value])

    def get(self, key, default=None):
        """Return the default value if the requested data doesn't exist"""
        try:
            return self[key]
        except KeyError:
            return default

    def getlist(self, key):
        """Return an empty list if the requested data doesn't exist"""
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return []

    def setlist(self, key, new_list):
        """Set new values for an key."""
        dict.__setitem__(self, key, list(new_list))

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        else:
            default = self[key]
        return default

    def setlistdefault(self, key, default_list=()):
        if key not in self:
            default_list = list(default_list)
            dict.__setitem__(self, key, default_list)
        else:
            default_list = self.getlist(key)
        return default_list

    def items(self):
        """
        Return a list of (key, value) pairs, where value is the last item in
        the list associated with the key.
        """
        return [(key, self[key]) for key in self.iterkeys()]

    lists = dict.items

    def values(self):
        """Returns a list of the last value on every key list."""
        return [self[key] for key in self.iterkeys()]

    listvalues = dict.values

    def iteritems(self):
        for key, values in dict.iteritems(self):
            yield key, values[0]

    iterlists = dict.iteritems

    def itervalues(self):
        for values in dict.itervalues(self):
            yield values[0]

    iterlistvalues = dict.itervalues

    def copy(self):
        """Return a shallow copy of this object."""
        return self.__class__(self)

    def update(self, other_dict):
        """update() extends rather than replaces existing key lists."""
        if isinstance(other_dict, MultiDict):
            for key, value_list in other_dict.iterlists():
                self.setlistdefault(key, []).extend(value_list)
        elif isinstance(other_dict, dict):
            for key, value in other_dict.items():
                self.setlistdefault(key, []).append(value)
        else:
            for key, value in other_dict:
                self.setlistdefault(key, []).append(value)

    def pop(self, *args):
        """Pop the first item for a list on the dict."""
        return dict.pop(self, *args)[0]

    def popitem(self):
        """Pop an item from the dict."""
        item = dict.popitem(self)
        return (item[0], item[1][0])

    poplist = dict.pop
    popitemlist = dict.popitem

    def __repr__(self):
        tmp = []
        for key, values in self.iterlists():
            for value in values:
                tmp.append((key, value))
        return '%s(%r)' % (self.__class__.__name__, tmp)


class Headers(object):
    """
    An object that stores some headers.
    """

    def __init__(self, defaults=None):
        self._list = []
        if isinstance(defaults, dict):
            for key, value in defaults.iteritems():
                if isinstance(value, (tuple, list)):
                    for v in value:
                        self._list.append((key, v))
                else:
                    self._list.append((key, value))
        elif defaults is not None:
            for key, value in defaults:
                self._list.append((key, value))

    def __getitem__(self, key):
        ikey = key.lower()
        for k, v in self._list:
            if k.lower() == ikey:
                return v
        raise KeyError(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def getlist(self, key):
        ikey = key.lower()
        result = []
        for k, v in self._list:
            if k.lower() == ikey:
                result.append((k, v))
        return result

    def setlist(self, key, values):
        del self[key]
        self.addlist(key, values)

    def addlist(self, key, values):
        self._list.extend(values)

    def lists(self, lowercased=False):
        if not lowercased:
            return self._list[:]
        return [(x.lower(), y) for x, y in self._list]

    def iterlists(self, lowercased=False):
        for key, value in self._list:
            if lowercased:
                key = key.lower()
            yield key, value

    def iterkeys(self):
        for key, _ in self.iterlists():
            yield key

    def itervalues(self):
        for _, value in self.iterlists():
            yield value

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def __delitem__(self, key):
        key = key.lower()
        new = []
        for k, v in self._list:
            if k != key:
                new.append((k, v))
        self._list[:] = new

    remove = __delitem__

    def __contains__(self, key):
        key = key.lower()
        for k, v in self._list:
            if k.lower() == key:
                return True
        return False

    has_key = __contains__

    def __iter__(self):
        return iter(self._list)

    def add(self, key, value):
        """add a new header tuple to the list"""
        self._list.append((key, value))

    def clear(self):
        """clears all headers"""
        del self._list[:]

    def set(self, key, value):
        """remove all header tuples for key and add
        a new one
        """
        del self[key]
        self.add(key, value)

    __setitem__ = set

    def to_list(self, charset):
        """Create a str only list of the headers."""
        result = []
        for k, v in self:
            if isinstance(v, unicode):
                v = v.encode(charset)
            else:
                v = str(v)
            result.append((k, v))
        return result

    def copy(self):
        return self.__class__(self._list)

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self._list
        )


class Session(dict):

    def __init__(self, sid):
        self.sid = sid
        if sid is not None:
            if path.exists(self.filename):
                with file(self.filename, 'rb') as f:
                    self.update(pickle.load(f))
        self._orig = dict(self)

    @property
    def filename(self):
        if self.sid is not None:
            return path.join(tempfile.gettempdir(), '__pydoc_sess' + self.sid)

    @property
    def worth_saving(self):
        return self != self._orig

    def save(self):
        if self.sid is None:
            self.sid = sha1('%s|%s' % (time(), random())).hexdigest()
        with file(self.filename, 'wb') as f:
            pickle.dump(dict(self), f, pickle.HIGHEST_PROTOCOL)
        self._orig = dict(self)


class Request(object):
    charset = 'utf-8'

    def __init__(self, environ):
        self.environ = environ
        self.environ['werkzeug.request'] = self
        self.session = Session(self.cookies.get(SID_COOKIE_NAME))
        self.user = self.session.get('user')

    def login(self, user):
        self.user = self.session['user'] = user

    def logout(self):
        self.user = None
        self.session.pop('user', None)

    def _get_file_stream(self):
        """Called to get a stream for the file upload.

        This must provide a file-like class with `read()`, `readline()`
        and `seek()` methods that is both writeable and readable."""
        return tempfile.TemporaryFile('w+b')

    def _load_post_data(self):
        """Method used internally to retrieve submitted data."""
        self._data = ''
        post = []
        files = []
        if self.environ['REQUEST_METHOD'] in ('POST', 'PUT'):
            storage = _StorageHelper(self.environ, self._get_file_stream)
            for key in storage.keys():
                values = storage[key]
                if not isinstance(values, list):
                    values = [values]
                for item in values:
                    if getattr(item, 'filename', None) is not None:
                        fn = item.filename.decode(self.charset, 'ignore')
                        # fix stupid IE bug
                        if len(fn) > 1 and fn[1] == ':' and '\\' in fn:
                            fn = fn[fn.index('\\') + 1:]
                        files.append((key, FileStorage(key, fn, item.type,
                                      item.length, item.file)))
                    else:
                        post.append((key, item.value.decode(self.charset,
                                                            'ignore')))
        self._form = MultiDict(post)
        self._files = MultiDict(files)

    def read(self, *args):
        if not hasattr(self, '_buffered_stream'):
            self._buffered_stream = StringIO(self.data)
        return self._buffered_stream.read(*args)

    def readline(self, *args):
        if not hasattr(self, '_buffered_stream'):
            self._buffered_stream = StringIO(self.data)
        return self._buffered_stream.readline(*args)

    def make_external_url(self, path):
        url = self.environ['wsgi.url_scheme'] + '://'
        if 'HTTP_HOST' in self.environ:
            url += self.environ['HTTP_HOST']
        else:
            url += self.environ['SERVER_NAME']
            if (self.environ['wsgi.url_scheme'], self.environ['SERVER_PORT']) not \
               in (('https', '443'), ('http', '80')):
                url += ':' + self.environ['SERVER_PORT']

        url += urllib.quote(self.environ.get('SCRIPT_INFO', '').rstrip('/'))
        if not path.startswith('/'):
            path = '/' + path
        return url + path

    def args(self):
        """URL parameters"""
        items = []
        qs = self.environ.get('QUERY_STRING', '')
        for key, values in cgi.parse_qs(qs, True).iteritems():
            for value in values:
                value = value.decode(self.charset, 'ignore')
                items.append((key, value))
        return MultiDict(items)
    args = lazy_property(args)

    def data(self):
        """raw value of input stream."""
        if not hasattr(self, '_data'):
            self._load_post_data()
        return self._data
    data = lazy_property(data)

    def form(self):
        """form parameters."""
        if not hasattr(self, '_form'):
            self._load_post_data()
        return self._form
    form = lazy_property(form)

    def files(self):
        """File uploads."""
        if not hasattr(self, '_files'):
            self._load_post_data()
        return self._files
    files = lazy_property(files)

    def cookies(self):
        """Stored Cookies."""
        cookie = SimpleCookie()
        cookie.load(self.environ.get('HTTP_COOKIE', ''))
        result = {}
        for key, value in cookie.iteritems():
            result[key] = value.value.decode(self.charset, 'ignore')
        return result
    cookies = lazy_property(cookies)

    def method(self):
        """Request method."""
        return self.environ['REQUEST_METHOD']
    method = property(method, doc=method.__doc__)

    def path(self):
        """Requested path."""
        path = '/' + (self.environ.get('PATH_INFO') or '').lstrip('/')
        path = path.decode(self.charset, self.charset)
        parts = path.replace('+', ' ').split('/')
        return u'/'.join(p for p in parts if p != '..')
    path = lazy_property(path)


class Response(object):
    charset = 'utf-8'
    default_mimetype = 'text/html'

    def __init__(self, response=None, headers=None, status=200, mimetype=None):
        if response is None:
            self.response = []
        elif isinstance(response, basestring):
            self.response = [response]
        else:
            self.response = iter(response)
        if not headers:
            self.headers = Headers()
        elif isinstance(headers, Headers):
            self.headers = headers
        else:
            self.headers = Headers(headers)
        if mimetype is None and 'Content-Type' not in self.headers:
            mimetype = self.default_mimetype
        if mimetype is not None:
            if 'charset=' not in mimetype and mimetype.startswith('text/'):
                mimetype += '; charset=' + self.charset
            self.headers['Content-Type'] = mimetype
        self.status = status
        self._cookies = None

    def write(self, value):
        if not isinstance(self.response, list):
            raise RuntimeError('cannot write to streaming response')
        self.write = self.response.append
        self.response.append(value)

    def set_cookie(self, key, value='', max_age=None, expires=None,
                   path='/', domain=None, secure=None):
        if self._cookies is None:
            self._cookies = SimpleCookie()
        if isinstance(value, unicode):
            value = value.encode(self.charset)
        self._cookies[key] = value
        if max_age is not None:
            self._cookies[key]['max-age'] = max_age
        if expires is not None:
            if isinstance(expires, basestring):
                self._cookies[key]['expires'] = expires
                expires = None
            elif isinstance(expires, datetime):
                expires = expires.utctimetuple()
            elif not isinstance(expires, (int, long)):
                expires = gmtime(expires)
            else:
                raise ValueError('datetime or integer required')
            month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                     'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][expires.tm_mon - 1]
            day = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                   'Friday', 'Saturday', 'Sunday'][expires.tm_wday]
            date = '%02d-%s-%s' % (
                expires.tm_mday, month, str(expires.tm_year)[-2:]
            )
            d = '%s, %s %02d:%02d:%02d GMT' % (day, date, expires.tm_hour,
                                               expires.tm_min, expires.tm_sec)
            self._cookies[key]['expires'] = d
        if path is not None:
            self._cookies[key]['path'] = path
        if domain is not None:
            self._cookies[key]['domain'] = domain
        if secure is not None:
            self._cookies[key]['secure'] = secure

    def delete_cookie(self, key):
        if self._cookies is None:
            self._cookies = SimpleCookie()
        if key not in self._cookies:
            self._cookies[key] = ''
        self._cookies[key]['max-age'] = 0

    def __call__(self, environ, start_response):
        req = environ['werkzeug.request']
        if req.session.worth_saving:
            req.session.save()
            self.set_cookie(SID_COOKIE_NAME, req.session.sid)

        headers = self.headers.to_list(self.charset)
        if self._cookies is not None:
            for morsel in self._cookies.values():
                headers.append(('Set-Cookie', morsel.output(header='')))
        status = '%d %s' % (self.status, HTTP_STATUS_CODES[self.status])

        charset = self.charset or 'ascii'
        start_response(status, headers)
        for item in self.response:
            if isinstance(item, unicode):
                yield item.encode(charset)
            else:
                yield str(item)

def get_base_uri(environ):
    url = environ['wsgi.url_scheme'] + '://'
    if 'HTTP_HOST' in environ:
        url += environ['HTTP_HOST']
    else:
        url += environ['SERVER_NAME']
        if (environ['wsgi.url_scheme'], environ['SERVER_PORT']) not \
               in (('https', '443'), ('http', '80')):
            url += ':' + environ['SERVER_PORT']
    url += urllib.quote(environ.get('SCRIPT_INFO', '').rstrip('/'))
    return url


class RedirectResponse(Response):

    def __init__(self, target_url, code=302):
        if not target_url.startswith('/'):
            target_url = '/' + target_url
        self.target_url = target_url
        super(RedirectResponse, self).__init__('Moved...', status=code)

    def __call__(self, environ, start_response):
        url = get_base_uri(environ) + self.target_url
        self.headers['Location'] = url
        return super(RedirectResponse, self).__call__(environ, start_response)


class JSONResponse(Response):

    def __init__(self, data):
        assert not isinstance(data, list), 'list unsafe for json dumping'
        super(JSONResponse, self).__init__(dump_json(data), mimetype='text/javascript')


class SharedDataMiddleware(object):
    """
    Redirects calls to an folder with static data.
    """

    def __init__(self, app, exports):
        self.app = app
        self.exports = exports
        self.cache = {}

    def serve_file(self, filename, start_response):
        from mimetypes import guess_type
        guessed_type = guess_type(filename)
        mime_type = guessed_type[0] or 'text/plain'
        expiry = time() + 3600 # one hour
        expiry = asctime(gmtime(expiry))
        start_response('200 OK', [('Content-Type', mime_type),
                                  ('Cache-Control', 'public'),
                                  ('Expires', expiry)])
        with open(filename, 'rb') as f:
            return [f.read()]

    def __call__(self, environ, start_response):
        p = environ.get('PATH_INFO', '')
        if p in self.cache:
            return self.serve_file(self.cache[p], start_response)
        for search_path, file_path in self.exports.iteritems():
            if not search_path.endswith('/'):
                search_path += '/'
            if p.startswith(search_path):
                real_path = path.join(file_path, p[len(search_path):])
                if path.exists(real_path) and path.isfile(real_path):
                    self.cache[p] = real_path
                    return self.serve_file(real_path, start_response)
        return self.app(environ, start_response)


class NotFound(Exception):
    """
    Raise to display the 404 error page.
    """

    def __init__(self, show_keyword_matches=False):
        self.show_keyword_matches = show_keyword_matches
        Exception.__init__(self, show_keyword_matches)
