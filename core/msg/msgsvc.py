import logging
import asyncio
import typing
# ALLOW util.* msg.msgabc msg.msgftr msg.msgtrf
from core.util import util, tasks, objconv
from core.msg import msgabc, msgftr


class TaskMailer(msgabc.Mailer):

    def __init__(self, subscriber: msgabc.Subscriber):
        self._subscriber = subscriber
        self._queue = asyncio.Queue()
        self._running, self._task = False, None

    def start(self) -> asyncio.Task:
        self._task = tasks.task_start(self._run(), name=objconv.obj_to_str(self))
        self._running = True
        return self._task

    def get_subscriber(self) -> msgabc.Subscriber:
        return self._subscriber

    def post(self, *vargs):
        if not self._running:
            util.clear_queue(self._queue)
            return False
        message = msgabc.Message.from_vargs(*vargs)
        try:
            if message is msgabc.STOP:
                self._running = False
                self._queue.put_nowait(message)
            elif self._subscriber.accepts(message):
                self._queue.put_nowait(message)
        except Exception as e:
            logging.warning('Posting exception. raised: %s', repr(e))
        return self._running

    async def stop(self):
        if not self._running:
            return
        # Not calling queue.join() because STOP will end the tasks.
        # Any message after STOP should stay in queue and be ignored.
        self.post(msgabc.STOP)
        await self._task

    async def _run(self) -> typing.Any:
        result, running = None, True
        while running:
            result = None
            message = await self._queue.get()
            if (message is not msgabc.STOP) or (message is msgabc.STOP and self._subscriber.accepts(msgabc.STOP)):
                result = await msgabc.try_handle(self._subscriber, message)
            if result is not None or message is msgabc.STOP:
                self._running, running = False, False
                if result is None:
                    result = True
            self._queue.task_done()
        tasks.task_end(self._task)
        return result


class TaskMulticastMailer(msgabc.MulticastMailer):

    def __init__(self, msg_filter: msgabc.Filter = msgftr.AcceptAll()):
        self._subscriber = _MulticastSubscriber(msg_filter)
        self._mailer = TaskMailer(self._subscriber)

    def start(self) -> asyncio.Task:
        return self._mailer.start()

    def register(self, subscriber: msgabc.Subscriber):
        mailer = TaskMailer(subscriber)
        task = mailer.start()
        self._subscriber.add(mailer)
        return task

    def post(self, *vargs):
        return self._mailer.post(*vargs)

    async def stop(self):
        expired = self._subscriber.mailers()
        await self._mailer.stop()
        for mailer in expired:
            await mailer.stop()  # This may post STOP again, but they will just be ignored


class _MulticastSubscriber(msgabc.AbcSubscriber):

    def __init__(self, msg_filter: msgabc.Filter):
        super().__init__(msgftr.Or(msg_filter, msgftr.IsStop()))
        self._mailers = []

    def mailers(self) -> tuple:
        return tuple(self._mailers)

    def add(self, mailer: msgabc.Mailer):
        self._mailers.append(mailer)

    def handle(self, message):
        expired = []
        for mailer in self._mailers:
            if not mailer.post(message):
                expired.append(mailer)
        for mailer in expired:
            self._mailers.remove(mailer)
        return None
