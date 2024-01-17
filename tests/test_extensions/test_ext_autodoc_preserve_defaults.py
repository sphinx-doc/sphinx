"""Test the autodoc extension."""

import pytest

from tests.test_extensions.test_ext_autodoc import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc',
                    confoverrides={'autodoc_preserve_defaults': True})
def test_preserve_defaults(app):
    color = "0xFFFFFF"

    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target.preserve_defaults', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.preserve_defaults',
        '',
        '',
        '.. py:class:: Class()',
        '   :module: target.preserve_defaults',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Class.clsmeth(name: str = CONSTANT, sentinel: ~typing.Any = '
        'SENTINEL, now: ~datetime.datetime = datetime.now(), color: int = %s, *, '
        'kwarg1, kwarg2=%s) -> None' % (color, color),
        '      :module: target.preserve_defaults',
        '      :classmethod:',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Class.meth(name: str = CONSTANT, sentinel: ~typing.Any = '
        'SENTINEL, now: ~datetime.datetime = datetime.now(), color: int = %s, *, '
        'kwarg1, kwarg2=%s) -> None' % (color, color),
        '      :module: target.preserve_defaults',
        '',
        '      docstring',
        '',
        '',
        '.. py:class:: MultiLine()',
        '   :module: target.preserve_defaults',
        '',
        '   docstring',
        '',
        '',
        '   .. py:property:: MultiLine.prop1',
        '      :module: target.preserve_defaults',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: MultiLine.prop2',
        '      :module: target.preserve_defaults',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: MultiLine.prop3',
        '      :module: target.preserve_defaults',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: MultiLine.prop4',
        '      :module: target.preserve_defaults',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: MultiLine.prop5',
        '      :module: target.preserve_defaults',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: foo(name: str = CONSTANT, sentinel: ~typing.Any = SENTINEL, '
        'now: ~datetime.datetime = datetime.now(), color: int = %s, *, kwarg1, '
        'kwarg2=%s) -> None' % (color, color),
        '   :module: target.preserve_defaults',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: get_sentinel(custom=SENTINEL)',
        '   :module: target.preserve_defaults',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc',
                    confoverrides={'autodoc_preserve_defaults': True})
def test_preserve_defaults_special_constructs(app):
    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target.preserve_defaults_special_constructs', options)

    # * dataclasses.dataclass:
    #   - __init__ source code is not available
    #   - default values specified at class level are not discovered
    #   - values wrapped in a field(...) expression cannot be analyzed
    #     easily even if annotations were to be parsed
    # * typing.NamedTuple:
    #   - __init__ source code is not available
    #   - default values specified at class level are not discovered
    # * collections.namedtuple:
    #   - default values are specified as "default=(d1, d2, ...)"
    #
    # In the future, it might be possible to find some additional default
    # values by parsing the source code of the annotations but the task is
    # rather complex.

    assert list(actual) == [
        '',
        '.. py:module:: target.preserve_defaults_special_constructs',
        '',
        '',
        '.. py:class:: DataClass('
        'a: int, b: object = <object object>, c: list[int] = <factory>)',
        '   :module: target.preserve_defaults_special_constructs',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: DataClassNoInit()',
        '   :module: target.preserve_defaults_special_constructs',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: MyNamedTuple1('
        'a: int, b: object = <object object>, c: list[int] = [1, 2, 3])',
        '   :module: target.preserve_defaults_special_constructs',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: MyNamedTuple1.a',
        '      :module: target.preserve_defaults_special_constructs',
        '      :type: int',
        '',
        '      Alias for field number 0',
        '',
        '',
        '   .. py:attribute:: MyNamedTuple1.b',
        '      :module: target.preserve_defaults_special_constructs',
        '      :type: object',
        '',
        '      Alias for field number 1',
        '',
        '',
        '   .. py:attribute:: MyNamedTuple1.c',
        '      :module: target.preserve_defaults_special_constructs',
        '      :type: list[int]',
        '',
        '      Alias for field number 2',
        '',
        '',
        '.. py:class:: MyNamedTuple2(a=0, b=<object object>)',
        '   :module: target.preserve_defaults_special_constructs',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: MyTypedDict',
        '   :module: target.preserve_defaults_special_constructs',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: SENTINEL',
        '   :module: target.preserve_defaults_special_constructs',
        '   :value: <object object>',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: foo(x, y, z=SENTINEL)',
        '   :module: target.preserve_defaults_special_constructs',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: ze_lambda(z=SENTINEL)',
        '   :module: target.preserve_defaults_special_constructs',
        '',
        '   docstring',
        '',
    ]
