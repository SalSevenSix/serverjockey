from __future__ import annotations
import abc
import asyncio
import inspect
import logging
import time
import typing


class Message:

    @staticmethod
    def from_vargs(*vargs):
        if len(vargs) == 1 and isinstance(vargs[0], Message):
            return vargs[0]
        return Message(*vargs)

    def __init__(self,
                 source: typing.Any,
                 name: str,
                 data: typing.Any = None,
                 reply_to: typing.Optional[Message] = None):
        self._created = time.time()
        self._source = source
        self._name = name
        self._data = data
        self._reply_to = reply_to

    def created(self):
        return self._created

    def source(self):
        return self._source

    def name(self):
        return self._name

    def has_data(self):
        return self._data is not None

    def data(self):
        return self._data

    def has_reply_to(self):
        return self._reply_to is not None

    def reply_to(self):
        return self._reply_to


STOP = Message(Message, 'msgsvc.STOP', '<internal messaging system stop signal>')


class Transformer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def transform(self, message: Message) -> typing.Any:
        pass


class Filter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def accepts(self, message: Message) -> bool:
        pass


class Handler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def handle(self, message: Message) -> typing.Any:
        pass


class Subscriber(Filter, Handler, metaclass=abc.ABCMeta):
    pass


class Mailer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def post(self, *vargs) -> bool:
        pass


class MulticastMailer(Mailer, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def register(self, subscriber: Subscriber) -> asyncio.Task:
        pass


class Catcher(Subscriber, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def get(self) -> typing.Union[None, Message, typing.Collection[Message]]:
        pass


class Producer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def next_message(self) -> typing.Optional[Message]:
        pass


class AbcSubscriber(Subscriber):

    def __init__(self, msg_filter: Filter):
        self._msg_filter = msg_filter

    def accepts(self, message):
        return self._msg_filter.accepts(message)

    async def handle(self, message):
        raise NotImplemented()


async def try_handle(source: str, handler: Handler, message: Message) -> typing.Any:
    try:
        if inspect.iscoroutinefunction(handler.handle):
            result = await handler.handle(message)
        else:
            result = handler.handle(message)
    except Exception as e:
        logging.error('%s handling exception. raised: %s', source, e)
        result = e
    return result
