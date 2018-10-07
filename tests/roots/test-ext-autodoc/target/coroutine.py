class AsyncClass:
    async def do_coroutine(self):
        """A documented coroutine function"""
        attr_coro_result = await _other_coro_func()  # NOQA


async def _other_coro_func():
    return "run"
