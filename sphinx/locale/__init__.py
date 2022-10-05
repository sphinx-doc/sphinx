"""Locale utilities."""

import locale
from gettext import NullTranslations, translation
from os import path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union


class _TranslationProxy:
    """
    Class for proxy strings from gettext translations. This is a helper for the
    lazy_* functions from this module.

    The proxy implementation attempts to be as complete as possible, so that
    the lazy objects should mostly work as expected, for example for sorting.
    """
    __slots__ = ('_func', '_args')

    def __new__(cls, func: Callable[..., str], *args: str) -> '_TranslationProxy':
        if not args:
            # not called with "function" and "arguments", but a plain string
            return str(func)  # type: ignore[return-value]
        return object.__new__(cls)

    def __getnewargs__(self) -> Tuple[str]:
        return (self._func,) + self._args  # type: ignore

    def __init__(self, func: Callable[..., str], *args: str) -> None:
        self._func = func
        self._args = args

    def __str__(self) -> str:
        return str(self._func(*self._args))

    def __dir__(self) -> List[str]:
        return dir(str)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.__str__(), name)

    def __getstate__(self) -> Tuple[Callable[..., str], Tuple[str, ...]]:
        return self._func, self._args

    def __setstate__(self, tup: Tuple[Callable[..., str], Tuple[str]]) -> None:
        self._func, self._args = tup

    def __copy__(self) -> '_TranslationProxy':
        return _TranslationProxy(self._func, *self._args)

    def __repr__(self) -> str:
        try:
            return 'i' + repr(str(self.__str__()))
        except Exception:
            return f'<{self.__class__.__name__} broken>'

    def __add__(self, other: str) -> str:
        return self.__str__() + other

    def __radd__(self, other: str) -> str:
        return other + self.__str__()

    def __mod__(self, other: str) -> str:
        return self.__str__() % other

    def __rmod__(self, other: str) -> str:
        return other % self.__str__()

    def __mul__(self, other: Any) -> str:
        return self.__str__() * other

    def __rmul__(self, other: Any) -> str:
        return other * self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return self.__str__() == other

    def __lt__(self, string):
        return self.__str__() < string

    def __contains__(self, char):
        return char in self.__str__()

    def __len__(self):
        return len(self.__str__())

    def __getitem__(self, index):
        return self.__str__()[index]


translators: Dict[Tuple[str, str], NullTranslations] = {}


def init(
    locale_dirs: List[Optional[str]],
    language: Optional[str],
    catalog: str = 'sphinx',
    namespace: str = 'general',
) -> Tuple[NullTranslations, bool]:
    """Look for message catalogs in `locale_dirs` and *ensure* that there is at
    least a NullTranslations catalog set in `translators`. If called multiple
    times or if several ``.mo`` files are found, their contents are merged
    together (thus making ``init`` reentrant).
    """
    global translators
    translator = translators.get((namespace, catalog))
    # ignore previously failed attempts to find message catalogs
    if translator.__class__ is NullTranslations:
        translator = None
    # the None entry is the system's default locale path
    has_translation = True

    if language and '_' in language:
        # for language having country code (like "de_AT")
        languages: Optional[List[str]] = [language, language.split('_')[0]]
    elif language:
        languages = [language]
    else:
        languages = None

    # loading
    for dir_ in locale_dirs:
        try:
            trans = translation(catalog, localedir=dir_, languages=languages)
            if translator is None:
                translator = trans
            else:
                translator.add_fallback(trans)
        except Exception:
            # Language couldn't be found in the specified path
            pass
    # guarantee translators[(namespace, catalog)] exists
    if translator is None:
        translator = NullTranslations()
        has_translation = False
    translators[(namespace, catalog)] = translator
    return translator, has_translation


def setlocale(category: int, value: Union[str, Iterable[str], None] = None) -> None:
    """Update locale settings.

    This does not throw any exception even if update fails.
    This is workaround for Python's bug.

    For more details:

    * https://github.com/sphinx-doc/sphinx/issues/5724
    * https://bugs.python.org/issue18378#msg215215

    .. note:: Only for internal use.  Please don't call this method from extensions.
              This will be removed in Sphinx 6.0.
    """
    try:
        locale.setlocale(category, value)
    except locale.Error:
        pass


_LOCALE_DIR = path.abspath(path.dirname(__file__))


def init_console(
    locale_dir: str = _LOCALE_DIR,
    catalog: str = 'sphinx',
) -> Tuple[NullTranslations, bool]:
    """Initialize locale for console.

    .. versionadded:: 1.8
    """
    try:
        # encoding is ignored
        language, _ = locale.getlocale(locale.LC_MESSAGES)
    except AttributeError:
        # LC_MESSAGES is not always defined. Fallback to the default language
        # in case it is not.
        language = None
    return init([locale_dir], language, catalog, 'console')


def get_translator(catalog: str = 'sphinx', namespace: str = 'general') -> NullTranslations:
    return translators.get((namespace, catalog), NullTranslations())


def is_translator_registered(catalog: str = 'sphinx', namespace: str = 'general') -> bool:
    return (namespace, catalog) in translators


def _lazy_translate(catalog: str, namespace: str, message: str) -> str:
    """Used instead of _ when creating TranslationProxy, because _ is
    not bound yet at that time.
    """
    translator = get_translator(catalog, namespace)
    return translator.gettext(message)


def get_translation(catalog: str, namespace: str = 'general') -> Callable[[str], str]:
    """Get a translation function based on the *catalog* and *namespace*.

    The extension can use this API to translate the messages on the
    extension::

        import os
        from sphinx.locale import get_translation

        MESSAGE_CATALOG_NAME = 'myextension'  # name of *.pot, *.po and *.mo files
        _ = get_translation(MESSAGE_CATALOG_NAME)
        text = _('Hello Sphinx!')


        def setup(app):
            package_dir = os.path.abspath(os.path.dirname(__file__))
            locale_dir = os.path.join(package_dir, 'locales')
            app.add_message_catalog(MESSAGE_CATALOG_NAME, locale_dir)

    With this code, sphinx searches a message catalog from
    ``${package_dir}/locales/${language}/LC_MESSAGES/myextension.mo``.
    The :confval:`language` is used for the searching.

    .. versionadded:: 1.8
    """
    def gettext(message: str, *args: Any) -> str:
        if not is_translator_registered(catalog, namespace):
            # not initialized yet
            return _TranslationProxy(_lazy_translate, catalog, namespace, message)  # type: ignore  # NOQA
        else:
            translator = get_translator(catalog, namespace)
            if len(args) <= 1:
                return translator.gettext(message)
            else:  # support pluralization
                return translator.ngettext(message, args[0], args[1])

    return gettext


# A shortcut for sphinx-core
#: Translation function for messages on documentation (menu, labels, themes and so on).
#: This function follows :confval:`language` setting.
_ = get_translation('sphinx')
#: Translation function for console messages
#: This function follows locale setting (`LC_ALL`, `LC_MESSAGES` and so on).
__ = get_translation('sphinx', 'console')


# labels
admonitionlabels = {
    'attention': _('Attention'),
    'caution':   _('Caution'),
    'danger':    _('Danger'),
    'error':     _('Error'),
    'hint':      _('Hint'),
    'important': _('Important'),
    'note':      _('Note'),
    'seealso':   _('See also'),
    'tip':       _('Tip'),
    'warning':   _('Warning'),
}

# Moved to sphinx.directives.other (will be overridden later)
versionlabels: Dict[str, str] = {}

# Moved to sphinx.domains.python (will be overridden later)
pairindextypes: Dict[str, str] = {}
