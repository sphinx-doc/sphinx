from __future__ import annotations

__all__ = ('Options',)

import contextlib
from types import MappingProxyType
from typing import TYPE_CHECKING, TypedDict, final, overload

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Mapping, Sequence
    from typing import ClassVar, Literal, TypeVar, Union

    from typing_extensions import Unpack

    from sphinx.testing._matcher.util import LinePattern

    FlagOption = Literal['ansi', 'keepends', 'keep_empty', 'compress', 'unique']

    StripOption = Literal['strip', 'stripline']
    StripChars = Union[bool, str, None]

    DeleteOption = Literal['delete']
    DeletePattern = Union[LinePattern, Sequence[LinePattern]]

    FilteringOption = Literal['ignore']
    LinePredicate = Callable[[str], object]

    FlavorOption = Literal['flavor']
    Flavor = Literal['re', 'fnmatch', 'none']

    # For some reason, mypy does not like Union of Literal,
    # so we wrap the Literal types inside a bigger Literal.
    OptionName = Literal[FlagOption, StripOption, DeleteOption, FilteringOption, FlavorOption]
    OptionValue = Union[bool, StripChars, DeletePattern, LinePredicate, Flavor]

    DT = TypeVar('DT')
    _OptionsView = Union['Options', 'CompleteOptions']


@final
class Options(TypedDict, total=False):
    """Options for a :class:`~sphinx.testing.matcher.LineMatcher` object.

    Some options directly act on the original string (e.g., :attr:`strip`),
    while others (e.g., :attr:`stripline`) act on the lines obtained after
    splitting the (transformed) original string.

    .. seealso:: :mod:`sphinx.testing._matcher.cleaner`
    """

    # only immutable fields should be used as options, otherwise undesired
    # side-effects might occur when using a default option mutable value

    ansi: bool
    """Indicate whether to keep the ANSI escape sequences.

    The default value is ``True``.
    """

    strip: StripChars
    """Call :meth:`str.strip` on the original source.

    The allowed values for :attr:`strip` are:

    * ``True`` -- remove leading and trailing whitespaces (the default).
    * ``False`` -- keep leading and trailing whitespaces.
    * a string (*chars*) -- remove leading and trailing characters in *chars*.
    """

    stripline: StripChars
    """Call :meth:`str.strip` on the lines obtained after splitting the source.

    The allowed values for :attr:`stripline` are:

    * ``True`` -- remove leading and trailing whitespaces.
    * ``False`` -- keep leading and trailing whitespaces (the default).
    * a string (*chars*) -- remove leading and trailing characters in *chars*.
    """

    keepends: bool
    """If true, keep line breaks in the output.

    The default value is ``False``.
    """

    keep_empty: bool
    """If false, eliminate empty lines in the output.

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

    delete: DeletePattern
    r"""Prefixes or patterns to remove from the output lines.

    The transformation is described for one or more :class:`str`
    or :class:`~re.Pattern` objects as follows:

    - Compile :class:`str` pattern into :class:`~re.Pattern` according
      to the pattern :attr:`flavor` and remove prefixes matching those
      patterns from the output lines.
    - Replace substrings in the output lines matching one or more
      patterns directly given as :class:`~re.Pattern` objects.

    The process is repeated until no output lines starts by any
    of the given strings or matches any of the given patterns.

    This transformation is applied at the end of the transformation
    chain, just before filtering the output lines are filtered with
    the :attr:`ignore` predicate.
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

    This option only affects non-compiled patterns (i.e., those given
    as :class:`str` and not :class:`~re.Pattern` objects).
    """


@final
class CompleteOptions(TypedDict):
    """Same as :class:`Options` but as a total dictionary.

    :meta private:
    """

    ansi: bool
    strip: StripChars
    stripline: StripChars

    keepends: bool
    keep_empty: bool
    compress: bool
    unique: bool

    delete: DeletePattern
    ignore: LinePredicate | None

    flavor: Flavor


class Configurable:
    """Mixin supporting a known set of options."""

    __slots__ = ('_options',)
    __tracebackhide__: bool = True

    default_options: ClassVar[CompleteOptions] = CompleteOptions(
        ansi=True,
        strip=False,
        stripline=False,
        keepends=False,
        keep_empty=True,
        compress=False,
        unique=False,
        delete=(),
        ignore=None,
        flavor='none',
    )
    """The default options to use when an option is not specified.

    Subclasses should override this field for different default options.
    """

    def __init__(self, /, *args: object, **options: Unpack[Options]) -> None:
        self._options = options

    @property
    def options(self) -> Mapping[str, object]:  # cannot use CompleteOptions :(
        """A read-only view on the current mapping of options."""
        return MappingProxyType(self._options)

    @contextlib.contextmanager
    def use(self, /, **options: Unpack[Options]) -> Generator[None, None, None]:
        """Temporarily replace the set of options with *options*."""
        local_options = self.default_options | options
        with self.override(**local_options):
            yield

    @contextlib.contextmanager
    def override(self, /, **options: Unpack[Options]) -> Generator[None, None, None]:
        """Temporarily extend the set of options with *options*."""
        saved_options = self._options.copy()
        self._options |= options
        try:
            yield
        finally:
            self._options = saved_options

    # When an option is added, add an overloaded definition
    # so that mypy can correctly deduce the option's type.
    #
    # fmt: off
    # boolean-like options
    @overload
    def get_option(self, name: FlagOption, /) -> bool: ...  # NoQA: E704
    # strip-like options
    @overload
    def get_option(self, name: StripOption, /) -> StripChars: ...  # NoQA: E704
    # delete prefix/suffix option
    @overload
    def get_option(self, name: DeleteOption, /) -> DeletePattern: ...  # NoQA: E704
    # filtering options
    @overload
    def get_option(self, name: FilteringOption, /) -> LinePredicate | None: ...  # NoQA: E704
    # miscellaneous options
    @overload
    def get_option(self, name: FlavorOption, /) -> Flavor: ...  # NoQA: E704
    # fmt: on
    def get_option(self, name: OptionName, /) -> object:  # NoQA: E301
        """Get a known option value, or its default value."""
        __tracebackhide__ = self.__tracebackhide__
        if name in self._options:
            return self._options[name]
        return self.default_options[name]

    # fmt: off
    @overload
    def set_option(self, name: FlagOption,  value: bool, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: StripOption, value: StripChars, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: DeleteOption, value: DeletePattern, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: FilteringOption, value:  LinePredicate | None, /) -> None: ...  # NoQA: E704
    @overload
    def set_option(self, name: FlavorOption, value: Flavor, /) -> None: ...  # NoQA: E704
    # fmt: on
    def set_option(self, name: OptionName, value: OptionValue, /) -> None:  # NoQA: E301
        """Set a persistent option value."""
        __tracebackhide__ = self.__tracebackhide__
        self._options[name] = value
