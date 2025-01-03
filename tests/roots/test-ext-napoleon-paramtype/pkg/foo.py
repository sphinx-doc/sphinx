class Foo:
    """The foo."""

    def do(
        self,
        *,
        keyword_paramtype,
        keyword_kwtype,
        kwarg_paramtype,
        kwarg_kwtype,
        kwparam_paramtype,
        kwparam_kwtype,
    ):
        """Some method.

        :keyword keyword_paramtype: some param
        :paramtype keyword_paramtype: list[int]
        :keyword keyword_kwtype: some param
        :kwtype keyword_kwtype: list[int]
        :kwarg kwarg_paramtype: some param
        :paramtype kwarg_paramtype: list[int]
        :kwarg kwarg_kwtype: some param
        :kwtype kwarg_kwtype: list[int]
        :kwparam kwparam_paramtype: some param
        :paramtype kwparam_paramtype: list[int]
        :kwparam kwparam_kwtype: some param
        :kwtype kwparam_kwtype: list[int]
        """
