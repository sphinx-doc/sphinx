from functools import cached_property


class Foo:
    @cached_property
    def prop(self) -> int:
        return 1
