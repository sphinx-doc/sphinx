from types import ModuleType

from sphinx.ext.autodoc._dynamic._type_comments import (
    ModuleAnalyzer,
    _update_module_annotations_from_type_comments,
)


def test_explicit_empty_class_annotations_are_preserved(monkeypatch):
    module = ModuleType('autodoc_type_comment_target')

    class Model:
        __annotations__ = {}

    module.Model = Model

    class Analyzer:
        annotations = {('Model', 'field'): 'int'}

        def analyze(self):
            pass

    analyzer = Analyzer()
    monkeypatch.setattr(
        ModuleAnalyzer,
        'for_module',
        classmethod(lambda cls, name: analyzer),
    )

    _update_module_annotations_from_type_comments(module)

    assert Model.__annotations__ == {}
