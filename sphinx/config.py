"""Build configuration file handling."""

from __future__ import annotations

import sys
import time
import traceback
import types
import warnings
from os import getenv, path
from typing import TYPE_CHECKING, Any, Literal, NamedTuple

from sphinx.deprecation import RemovedInSphinx90Warning
from sphinx.errors import ConfigError, ExtensionError
from sphinx.locale import _, __
from sphinx.util import logging
from sphinx.util.osutil import fs_encoding
from sphinx.util.typing import NoneType

if sys.version_info >= (3, 11):
    from contextlib import chdir
else:
    from sphinx.util.osutil import _chdir as chdir

if TYPE_CHECKING:
    import os
    from collections.abc import Iterator, Sequence

    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment
    from sphinx.util.tags import Tags
    from sphinx.util.typing import _ExtensionSetupFunc

logger = logging.getLogger(__name__)

_ConfigRebuild = Literal['', 'env', 'epub', 'gettext', 'html']

CONFIG_FILENAME = 'conf.py'
UNSERIALIZABLE_TYPES = (type, types.ModuleType, types.FunctionType)


class ConfigValue(NamedTuple):
    name: str
    value: Any
    rebuild: _ConfigRebuild


def is_serializable(obj: Any) -> bool:
    """Check if object is serializable or not."""
    if isinstance(obj, UNSERIALIZABLE_TYPES):
        return False
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if not is_serializable(key) or not is_serializable(value):
                return False
    elif isinstance(obj, (list, tuple, set)):
        return all(map(is_serializable, obj))

    return True


class ENUM:
    """Represents the candidates which a config value should be one of.

    Example:
        app.add_config_value('latex_show_urls', 'no', None, ENUM('no', 'footnote', 'inline'))
    """
    def __init__(self, *candidates: str | bool | None) -> None:
        self.candidates = candidates

    def match(self, value: str | list | tuple) -> bool:
        if isinstance(value, (list, tuple)):
            return all(item in self.candidates for item in value)
        else:
            return value in self.candidates


class _Opt:
    __slots__ = 'default', 'rebuild', 'valid_types'

    default: Any
    rebuild: _ConfigRebuild
    valid_types: Sequence[type] | ENUM | Any

    def __init__(
        self,
        default: Any,
        rebuild: _ConfigRebuild,
        valid_types: Sequence[type] | ENUM | Any,
    ) -> None:
        """Configuration option type for Sphinx.

        The type is intended to be immutable; changing the field values
        is an unsupported action.
        No validation is performed on the values, though consumers will
        likely expect them to be of the types advertised.
        The old tuple-based interface will be removed in Sphinx 9.
        """
        super().__setattr__('default', default)
        super().__setattr__('rebuild', rebuild)
        super().__setattr__('valid_types', valid_types)

    def __repr__(self):
        return (
            f'{self.__class__.__qualname__}('
            f'default={self.default!r}, '
            f'rebuild={self.rebuild!r}, '
            f'valid_types={self.valid_types!r})'
        )

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            self_tpl = (self.default, self.rebuild, self.valid_types)
            other_tpl = (other.default, other.rebuild, other.valid_types)
            return self_tpl == other_tpl
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            self_tpl = (self.default, self.rebuild, self.valid_types)
            other_tpl = (other.default, other.rebuild, other.valid_types)
            return self_tpl > other_tpl
        return NotImplemented

    def __hash__(self):
        return hash((self.default, self.rebuild, self.valid_types))

    def __setattr__(self, key, value):
        if key in {'default', 'rebuild', 'valid_types'}:
            msg = f'{self.__class__.__name__!r} object does not support assignment to {key!r}'
            raise TypeError(msg)
        super().__setattr__(key, value)

    def __delattr__(self, key):
        if key in {'default', 'rebuild', 'valid_types'}:
            msg = f'{self.__class__.__name__!r} object does not support deletion of {key!r}'
            raise TypeError(msg)
        super().__delattr__(key)

    def __getstate__(self):
        return self.default, self.rebuild, self.valid_types

    def __setstate__(self, state):
        default, rebuild, valid_types = state
        super().__setattr__('default', default)
        super().__setattr__('rebuild', rebuild)
        super().__setattr__('valid_types', valid_types)

    def __getitem__(self, item):
        warnings.warn(
            f'The {self.__class__.__name__!r} object tuple interface is deprecated, '
            "use attribute access instead for 'default', 'rebuild', and 'valid_types'.",
            RemovedInSphinx90Warning, stacklevel=2)
        return (self.default, self.rebuild, self.valid_types)[item]


