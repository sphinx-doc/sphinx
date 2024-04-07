"""Module for the :class:`~sphinx.testing.matcher.LineMatcher` options."""

from __future__ import annotations

__all__ = ('Options', 'CompleteOptions', 'OptionsHolder')

import contextlib
from types import MappingProxyType
from typing import TYPE_CHECKING, TypedDict, final, overload

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping, Sequence
    from typing import Any, ClassVar, Literal, TypeVar, Union

    from typing_extensions import Unpack

    from sphinx.testing.matcher._util import LinePredicate, PatternLike

    FlagOption = Literal['keep_ansi', 'keep_break', 'keep_empty', 'compress', 'unique']

    StripOption = Literal['strip', 'stripline']
    StripChars = Union[bool, str, None]
    """Allowed values for :attr:`Options.strip` and :attr:`Options.stripline`."""

    PruneOption = Literal['delete']
    PrunePattern = Union[PatternLike, Sequence[PatternLike]]
    """One or more patterns to prune."""

    IgnoreOption = Literal['ignore']

    FlavorOption = Literal['flavor']
    Flavor = Literal['re', 'fnmatch', 'none']
    """Allowed values for :attr:`Options.flavor`."""

    # For some reason, mypy does not like Union of Literal,
    # so we wrap the Literal types inside a bigger Literal.
    OptionValue = Union[bool, StripChars, PrunePattern, Union[LinePredicate, None], Flavor]
    OptionName = Literal[FlagOption, StripOption, PruneOption, IgnoreOption, FlavorOption]

    DT = TypeVar('DT')


@final
class Options(TypedDict, total=False):
    """Options for a :class:`~sphinx.testing.matcher.LineMatcher` object.

    Some options directly act on the original string (e.g., :attr:`strip`),
    while others (e.g., :attr:`stripline`) act on the lines obtained after
    splitting the (transformed) original string.

    .. seealso:: :mod:`sphinx.testing.matcher._cleaner`
    """

    # only immutable fields should be used as options, otherwise undesired
    # side-effects might occur when using a default option mutable value

    keep_ansi: bool
    """Indicate whether to keep the ANSI escape sequences.

    The default value is ``True``.
    """

    strip: StripChars
    """Describe the characters to strip from the source.

    The allowed values for :attr:`strip` are:

    * ``False`` -- keep leading and trailing whitespaces (the default).
    * ``True`` -- remove leading and trailing whitespaces.
    * a string (*chars*) -- remove leading and trailing characters in *chars*.
    """

    keep_break: bool
    """Indicate whether to keep line breaks at the end of each line.

    The default value is ``False`` (to mirror :meth:`str.splitlines`).
    """

    stripline: StripChars
    """Describe the characters to strip from each source's line.

    The allowed values for :attr:`stripline` are:

    * ``False`` -- keep leading and trailing whitespaces (the default).
    * ``True`` -- remove leading and trailing whitespaces.
    * a string (*chars*) -- remove leading and trailing characters in *chars*.
    """

    keep_empty: bool
    """Indicate whether to keep empty lines in the output.

    The default value is ``True``.
    """

    compress: bool
    """Eliminate duplicated consecutive lines in the output.

    The default value is ``False``.

    For instance, ``['a', 'b', 'b', 'c'] -> ['a', 'b', 'c']``.

    Note that if :attr:`empty` is ``False``, empty lines are removed *before*
    the duplicated lines, i.e., ``['a', 'b', '', 'b'] -> ['a', 'b']``.
    """

    unique: bool
    """Eliminate multiple occurrences of lines in the output.

    The default value is ``False``.

    This option is only applied at the very end of the transformation chain,
    after empty and duplicated consecutive lines might have been eliminated.
    """

    delete: PrunePattern
    r"""Regular expressions for substrings to prune from the output lines.

    The output lines are pruned from their matching substrings (checked
    using :func:`re.match`) until the output lines are stabilized.

    This transformation is applied at the end of the transformation
    chain, just before filtering the output lines are filtered with
    the :attr:`ignore` predicate.

    See :func:`sphinx.testing.matcher.cleaner.prune_lines` for an example.
    """

    ignore: LinePredicate | None
    """A predicate for filtering the output lines.

    Lines that satisfy this predicate are not included in the output.

    The default is ``None``, meaning that all lines are included.
    """

    flavor: Flavor
    """Indicate how strings are matched against non-compiled patterns.

    The allowed values for :attr:`flavor` are:

    * ``'none'`` -- match lines using string equality (the default).
    * ``'fnmatch'`` -- match lines using :mod:`fnmatch`-style patterns.
    * ``'re'`` -- match lines using :mod:`re`-style patterns.

    This option only affects non-compiled patterns. Unless stated otheriwse,
    matching is performed on compiled patterns by :func:`~re.Pattern.match`.
    """


