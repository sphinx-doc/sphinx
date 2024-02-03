"""Test the sphinx.quickstart module."""

import time
from io import StringIO
from os import path

import pytest

from sphinx import application
from sphinx.cmd import quickstart as qs
from sphinx.util.console import coloron, nocolor

warnfile = StringIO()


def setup_module():
    nocolor()


def mock_input(answers, needanswer=False):
    called = set()

    def input_(prompt):
        if prompt in called:
            raise AssertionError('answer for %r missing and no default '
                                 'present' % prompt)
        called.add(prompt)
        for question in answers:
            if prompt.startswith(qs.PROMPT_PREFIX + question):
                return answers[question]
        if needanswer:
            raise AssertionError('answer for %r missing' % prompt)
        return ''
    return input_


real_input = input


def teardown_module():
    qs.term_input = real_input
    coloron()


def test_do_prompt():
    answers = {
        'Q2': 'v2',
        'Q3': 'v3',
        'Q4': 'yes',
        'Q5': 'no',
        'Q6': 'foo',
    }
    qs.term_input = mock_input(answers)

    assert qs.do_prompt('Q1', default='v1') == 'v1'
    assert qs.do_prompt('Q3', default='v3_default') == 'v3'
    assert qs.do_prompt('Q2') == 'v2'
    assert qs.do_prompt('Q4', validator=qs.boolean) is True
    assert qs.do_prompt('Q5', validator=qs.boolean) is False
    with pytest.raises(AssertionError):
        qs.do_prompt('Q6', validator=qs.boolean)


def test_do_prompt_inputstrip():
    answers = {
        'Q1': 'Y',
        'Q2': ' Yes ',
        'Q3': 'N',
        'Q4': 'N ',
    }
    qs.term_input = mock_input(answers)

    assert qs.do_prompt('Q1') == 'Y'
    assert qs.do_prompt('Q2') == 'Yes'
    assert qs.do_prompt('Q3') == 'N'
    assert qs.do_prompt('Q4') == 'N'


def test_do_prompt_with_nonascii():
    answers = {
        'Q1': '\u30c9\u30a4\u30c4',
    }
    qs.term_input = mock_input(answers)
    result = qs.do_prompt('Q1', default='\u65e5\u672c')
    assert result == '\u30c9\u30a4\u30c4'


def test_quickstart_defaults(tmp_path):
    answers = {
        'Root path': str(tmp_path),
        'Project name': 'Sphinx Test',
        'Author name': 'Georg Brandl',
        'Project version': '0.1',
    }
    qs.term_input = mock_input(answers)
    d = {}
    qs.ask_user(d)
    qs.generate(d)

    conffile = tmp_path / 'conf.py'
    assert conffile.is_file()
    ns = {}
    exec(conffile.read_text(encoding='utf8'), ns)  # NoQA: S102
    assert ns['extensions'] == []
    assert ns['templates_path'] == ['_templates']
    assert ns['project'] == 'Sphinx Test'
    assert ns['copyright'] == '%s, Georg Brandl' % time.strftime('%Y')
    assert ns['version'] == '0.1'
    assert ns['release'] == '0.1'
    assert ns['html_static_path'] == ['_static']

    assert (tmp_path / '_static').is_dir()
    assert (tmp_path / '_templates').is_dir()
    assert (tmp_path / 'index.rst').is_file()
    assert (tmp_path / 'Makefile').is_file()
    assert (tmp_path / 'make.bat').is_file()


