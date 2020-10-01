from __future__ import annotations
import abc
import asyncio
import time
import uuid
import typing


class Message:

    @staticmethod
    def from_vargs(*vargs):
        if len(vargs) == 1 and isinstance(vargs[0], Message):
            return vargs[0]
        return Message(*vargs)

    def __init__(
            self, source: typing.Any, name: str, data: typing.Any = None,
            reply_to: typing.Optional[Message] = None):
        self._identity = uuid.uuid4()
        self._created = time.time()
        self._source = source
        self._name = name
        self._data = data
        self._reply_to = reply_to

    def identity(self):
        return self._identity

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