class Config:
    r"""Configuration file abstraction.

    The config object makes the values of all config values available as
    attributes.

    It is exposed via the :py:class:`~sphinx.application.Sphinx`\ ``.config``
    and :py:class:`sphinx.environment.BuildEnvironment`\ ``.config`` attributes.
    For example, to get the value of :confval:`language`, use either
    ``app.config.language`` or ``env.config.language``.
    """

    # The values are:
    # 1. Default
    # 2. What needs to be rebuilt if changed
    # 3. Valid types

    # If you add a value here, remember to include it in the docs!

    config_values: dict[str, _Opt] = {
        # general options
        'project': _Opt('Python', 'env', []),
        'author': _Opt('unknown', 'env', []),
        'project_copyright': _Opt('', 'html', [str, tuple, list]),
        'copyright': _Opt(lambda c: c.project_copyright, 'html', [str, tuple, list]),
        'version': _Opt('', 'env', []),
        'release': _Opt('', 'env', []),
        'today': _Opt('', 'env', []),
        # the real default is locale-dependent
        'today_fmt': _Opt(None, 'env', [str]),

        'language': _Opt('en', 'env', [str]),
        'locale_dirs': _Opt(['locales'], 'env', []),
        'figure_language_filename': _Opt('{root}.{language}{ext}', 'env', [str]),
        'gettext_allow_fuzzy_translations': _Opt(False, 'gettext', []),
        'translation_progress_classes': _Opt(
            False, 'env', ENUM(True, False, 'translated', 'untranslated')),

        'master_doc': _Opt('index', 'env', []),
        'root_doc': _Opt(lambda config: config.master_doc, 'env', []),
        'source_suffix': _Opt({'.rst': 'restructuredtext'}, 'env', Any),
        'source_encoding': _Opt('utf-8-sig', 'env', []),
        'exclude_patterns': _Opt([], 'env', [str]),
        'include_patterns': _Opt(["**"], 'env', [str]),
        'default_role': _Opt(None, 'env', [str]),
        'add_function_parentheses': _Opt(True, 'env', []),
        'add_module_names': _Opt(True, 'env', []),
        'toc_object_entries': _Opt(True, 'env', [bool]),
        'toc_object_entries_show_parents': _Opt(
            'domain', 'env', ENUM('domain', 'all', 'hide')),
        'trim_footnote_reference_space': _Opt(False, 'env', []),
        'show_authors': _Opt(False, 'env', []),
        'pygments_style': _Opt(None, 'html', [str]),
        'highlight_language': _Opt('default', 'env', []),
        'highlight_options': _Opt({}, 'env', []),
        'templates_path': _Opt([], 'html', []),
        'template_bridge': _Opt(None, 'html', [str]),
        'keep_warnings': _Opt(False, 'env', []),
        'suppress_warnings': _Opt([], 'env', []),
        'modindex_common_prefix': _Opt([], 'html', []),
        'rst_epilog': _Opt(None, 'env', [str]),
        'rst_prolog': _Opt(None, 'env', [str]),
        'trim_doctest_flags': _Opt(True, 'env', []),
        'primary_domain': _Opt('py', 'env', [NoneType]),
        'needs_sphinx': _Opt(None, '', [str]),
        'needs_extensions': _Opt({}, '', []),
        'manpages_url': _Opt(None, 'env', []),
        'nitpicky': _Opt(False, '', []),
        'nitpick_ignore': _Opt([], '', [set, list, tuple]),
        'nitpick_ignore_regex': _Opt([], '', [set, list, tuple]),
        'numfig': _Opt(False, 'env', []),
        'numfig_secnum_depth': _Opt(1, 'env', []),
        'numfig_format': _Opt({}, 'env', []),  # will be initialized in init_numfig_format()
        'maximum_signature_line_length': _Opt(None, 'env', {int, None}),
        'math_number_all': _Opt(False, 'env', []),
        'math_eqref_format': _Opt(None, 'env', [str]),
        'math_numfig': _Opt(True, 'env', []),
        'tls_verify': _Opt(True, 'env', []),
        'tls_cacerts': _Opt(None, 'env', []),
        'user_agent': _Opt(None, 'env', [str]),
        'smartquotes': _Opt(True, 'env', []),
        'smartquotes_action': _Opt('qDe', 'env', []),
        'smartquotes_excludes': _Opt(
            {'languages': ['ja'], 'builders': ['man', 'text']}, 'env', []),
        'option_emphasise_placeholders': _Opt(False, 'env', []),
    }

    def __init__(self, config: dict[str, Any] | None = None,
                 overrides: dict[str, Any] | None = None) -> None:
        raw_config: dict[str, Any] = config or {}
        self.overrides = dict(overrides) if overrides is not None else {}
        self.values = Config.config_values.copy()
        self._raw_config = raw_config
        self.setup: _ExtensionSetupFunc | None = raw_config.get('setup')

        if 'extensions' in self.overrides:
            extensions = self.overrides.pop('extensions')
            if isinstance(extensions, str):
                raw_config['extensions'] = extensions.split(',')
            else:
                raw_config['extensions'] = extensions
        self.extensions: list[str] = raw_config.get('extensions', [])

    @classmethod
    def read(cls, confdir: str | os.PathLike[str], overrides: dict | None = None,
             tags: Tags | None = None) -> Config:
        """Create a Config object from configuration file."""
        filename = path.join(confdir, CONFIG_FILENAME)
        if not path.isfile(filename):
            raise ConfigError(__("config directory doesn't contain a conf.py file (%s)") %
                              confdir)
        namespace = eval_config_file(filename, tags)

        # Note: Old sphinx projects have been configured as "language = None" because
        #       sphinx-quickstart previously generated this by default.
        #       To keep compatibility, they should be fallback to 'en' for a while
        #       (This conversion should not be removed before 2025-01-01).
        if namespace.get("language", ...) is None:
            logger.warning(__("Invalid configuration value found: 'language = None'. "
                              "Update your configuration to a valid language code. "
                              "Falling back to 'en' (English)."))
            namespace["language"] = "en"

        return cls(namespace, overrides)

    def convert_overrides(self, name: str, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        else:
            opt = self.values[name]
            default = opt.default
            valid_types = opt.valid_types
            if valid_types == Any:
                return value
            elif valid_types == {bool, str}:
                if value == '0':
                    # given falsy string from command line option
                    return False
                elif value == '1':
                    return True
                else:
                    return value
            elif type(default) is bool or valid_types == [bool]:
                if value == '0':
                    # given falsy string from command line option
                    return False
                else:
                    return bool(value)
            elif isinstance(default, dict):
                raise ValueError(__('cannot override dictionary config setting %r, '
                                    'ignoring (use %r to set individual elements)') %
                                 (name, name + '.key=value'))
            elif isinstance(default, list):
                return value.split(',')
            elif isinstance(default, int):
                try:
                    return int(value)
                except ValueError as exc:
                    raise ValueError(__('invalid number %r for config value %r, ignoring') %
                                     (value, name)) from exc
            elif callable(default):
                return value
            elif default is not None and not isinstance(default, str):
                raise ValueError(__('cannot override config setting %r with unsupported '
                                    'type, ignoring') % name)
            else:
                return value

    def pre_init_values(self) -> None:
        """
        Initialize some limited config variables before initializing i18n and loading
        extensions.
        """
        for name in 'needs_sphinx', 'suppress_warnings', 'language', 'locale_dirs':
            try:
                if name in self.overrides:
                    self.__dict__[name] = self.convert_overrides(name, self.overrides[name])
                elif name in self._raw_config:
                    self.__dict__[name] = self._raw_config[name]
            except ValueError as exc:
                logger.warning("%s", exc)

    def init_values(self) -> None:
        config = self._raw_config
        for name, value in self.overrides.items():
            try:
                if '.' in name:
                    real_name, key = name.split('.', 1)
                    config.setdefault(real_name, {})[key] = value
                    continue
                if name not in self.values:
                    logger.warning(__('unknown config value %r in override, ignoring'),
                                   name)
                    continue
                if isinstance(value, str):
                    config[name] = self.convert_overrides(name, value)
                else:
                    config[name] = value
            except ValueError as exc:
                logger.warning("%s", exc)
        for name in config:
            if name in self.values:
                self.__dict__[name] = config[name]

    def post_init_values(self) -> None:
        """
        Initialize additional config variables that are added after init_values() called.
        """
        config = self._raw_config
        for name in config:
            if name not in self.__dict__ and name in self.values:
                self.__dict__[name] = config[name]

        check_confval_types(None, self)

    def __repr__(self):
        values = []
        for opt_name in self.values:
            try:
                opt_value = getattr(self, opt_name)
            except Exception:
                opt_value = '<error!>'
            values.append(f"{opt_name}={opt_value!r}")
        return self.__class__.__qualname__ + '(' + ', '.join(values) + ')'

    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in self.values:
            raise AttributeError(__('No such config value: %s') % name)
        default = self.values[name].default
        if callable(default):
            return default(self)
        return default

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)

    def __setitem__(self, name: str, value: Any) -> None:
        setattr(self, name, value)

    def __delitem__(self, name: str) -> None:
        delattr(self, name)

    def __contains__(self, name: str) -> bool:
        return name in self.values

    def __iter__(self) -> Iterator[ConfigValue]:
        for name, opt in self.values.items():
            yield ConfigValue(name, getattr(self, name), opt.rebuild)

    def add(self, name: str, default: Any, rebuild: _ConfigRebuild,
            types: Sequence[type] | ENUM | Any) -> None:
        valid_types = types
        if name in self.values:
            raise ExtensionError(__('Config value %r already present') % name)

        # standardise rebuild
        if isinstance(rebuild, bool):
            rebuild = 'env' if rebuild else ''

        self.values[name] = _Opt(default, rebuild, valid_types)

    def filter(self, rebuild: str | Sequence[str]) -> Iterator[ConfigValue]:
        if isinstance(rebuild, str):
            return (value for value in self if value.rebuild == rebuild)
        return (value for value in self if value.rebuild in rebuild)

    def __getstate__(self) -> dict:
        """Obtains serializable data for pickling."""
        # remove potentially pickling-problematic values from config
        __dict__ = {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith('_') and is_serializable(value)
        }
        # create a picklable copy of values list
        __dict__['values'] = values = {}
        for name, opt in self.values.items():
            real_value = getattr(self, name)
            if not is_serializable(real_value):
                # omit unserializable value
                real_value = None
            # valid_types is also omitted
            values[name] = real_value, opt.rebuild

        return __dict__

    def __setstate__(self, state: dict) -> None:
        self.values = {
            name: _Opt(real_value, rebuild, ())
            for name, (real_value, rebuild) in state.pop('values').items()
        }
        self.__dict__.update(state)


