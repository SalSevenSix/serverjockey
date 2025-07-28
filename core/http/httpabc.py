from __future__ import annotations
import abc
import enum
import typing
import inspect
from aiohttp import web_exceptions as we
from yarl import URL
# ALLOW util.* msg.* context.*
from core.util import io


class HttpServiceCallbacks(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def initialise(self) -> Resource:
        pass

    @abc.abstractmethod
    async def shutdown(self):
        pass


class Method(enum.Enum):
    OPTIONS, GET, POST = 'OPTIONS', 'GET', 'POST'

    @staticmethod
    def resolve(value: str) -> typing.Optional[Method]:
        value = value.upper()
        for method in tuple(Method):
            if value == method.value:
                return method
        return None


class ResourceKind(enum.Enum):
    PATH = enum.auto()
    ARG = enum.auto()
    ARG_ENCODED = enum.auto()
    ARG_TAIL = enum.auto()

    def is_path(self) -> bool:
        return self is ResourceKind.PATH

    def is_arg(self) -> bool:
        return self in (ResourceKind.ARG, ResourceKind.ARG_ENCODED, ResourceKind.ARG_TAIL)


class ResponseBody:
    NO_CONTENT = we.HTTPNoContent
    NOT_FOUND = we.HTTPNotFound
    CONFLICT = we.HTTPConflict
    BAD_REQUEST = we.HTTPBadRequest
    UNAVAILABLE = we.HTTPServiceUnavailable
    UNAUTHORISED = we.HTTPUnauthorized
    ERRORS = (NOT_FOUND, CONFLICT, BAD_REQUEST, UNAVAILABLE, UNAUTHORISED)

    def __init__(self, body: bytes, content_type: ContentType):
        self._body, self._content_type = body, content_type

    def body(self) -> bytes:
        return self._body

    def content_type(self) -> ContentType:
        return self._content_type


class ContentType(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def content_type(self) -> str:
        pass

    @abc.abstractmethod
    def mime_type(self) -> str:
        pass

    @abc.abstractmethod
    def encoding(self) -> str:
        pass

    @abc.abstractmethod
    def is_text_type(self) -> bool:
        pass


class ByteStream(io.Readable, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def content_type(self) -> ContentType:
        pass

    @abc.abstractmethod
    def content_length(self) -> int | None:
        pass


AbcDataGet = typing.Dict[str, typing.Union[str, int, float, bool]]
AbcDataPost = typing.Dict[str, typing.Union[AbcDataGet, str, int, float, bool, tuple, list, ByteStream]]
AbcResponse = typing.Union[dict, tuple, list, str, bytes, ByteStream, ResponseBody, we.HTTPException]


class AllowMethod(metaclass=abc.ABCMeta):

    @staticmethod
    def call(method: Method, handler: typing.Optional[AbcHandler]) -> bool:
        if handler is None:
            return False
        if isinstance(handler, AllowMethod):
            return handler.allows(method)
        if method is Method.GET:
            return isinstance(handler, GetHandler)
        if method is Method.POST:
            return isinstance(handler, PostHandler)
        return False

    @abc.abstractmethod
    def allows(self, method: Method) -> bool:
        pass


class Resource(AllowMethod, metaclass=abc.ABCMeta):

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
    async def handle_get(self, url: URL, secure: bool, subpath: str = '') -> AbcResponse:
        pass

    @abc.abstractmethod
    async def handle_post(self, url: URL,
                          body: typing.Union[str, AbcDataGet, ByteStream], subpath: str = '') -> AbcResponse:
        pass


class GetHandler(metaclass=abc.ABCMeta):

    @staticmethod
    async def call(handler: GetHandler, resource: Resource, data: AbcDataGet) -> AbcResponse:
        if inspect.iscoroutinefunction(handler.handle_get):
            return await handler.handle_get(resource, data)
        return handler.handle_get(resource, data)

    @abc.abstractmethod
    def handle_get(self, resource: Resource, data: AbcDataGet) -> AbcResponse:
        pass


class PostHandler(metaclass=abc.ABCMeta):

    @staticmethod
    async def call(handler: PostHandler, resource: Resource, data: AbcDataPost) -> AbcResponse:
        if inspect.iscoroutinefunction(handler.handle_post):
            return await handler.handle_post(resource, data)
        return handler.handle_post(resource, data)

    @abc.abstractmethod
    def handle_post(self, resource: Resource, data: AbcDataPost) -> AbcResponse:
        pass


AbcHandler = typing.Union[GetHandler, PostHandler]


class InterceptorHandler(AllowMethod, GetHandler, PostHandler, metaclass=abc.ABCMeta):
    pass


class InterceptorBuilder(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def wrap(self, handler: AbcHandler) -> AbcHandler:
        pass
