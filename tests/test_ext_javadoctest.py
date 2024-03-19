import pytest


@pytest.mark.sphinx('javadoctest', testroot='ext-javadoctest')
def test_build(app, status, warning):
    # app.builder.build_specific(['roots/test-ext-javadoctest/javadoctest.rst'])
    # app.builder.build_specific(['javadoctest.rst'])
    app.builder.build_all()
    assert app.statuscode == 0, 'failures in javadoctest:' + status.getvalue()


@pytest.mark.sphinx('javadoctest', testroot='ext-javadoctest-maven')
def test_build_maven(app, status, warning):
    app.builder.build_all()
    assert app.statuscode == 0, 'failures in doctests:' + status.getvalue()