def eval_config_file(filename: str, tags: Tags | None) -> dict[str, Any]:
    """Evaluate a config file."""
    namespace: dict[str, Any] = {}
    namespace['__file__'] = filename
    namespace['tags'] = tags

    with chdir(path.dirname(filename)):
        # during executing config file, current dir is changed to ``confdir``.
        try:
            with open(filename, 'rb') as f:
                code = compile(f.read(), filename.encode(fs_encoding), 'exec')
                exec(code, namespace)  # NoQA: S102
        except SyntaxError as err:
            msg = __("There is a syntax error in your configuration file: %s\n")
            raise ConfigError(msg % err) from err
        except SystemExit as exc:
            msg = __("The configuration file (or one of the modules it imports) "
                     "called sys.exit()")
            raise ConfigError(msg) from exc
        except ConfigError:
            # pass through ConfigError from conf.py as is.  It will be shown in console.
            raise
        except Exception as exc:
            msg = __("There is a programmable error in your configuration file:\n\n%s")
            raise ConfigError(msg % traceback.format_exc()) from exc

    return namespace


def convert_source_suffix(app: Sphinx, config: Config) -> None:
    """Convert old styled source_suffix to new styled one.

    * old style: str or list
    * new style: a dict which maps from fileext to filetype
    """
    source_suffix = config.source_suffix
    if isinstance(source_suffix, str):
        # if str, considers as default filetype (None)
        #
        # The default filetype is determined on later step.
        # By default, it is considered as restructuredtext.
        config.source_suffix = {source_suffix: None}  # type: ignore[attr-defined]
    elif isinstance(source_suffix, (list, tuple)):
        # if list, considers as all of them are default filetype
        config.source_suffix = dict.fromkeys(source_suffix, None)  # type: ignore[attr-defined]
    elif not isinstance(source_suffix, dict):
        logger.warning(__("The config value `source_suffix' expects "
                          "a string, list of strings, or dictionary. "
                          "But `%r' is given." % source_suffix))


