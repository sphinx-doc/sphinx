"""Check Python modules for coverage.

Unlike the coverage extension, this one focuses exclusively on Python code,
including checking that all parameters and return types are documented too.
"""

from __future__ import annotations

import inspect
import itertools
import json
import re
from importlib import import_module
from os import path
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, cast

import sphinx
from sphinx.builders import Builder
from sphinx.domains.python import PythonDomain
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.inspect import safe_getattr

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from types import FunctionType, MethodType, ModuleType

    from sphinx.application import Sphinx

logger = logging.getLogger(__name__)


class DocEntry(NamedTuple):
    kind: Literal["module", "class", "function", "parameter"]
    full_name: str
    documented: bool


class PyCoverageBuilder(Builder):
    """
    Evaluates coverage of Python code in the documentation.
    """

    name = "pycoverage"
    epilog = __(
        "Testing of coverage in the sources finished, look at the "
        "results in %(outdir)s" + path.sep + "pycov.json."
    )

    def init(self) -> None:
        self.domain = cast(PythonDomain, self.env.get_domain("py"))
        self.doc_entries: list[DocEntry] = []
        self.excess_doc_params: list[str] = []

    def write(
        self,
        build_docnames: Iterable[str] | None,
        updated_docnames: Sequence[str],
        method: str = "update",
    ) -> None:
        self.build_py_coverage()
        self.write_py_coverage()

    def get_outdated_docs(self) -> str:
        return "Python coverage overview"

    def build_py_coverage(self) -> None:
        modules: set[str] = set()
        for mod_name in self.domain.modules:
            top_module = mod_name.split(".", maxsplit=1)[0]
            modules.add(top_module)
            modules.add(mod_name)

        for mod_name in sorted(modules):
            try:
                mod = import_module(mod_name)
            except ImportError as err:
                logger.warning(__("module %s could not be imported: %s"), mod_name, err)
                self.doc_entries.append(DocEntry("module", mod_name, False))
            else:
                self._visit_module(mod, mod_name)

    def _visit_module(self, mod: ModuleType, full_name: str) -> None:
        for name, member in inspect.getmembers(mod):
            if name.startswith("_"):
                continue
            member_full_name = f"{full_name}.{name}"

            if inspect.isclass(member):
                self._visit_class(member, member_full_name)

            elif inspect.isfunction(member):
                self._visit_func(member, member_full_name, bound=False)

    def _visit_class(self, cls: type[Any], full_name: str) -> None:
        self.doc_entries.append(
            DocEntry("class", full_name, full_name in self.domain.objects)
        )

        for name, kind, defining_cls, _attr in inspect.classify_class_attrs(cls):
            if name.startswith("_"):
                continue

            if defining_cls != cls:
                continue

            if kind == "data":
                continue
            if kind == "property":
                continue

            attr = safe_getattr(cls, name)  # can't use _attr for classmethods
            self._visit_func(attr, f"{full_name}.{name}", bound=kind == "method")

    def _visit_func(
        self, func: FunctionType | MethodType, full_name: str, *, bound: bool
    ) -> None:
        documented = full_name in self.domain.objects
        self.doc_entries.append(DocEntry("function", full_name, documented))
        if documented:
            sig = inspect.signature(func)
            docstring = func.__doc__ or ""

            documented_names = set(re.findall(r":param (\w+):", func.__doc__ or ""))

            for param in itertools.islice(
                sig.parameters.values(),
                1 if bound else 0,
                None,
            ):
                full_param_name = f"{full_name}.{param.name}"
                self.doc_entries.append(
                    DocEntry(
                        "parameter", full_param_name, param.name in documented_names
                    )
                )
                documented_names.discard(param.name)

            for param_name in documented_names:
                full_param_name = f"{full_name}.{param_name}"
                self.excess_doc_params.append(full_param_name)

            if sig.return_annotation not in (inspect.Signature.empty, None, "None"):
                full_param_name = f"{full_name}.return"
                self.doc_entries.append(
                    DocEntry(
                        "parameter",
                        full_param_name,
                        ":return:" in docstring or ":returns" in docstring,
                    )
                )

    def write_py_coverage(self) -> None:
        output_file = path.join(self.outdir, "pycov.json")

        coverage: dict[str, tuple[int, int]] = {}

        for entry in self.doc_entries:
            current_part = ""
            for part in entry.full_name.split("."):
                current_part += f".{part}"
                documented, total = coverage.setdefault(current_part, (0, 0))
                coverage[current_part] = (documented + entry.documented, total + 1)

        lines = (
            json.dumps(
                {
                    "entry": entry,
                    "documented": documented,
                    "total": total,
                    "percent": documented / total,
                }
            )
            for entry, (documented, total) in coverage.items()
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("[\n  ")
            f.write(",\n  ".join(lines))
            f.write("]\n")


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_builder(PyCoverageBuilder)
    return {"version": sphinx.__display_version__, "parallel_read_safe": True}
