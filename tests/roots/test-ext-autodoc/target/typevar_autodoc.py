from __future__ import annotations

from typing import Generic, ParamSpec, TypeVar

#: A documented type variable.
Documented = TypeVar('Documented')

_T = TypeVar('_T')
_T_co = TypeVar('_T_co', covariant=True)
_T_bound = TypeVar('_T_bound', bound=int)
_T_constrained = TypeVar('_T_constrained', int, str)
_P = ParamSpec('_P')


class DocumentedHolder(Generic[Documented]):  # NoQA: UP046
    """Use a documented type variable in the base and a method."""

    def echo(self, item: Documented) -> Documented:
        """Return *item* unchanged."""
        raise NotImplementedError


class UndocumentedHolder(Generic[_T]):  # NoQA: UP046
    """Use an undocumented type variable in the base and a method."""

    def echo(self, item: _T) -> _T:
        """Return *item* unchanged."""
        raise NotImplementedError


class CovariantHolder(Generic[_T_co]):  # NoQA: UP046
    """Use a covariant type variable."""


class BoundHolder(Generic[_T_bound]):  # NoQA: UP046
    """Use a bound type variable."""


class ConstrainedHolder(Generic[_T_constrained]):  # NoQA: UP046
    """Use a constrained type variable."""


class ParamSpecHolder(Generic[_P]):  # NoQA: UP046
    """Use a ParamSpec as a generic parameter."""


def identity(value: _T) -> _T:  # NoQA: UP047
    """Return *value* unchanged from a module-level function."""
    raise NotImplementedError