def convert_highlight_options(app: Sphinx, config: Config) -> None:
    """Convert old styled highlight_options to new styled one.

    * old style: options
    * new style: a dict which maps from language name to options
    """
    options = config.highlight_options
    if options and not all(isinstance(v, dict) for v in options.values()):
        # old styled option detected because all values are not dictionary.
        config.highlight_options = {config.highlight_language:  # type: ignore[attr-defined]
                                    options}


def init_numfig_format(app: Sphinx, config: Config) -> None:
    """Initialize :confval:`numfig_format`."""
    numfig_format = {'section': _('Section %s'),
                     'figure': _('Fig. %s'),
                     'table': _('Table %s'),
                     'code-block': _('Listing %s')}

    # override default labels by configuration
    numfig_format.update(config.numfig_format)
    config.numfig_format = numfig_format  # type: ignore[attr-defined]


def correct_copyright_year(_app: Sphinx, config: Config) -> None:
    """Correct values of copyright year that are not coherent with
    the SOURCE_DATE_EPOCH environment variable (if set)

    See https://reproducible-builds.org/specs/source-date-epoch/
    """
    if (source_date_epoch := getenv('SOURCE_DATE_EPOCH')) is None:
        return

    source_date_epoch_year = str(time.gmtime(int(source_date_epoch)).tm_year)

    for k in ('copyright', 'epub_copyright'):
        if k in config:
            value: str | Sequence[str] = config[k]
            if isinstance(value, str):
                config[k] = _substitute_copyright_year(value, source_date_epoch_year)
            else:
                items = (_substitute_copyright_year(x, source_date_epoch_year) for x in value)
                config[k] = type(value)(items)  # type: ignore[call-arg]


