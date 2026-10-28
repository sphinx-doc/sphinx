from sphinx.ext.autodoc._dynamic._type_comments import (
    _annotations_for_type_comment_update,
)


def test_type_comment_update_preserves_explicitly_cleared_annotations() -> None:
    class RuntimeModel:
        value: int

    RuntimeModel.__annotations__ = {}

    assert _annotations_for_type_comment_update(RuntimeModel) is None
    assert RuntimeModel.__annotations__ == {}


def test_type_comment_update_copies_normal_annotations() -> None:
    class Model:
        value: int

    annotations = _annotations_for_type_comment_update(Model)

    assert annotations == {'value': int}
    assert annotations is not Model.__annotations__
