"""Module for the :class:`~sphinx.testing.matcher.LineMatcher` options."""

from __future__ import annotations

__all__ = ('Options', 'CompleteOptions', 'OptionsHolder')

import contextlib
from collections.abc import Sequence
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, TypedDict, Union, final, overload

from sphinx.testing.matcher._util import LinePredicate, PatternLike

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from typing import Any, ClassVar, TypeVar

    from typing_extensions import TypeAlias, Unpack

    DT = TypeVar('DT')

_FLAG: TypeAlias = Literal['keep_ansi', 'keep_break', 'keep_empty', 'compress', 'unique']

_STRIP: TypeAlias = Literal['strip', 'strip_line']
StripChars: TypeAlias = Union[bool, str, None]
"""Allowed values for :attr:`Options.strip` and :attr:`Options.strip_line`."""

_PRUNE: TypeAlias = Literal['prune']
PrunePattern: TypeAlias = Union[PatternLike, Sequence[PatternLike]]
"""One or more (non-empty) patterns to prune."""

_IGNORE: TypeAlias = Literal['ignore']
IgnorePredicate: TypeAlias = Union[LinePredicate, None]

_OPCODES = Literal['ops']
# must be kept in sync with :mod:`sphinx.testing.matcher._codes`
# and  must be present at runtime for testing the synchronization
OpCode: TypeAlias = Literal['strip', 'check', 'compress', 'unique', 'prune', 'filter']
"""Known operation codes (see :attr:`Options.ops`)."""
OpCodes: TypeAlias = Sequence[OpCode]

_FLAVOR: TypeAlias = Literal['flavor']
# When Python 3.11 becomes the minimal version, change this for a string enumeration.
Flavor: TypeAlias = Literal['literal', 'fnmatch', 're']
"""Allowed values for :attr:`Options.flavor`."""

# For some reason, mypy does not like Union of Literal when used as keys
# of a TypedDict (see: https://github.com/python/mypy/issues/16818), so
# we instead use a Literal of those (which is equivalent).
_OPTION: TypeAlias = Literal[_FLAG, _STRIP, _PRUNE, _IGNORE, _OPCODES, _FLAVOR]


