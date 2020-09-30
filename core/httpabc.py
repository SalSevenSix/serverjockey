from __future__ import annotations
import abc
import enum
import typing
from aiohttp import web_exceptions as we
from core import util

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
    def is_path(self) -> bool:
        pass

    @abc.abstractmethod
    def is_arg(self) -> bool:
        pass

    @abc.abstractmethod
    def get_name(self) -> str:
        pass

    @abc.abstractmethod
    def get_path(self) -> str:
        pass

    @abc.abstractmethod
    def lookup(self, path: str) -> typing.Optional[Resource]:
        pass

    @abc.abstractmethod
    def get_parent_resource(self) -> typing.Optional[Resource]:
        pass

    @abc.abstractmethod
    def get_resource(self, name: str) -> typing.Optional[Resource]:
        pass

    @abc.abstractmethod
    def get_path_resources(self) -> typing.Tuple[Resource]:
        pass

    @abc.abstractmethod
    def get_path_resource(self, name: str) -> typing.Optional[Resource]:
        pass

    @abc.abstractmethod
    def get_arg_resource(self) -> typing.Optional[Resource]:
        pass

    @abc.abstractmethod
    def allows(self, method: Method.GET) -> bool:
        pass

    @abc.abstractmethod
    async def handle_get(self, path: str, secure: bool = False) -> ABC_RESPONSE:
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


class DecoderProvider(metaclass=abc.ABCMeta):   # TODO remove this and pull URL coding into Resource & helper classes
    @abc.abstractmethod
    def decoder(self) -> DictionaryCoder:
        pass


class DictionaryCoder:   # TODO ... and this too

    def __init__(self):
        self._coders: typing.Dict[str, typing.Callable[[str], str]] = {}

    def append(self, key: str, coder: typing.Callable[[str], str]) -> DictionaryCoder:
        self._coders.update({key: coder})
        return self

    def process(self, dictionary: ABC_DATA_GET) -> ABC_DATA_GET:
        for key, value in iter(self._coders.items()):
            if key in dictionary:
                dictionary[key] = self._coders[key](value)
        return dictionary


ABC_HANDLER = typing.Union[DecoderProvider, GetHandler, AsyncGetHandler, PostHandler, AsyncPostHandler]
