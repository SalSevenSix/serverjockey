from __future__ import annotations
import abc
import enum
import typing
from aiohttp import abc as webabc, web_exceptions as we
from yarl import URL
from core.util import util


SECURE = '_SECURE'
X_SECRET = 'X-Secret'
RESOURCES_READY = 'RESOURCES_READY'

HOST = 'Host'
ORIGIN = 'Origin'
CONTENT_TYPE = 'Content-Type'
UTF8 = 'UTF-8'
CONTENT_LENGTH = 'Content-Length'
CONTENT_ENCODING = 'Content-Encoding'
GZIP = 'gzip'
CONTENT_DISPOSITION = 'Content-Disposition'
CACHE_CONTROL = 'Cache-Control'
CACHE_CONTROL_NO_CACHE = 'no-cache'
ACCEPT_ENCODING = 'Accept-Encoding'
ALLOW = 'Allow'
ACCESS_CONTROL_ALLOW_METHODS = 'Access-Control-Allow-Methods'
ACCESS_CONTROL_ALLOW_HEADERS = 'Access-Control-Allow-Headers'
ACCESS_CONTROL_ALLOW_ORIGIN = 'Access-Control-Allow-Origin'
WEBDEV_ORIGIN = 'http://localhost:3000'


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
    ARG_TAIL = enum.auto()

    def is_path(self) -> bool:
        return self is ResourceKind.PATH

    def is_arg(self) -> bool:
        return self in (ResourceKind.ARG, ResourceKind.ARG_ENCODED, ResourceKind.ARG_TAIL)


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
    def content_type(self) -> ContentType:
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


class ContentType:
    def __init__(self, content_type: str):
        self._content_type = content_type
        self._mime_type, self._encoding = ContentType._parse(content_type)
        self._text_type = self._mime_type in _TEXT_TYPES or self._encoding

    @staticmethod
    def lookup(path: str) -> ContentType:
        return util.get(path.split('.')[-1], _CONTENT_TYPES, CONTENT_TYPE_APPLICATION_BIN)

    def content_type(self) -> str:
        return self._content_type

    def mime_type(self) -> str:
        return self._mime_type

    def encoding(self) -> str:
        return self._encoding

    def is_text_type(self) -> bool:
        return self._text_type

    @staticmethod
    def _parse(content_type: str) -> typing.Tuple[typing.Optional[str], typing.Optional[str]]:
        result = content_type.replace(' ', '').split(_CHARSET.replace(' ', ''))
        if len(result) == 1:
            return result[0], None
        return result[0], result[1]


MIME_TEXT_PLAIN = 'text/plain'
MIME_APPLICATION_JSON = 'application/json'
MIME_APPLICATION_BIN = 'application/octet-stream'
_TEXT_TYPES = (MIME_TEXT_PLAIN, MIME_APPLICATION_JSON, 'text/html', 'application/xml',
               'text/css', 'application/javascript', 'application/typescript',
               'image/svg+xml')
_CHARSET = '; charset='
CONTENT_TYPE_TEXT_PLAIN = ContentType(MIME_TEXT_PLAIN)
CONTENT_TYPE_TEXT_PLAIN_UTF8 = ContentType(MIME_TEXT_PLAIN + _CHARSET + UTF8)
CONTENT_TYPE_APPLICATION_JSON = ContentType(MIME_APPLICATION_JSON)
CONTENT_TYPE_APPLICATION_BIN = ContentType(MIME_APPLICATION_BIN)
_CONTENT_TYPES = {
    'txt': CONTENT_TYPE_TEXT_PLAIN,
    'text': CONTENT_TYPE_TEXT_PLAIN,
    'log': CONTENT_TYPE_TEXT_PLAIN,
    'lua': CONTENT_TYPE_TEXT_PLAIN,
    'json': CONTENT_TYPE_APPLICATION_JSON,
    'html': ContentType('text/html'),
    'xml': ContentType('application/xml'),
    'css': ContentType('text/css'),
    'js': ContentType('application/javascript'),
    'ts': ContentType('application/typescript'),
    'svg': ContentType('image/svg+xml'),
    'ico': ContentType('image/x-icon'),
    'gif': ContentType('image/gif'),
    'jpg': ContentType('image/jpeg'),
    'jpeg': ContentType('image/jpeg'),
    'png': ContentType('image/png'),
    'webp': ContentType('image/webp'),
    'woff': ContentType('font/woff'),
    'woff2': ContentType('font/woff2'),
    'zip': ContentType('application/zip')
}


# TODO doesn't belong here
class HeadersTool:

    def __init__(self, request: webabc.Request):
        self._request = request
        self._headers = request.headers

    def get(self, key: str) -> str:
        return self._headers.getone(key) if key in self._headers else None

    def is_secure(self, secret: str) -> bool:
        value = self.get(X_SECRET)
        if value is None:
            value = self._request.cookies.get('secret')
        return value is not None and value == secret

    def get_content_length(self) -> int:
        content_length = self.get(CONTENT_LENGTH)
        return int(content_length) if content_length else None

    def get_content_type(self) -> typing.Optional[ContentType]:
        content_type = self.get(CONTENT_TYPE)
        return ContentType(content_type) if content_type else None

    def accepts_encoding(self, encoding) -> bool:
        accepts = self.get(ACCEPT_ENCODING)
        return accepts and accepts.find(encoding) != -1
