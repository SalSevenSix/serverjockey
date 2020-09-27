import asyncio
import logging


class _Tasker:

    def __init__(self):
        self.task_count = 0

    def task_start(self, coro, name=None):
        task = asyncio.create_task(coro, name=name)
        self.task_count = self.task_count + 1
        logging.debug('Task START ({}) : {}'.format(self.task_count, task))
        return task

    def task_end(self, task):
        self.task_count = self.task_count - 1
        logging.debug('Task END   ({}) : {}'.format(self.task_count, task))


TASKER = _Tasker()


def task_start(coro, name=None):
    return TASKER.task_start(coro, name=name)


def task_end(task):
    TASKER.task_end(task)
