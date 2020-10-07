from __future__ import annotations
import abc
import enum
import typing
from aiohttp import web_exceptions as we
from core.util import util

SECURE = '_SECURE'


def make_secure(data: ABC_DATA_GET):
    data.update({SECURE: True})


def is_secure(data: ABC_DATA_GET) -> bool:
    return util.get(SECURE, data) is True


class Method(enum.Enum):
    GET = 'GET'
    POST = 'POST'

    @staticmethod
    def resolve(value: str) -> typing.Optional[Method]:
        value = value.upper()
        for method in iter(tuple(Method)):
            if value == method.value:
                return method
        return None


class ResourceKind(enum.Enum):
    PATH = enum.auto()
    ARG = enum.auto()
    ARG_ENCODED = enum.auto()


class ResponseBody:
    NO_CONTENT = we.HTTPNoContent
    NOT_FOUND = we.HTTPNotFound
    BAD_REQUEST = we.HTTPBadRequest
    UNAVAILABLE = we.HTTPServiceUnavailable
    UNAUTHORISED = we.HTTPUnauthorized
    ERRORS = (NOT_FOUND, BAD_REQUEST, UNAVAILABLE, UNAUTHORISED)


ABC_DATA_GET = typing.Dict[str, typing.Union[str, int, float, bool]]
ABC_DATA_POST = typing.Union[ABC_DATA_GET, tuple, list, str, bytes]
ABC_RESPONSE = typing.Union[dict, tuple, list, str, bytes, we.HTTPException]


class Resource:

    @abc.abstractmethod
    def append(self, resource: Resource) -> Resource:
        pass

    @abc.abstractmethod
    def remove(self, name: str) -> typing.Optional[Resource]:
        pass

    @abc.abstractmethod
    def kind(self) -> ResourceKind:
        pass

    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def path(self, args: typing.Optional[typing.Dict[str, str]] = None) -> str:
        pass

    @abc.abstractmethod
    def lookup(self, path: str) -> typing.Optional[Resource]:
        pass

    @abc.abstractmethod
    def parent(self) -> typing.Optional[Resource]:
        pass

    @abc.abstractmethod
    def child(self, name: str) -> typing.Optional[Resource]:
        pass

    @abc.abstractmethod
    def children(self, *kinds: ResourceKind) -> typing.List[Resource]:
        pass

    @abc.abstractmethod
    def allows(self, method: Method) -> bool:
        pass

    @abc.abstractmethod
    async def handle_get(self, path: str, secure: bool) -> ABC_RESPONSE:
        pass

    @abc.abstractmethod
    async def handle_post(self, path: str, body: ABC_DATA_POST) -> ABC_RESPONSE:
        pass


class GetHandler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def handle_get(self, resource: Resource, data: ABC_DATA_GET) -> ABC_RESPONSE:
        pass


class AsyncGetHandler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def handle_get(self, resource: Resource, data: ABC_DATA_GET) -> ABC_RESPONSE:
        pass


class PostHandler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def handle_post(self, resource: Resource, data: ABC_DATA_POST) -> ABC_RESPONSE:
        pass


class AsyncPostHandler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def handle_post(self, resource: Resource, data: ABC_DATA_POST) -> ABC_RESPONSE:
        pass


class HttpServiceCallbacks(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def initialise(self) -> Resource:
        pass

    async def shutdown(self):
        pass


ABC_HANDLER = typing.Union[GetHandler, AsyncGetHandler, PostHandler, AsyncPostHandler]
