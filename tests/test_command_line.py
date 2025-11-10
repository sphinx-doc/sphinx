from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.cmd import make_mode
from sphinx.cmd.build import get_parser
from sphinx.cmd.make_mode import run_make_mode

if TYPE_CHECKING:
    from typing import Any

broken_argparse = (
    sys.version_info[:3] <= (3, 12, 6)
    or sys.version_info[:3] == (3, 13, 0)
)  # fmt: skip

DEFAULTS = {
    'filenames': [],
    'jobs': 1,
    'force_all': False,
    'freshenv': False,
    'doctreedir': None,
    'confdir': None,
    'noconfig': False,
    'define': [],
    'htmldefine': [],
    'tags': [],
    'nitpicky': False,
    'verbosity': 0,
    'quiet': False,
    'really_quiet': False,
    'color': 'auto',
    'warnfile': None,
    'warningiserror': False,
    'keep_going': False,
    'traceback': False,
    'pdb': False,
    'exception_on_warning': False,
}

EXPECTED_BUILD_MAIN = {
    'builder': 'html',
    'sourcedir': 'source_dir',
    'outputdir': 'build_dir',
    'filenames': ['filename1', 'filename2'],
    'freshenv': True,
    'noconfig': True,
    'quiet': True,
}

EXPECTED_MAKE_MODE = {
    'builder': 'html',
    'sourcedir': 'source_dir',
    'outputdir': str(Path('build_dir', 'html')),
    'doctreedir': str(Path('build_dir', 'doctrees')),
    'filenames': ['filename1', 'filename2'],
    'freshenv': True,
    'noconfig': True,
    'quiet': True,
}

BUILDER_BUILD_MAIN = [
    '--builder',
    'html',
]
BUILDER_MAKE_MODE = [
    'html',
]
POSITIONAL_DIRS = [
    'source_dir',
    'build_dir',
]
POSITIONAL_FILENAMES = [
    'filename1',
    'filename2',
]
POSITIONAL = POSITIONAL_DIRS + POSITIONAL_FILENAMES
POSITIONAL_MAKE_MODE = BUILDER_MAKE_MODE + POSITIONAL
EARLY_OPTS = [
    '--quiet',
]
LATE_OPTS = [
    '-E',
    '--isolated',
]
OPTS = EARLY_OPTS + LATE_OPTS


def parse_arguments(args: list[str]) -> dict[str, Any]:
    parsed = vars(get_parser().parse_args(args))
    return {k: v for k, v in parsed.items() if k not in DEFAULTS or v != DEFAULTS[k]}


def test_build_main_parse_arguments_pos_first() -> None:
    # <positional...> <opts>
    args = [
        *POSITIONAL,
        *OPTS,
    ]
    assert parse_arguments(args) == EXPECTED_BUILD_MAIN


def test_build_main_parse_arguments_pos_last() -> None:
    # <opts> <positional...>
    args = [
        *OPTS,
        *POSITIONAL,
    ]
    assert parse_arguments(args) == EXPECTED_BUILD_MAIN


def test_build_main_parse_arguments_pos_middle() -> None:
    # <opts> <positional...> <opts>
    args = [
        *EARLY_OPTS,
        *BUILDER_BUILD_MAIN,
        *POSITIONAL,
        *LATE_OPTS,
    ]
    assert parse_arguments(args) == EXPECTED_BUILD_MAIN


@pytest.mark.xfail(
    broken_argparse,
    reason='sphinx-build does not yet support filenames after options',
)
def test_build_main_parse_arguments_filenames_last() -> None:
    args = [
        *POSITIONAL_DIRS,
        *OPTS,
        *POSITIONAL_FILENAMES,
    ]
    assert parse_arguments(args) == EXPECTED_BUILD_MAIN


def test_build_main_parse_arguments_pos_intermixed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = [
        *EARLY_OPTS,
        *BUILDER_BUILD_MAIN,
        *POSITIONAL_DIRS,
        *LATE_OPTS,
        *POSITIONAL_FILENAMES,
    ]
    if broken_argparse:
        with pytest.raises(SystemExit):
            parse_arguments(args)
        stderr = strip_escape_sequences(capsys.readouterr().err).splitlines()
        assert stderr[-1].endswith('error: unrecognized arguments: filename1 filename2')
    else:
        assert parse_arguments(args) == EXPECTED_BUILD_MAIN


def test_make_mode_parse_arguments_pos_first(monkeypatch: pytest.MonkeyPatch) -> None:
    # -M <positional...> <opts>
    monkeypatch.setattr(make_mode, 'build_main', parse_arguments)
    args = [
        *POSITIONAL_MAKE_MODE,
        *OPTS,
    ]
    assert run_make_mode(args) == EXPECTED_MAKE_MODE


def test_make_mode_parse_arguments_pos_last(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # -M <opts> <positional...>
    monkeypatch.setattr(make_mode, 'build_main', parse_arguments)
    args = [
        *OPTS,
        *POSITIONAL_MAKE_MODE,
    ]
    with pytest.raises(SystemExit):
        run_make_mode(args)
    stderr = strip_escape_sequences(capsys.readouterr().err).splitlines()
    assert stderr[-1].endswith('error: argument --builder/-b: expected one argument')


def test_make_mode_parse_arguments_pos_middle(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # -M <opts> <positional...> <opts>
    monkeypatch.setattr(make_mode, 'build_main', parse_arguments)
    args = [
        *EARLY_OPTS,
        *POSITIONAL_MAKE_MODE,
        *LATE_OPTS,
    ]
    with pytest.raises(SystemExit):
        run_make_mode(args)
    stderr = strip_escape_sequences(capsys.readouterr().err).splitlines()
    assert stderr[-1].endswith('error: argument --builder/-b: expected one argument')


@pytest.mark.xfail(
    broken_argparse,
    reason='sphinx-build does not yet support filenames after options',
)
def test_make_mode_parse_arguments_filenames_last(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # -M <positional...> <opts> <filenames...>
    monkeypatch.setattr(make_mode, 'build_main', parse_arguments)
    args = [
        *BUILDER_MAKE_MODE,
        *POSITIONAL_DIRS,
        *OPTS,
        *POSITIONAL_FILENAMES,
    ]
    assert run_make_mode(args) == EXPECTED_MAKE_MODE


def test_make_mode_parse_arguments_pos_intermixed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # -M <opts> <positional...> <opts> <filenames...>
    monkeypatch.setattr(make_mode, 'build_main', parse_arguments)
    args = [
        *EARLY_OPTS,
        *BUILDER_MAKE_MODE,
        *POSITIONAL_DIRS,
        *LATE_OPTS,
        *POSITIONAL_FILENAMES,
    ]
    with pytest.raises(SystemExit):
        run_make_mode(args)
    stderr = strip_escape_sequences(capsys.readouterr().err).splitlines()
    assert stderr[-1].endswith('error: argument --builder/-b: expected one argument')