def test_quickstart_all_answers(tmp_path):
    answers = {
        'Root path': str(tmp_path),
        'Separate source and build': 'y',
        'Name prefix for templates': '.',
        'Project name': 'STASI™',
        'Author name': "Wolfgang Schäuble & G'Beckstein",
        'Project version': '2.0',
        'Project release': '2.0.1',
        'Project language': 'de',
        'Source file suffix': '.txt',
        'Name of your master document': 'contents',
        'autodoc': 'y',
        'doctest': 'yes',
        'intersphinx': 'no',
        'todo': 'y',
        'coverage': 'no',
        'imgmath': 'N',
        'mathjax': 'no',
        'ifconfig': 'no',
        'viewcode': 'no',
        'githubpages': 'no',
        'Create Makefile': 'no',
        'Create Windows command file': 'no',
        'Do you want to use the epub builder': 'yes',
    }
    qs.term_input = mock_input(answers, needanswer=True)
    d = {}
    qs.ask_user(d)
    qs.generate(d)

    conffile = tmp_path / 'source' / 'conf.py'
    assert conffile.is_file()
    ns = {}
    exec(conffile.read_text(encoding='utf8'), ns)  # NoQA: S102
    assert ns['extensions'] == [
        'sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.todo',
    ]
    assert ns['templates_path'] == ['.templates']
    assert ns['source_suffix'] == '.txt'
    assert ns['root_doc'] == 'contents'
    assert ns['project'] == 'STASI™'
    assert ns['copyright'] == "%s, Wolfgang Schäuble & G'Beckstein" % \
        time.strftime('%Y')
    assert ns['version'] == '2.0'
    assert ns['release'] == '2.0.1'
    assert ns['todo_include_todos'] is True
    assert ns['html_static_path'] == ['.static']

    assert (tmp_path / 'build').is_dir()
    assert (tmp_path / 'source' / '.static').is_dir()
    assert (tmp_path / 'source' / '.templates').is_dir()
    assert (tmp_path / 'source' / 'contents.txt').is_file()


def test_generated_files_eol(tmp_path):
    answers = {
        'Root path': str(tmp_path),
        'Project name': 'Sphinx Test',
        'Author name': 'Georg Brandl',
        'Project version': '0.1',
    }
    qs.term_input = mock_input(answers)
    d = {}
    qs.ask_user(d)
    qs.generate(d)

    def assert_eol(filename, eol):
        content = filename.read_bytes().decode()
        assert all(l[-len(eol):] == eol for l in content.splitlines(keepends=True))

    assert_eol(tmp_path / 'make.bat', '\r\n')
    assert_eol(tmp_path / 'Makefile', '\n')


def test_quickstart_and_build(tmp_path):
    answers = {
        'Root path': str(tmp_path),
        'Project name': 'Fullwidth characters: \u30c9\u30a4\u30c4',
        'Author name': 'Georg Brandl',
        'Project version': '0.1',
    }
    qs.term_input = mock_input(answers)
    d = {}
    qs.ask_user(d)
    qs.generate(d)

    app = application.Sphinx(
        tmp_path,  # srcdir
        tmp_path,  # confdir
        (tmp_path / '_build' / 'html'),  # outdir
        (tmp_path / '_build' / '.doctree'),  # doctreedir
        'html',  # buildername
        status=StringIO(),
        warning=warnfile)
    app.build(force_all=True)
    warnings = warnfile.getvalue()
    assert not warnings


def test_default_filename(tmp_path):
    answers = {
        'Root path': str(tmp_path),
        'Project name': '\u30c9\u30a4\u30c4',  # Fullwidth characters only
        'Author name': 'Georg Brandl',
        'Project version': '0.1',
    }
    qs.term_input = mock_input(answers)
    d = {}
    qs.ask_user(d)
    qs.generate(d)

    conffile = tmp_path / 'conf.py'
    assert conffile.is_file()
    ns = {}
    exec(conffile.read_text(encoding='utf8'), ns)  # NoQA: S102


def test_extensions(tmp_path):
    qs.main(['-q', '-p', 'project_name', '-a', 'author',
             '--extensions', 'foo,bar,baz', str(tmp_path)])

    conffile = tmp_path / 'conf.py'
    assert conffile.is_file()
    ns = {}
    exec(conffile.read_text(encoding='utf8'), ns)  # NoQA: S102
    assert ns['extensions'] == ['foo', 'bar', 'baz']


def test_exits_when_existing_confpy(monkeypatch):
    # The code detects existing conf.py with path.is_file()
    # so we mock it as True with pytest's monkeypatch
    def mock_isfile(path):
        return True
    monkeypatch.setattr(path, 'isfile', mock_isfile)

    qs.term_input = mock_input({
        'Please enter a new root path (or just Enter to exit)': '',
    })
    d = {}
    with pytest.raises(SystemExit):
        qs.ask_user(d)
