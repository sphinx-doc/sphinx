import asyncio
from functools import wraps


class AsyncClass:
    async def do_coroutine(self) -> None:
        """A documented coroutine function"""
        attr_coro_result = await _other_coro_func()

    @classmethod
    async def do_coroutine2(cls) -> None:
        """A documented coroutine classmethod"""
        pass

    @staticmethod
    async def do_coroutine3() -> None:
        """A documented coroutine staticmethod"""
        pass

    async def do_asyncgen(self):
        """A documented async generator"""
        yield


async def _other_coro_func() -> str:  # NoQA: RUF029
    return 'run'


def myawait(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        awaitable = f(*args, **kwargs)
        return asyncio.run(awaitable)

    return wrapper


sync_func = myawait(_other_coro_func)
