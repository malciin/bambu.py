import asyncio
from typing import TypeVar

T = TypeVar("T")

def get_or_none(dict: dict[str, T], key: str) -> T:
    if key not in dict: return None

    return dict[key]

def set_future(future: asyncio.Future[T], value: T, loop: asyncio.AbstractEventLoop):
    async def __set_future(future: asyncio.Future[T], value: T):
        future.set_result(value)

    asyncio.run_coroutine_threadsafe(__set_future(future, value), loop)
