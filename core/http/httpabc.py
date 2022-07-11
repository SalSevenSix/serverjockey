from __future__ import annotations
import abc
import enum
import typing
from aiohttp import abc as webabc, web_exceptions as we
from yarl import URL
from core.util import util


SECURE = '_SECURE'

REQUEST = 'REQUEST'
RESPONSE = 'RESPONSE'
UTF8 = 'UTF-8'
GZIP = 'gzip'
CHARSET_STRING = ';charset='
TEXT_PLAIN = 'text/plain'
TEXT_PLAIN_UTF8 = TEXT_PLAIN + CHARSET_STRING + UTF8
APPLICATION_JSON = 'application/json'
APPLICATION_BIN = 'application/octet-stream'
ACCEPTED_MIME_TYPES = (TEXT_PLAIN, APPLICATION_JSON, APPLICATION_BIN)

HOST = 'Host'
ORIGIN = 'Origin'
CONTENT_TYPE = 'Content-Type'
CONTENT_LENGTH = 'Content-Length'
CONTENT_ENCODING = 'Content-Encoding'
CONTENT_DISPOSITION = 'Content-Disposition'
CACHE_CONTROL = 'Cache-Control'
ACCEPT_ENCODING = 'Accept-Encoding'
ALLOW = 'Allow'
ACCESS_CONTROL_ALLOW_METHODS = 'Access-Control-Allow-Methods'
ACCESS_CONTROL_ALLOW_HEADERS = 'Access-Control-Allow-Headers'
ACCESS_CONTROL_ALLOW_ORIGIN = 'Access-Control-Allow-Origin'
WEBDEV_ORIGIN = 'http://localhost:3000'
X_SECRET = 'X-Secret'


def make_secure(data: ABC_DATA_GET):
    data.update({SECURE: True})


# TODO Move all use of this up to core. GET handlers should be flagged as secure at binding
def is_secure(data: ABC_DATA_GET) -> bool:
    return util.get(SECURE, data) is True


class Method(enum.Enum):
    OPTIONS = 'OPTIONS'
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


class ByteStream(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    async def content_length(self) -> typing.Optional[int]:
        pass

    @abc.abstractmethod
    async def read(self, length: int = -1) -> bytes:
        pass


ABC_DATA_GET = typing.Dict[str, typing.Union[str, int, float, bool]]
ABC_DATA_POST = typing.Dict[str, typing.Union[ABC_DATA_GET, str, int, float, bool, tuple, list, ByteStream]]
ABC_RESPONSE = typing.Union[dict, tuple, list, str, ByteStream, we.HTTPException]


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
    async def handle_get(self, url: URL, secure: bool) -> ABC_RESPONSE:
        pass

    @abc.abstractmethod
    async def handle_post(self, url: URL, body: typing.Union[str, ABC_DATA_GET, ByteStream]) -> ABC_RESPONSE:
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


# TODO doesn't belong here
class HeadersTool:

    def __init__(self, request: webabc.Request):
        self._headers = request.headers

    def get(self, key: str) -> str:
        return self._headers.getone(key) if key in self._headers else None

    def is_secure(self, secret: str) -> bool:
        value = self.get(X_SECRET)
        return value is not None and value == secret

    def get_content_length(self) -> int:
        content_length = self.get(CONTENT_LENGTH)
        return None if content_length is None else int(content_length)

    def get_content_type(self) -> typing.Tuple[typing.Optional[str], typing.Optional[str]]:
        content_type = self.get(CONTENT_TYPE)
        if content_type is None:
            return None, None
        content_type = str(content_type).replace(' ', '')
        result = str(content_type).split(CHARSET_STRING)
        if len(result) == 1:
            return result[0], None
        return result[0], result[1]

    def accepts_encoding(self, encoding) -> bool:
        accepts = self.get(ACCEPT_ENCODING)
        return accepts is not None and accepts.find(encoding) != -1
