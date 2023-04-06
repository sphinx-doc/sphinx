import pytest


@pytest.mark.sphinx('javadoctest', testroot='ext-javadoctest')
def test_build(app, status, warning):
    app.builder.build_all()
    if app.statuscode != 0:
        raise AssertionError('failures in doctests:' + status.getvalue())


@pytest.mark.sphinx('javadoctest', testroot='ext-javadoctest-maven')
def test_build_maven(app, status, warning):
    app.builder.build_all()
    if app.statuscode != 0:
        raise AssertionError('failures in doctests:' + status.getvalue())
