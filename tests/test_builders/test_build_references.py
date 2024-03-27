"""Test the build process of the references builder."""

import json

import pytest


@pytest.mark.sphinx('references', testroot='build-refs-basic')
def test_basic(app):
    """Test for a basic document build."""
    app.build()
    # there should be no warnings
    assert not app.warning.getvalue()
    # there should be only one file in the output
    assert [p.relative_to(app.outdir).as_posix() for p in app.outdir.iterdir()] == [
        'references.json'
    ]
    # test the content of the reference file
    content = (app.outdir / 'references.json').read_text('utf-8')
    data = json.loads(content)
    assert data == {
        'std': {
            'doc': {
                'items': {
                    'index': [
                        {
                            'dispname': 'The basic Sphinx documentation for testing',
                            'document': str(app.srcdir / 'index.rst'),
                            'type': 'local',
                        }
                    ]
                },
                'roles': ['doc'],
            },
            'label': {
                'items': {
                    'genindex': [
                        {
                            'dispname': 'Index',
                            'document': str(app.srcdir / 'genindex.rst'),
                            'type': 'local',
                        }
                    ],
                    'modindex': [
                        {
                            'dispname': 'Module Index',
                            'document': str(app.srcdir / 'py-modindex.rst'),
                            'type': 'local',
                        }
                    ],
                    'py-modindex': [
                        {
                            'dispname': 'Python Module Index',
                            'document': str(app.srcdir / 'py-modindex.rst'),
                            'type': 'local',
                        }
                    ],
                    'search': [
                        {
                            'dispname': 'Search Page',
                            'document': str(app.srcdir / 'search.rst'),
                            'type': 'local',
                        }
                    ],
                },
                'roles': ['ref', 'keyword'],
            },
        }
    }


@pytest.mark.sphinx('references', testroot='build-refs-with-intersphinx')
def test_with_intersphinx(app):
    """Test for a document built with an intersphinx mapping configured."""
    app.build()
    # there should be no warnings
    assert not app.warning.getvalue()
    # there should be only one file in the output
    assert [p.relative_to(app.outdir).as_posix() for p in app.outdir.iterdir()] == [
        'references.json'
    ]
    # test the content of the reference file
    content = (app.outdir / 'references.json').read_text('utf-8')
    data = json.loads(content)
    assert data == {
        'std': {
            'doc': {
                'items': {
                    'index': [
                        {
                            'dispname': 'The basic Sphinx documentation for testing',
                            'document': str(app.srcdir / 'index.rst'),
                            'type': 'local',
                        }
                    ]
                },
                'roles': ['doc'],
            },
            'label': {
                'items': {
                    'genindex': [
                        {
                            'dispname': 'Index',
                            'document': str(app.srcdir / 'genindex.rst'),
                            'type': 'local',
                        }
                    ],
                    'modindex': [
                        {
                            'dispname': 'Module Index',
                            'document': str(app.srcdir / 'py-modindex.rst'),
                            'type': 'local',
                        }
                    ],
                    'py-modindex': [
                        {
                            'dispname': 'Python Module Index',
                            'document': str(app.srcdir / 'py-modindex.rst'),
                            'type': 'local',
                        }
                    ],
                    'search': [
                        {
                            'dispname': 'Search Page',
                            'document': str(app.srcdir / 'search.rst'),
                            'type': 'local',
                        }
                    ],
                },
                'roles': ['ref', 'keyword'],
            },
        },
        'py': {
            'module': {
                'items': {
                    'module1': [
                        {
                            'dispname': 'Long Module desc',
                            'key': 'key',
                            'type': 'remote',
                            'url': 'https://example.com/foo.html#module-module1',
                        }
                    ],
                    'module2': [
                        {
                            'key': 'key',
                            'type': 'remote',
                            'url': 'https://example.com/foo.html#module-module2',
                        }
                    ],
                },
                'roles': ['mod', 'obj'],
            }
        },
    }
