"""Test the build process with gettext builder with the test root."""

from __future__ import annotations

import gettext
import re
import subprocess
from contextlib import chdir
from pathlib import Path
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

import pytest

from sphinx.builders.gettext import Catalog, MsgOrigin
from sphinx.testing.util import SphinxTestApp

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp

_MSGID_PATTERN = re.compile(r'msgid "((?:\n|.)*?)"\nmsgstr', re.MULTILINE)


def get_msgids(pot: str) -> list[str]:
    matches = _MSGID_PATTERN.findall(pot)
    return [m.replace('"\n"', '') for m in matches[1:]]


def test_Catalog_duplicated_message() -> None:
    catalog = Catalog()
    catalog.add('hello', MsgOrigin('/path/to/filename', 1))
    catalog.add('hello', MsgOrigin('/path/to/filename', 1))
    catalog.add('hello', MsgOrigin('/path/to/filename', 2))
    catalog.add('hello', MsgOrigin('/path/to/yetanother', 1))
    catalog.add('world', MsgOrigin('/path/to/filename', 1))

    assert len(list(catalog)) == 2

    msg1, msg2 = list(catalog)
    assert msg1.text == 'hello'
    assert msg1.locations == [
        ('/path/to/filename', 1),
        ('/path/to/filename', 2),
        ('/path/to/yetanother', 1),
    ]
    assert msg2.text == 'world'
    assert msg2.locations == [('/path/to/filename', 1)]


@pytest.mark.sphinx(
    'gettext',
    testroot='root',
    srcdir='root-gettext',
)
def test_build_gettext(app: SphinxTestApp) -> None:
    # Generic build; should fail only when the builder is horribly broken.
    app.build(force_all=True)

    # Do messages end up in the correct location?
    # top-level documents end up in a message catalog
    assert (app.outdir / 'extapi.pot').is_file()
    # directory items are grouped into sections
    assert (app.outdir / 'subdir.pot').is_file()

    # regression test for https://github.com/sphinx-doc/sphinx/issues/960
    catalog = (app.outdir / 'markup.pot').read_text(encoding='utf8')
    assert 'msgid "something, something else, something more"' in catalog


