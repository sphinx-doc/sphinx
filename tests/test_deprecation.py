import warnings
from pathlib import Path

import pytest

from sphinx import deprecation


def test_old_jinja_suffix_warning_is_warning():
    assert isinstance(deprecation.OldJinjaSuffixWarning, type)
    assert issubclass(deprecation.OldJinjaSuffixWarning, Warning)
    assert issubclass(deprecation.OldJinjaSuffixWarning, PendingDeprecationWarning)

    with pytest.warns(deprecation.OldJinjaSuffixWarning):
        warnings.warn('test_1', category=deprecation.OldJinjaSuffixWarning)

    with pytest.warns(PendingDeprecationWarning):
        warnings.warn('test_2', category=deprecation.OldJinjaSuffixWarning)

    with pytest.warns(Warning):
        warnings.warn('test_3', category=deprecation.OldJinjaSuffixWarning)


def test_old_jinja_suffix_warning_simplefilter_always(recwarn):
    assert len(recwarn) == 0
    warnings.resetwarnings()

    warnings.simplefilter('always', category=deprecation.OldJinjaSuffixWarning)
    warnings.warn('test_simplefilter_always', category=deprecation.OldJinjaSuffixWarning)

    assert len(recwarn) == 1
    caught_warning = recwarn[0]
    assert caught_warning.category is deprecation.OldJinjaSuffixWarning
    assert str(caught_warning.message) == 'test_simplefilter_always'


def test_old_jinja_suffix_warning_filterwarnings_always(recwarn):
    assert len(recwarn) == 0
    warnings.resetwarnings()

    warnings.filterwarnings('always', category=deprecation.OldJinjaSuffixWarning)
    warnings.warn('test_filterwarnings_always', category=deprecation.OldJinjaSuffixWarning)

    assert len(recwarn) == 1
    caught_warning = recwarn[0]
    assert caught_warning.category is deprecation.OldJinjaSuffixWarning
    assert str(caught_warning.message) == 'test_filterwarnings_always'


def test_old_jinja_suffix_warning_simplefilter_ignore(recwarn):
    assert len(recwarn) == 0
    warnings.resetwarnings()

    warnings.simplefilter('ignore', deprecation.OldJinjaSuffixWarning)
    warnings.warn('test_simplefilter_ignore', category=deprecation.OldJinjaSuffixWarning)

    assert len(recwarn) == 0


def test_old_jinja_suffix_warning_filterwarnings_ignore(recwarn):
    assert len(recwarn) == 0
    warnings.resetwarnings()

    warnings.filterwarnings('ignore', category=deprecation.OldJinjaSuffixWarning)
    warnings.warn('test_filterwarnings_ignore', category=deprecation.OldJinjaSuffixWarning)

    assert len(recwarn) == 0


def test__old_jinja_template_suffix_no_warning_css(recwarn):
    assert len(recwarn) == 0
    warnings.resetwarnings()
    warnings.simplefilter('always', category=deprecation.OldJinjaSuffixWarning)

    deprecation._old_jinja_template_suffix_warning('template.css')

    assert len(recwarn) == 0


def test__old_jinja_template_suffix_no_warning_jinja(recwarn):
    assert len(recwarn) == 0
    warnings.resetwarnings()
    warnings.simplefilter('always', category=deprecation.OldJinjaSuffixWarning)

    deprecation._old_jinja_template_suffix_warning('template.css.jinja')

    assert len(recwarn) == 0


def test__old_jinja_template_suffix_warning__t():
    with pytest.warns(deprecation.OldJinjaSuffixWarning,
                      match=r"the '_t' suffix for Jinja templates is deprecated"):
        deprecation._old_jinja_template_suffix_warning('template.css_t')


def test__old_jinja_template_suffix_warning_stacklevel():
    # _old_jinja_template_suffix_warning is only called within functions that
    # use template files.
    def do_something_with_templates(filename):
        deprecation._old_jinja_template_suffix_warning(filename)

    # TOJTSWS line number marker
    with pytest.warns(deprecation.OldJinjaSuffixWarning) as caught:
        do_something_with_templates('template.css_t')

    lines = [b''] + Path(__file__).read_bytes().splitlines()
    line_number = lines.index(b'    # TOJTSWS line number marker') + 2

    assert len(caught) == 1
    caught_warning = caught[0]
    assert caught_warning.category is deprecation.OldJinjaSuffixWarning
    assert "the '_t' suffix for Jinja templates is deprecated" in str(caught_warning.message)
    assert caught_warning.filename == __file__
    assert caught_warning.lineno == line_number