def _substitute_copyright_year(copyright_line: str, replace_year: str) -> str:
    """Replace the year in a single copyright line.

    Legal formats are:

    * ``YYYY``
    * ``YYYY,``
    * ``YYYY ``
    * ``YYYY-YYYY,``
    * ``YYYY-YYYY ``

    The final year in the string is replaced with ``replace_year``.
    """
    if len(copyright_line) < 4 or not copyright_line[:4].isdigit():
        return copyright_line

    if copyright_line[4:5] in {'', ' ', ','}:
        return replace_year + copyright_line[4:]

    if copyright_line[4] != '-':
        return copyright_line

    if copyright_line[5:9].isdigit() and copyright_line[9] in ' ,':
        return copyright_line[:5] + replace_year + copyright_line[9:]

    return copyright_line


def check_confval_types(app: Sphinx | None, config: Config) -> None:
    """Check all values for deviation from the default value's type, since
    that can result in TypeErrors all over the place NB.
    """
    for name, opt in config.values.items():
        default = opt.default
        valid_types = opt.valid_types
        value = getattr(config, name)

        if callable(default):
            default = default(config)  # evaluate default value
        if default is None and not valid_types:
            continue  # neither inferable nor explicitly annotated types

        if valid_types is Any:  # any type of value is accepted
            continue

        if isinstance(valid_types, ENUM):
            if not valid_types.match(value):
                msg = __("The config value `{name}` has to be a one of {candidates}, "
                         "but `{current}` is given.")
                logger.warning(
                    msg.format(name=name, current=value, candidates=valid_types.candidates),
                    once=True,
                )
            continue

        type_value = type(value)
        type_default = type(default)

        if type_value is type_default:  # attempt to infer the type
            continue

        if type_value in valid_types:  # check explicitly listed types
            continue

        common_bases = (set(type_value.__bases__ + (type_value,))
                        & set(type_default.__bases__))
        common_bases.discard(object)
        if common_bases:
            continue  # at least we share a non-trivial base class

        if valid_types:
            msg = __("The config value `{name}' has type `{current.__name__}'; "
                     "expected {permitted}.")
            wrapped_valid_types = [f"`{c.__name__}'" for c in valid_types]
            if len(wrapped_valid_types) > 2:
                permitted = (", ".join(wrapped_valid_types[:-1])
                             + f", or {wrapped_valid_types[-1]}")
            else:
                permitted = " or ".join(wrapped_valid_types)
            logger.warning(
                msg.format(name=name, current=type_value, permitted=permitted),
                once=True,
            )
        else:
            msg = __("The config value `{name}' has type `{current.__name__}', "
                     "defaults to `{default.__name__}'.")
            logger.warning(
                msg.format(name=name, current=type_value, default=type_default),
                once=True,
            )