@final
class CompleteOptions(TypedDict):
    """Same as :class:`Options` but as a total dictionary."""

    keep_ansi: bool
    strip: StripChars
    stripline: StripChars

    keep_break: bool
    keep_empty: bool
    compress: bool
    unique: bool

    delete: PrunePattern
    ignore: LinePredicate | None

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
        stripline=False,
        keep_break=False,
        keep_empty=True,
        compress=False,
        unique=False,
        delete=(),
        ignore=None,
        flavor='none',
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

        It can be regarded as a proxy on a :class:`Options` dictionary.
        """
        return MappingProxyType(self.__options)

    @property
    def complete_options(self) -> Mapping[str, object]:
        """A read-only view of the *complete* mapping of options.

        It can be regarded as a proxy on a :class:`CompleteOptions` dictionary.
        """
        return MappingProxyType(self.default_options | self.__options)

    @contextlib.contextmanager
    def set_options(self, /, **options: Unpack[Options]) -> Generator[None, None, None]:
        """Temporarily replace the set of options with *options*."""
        return self.__set_options(options)

    @contextlib.contextmanager
    def override(self, /, **options: Unpack[Options]) -> Generator[None, None, None]:
        """Temporarily extend the set of options with *options*."""
        return self.__set_options(self.__options | options)

    def __set_options(self, options: Options) -> Generator[None, None, None]:
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
    def get_option(self, name: FlagOption, /) -> bool: ...  # NoQA: E704
    @overload
    def get_option(self, name: FlagOption, default: bool, /) -> bool: ...  # NoQA: E704
    @overload
    def get_option(self, name: FlagOption, default: DT, /) -> bool | DT: ...  # NoQA: E704
    # strip-like options
    @overload
    def get_option(self, name: StripOption, /) -> StripChars: ...  # NoQA: E704
    @overload
    def get_option(self, name: StripOption, default: StripChars, /) -> StripChars: ...  # NoQA: E704
    @overload
    def get_option(self, name: StripOption, default: DT, /) -> StripChars | DT: ...  # NoQA: E704
    # pruning option
    @overload
    def get_option(self, name: PruneOption, /) -> PrunePattern: ...  # NoQA: E704
    @overload
    def get_option(self, name: PruneOption, default: PrunePattern, /) -> PrunePattern: ...  # NoQA: E704
    @overload
    def get_option(self, name: PruneOption, default: DT, /) -> PrunePattern | DT: ...  # NoQA: E704
    # filtering options
    @overload
    def get_option(self, name: IgnoreOption, /) -> LinePredicate | None: ...  # NoQA:  E704
    @overload  # NoQA: E301
    def get_option(  # NoQA: E704
        self, name: IgnoreOption, default: LinePredicate | None, /
    ) -> LinePredicate | None: ...
    @overload  # NoQA: E301
    def get_option(  # NoQA: E704
        self, name: IgnoreOption, default: DT, /
    ) -> LinePredicate | None | DT: ...
    # miscellaneous options
    @overload
    def get_option(self, name: FlavorOption, /) -> Flavor: ...  # NoQA: E704
    @overload
    def get_option(self, name: FlavorOption, default: Flavor, /) -> Flavor: ...  # NoQA: E704
    @overload
    def get_option(self, name: FlavorOption, default: DT, /) -> Flavor | DT: ...  # NoQA: E704
    def get_option(self, name: OptionName, /, *default: object) -> object:  # NoQA: E301
        """Get an option value, or a default value.

        :param name: An option name specified in :attr:`default_options`.
        :return: An option value.

        When *default* is specified and *name* is not explicitly set, it is
        returned instead of the default specified in :attr:`default_options`.
        """
        if name in self.__options:
            return self.__options[name]
        return default[0] if default else self.default_options[name]

    @overload
    def set_option(self, name: FlagOption, value: bool, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: StripOption, value: StripChars, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: PruneOption, value: PrunePattern, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: IgnoreOption, value: LinePredicate | None, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: FlavorOption, value: Flavor, /) -> None: ...  # NoQA: E704
    def set_option(self, name: OptionName, value: Any, /) -> None:  # NoQA: E301
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
    def stripline(self) -> StripChars:
        """See :attr:`Options.stripline`."""
        return self.get_option('stripline')

    @stripline.setter
    def stripline(self, value: StripChars) -> None:
        self.set_option('stripline', value)

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
    def delete(self) -> PrunePattern:
        """See :attr:`Options.delete`."""
        return self.get_option('delete')

    @delete.setter
    def delete(self, value: PrunePattern) -> None:
        self.set_option('delete', value)

    @property
    def ignore(self) -> LinePredicate | None:
        """See :attr:`Options.ignore`."""
        return self.get_option('ignore')

    @ignore.setter
    def ignore(self, value: LinePredicate | None) -> None:
        self.set_option('ignore', value)

    @property
    def flavor(self) -> Flavor:
        """See :attr:`Options.flavor`."""
        return self.get_option('flavor')

    @flavor.setter
    def flavor(self, value: Flavor) -> None:
        self.set_option('flavor', value)
