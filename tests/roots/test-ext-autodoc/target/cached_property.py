from functools import cached_property


class Foo:
    @cached_property
    def prop(self) -> int:
        return 1

    @cached_property
    def prop_with_type_comment(self):
        # type: () -> int
        return 1
