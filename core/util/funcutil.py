import typing
import logging
import asyncio
import inspect
from functools import wraps
# ALLOW util.util


def to_async(func: typing.Callable) -> typing.Callable:
    @wraps(func)
    async def run(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return run


async def silently_cleanup(obj: typing.Any):
    if obj is None:
        return
    if hasattr(obj, 'stop'):
        await silently_call(obj.stop)
    if hasattr(obj, 'close'):
        await silently_call(obj.close)
    if hasattr(obj, 'shutdown'):
        await silently_call(obj.shutdown)
    if hasattr(obj, 'dispose'):
        await silently_call(obj.dispose)
    if hasattr(obj, 'cleanup'):
        await silently_call(obj.cleanup)


async def silently_call(invokable: typing.Union[typing.Callable, typing.Coroutine]):
    if not invokable:
        return
    if inspect.iscoroutine(invokable):
        try:
            await invokable
        except Exception as e:
            logging.debug('silently_call(coroutine) %s', repr(e))
        return
    if not callable(invokable):
        return
    try:
        if inspect.iscoroutinefunction(invokable):
            await invokable()
        else:
            invokable()
    except Exception as e:
        logging.debug('silently_call(callable) %s', repr(e))