@pytest.mark.sphinx(
    'gettext',
    testroot='root',
    srcdir='root-gettext',
)
def test_msgfmt(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    (app.outdir / 'en' / 'LC_MESSAGES').mkdir(parents=True, exist_ok=True)
    with chdir(app.outdir):
        try:
            args = [
                'msginit',
                '--no-translator',
                '-i',
                'markup.pot',
                '--locale',
                'en_US',
            ]
            subprocess.run(args, capture_output=True, check=True)
        except OSError:
            pytest.skip()  # most likely msginit was not found
        except CalledProcessError as exc:
            print(exc.stdout)
            print(exc.stderr)
            msg = f'msginit exited with return code {exc.returncode}'
            raise AssertionError(msg) from exc

        assert (app.outdir / 'en_US.po').is_file(), 'msginit failed'
        try:
            args = [
                'msgfmt',
                'en_US.po',
                '-o',
                str(Path('en', 'LC_MESSAGES', 'test_root.mo')),
            ]
            subprocess.run(args, capture_output=True, check=True)
        except OSError:
            pytest.skip()  # most likely msgfmt was not found
        except CalledProcessError as exc:
            print(exc.stdout)
            print(exc.stderr)
            msg = f'msgfmt exited with return code {exc.returncode}'
            raise AssertionError(msg) from exc

        mo = app.outdir / 'en' / 'LC_MESSAGES' / 'test_root.mo'
        assert mo.is_file(), 'msgfmt failed'

    _ = gettext.translation('test_root', app.outdir, languages=['en']).gettext
    assert _('Testing various markup') == 'Testing various markup'


@pytest.mark.sphinx(
    'gettext',
    testroot='intl',
    srcdir='gettext',
    confoverrides={'gettext_compact': False},
)
def test_gettext_index_entries(app: SphinxTestApp) -> None:
    # regression test for https://github.com/sphinx-doc/sphinx/issues/976
    app.build(filenames=[app.srcdir / 'index_entries.txt'])

    pot = (app.outdir / 'index_entries.pot').read_text(encoding='utf8')
    msg_ids = get_msgids(pot)

    assert msg_ids == [
        'i18n with index entries',
        'index target section',
        'this is :index:`Newsletter` target paragraph.',
        'various index entries',
        "That's all.",
        'Mailing List',
        'Newsletter',
        'Recipients List',
        'First',
        'Second',
        'Third',
        'Entry',
        'See',
    ]


@pytest.mark.sphinx(
    'gettext',
    testroot='intl',
    srcdir='gettext',
    confoverrides={'gettext_compact': False, 'gettext_additional_targets': []},
)
def test_gettext_disable_index_entries(app: SphinxTestApp) -> None:
    # regression test for https://github.com/sphinx-doc/sphinx/issues/976
    app.env._pickled_doctree_cache.clear()  # clear cache
    app.build(filenames=[app.srcdir / 'index_entries.txt'])

    pot = (app.outdir / 'index_entries.pot').read_text(encoding='utf8')
    msg_ids = get_msgids(pot)

    assert msg_ids == [
        'i18n with index entries',
        'index target section',
        'this is :index:`Newsletter` target paragraph.',
        'various index entries',
        "That's all.",
    ]


@pytest.mark.sphinx(
    'gettext',
    testroot='intl',
    srcdir='gettext',
)
def test_gettext_template(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    assert (app.outdir / 'sphinx.pot').is_file()

    result = (app.outdir / 'sphinx.pot').read_text(encoding='utf8')
    assert 'Welcome' in result
    assert 'Sphinx %(version)s' in result


@pytest.mark.sphinx('gettext', testroot='gettext-template')
def test_gettext_template_msgid_order_in_sphinxpot(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert (app.outdir / 'sphinx.pot').is_file()

    result = (app.outdir / 'sphinx.pot').read_text(encoding='utf8')
    assert re.search(
        (
            'msgid "Template 1".*'
            'msgid "This is Template 1\\.".*'
            'msgid "Template 2".*'
            'msgid "This is Template 2\\.".*'
        ),
        result,
        flags=re.DOTALL,
    )


@pytest.mark.sphinx('gettext', testroot='gettext-custom-output-template')
def test_gettext_custom_output_template(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert (app.outdir / 'index.pot').is_file()

    result = (app.outdir / 'index.pot').read_text(encoding='utf8')
    assert 'EVEN MORE DESCRIPTIVE TITLE' in result


@pytest.mark.sphinx(
    'gettext',
    testroot='root',
    srcdir='root-gettext',
    confoverrides={'gettext_compact': 'documentation'},
)
def test_build_single_pot(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    assert (app.outdir / 'documentation.pot').is_file()

    result = (app.outdir / 'documentation.pot').read_text(encoding='utf8')
    assert re.search(
        (
            'msgid "Todo".*'
            'msgid "Like footnotes.".*'
            'msgid "The minute.".*'
            'msgid "Generated section".*'
        ),
        result,
        flags=re.DOTALL,
    )


@pytest.mark.sphinx(
    'gettext',
    testroot='intl_substitution_definitions',
    srcdir='gettext-subst',
    confoverrides={'gettext_compact': False, 'gettext_additional_targets': ['image']},
)
def test_gettext_prolog_epilog_substitution(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    assert (app.outdir / 'prolog_epilog_substitution.pot').is_file()
    pot = (app.outdir / 'prolog_epilog_substitution.pot').read_text(encoding='utf8')
    msg_ids = get_msgids(pot)

    assert msg_ids == [
        'i18n with prologue and epilogue substitutions',
        'This is content that contains |subst_prolog_1|.',
        'Substituted image |subst_prolog_2| here.',
        'subst_prolog_2',
        '.. image:: /img.png',
        'This is content that contains |subst_epilog_1|.',
        'Substituted image |subst_epilog_2| here.',
        'subst_epilog_2',
        '.. image:: /i18n.png',
    ]


@pytest.mark.sphinx(
    'gettext',
    testroot='intl_substitution_definitions',
    srcdir='gettext-subst',
    confoverrides={'gettext_compact': False, 'gettext_additional_targets': ['image']},
)
def test_gettext_prolog_epilog_substitution_excluded(app: SphinxTestApp) -> None:
    # regression test for https://github.com/sphinx-doc/sphinx/issues/9428
    app.build(force_all=True)

    assert (app.outdir / 'prolog_epilog_substitution_excluded.pot').is_file()
    pot = (app.outdir / 'prolog_epilog_substitution_excluded.pot').read_text(
        encoding='utf8'
    )
    msg_ids = get_msgids(pot)

    assert msg_ids == [
        'i18n without prologue and epilogue substitutions',
        'This is content that does not include prologue and epilogue substitutions.',
    ]


@pytest.mark.sphinx(
    'gettext',
    testroot='root',
    srcdir='gettext',
    confoverrides={
        'gettext_compact': False,
        'gettext_additional_targets': ['literal-block', 'doctest-block'],
    },
)
def test_gettext_literalblock_additional(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    assert (app.outdir / 'literalblock.pot').is_file()
    pot = (app.outdir / 'literalblock.pot').read_text(encoding='utf8')
    msg_ids = get_msgids(pot)

    assert msg_ids == [
        'i18n with literal block',
        'Correct literal block::',
        'this is\\nliteral block',
        'Missing literal block::',
        "That's all.",
        'included raw.txt',
        '===\\nRaw\\n===\\n\\n.. raw:: html\\n\\n   <iframe src=\\"https://sphinx-doc.org\\"></iframe>\\n\\n',
        'code blocks',
        "def main\\n   'result'\\nend",
        '#include <stdlib.h>\\nint main(int argc, char** argv)\\n{\\n    return 0;\\n}',
        'example of C language',
        '#include <stdio.h>\\nint main(int argc, char** argv)\\n{\\n    return 0;\\n}',
        'literal-block\\nin list',
        'test_code_for_noqa()\\ncontinued()',
        'doctest blocks',
        '>>> import sys  # sys importing\\n>>> def main():  # define main '
        "function\\n...     sys.stdout.write('hello')  # call write method of "
        "stdout object\\n>>>\\n>>> if __name__ == '__main__':  # if run this py "
        'file as python script\\n...     main()  # call main',
    ]


@pytest.mark.sphinx('gettext', testroot='intl', srcdir='gettext')
def test_gettext_trailing_backslashes(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    assert (app.outdir / 'backslashes.pot').is_file()
    pot = (app.outdir / 'backslashes.pot').read_text(encoding='utf8')
    msg_ids = get_msgids(pot)
    assert msg_ids == [
        'i18n with backslashes',
        (
            'line 1 line 2 line 3 '
            # middle backslashes are escaped normally
            'line 4a \\\\ and 4b '
            # whitespaces after backslashes are dropped
            'line       with spaces after backslash '
            'last line       with spaces '
            'and done 1'
        ),
        'a b c',
        'last trailing \\\\ \\\\ is ignored',
        'See [#]_',
        'footnote with backslashes and done 2',
        'directive with backslashes',
    ]
