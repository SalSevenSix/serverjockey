import inspect
import logging
import asyncio
import time
import uuid
from core import msgftr


def is_message(candidate):
    return candidate is not None \
        and isinstance(candidate, Message)


def is_mailer(candidate):
    return candidate is not None \
        and hasattr(candidate, 'post') \
        and callable(candidate.post)


def is_multimailer(candidate):
    return is_mailer(candidate) \
        and hasattr(candidate, 'register') \
        and callable(candidate.register)


def is_handler(candidate):
    return candidate is not None \
        and hasattr(candidate, 'handle') \
        and callable(candidate.handle)


def is_subscriber(candidate):
    return msgftr.is_filter(candidate) \
        and is_handler(candidate)


def is_catcher(candidate):
    return is_subscriber(candidate) \
        and hasattr(candidate, 'get') \
        and callable(candidate.get)


def is_producer(candidate):
    return candidate is not None \
        and hasattr(candidate, 'next_message') \
        and callable(candidate.next_message)


def is_serializer(candidate):
    return candidate is not None \
        and hasattr(candidate, 'serialize') \
        and callable(candidate.serialize)


class Message:

    @staticmethod
    def from_vargs(*vargs):
        if len(vargs) == 1 and is_message(vargs[0]):
            return vargs[0]
        return Message(*vargs)

    def __init__(self, source, name, data=None, reply_to=None):
        assert source is not None
        assert name is not None
        assert reply_to is None or is_message(reply_to)
        self.id = uuid.uuid4()
        self.created = time.time()
        self.source = source
        self.name = name
        self.data = data
        self.reply_to = reply_to

    def get_id(self):
        return self.id

    def get_created(self):
        return self.created

    def get_source(self):
        return self.source

    def get_name(self):
        return self.name

    def has_data(self):
        return self.data is not None

    def get_data(self):
        return self.data

    def has_reply_to(self):
        return self.reply_to is not None

    def get_reply_to(self):
        return self.reply_to


class Mailer:

    def __init__(self, subscriber):
        assert is_subscriber(subscriber)
        self.subscriber = subscriber
        self.queue = asyncio.Queue()
        self.task = None

    def is_running(self):
        return self.task is not None

    def start(self):
        self.task = True
        self.task = asyncio.create_task(self.run())
        return self.task

    def get_subscriber(self):
        return self.subscriber

    def post(self, *vargs):
        message = Message.from_vargs(*vargs)
        if not self.is_running():
            return False
        if message is STOP:
            self.task = None
        try:
            if message is STOP or self.subscriber.accepts(message):
                self.queue.put_nowait(message)
        except Exception as e:
            logging.warning('Posting exception. raised: %s', e)
        return self.is_running()

    async def stop(self):
        if not self.is_running():
            return
        # Not calling queue.join() because STOP will end the tasks.
        # Any message after STOP should stay in queue and be ignored.
        task = self.task
        self.post(STOP)
        await task

    async def run(self):
        response = None
        running = True
        while running:
            message = await self.queue.get()   # blocking
            response = None
            try:
                if (message is not STOP) or (message is STOP and self.subscriber.accepts(STOP)):
                    if inspect.iscoroutinefunction(self.subscriber.handle):
                        response = await self.subscriber.handle(message)
                    else:
                        response = self.subscriber.handle(message)
            except Exception as e:
                logging.error('Handling exception. raised: %s', e)
                response = e
            finally:
                if response is not None or message is STOP:
                    running = False
                    if response is None:
                        response = True
            self.queue.task_done()
        self.task = None
        return response


class MulticastMailer:

    def __init__(self, msg_filter=None):
        if not msg_filter:
            msg_filter = msgftr.AcceptAll()
        self.subscriber = self._Subscriber(self, msg_filter)
        self.mailer = Mailer(self.subscriber)

    def start(self):
        return self.mailer.start()

    def register(self, subscriber):
        return self.subscriber.add_mailer(subscriber).start()

    def post(self, *vargs):
        return self.mailer.post(*vargs)

    async def stop(self):
        expired = self.subscriber.mailers.copy()
        await self.mailer.stop()
        for mailer in iter(expired):
            await mailer.stop()   # This may post STOP again but they will just be ignored

    class _Subscriber:

        def __init__(self, mailer, msg_filter):
            self.mailer = mailer
            self.msg_filter = msg_filter
            self.mailers = []

        def add_mailer(self, subscriber):
            mailer = Mailer(subscriber)
            self.mailers.append(mailer)
            return mailer

        def accepts(self, message):
            return message is STOP or self.msg_filter.accepts(message)

        def handle(self, message):
            expired = []
            for mailer in iter(self.mailers):
                if not mailer.post(message):
                    expired.append(mailer)
            for mailer in iter(expired):
                self.mailers.remove(mailer)
            return None


STOP = Message(Mailer, 'msgsvc.STOP', '<internal messaging system stop signal>')