@final
class Options(TypedDict, total=False):
    """Options for a :class:`~sphinx.testing.matcher.LineMatcher` object.

    Some options directly act on the original string (e.g., :attr:`strip`),
    while others (e.g., :attr:`strip_line`) act on the lines obtained after
    splitting the (transformed) original string.

    .. seealso:: :mod:`sphinx.testing.matcher.cleaner`
    """

    # only immutable fields should be used as options, otherwise undesired
    # side-effects might occur when using a default option mutable value

    keep_ansi: bool
    """Indicate whether to keep the ANSI escape sequences.

    The default value is :py3:`True`.
    """

    strip: StripChars
    """Describe the characters to strip from the source.

    The allowed values for :attr:`strip` are:

    * :py3:`False` -- keep leading and trailing whitespaces (the default).
    * :py3:`True` or :py3:`None` -- remove leading and trailing whitespaces.
    * a string (*chars*) -- remove leading and trailing characters in *chars*.
    """

    keep_break: bool
    """Indicate whether to keep line breaks at the end of each line.

    The default value is :py3:`False` (to mirror :meth:`str.splitlines`).
    """

    strip_line: StripChars
    """Describe the characters to strip from each source's line.

    The allowed values for :attr:`strip_line` are:

    * :py3:`False` -- keep leading and trailing whitespaces (the default).
    * :py3:`True` or :py3:`None` -- remove leading and trailing whitespaces.
    * a string (*chars*) -- remove leading and trailing characters in *chars*.
    """

    keep_empty: bool
    """Indicate whether to keep empty lines in the output.

    The default value is :py3:`True`.
    """

    compress: bool
    """Eliminate duplicated consecutive lines in the output.

    The default value is :py3:`False`.
    """

    unique: bool
    """Eliminate multiple occurrences of lines in the output.

    The default value is :py3:`False`.
    """

    prune: PrunePattern
    r"""Regular expressions for substrings to prune from the output lines.

    The output lines are pruned from their matching substrings (checked
    using :func:`re.match`) until the output lines are stabilized.

    See :func:`sphinx.testing.matcher.cleaner.prune_lines` for an example.
    """

    ignore: IgnorePredicate
    """A predicate for filtering the output lines.

    Lines that satisfy this predicate are not included in the output.

    The default is :py3:`None`, meaning that all lines are included.
    """

    ops: OpCodes
    """A sequence of *opcode* representing the line operations.

    The following table describes the allowed *opcode*.

    .. default-role:: py3r

    +------------+--------------------+---------------------------------------+
    | Op. Code   | Option             | Description                           |
    +============+====================+=======================================+
    | `strip`    | :attr:`strip_line` | Strip leading and trailing characters |
    +------------+--------------------+---------------------------------------+
    | `check`    | :attr:`keep_empty` | Remove empty lines                    |
    +------------+--------------------+---------------------------------------+
    | `compress` | :attr:`compress`   | Remove consecutive duplicated lines   |
    +------------+--------------------+---------------------------------------+
    | `unique`   | :attr:`unique`     | Remove duplicated lines               |
    +------------+--------------------+---------------------------------------+
    | `prune`    | :attr:`prune`      | Remove matching substrings            |
    +------------+--------------------+---------------------------------------+
    | `filter`   | :attr:`ignore`     | Ignore matching lines                 |
    +------------+--------------------+---------------------------------------+

    .. default-role::

    The default value::

        ('strip', 'check', 'compress', 'unique', 'prune', 'filter')

    .. rubric:: Example

    Consider the following setup::

        lines = ['a', '', 'a', '', 'a']
        options = Options(strip_line=True, keep_empty=False, compress=True)

    By default, the lines are transformed into :py3:`['a']` since empty lines
    are removed before serial duplicates. On the other hand, assume that::

        options = Options(strip_line=True, keep_empty=False, compress=True,
                          ops=('strip', 'compress', 'check'))

    Here, the empty lines will be removed *after* the serial duplicates,
    and therefore the lines are trasnformed into :py3:`['a', 'a', 'a']`.
    """

    flavor: Flavor
    """Indicate how strings are matched against non-compiled patterns.

    The allowed values for :attr:`flavor` are:

    * :py3r:`literal` -- match lines using string equality (the default).
    * :py3r:`fnmatch` -- match lines using :mod:`fnmatch`-style patterns.
    * :py3r:`re` -- match lines using :mod:`re`-style patterns.

    This option only affects non-compiled patterns. Unless stated otherwise,
    matching is performed on compiled patterns by :meth:`re.Pattern.match`.
    """


@final
class CompleteOptions(TypedDict):
    """Same as :class:`Options` but as a total dictionary."""

    keep_ansi: bool
    strip: StripChars
    strip_line: StripChars

    keep_break: bool
    keep_empty: bool
    compress: bool
    unique: bool

    prune: PrunePattern
    ignore: IgnorePredicate

    ops: OpCodes
    flavor: Flavor


