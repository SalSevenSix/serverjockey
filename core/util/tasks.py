import asyncio
import logging
import typing
# ALLOW util.*


class _Tasker:

    def __init__(self):
        self._tasks = []

    def task_start(self, coro: typing.Coroutine, name: str) -> asyncio.Task:
        task = asyncio.create_task(coro, name=name)
        self._tasks.append(task)
        logging.debug('tsk> START (%s) : %s', len(self._tasks), repr(task))
        return task

    def task_end(self, task: asyncio.Task):
        self._tasks.remove(task)
        logging.debug('tsk> END   (%s) : %s', len(self._tasks), repr(task))

    def dump(self):
        for task in self._tasks:
            logging.debug('tsk> REMAINING %s', repr(task))


_TASKER = _Tasker()


def _str_name(name: typing.Any) -> str:
    if isinstance(name, str):
        return name
    return type(name).__name__ + '[' + str(id(name)) + ']'


def task_start(coro: typing.Coroutine, name: typing.Any) -> asyncio.Task:
    return _TASKER.task_start(coro, _str_name(name))


def task_fork(coro: typing.Coroutine, name: typing.Any) -> asyncio.Task:
    task = asyncio.create_task(coro, name=_str_name(name))
    logging.debug('tsk> FORK : %s', repr(task))
    return task


def task_end(task: asyncio.Task):
    _TASKER.task_end(task)


def dump():
    _TASKER.dump()


async def wait_for(task: asyncio.Task, timeout: float):
    if not task:
        return
    try:
        await asyncio.wait_for(task, timeout)
    except asyncio.TimeoutError:
        task.cancel()
        task_end(task)