def check_primary_domain(app: Sphinx, config: Config) -> None:
    primary_domain = config.primary_domain
    if primary_domain and not app.registry.has_domain(primary_domain):
        logger.warning(__('primary_domain %r not found, ignored.'), primary_domain)
        config.primary_domain = None  # type: ignore[attr-defined]


def check_root_doc(app: Sphinx, env: BuildEnvironment, added: set[str],
                   changed: set[str], removed: set[str]) -> set[str]:
    """Adjust root_doc to 'contents' to support an old project which does not have
    any root_doc setting.
    """
    if (app.config.root_doc == 'index' and
            'index' not in app.project.docnames and
            'contents' in app.project.docnames):
        logger.warning(__('Since v2.0, Sphinx uses "index" as root_doc by default. '
                          'Please add "root_doc = \'contents\'" to your conf.py.'))
        app.config.root_doc = "contents"  # type: ignore[attr-defined]

    return changed


def setup(app: Sphinx) -> dict[str, Any]:
    app.connect('config-inited', convert_source_suffix, priority=800)
    app.connect('config-inited', convert_highlight_options, priority=800)
    app.connect('config-inited', init_numfig_format, priority=800)
    app.connect('config-inited', correct_copyright_year, priority=800)
    app.connect('config-inited', check_confval_types, priority=800)
    app.connect('config-inited', check_primary_domain, priority=800)
    app.connect('env-get-outdated', check_root_doc)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
