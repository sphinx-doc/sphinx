"""
    sphinx.util.i18n
    ~~~~~~~~~~~~~~~~

    Builder superclass for all builders.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import gettext
import os
import re
import warnings
from collections import namedtuple
from datetime import datetime
from os import path

import babel.dates
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

from sphinx.deprecation import RemovedInSphinx30Warning, RemovedInSphinx40Warning
from sphinx.errors import SphinxError
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.matching import Matcher
from sphinx.util.osutil import SEP, canon_path, relpath


logger = logging.getLogger(__name__)

if False:
    # For type annotation
    from typing import Callable, Generator, List, Set, Tuple  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA

LocaleFileInfoBase = namedtuple('CatalogInfo', 'base_dir,domain,charset')


class CatalogInfo(LocaleFileInfoBase):

    @property
    def po_file(self):
        # type: () -> str
        return self.domain + '.po'

    @property
    def mo_file(self):
        # type: () -> str
        return self.domain + '.mo'

    @property
    def po_path(self):
        # type: () -> str
        return path.join(self.base_dir, self.po_file)

    @property
    def mo_path(self):
        # type: () -> str
        return path.join(self.base_dir, self.mo_file)

    def is_outdated(self):
        # type: () -> bool
        return (
            not path.exists(self.mo_path) or
            path.getmtime(self.mo_path) < path.getmtime(self.po_path))

    def write_mo(self, locale):
        # type: (str) -> None
        with open(self.po_path, encoding=self.charset) as file_po:
            try:
                po = read_po(file_po, locale)
            except Exception as exc:
                logger.warning(__('reading error: %s, %s'), self.po_path, exc)
                return

        with open(self.mo_path, 'wb') as file_mo:
            try:
                write_mo(file_mo, po)
            except Exception as exc:
                logger.warning(__('writing error: %s, %s'), self.mo_path, exc)


class CatalogRepository:
    """A repository for message catalogs."""

    def __init__(self, basedir, locale_dirs, language, encoding):
        # type: (str, List[str], str, str) -> None
        self.basedir = basedir
        self._locale_dirs = locale_dirs
        self.language = language
        self.encoding = encoding

    @property
    def locale_dirs(self):
        # type: () -> Generator[str, None, None]
        if not self.language:
            return

        for locale_dir in self._locale_dirs:
            locale_dir = path.join(self.basedir, locale_dir)
            if path.exists(path.join(locale_dir, self.language, 'LC_MESSAGES')):
                yield locale_dir

    @property
    def pofiles(self):
        # type: () -> Generator[Tuple[str, str], None, None]
        for locale_dir in self.locale_dirs:
            basedir = path.join(locale_dir, self.language, 'LC_MESSAGES')
            for root, dirnames, filenames in os.walk(basedir):
                # skip dot-directories
                for dirname in dirnames:
                    if dirname.startswith('.'):
                        dirnames.remove(dirname)

                for filename in filenames:
                    if filename.endswith('.po'):
                        fullpath = path.join(root, filename)
                        yield basedir, relpath(fullpath, basedir)

    @property
    def catalogs(self):
        # type: () -> Generator[CatalogInfo, None, None]
        for basedir, filename in self.pofiles:
            domain = canon_path(path.splitext(filename)[0])
            yield CatalogInfo(basedir, domain, self.encoding)


def find_catalog(docname, compaction):
    # type: (str, bool) -> str
    warnings.warn('find_catalog() is deprecated.',
                  RemovedInSphinx40Warning, stacklevel=2)
    if compaction:
        ret = docname.split(SEP, 1)[0]
    else:
        ret = docname

    return ret


def docname_to_domain(docname, compation):
    # type: (str, bool) -> str
    """Convert docname to domain for catalogs."""
    if compation:
        return docname.split(SEP, 1)[0]
    else:
        return docname


def find_catalog_files(docname, srcdir, locale_dirs, lang, compaction):
    # type: (str, str, List[str], str, bool) -> List[str]
    warnings.warn('find_catalog_files() is deprecated.',
                  RemovedInSphinx40Warning, stacklevel=2)
    if not(lang and locale_dirs):
        return []

    domain = find_catalog(docname, compaction)
    files = [gettext.find(domain, path.join(srcdir, dir_), [lang])
             for dir_ in locale_dirs]
    files = [relpath(f, srcdir) for f in files if f]
    return files


def find_catalog_source_files(locale_dirs, locale, domains=None, gettext_compact=None,
                              charset='utf-8', force_all=False,
                              excluded=Matcher([])):
    # type: (List[str], str, List[str], bool, str, bool, Matcher) -> Set[CatalogInfo]
    """
    :param list locale_dirs:
       list of path as `['locale_dir1', 'locale_dir2', ...]` to find
       translation catalogs. Each path contains a structure such as
       `<locale>/LC_MESSAGES/domain.po`.
    :param str locale: a language as `'en'`
    :param list domains: list of domain names to get. If empty list or None
       is specified, get all domain names. default is None.
    :param boolean force_all:
       Set True if you want to get all catalogs rather than updated catalogs.
       default is False.
    :return: [CatalogInfo(), ...]
    """
    warnings.warn('find_catalog_source_files() is deprecated.',
                  RemovedInSphinx40Warning, stacklevel=2)
    if gettext_compact is not None:
        warnings.warn('gettext_compact argument for find_catalog_source_files() '
                      'is deprecated.', RemovedInSphinx30Warning, stacklevel=2)

    catalogs = set()  # type: Set[CatalogInfo]

    if not locale:
        return catalogs  # locale is not specified

    for locale_dir in locale_dirs:
        if not locale_dir:
            continue  # skip system locale directory

        base_dir = path.join(locale_dir, locale, 'LC_MESSAGES')

        if not path.exists(base_dir):
            continue  # locale path is not found

        for dirpath, dirnames, filenames in os.walk(base_dir, followlinks=True):
            filenames = [f for f in filenames if f.endswith('.po')]
            for filename in filenames:
                if excluded(path.join(relpath(dirpath, base_dir), filename)):
                    continue
                base = path.splitext(filename)[0]
                domain = relpath(path.join(dirpath, base), base_dir).replace(path.sep, SEP)
                if domains and domain not in domains:
                    continue
                cat = CatalogInfo(base_dir, domain, charset)
                if force_all or cat.is_outdated():
                    catalogs.add(cat)

    return catalogs


# date_format mappings: ustrftime() to bable.dates.format_datetime()
date_format_mappings = {
    '%a':  'EEE',     # Weekday as locale’s abbreviated name.
    '%A':  'EEEE',    # Weekday as locale’s full name.
    '%b':  'MMM',     # Month as locale’s abbreviated name.
    '%B':  'MMMM',    # Month as locale’s full name.
    '%c':  'medium',  # Locale’s appropriate date and time representation.
    '%-d': 'd',       # Day of the month as a decimal number.
    '%d':  'dd',      # Day of the month as a zero-padded decimal number.
    '%-H': 'H',       # Hour (24-hour clock) as a decimal number [0,23].
    '%H':  'HH',      # Hour (24-hour clock) as a zero-padded decimal number [00,23].
    '%-I': 'h',       # Hour (12-hour clock) as a decimal number [1,12].
    '%I':  'hh',      # Hour (12-hour clock) as a zero-padded decimal number [01,12].
    '%-j': 'D',       # Day of the year as a decimal number.
    '%j':  'DDD',     # Day of the year as a zero-padded decimal number.
    '%-m': 'M',       # Month as a decimal number.
    '%m':  'MM',      # Month as a zero-padded decimal number.
    '%-M': 'm',       # Minute as a decimal number [0,59].
    '%M':  'mm',      # Minute as a zero-padded decimal number [00,59].
    '%p':  'a',       # Locale’s equivalent of either AM or PM.
    '%-S': 's',       # Second as a decimal number.
    '%S':  'ss',      # Second as a zero-padded decimal number.
    '%U':  'WW',      # Week number of the year (Sunday as the first day of the week)
                      # as a zero padded decimal number. All days in a new year preceding
                      # the first Sunday are considered to be in week 0.
    '%w':  'e',       # Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.
    '%-W': 'W',       # Week number of the year (Monday as the first day of the week)
                      # as a decimal number. All days in a new year preceding the first
                      # Monday are considered to be in week 0.
    '%W':  'WW',      # Week number of the year (Monday as the first day of the week)
                      # as a zero-padded decimal number.
    '%x':  'medium',  # Locale’s appropriate date representation.
    '%X':  'medium',  # Locale’s appropriate time representation.
    '%y':  'YY',      # Year without century as a zero-padded decimal number.
    '%Y':  'yyyy',    # Year with century as a decimal number.
    '%Z':  'zzzz',    # Time zone name (no characters if no time zone exists).
    '%%':  '%',
}

date_format_re = re.compile('(%s)' % '|'.join(date_format_mappings))


def babel_format_date(date, format, locale, formatter=babel.dates.format_date):
    # type: (datetime, str, str, Callable) -> str
    if locale is None:
        locale = 'en'

    # Check if we have the tzinfo attribute. If not we cannot do any time
    # related formats.
    if not hasattr(date, 'tzinfo'):
        formatter = babel.dates.format_date

    try:
        return formatter(date, format, locale=locale)
    except (ValueError, babel.core.UnknownLocaleError):
        # fallback to English
        return formatter(date, format, locale='en')
    except AttributeError:
        logger.warning(__('Invalid date format. Quote the string by single quote '
                          'if you want to output it directly: %s'), format)
        return format


def format_date(format, date=None, language=None):
    # type: (str, datetime, str) -> str
    if date is None:
        # If time is not specified, try to use $SOURCE_DATE_EPOCH variable
        # See https://wiki.debian.org/ReproducibleBuilds/TimestampsProposal
        source_date_epoch = os.getenv('SOURCE_DATE_EPOCH')
        if source_date_epoch is not None:
            date = datetime.utcfromtimestamp(float(source_date_epoch))
        else:
            date = datetime.now()

    result = []
    tokens = date_format_re.split(format)
    for token in tokens:
        if token in date_format_mappings:
            babel_format = date_format_mappings.get(token, '')

            # Check if we have to use a different babel formatter then
            # format_datetime, because we only want to format a date
            # or a time.
            if token == '%x':
                function = babel.dates.format_date
            elif token == '%X':
                function = babel.dates.format_time
            else:
                function = babel.dates.format_datetime

            result.append(babel_format_date(date, babel_format, locale=language,
                                            formatter=function))
        else:
            result.append(token)

    return "".join(result)


def get_image_filename_for_language(filename, env):
    # type: (str, BuildEnvironment) -> str
    if not env.config.language:
        return filename

    filename_format = env.config.figure_language_filename
    d = dict()
    d['root'], d['ext'] = path.splitext(filename)
    dirname = path.dirname(d['root'])
    if dirname and not dirname.endswith(path.sep):
        dirname += path.sep
    d['path'] = dirname
    d['basename'] = path.basename(d['root'])
    d['language'] = env.config.language
    try:
        return filename_format.format(**d)
    except KeyError as exc:
        raise SphinxError('Invalid figure_language_filename: %r' % exc)


def search_image_for_language(filename, env):
    # type: (str, BuildEnvironment) -> str
    if not env.config.language:
        return filename

    translated = get_image_filename_for_language(filename, env)
    dirname = path.dirname(env.docname)
    if path.exists(path.join(env.srcdir, dirname, translated)):
        return translated
    else:
        return filename
