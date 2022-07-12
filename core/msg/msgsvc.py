import logging
import asyncio
import typing
from core.util import tasks, util
from core.msg import msgabc, msgftr


class TaskMailer(msgabc.Mailer):

    def __init__(self, subscriber: msgabc.Subscriber):
        self._subscriber = subscriber
        self._task, self._queue = None, None

    def is_running(self) -> bool:
        return self._task is not None

    def start(self) -> asyncio.Task:
        self._queue = asyncio.Queue()
        self._task = tasks.task_start(self._run(), name=util.obj_to_str(self))
        return self._task

    def get_subscriber(self) -> msgabc.Subscriber:
        return self._subscriber

    def post(self, *vargs):
        if not self.is_running():
            return False
        message = msgabc.Message.from_vargs(*vargs)
        if message is msgabc.STOP:
            self._task = None
        try:
            if message is msgabc.STOP or self._subscriber.accepts(message):
                self._queue.put_nowait(message)
        except Exception as e:
            logging.warning('Posting exception. raised: %s', e)
        return self.is_running()

    async def stop(self):
        task = self._task
        if not self.is_running():
            return
        # Not calling queue.join() because STOP will end the tasks.
        # Any message after STOP should stay in queue and be ignored.
        self.post(msgabc.STOP)
        await task

    async def _run(self) -> typing.Any:
        result, running = None, True
        while running:
            result = None
            message = await self._queue.get()   # blocking
            if (message is not msgabc.STOP) or (message is msgabc.STOP and self._subscriber.accepts(msgabc.STOP)):
                result = await msgabc.try_handle('TaskMailer', self._subscriber, message)
            if result is not None or message is msgabc.STOP:
                running = False
                if result is None:
                    result = True
            self._queue.task_done()
        tasks.task_end(self._task)
        self._task, self._queue = None, None
        return result


class TaskMulticastMailer(msgabc.MulticastMailer):

    def __init__(self, msg_filter: msgabc.Filter = msgftr.AcceptAll()):
        self._subscriber = _TaskMulticastSubscriber(self, msg_filter)
        self._mailer = TaskMailer(self._subscriber)

    def start(self) -> asyncio.Task:
        return self._mailer.start()

    def register(self, subscriber: msgabc.Subscriber):
        return self._subscriber.add_mailer(subscriber).start()

    def post(self, *vargs):
        return self._mailer.post(*vargs)

    async def stop(self):
        expired = self._subscriber.mailers.copy()
        await self._mailer.stop()
        for mailer in iter(expired):
            await mailer.stop()   # This may post STOP again, but they will just be ignored


class _TaskMulticastSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer, msg_filter: msgabc.Filter):
        super().__init__(msgftr.Or(msg_filter, msgftr.IsStop()))
        self.mailer = mailer
        self.mailers = []

    def add_mailer(self, subscriber: msgabc.Subscriber) -> TaskMailer:
        mailer = TaskMailer(subscriber)
        self.mailers.append(mailer)
        return mailer

    def handle(self, message):
        expired = []
        for mailer in iter(self.mailers):
            if not mailer.post(message):
                expired.append(mailer)
        for mailer in iter(expired):
            self.mailers.remove(mailer)
        return None