class OptionsHolder:
    """Mixin supporting a known set of options.

    An :class:`OptionsHolder` object stores a set of partial options,
    overriding the default values specified by :attr:`default_options`.

    At runtime, only the options given at construction time, explicitly
    set via :meth:`set_option` or the corresponding property are stored
    by this object.

    As such, :attr:`options` and :attr:`complete_options` return a proxy
    on :class:`Options` and :class:`CompleteOptions` respectively, e.g.::

        obj = OptionsHolder(strip=True)
        assert obj.options == {'strip': True}
        assert obj.complete_options == dict(obj.default_options, strip=True)
    """

    __slots__ = ('__options',)

    default_options: ClassVar[CompleteOptions] = CompleteOptions(
        keep_ansi=True,
        strip=False,
        strip_line=False,
        keep_break=False,
        keep_empty=True,
        compress=False,
        unique=False,
        prune=(),
        ignore=None,
        ops=('strip', 'check', 'compress', 'unique', 'prune', 'filter'),
        flavor='literal',
    )
    """The supported options specifications and their default values.

    Subclasses should override this field for different default options.
    """

    def __init__(self, /, **options: Unpack[Options]) -> None:
        """Construct an :class:`OptionsHolder` object."""
        self.__options = options

    @property
    def options(self) -> Mapping[str, object]:
        """A read-only view of the *current* mapping of options.

        It can be regarded as a proxy on an :class:`Options` dictionary.
        """
        return MappingProxyType(self.__options)

    @property
    def complete_options(self) -> Mapping[str, object]:
        """A read-only view of the *complete* mapping of options.

        It can be regarded as a proxy on a :class:`CompleteOptions` dictionary.
        """
        return MappingProxyType(self.default_options | self.__options)

    @contextlib.contextmanager
    def set_options(self, /, **options: Unpack[Options]) -> Iterator[None]:
        """Temporarily replace the set of options with *options*."""
        return self.__set_options(options)

    @contextlib.contextmanager
    def override(self, /, **options: Unpack[Options]) -> Iterator[None]:
        """Temporarily extend the set of options with *options*."""
        return self.__set_options(self.__options | options)

    def __set_options(self, options: Options) -> Iterator[None]:
        saved_options = self.__options.copy()
        self.__options = options
        try:
            yield
        finally:
            self.__options = saved_options

    # When an option is added, add an overloaded definition
    # so that mypy can correctly deduce the option's type.
    #
    # boolean-like options
    @overload
    def get_option(self, name: _FLAG, /) -> bool: ...  # NoQA: E704
    @overload
    def get_option(self, name: _FLAG, default: bool, /) -> bool: ...  # NoQA: E704
    @overload
    def get_option(self, name: _FLAG, default: DT, /) -> bool | DT: ...  # NoQA: E704
    # strip-like options
    @overload
    def get_option(self, name: _STRIP, /) -> StripChars: ...  # NoQA: E704
    @overload
    def get_option(self, name: _STRIP, default: StripChars, /) -> StripChars: ...  # NoQA: E704
    @overload
    def get_option(self, name: _STRIP, default: DT, /) -> StripChars | DT: ...  # NoQA: E704
    # pruning option
    @overload
    def get_option(self, name: _PRUNE, /) -> PrunePattern: ...  # NoQA: E704
    @overload
    def get_option(self, name: _PRUNE, default: PrunePattern, /) -> PrunePattern: ...  # NoQA: E704
    @overload
    def get_option(self, name: _PRUNE, default: DT, /) -> PrunePattern | DT: ...  # NoQA: E704
    # filtering options
    @overload
    def get_option(self, name: _IGNORE, /) -> IgnorePredicate: ...  # NoQA:  E704
    @overload
    def get_option(self, name: _IGNORE, default: IgnorePredicate, /) -> IgnorePredicate: ...  # NoQA:  E704
    @overload
    def get_option(self, name: _IGNORE, default: DT, /) -> IgnorePredicate | DT: ...  # NoQA: E704
    # miscellaneous options
    @overload
    def get_option(self, name: _OPCODES, /) -> OpCodes: ...  # NoQA: E704
    @overload
    def get_option(self, name: _OPCODES, default: OpCodes, /) -> OpCodes: ...  # NoQA: E704
    @overload
    def get_option(self, name: _OPCODES, default: DT, /) -> OpCodes | DT: ...  # NoQA: E704
    @overload
    def get_option(self, name: _FLAVOR, /) -> Flavor: ...  # NoQA: E704
    @overload
    def get_option(self, name: _FLAVOR, default: Flavor, /) -> Flavor: ...  # NoQA: E704
    @overload
    def get_option(self, name: _FLAVOR, default: DT, /) -> Flavor | DT: ...  # NoQA: E704
    def get_option(self, name: _OPTION, /, *default: object) -> object:  # NoQA: E301
        """Get an option value, or a default value.

        :param name: An option name specified in :attr:`default_options`.
        :return: An option value.

        When *default* is specified and *name* is not explicitly stored by
        this object, that *default* is returned instead of the default value
        specified in :attr:`default_options`.
        """
        if name in self.__options:
            return self.__options[name]
        return default[0] if default else self.default_options[name]

    @overload
    def set_option(self, name: _FLAG, value: bool, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: _STRIP, value: StripChars, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: _PRUNE, value: PrunePattern, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: _IGNORE, value: LinePredicate | None, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: _OPCODES, value: OpCodes, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: _FLAVOR, value: Flavor, /) -> None: ...  # NoQA: E704
    def set_option(self, name: _OPTION, value: Any, /) -> None:  # NoQA: E301
        """Set a persistent option value.

        The *name* should be an option for which a default value is specified
        in :attr:`default_options`, but this is not enforced at runtime; thus,
        the consistency of this object's state is left to the user.
        """
        self.__options[name] = value

    @property
    def keep_ansi(self) -> bool:
        """See :attr:`Options.keep_ansi`."""
        return self.get_option('keep_ansi')

    @keep_ansi.setter
    def keep_ansi(self, value: bool) -> None:
        self.set_option('keep_ansi', value)

    @property
    def strip(self) -> StripChars:
        """See :attr:`Options.strip`."""
        return self.get_option('strip')

    @strip.setter
    def strip(self, value: StripChars) -> None:
        self.set_option('strip', value)

    @property
    def strip_line(self) -> StripChars:
        """See :attr:`Options.strip_line`."""
        return self.get_option('strip_line')

    @strip_line.setter
    def strip_line(self, value: StripChars) -> None:
        self.set_option('strip_line', value)

    @property
    def keep_break(self) -> bool:
        """See :attr:`Options.keep_break`."""
        return self.get_option('keep_break')

    @keep_break.setter
    def keep_break(self, value: bool) -> None:
        self.set_option('keep_break', value)

    @property
    def keep_empty(self) -> bool:
        """See :attr:`Options.keep_empty`."""
        return self.get_option('keep_empty')

    @keep_empty.setter
    def keep_empty(self, value: bool) -> None:
        self.set_option('keep_empty', value)

    @property
    def compress(self) -> bool:
        """See :attr:`Options.compress`."""
        return self.get_option('compress')

    @compress.setter
    def compress(self, value: bool) -> None:
        self.set_option('compress', value)

    @property
    def unique(self) -> bool:
        """See :attr:`Options.unique`."""
        return self.get_option('unique')

    @unique.setter
    def unique(self, value: bool) -> None:
        self.set_option('unique', value)

    @property
    def prune(self) -> PrunePattern:
        """See :attr:`Options.prune`."""
        return self.get_option('prune')

    @prune.setter
    def prune(self, value: PrunePattern) -> None:
        self.set_option('prune', value)

    @property
    def ignore(self) -> LinePredicate | None:
        """See :attr:`Options.ignore`."""
        return self.get_option('ignore')

    @ignore.setter
    def ignore(self, value: LinePredicate | None) -> None:
        self.set_option('ignore', value)

    @property
    def ops(self) -> Sequence[OpCode]:
        """See :attr:`Options.ops`."""
        return self.get_option('ops')

    @ops.setter
    def ops(self, value: OpCodes) -> None:
        self.set_option('ops', value)

    @property
    def flavor(self) -> Flavor:
        """See :attr:`Options.flavor`."""
        return self.get_option('flavor')

    @flavor.setter
    def flavor(self, value: Flavor) -> None:
        self.set_option('flavor', value)
