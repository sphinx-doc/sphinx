"""Tests for the format-placeholder check in ``utils/babel_runner.py``.

The check exists because babel's ``Catalog.check()`` only validates
messages flagged ``python-brace-format``, which catalogues downloaded
from Transifex largely are not, so damaged placeholders slip through
(see issue #14664).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from babel.messages.catalog import Message

if TYPE_CHECKING:
    from types import ModuleType
    from typing import Any


def _load_babel_runner() -> ModuleType:
    path = Path(__file__).parent.parent / 'utils' / 'babel_runner.py'
    spec = importlib.util.spec_from_file_location('babel_runner', path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


babel_runner = _load_babel_runner()


def _errors(msgid: str | tuple[str, str], msgstr: str | tuple[str, ...]) -> list[str]:
    return babel_runner._placeholder_errors(Message(msgid, msgstr))


def test_clean_named_placeholders_pass() -> None:
    assert _errors('bad value {name!r}', 'mauvaise valeur {name!r}') == []


def test_missing_placeholder_is_not_an_error() -> None:
    # dropping a placeholder never breaks str.format(); extra keyword
    # arguments are simply unused
    assert _errors('bad value {name!r}', 'valeur incorrecte') == []


def test_unknown_placeholder_is_an_error() -> None:
    assert _errors('bad value {name!r}', 'valeur incorrecte {nom!r}') == [
        "placeholder 'nom' in translation does not appear in the msgid"
    ]


def test_damaged_syntax_is_an_error() -> None:
    # the Greek catalogue damage from #14664
    assert _errors(
        "the config value '{name}' has type '{current.__name__}';"
        " expected '{permitted}'.",
        "η τιμή '{name]' έχει τύπο '[current__name__}'; αναμενόμενη {permitted}.",
    ) == ['invalid brace-format syntax in translation']


def test_renamed_placeholder_is_an_error() -> None:
    # the Greek catalogue damage from #14664 (dots dropped from the names)
    assert _errors(
        "value '{name}' has type '{current.__name__}',"
        " defaults to '{default.__name__}'.",
        "τιμή '{name}' έχει τύπο '{current__name__}',"
        " αρχικοποίηση σε '{default__name__}'.",
    ) == [
        "placeholder 'current__name__' in translation does not appear in the msgid",
        "placeholder 'default__name__' in translation does not appear in the msgid",
    ]


def test_placeholder_from_sibling_message_is_an_error() -> None:
    # the Persian catalogue damage from #14664: {permitted} belongs to the
    # other config warning, not this one
    assert _errors(
        "value '{name}' has type '{current.__name__}',"
        " default is '{default.__name__}'.",
        "مقدار '{name}' دارای نوع '{current.__name__}' است،"
        ' حالت پیش‌فرض {permitted} است.',
    ) == ["placeholder 'permitted' in translation does not appear in the msgid"]


def test_damaged_msgid_is_not_a_translation_error() -> None:
    assert _errors('{broken', 'translation {ok}') == []


def test_percent_placeholders_are_checked() -> None:
    assert _errors('bad value %(name)r', 'valeur incorrecte %(nom)r') == [
        "placeholder 'nom' in translation does not appear in the msgid"
    ]


def test_each_plural_form_is_checked() -> None:
    msgid = '{name} files', '{name} files'
    msgstr = 'fichiers {nom}', '{name} fichiers'
    assert _errors(msgid, msgstr) == [
        "placeholder 'nom' in translation does not appear in the msgid"
    ]


def _missing(msgid: str | tuple[str, str], msgstr: str | tuple[str, ...]) -> list[str]:
    return babel_runner._missing_placeholders(Message(msgid, msgstr))


def test_missing_placeholder_is_a_warning() -> None:
    assert _missing('bad value {name!r}', 'valeur incorrecte') == [
        "placeholder 'name' from the msgid is missing in translation"
    ]


def test_missing_percent_placeholder_is_a_warning() -> None:
    assert _missing('bad value %(name)r', 'valeur incorrecte') == [
        "placeholder 'name' from the msgid is missing in translation"
    ]


def test_complete_translation_has_no_missing_placeholders() -> None:
    assert _missing('bad value {name!r}', 'mauvaise valeur {name!r}') == []


def test_reordered_placeholders_are_not_missing() -> None:
    assert _missing('{name} in {path}', 'dans {path}: {name}') == []


def test_plural_placeholder_needs_only_one_form() -> None:
    # the singular form may legitimately omit the count
    msgid = 'one file in {path}', '{n} files in {path}'
    msgstr = 'un fichier dans {path}', '{n} fichiers dans {path}'
    assert _missing(msgid, msgstr) == []
    assert _missing(msgid, ('un fichier', '{n} fichiers')) == [
        "placeholder 'path' from the msgid is missing in translation"
    ]


def test_positional_placeholders_are_not_compared() -> None:
    assert _missing('bad value {}', 'valeur incorrecte') == []


def test_damaged_syntax_is_not_also_reported_missing() -> None:
    assert _missing('bad value {name}', 'valeur incorrecte {name]') == []


def test_run_check_reports_and_excludes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    locale_dir = tmp_path / 'sphinx' / 'locale'
    damaged = dedent(
        """\
        msgid "value '{name}'"
        msgstr "valeur '{nom}'"
        """
    )
    clean = dedent(
        """\
        msgid "value '{name}'"
        msgstr "valeur '{name}'"
        """
    )
    for locale, content in (('fr', clean), ('el', damaged)):
        d = locale_dir / locale / 'LC_MESSAGES'
        d.mkdir(parents=True)
        (d / 'sphinx.po').write_text(content, encoding='utf-8')

    reverted = []

    def fake_git(*args: Any, **kwargs: Any) -> int:
        argv = args[0]
        assert argv[:3] == ('git', 'checkout', '--')
        assert kwargs.get('check') is True
        reverted.append(argv[3])
        return 0

    monkeypatch.setattr(babel_runner, 'ROOT', tmp_path)
    monkeypatch.setattr(babel_runner.subprocess, 'run', fake_git)
    monkeypatch.setattr(babel_runner, '_write_pr_body_line', lambda m: None)

    # plain mode: reports the damaged catalogue and exits non-zero
    with caplog.at_level('WARNING', logger='babel'), pytest.raises(SystemExit) as exc:
        babel_runner.run_check()
    assert exc.value.code == 1
    assert any('el' in record.getMessage() for record in caplog.records)
    # the renamed placeholder is an error only, not also a missing one
    assert not [r for r in caplog.records if r.levelname == 'WARNING']

    # exclusion mode: reverts the damaged catalogue and exits cleanly
    babel_runner.run_check(exclude_failing=True)
    assert len(reverted) == 1
    assert Path(reverted[0]).name == 'sphinx.po'
    assert Path(reverted[0]).parent.parent.name == 'el'


def test_run_check_warns_without_excluding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    d = tmp_path / 'sphinx' / 'locale' / 'el' / 'LC_MESSAGES'
    d.mkdir(parents=True)
    (d / 'sphinx.po').write_text(
        dedent(
            """\
            msgid "value '{name}'"
            msgstr "valeur"
            """
        ),
        encoding='utf-8',
    )

    def fake_git(*_args: Any, **_kwargs: Any) -> int:
        pytest.fail('a catalogue with only missing placeholders was reverted')

    body: list[str] = []
    monkeypatch.setattr(babel_runner, 'ROOT', tmp_path)
    monkeypatch.setattr(babel_runner.subprocess, 'run', fake_git)
    monkeypatch.setattr(babel_runner, '_write_pr_body_line', body.append)

    # neither mode fails or excludes the catalogue
    with caplog.at_level('WARNING', logger='babel'):
        babel_runner.run_check()
        babel_runner.run_check(exclude_failing=True)
    warnings = [r for r in caplog.records if r.levelname == 'WARNING']
    assert len(warnings) == 2
    assert "'name'" in warnings[0].getMessage()
    assert '* el: 1 placeholder' in body
    assert '## Catalogues excluded from this update' not in body
