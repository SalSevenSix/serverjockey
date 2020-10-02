import asyncio
import logging
import typing


class _Tasker:
    __instance = None

    @staticmethod
    def instance():
        if not _Tasker.__instance:
            _Tasker.__instance = _Tasker()
        return _Tasker.__instance

    def __init__(self):
        self._task_count = 0

    def task_start(self, coro: typing.Coroutine, name: str) -> asyncio.Task:
        task = asyncio.create_task(coro, name=name)
        self._task_count = self._task_count + 1
        logging.debug('Task START ({}) : {}'.format(self._task_count, task))
        return task

    def task_end(self, task: asyncio.Task):
        self._task_count = self._task_count - 1
        logging.debug('Task END   ({}) : {}'.format(self._task_count, task))


def task_start(coro: typing.Coroutine, name: str) -> asyncio.Task:
    return _Tasker.instance().task_start(coro, name=name)


def task_end(task: asyncio.Task):
    _Tasker.instance().task_end(task)