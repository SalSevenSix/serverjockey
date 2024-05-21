import asyncio
import logging
import typing
# ALLOW const.* util.*


class _Tasker:
    __instance = None

    @staticmethod
    def instance():
        if not _Tasker.__instance:
            _Tasker.__instance = _Tasker()
        return _Tasker.__instance

    def __init__(self):
        self._tasks = []

    def task_start(self, coro: typing.Coroutine, name: str) -> asyncio.Task:
        task = asyncio.create_task(coro, name=name)
        self._tasks.append(task)
        logging.debug('tsk> START ({}) : {}'.format(len(self._tasks), task))
        return task

    def task_end(self, task: asyncio.Task):
        self._tasks.remove(task)
        logging.debug('tsk> END   ({}) : {}'.format(len(self._tasks), task))

    def dump(self):
        for task in self._tasks:
            logging.debug('tsk> REMAINING ' + repr(task))


def _str_name(name: typing.Any) -> str:
    if isinstance(name, str):
        return name
    return type(name).__name__ + '[' + str(id(name)) + ']'


def task_start(coro: typing.Coroutine, name: typing.Any) -> asyncio.Task:
    return _Tasker.instance().task_start(coro, _str_name(name))


def task_fork(coro: typing.Coroutine, name: typing.Any) -> asyncio.Task:
    task = asyncio.create_task(coro, name=_str_name(name))
    logging.debug('tsk> FORK       : {}'.format(task))
    return task


def task_end(task: asyncio.Task):
    _Tasker.instance().task_end(task)


def dump():
    _Tasker.instance().dump()


async def wait_for(task: asyncio.Task, timeout: float):
    if not task:
        return
    try:
        await asyncio.wait_for(task, timeout)
    except asyncio.TimeoutError:
        task.cancel()
        task_end(task)
