import inspect
import logging
import typing
import asyncio
from functools import partial, wraps
# ALLOW util.util


def to_async(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, partial(func, *args, **kwargs))

    return run


def callable_dict(obj: typing.Any, names: typing.Collection[str]) -> typing.Dict[str, typing.Callable]:
    result = {}
    for name in names:
        if hasattr(obj, name):
            attribute = getattr(obj, name)
            if callable(attribute):
                result[name] = attribute
    return result


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
            logging.debug('silently_call(coroutine) ' + repr(e))
        return
    if not callable(invokable):
        return
    try:
        if inspect.iscoroutinefunction(invokable):
            await invokable()
        else:
            invokable()
    except Exception as e:
        logging.debug('silently_call(callable) ' + repr(e))
