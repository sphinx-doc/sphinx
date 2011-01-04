# -*- coding: utf-8 -*-
"""
    sphinx.locale
    ~~~~~~~~~~~~~

    Locale utilities.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import gettext
import UserString


class _TranslationProxy(UserString.UserString, object):
    """Class for proxy strings from gettext translations.  This is a helper
    for the lazy_* functions from this module.

    The proxy implementation attempts to be as complete as possible, so that
    the lazy objects should mostly work as expected, for example for sorting.

    This inherits from UserString because some docutils versions use UserString
    for their Text nodes, which then checks its argument for being either a
    basestring or UserString, otherwise calls str() -- not unicode() -- on it.
    This also inherits from object to make the __new__ method work.
    """
    __slots__ = ('_func', '_args')

    def __new__(cls, func, *args):
        if not args:
            # not called with "function" and "arguments", but a plain string
            return unicode(func)
        return object.__new__(cls)

    def __getnewargs__(self):
        return (self._func,) + self._args

    def __init__(self, func, *args):
        self._func = func
        self._args = args

    data = property(lambda x: x._func(*x._args))

    # replace function from UserString; it instantiates a self.__class__
    # for the encoding result

    def encode(self, encoding=None, errors=None):
        if encoding:
            if errors:
                return self.data.encode(encoding, errors)
            else:
                return self.data.encode(encoding)
        else:
            return self.data.encode()

    def __contains__(self, key):
        return key in self.data

    def __nonzero__(self):
        return bool(self.data)

    def __dir__(self):
        return dir(unicode)

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return str(self.data)

    def __unicode__(self):
        return unicode(self.data)

    def __add__(self, other):
        return self.data + other

    def __radd__(self, other):
        return other + self.data

    def __mod__(self, other):
        return self.data % other

    def __rmod__(self, other):
        return other % self.data

    def __mul__(self, other):
        return self.data * other

    def __rmul__(self, other):
        return other * self.data

    def __lt__(self, other):
        return self.data < other

    def __le__(self, other):
        return self.data <= other

    def __eq__(self, other):
        return self.data == other

    def __ne__(self, other):
        return self.data != other

    def __gt__(self, other):
        return self.data > other

    def __ge__(self, other):
        return self.data >= other

    def __getattr__(self, name):
        if name == '__members__':
            return self.__dir__()
        return getattr(self.data, name)

    def __getstate__(self):
        return self._func, self._args

    def __setstate__(self, tup):
        self._func, self._args = tup

    def __getitem__(self, key):
        return self.data[key]

    def __copy__(self):
        return self

    def __repr__(self):
        try:
            return 'i' + repr(unicode(self.data))
        except:
            return '<%s broken>' % self.__class__.__name__

def mygettext(string):
    """Used instead of _ when creating TranslationProxies, because _ is
    not bound yet at that time."""
    return _(string)

def lazy_gettext(string):
    """A lazy version of `gettext`."""
    #if isinstance(string, _TranslationProxy):
    #    return string
    return _TranslationProxy(mygettext, string)

l_ = lazy_gettext


admonitionlabels = {
    'attention': l_('Attention'),
    'caution':   l_('Caution'),
    'danger':    l_('Danger'),
    'error':     l_('Error'),
    'hint':      l_('Hint'),
    'important': l_('Important'),
    'note':      l_('Note'),
    'seealso':   l_('See Also'),
    'tip':       l_('Tip'),
    'warning':   l_('Warning'),
}

versionlabels = {
    'versionadded':   l_('New in version %s'),
    'versionchanged': l_('Changed in version %s'),
    'deprecated':     l_('Deprecated since version %s'),
}

pairindextypes = {
    'module':    l_('module'),
    'keyword':   l_('keyword'),
    'operator':  l_('operator'),
    'object':    l_('object'),
    'exception': l_('exception'),
    'statement': l_('statement'),
    'builtin':   l_('built-in function'),
}

translator = None

def _(message):
    return translator.ugettext(message)

def init(locale_dirs, language):
    global translator
    # the None entry is the system's default locale path
    has_translation = True
    for dir_ in locale_dirs:
        try:
            trans = gettext.translation('sphinx', localedir=dir_,
                    languages=[language])
            if translator is None:
                translator = trans
            else:
                translator._catalog.update(trans._catalog)
        except Exception:
            # Language couldn't be found in the specified path
            pass
    if translator is None:
        translator = gettext.NullTranslations()
        has_translation = False
    return translator, has_translation
