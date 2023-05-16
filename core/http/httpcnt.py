from __future__ import annotations
import typing
from aiohttp import abc as webabc
# ALLOW util.* msg.* context.* http.httpabc
from core.util import util
from core.http import httpabc

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


def make_secure(data: httpabc.ABC_DATA_GET):
    data.update({SECURE: True})


def is_secure(data: httpabc.ABC_DATA_GET) -> bool:
    return util.get(SECURE, data) is True


class ContentTypeImpl(httpabc.ContentType):

    def __init__(self, content_type: str):
        self._content_type = content_type
        self._mime_type, self._encoding = ContentTypeImpl._parse(content_type)
        self._text_type = self._mime_type in _TEXT_TYPES or self._encoding

    @staticmethod
    def lookup(path: str) -> httpabc.ContentType:
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
        result = content_type.replace(' ', '').split(';')
        if len(result) == 1:
            return result[0], None
        if not result[1].startswith(_CHARSET):
            return result[0], None
        return result[0], result[1][len(_CHARSET):]


class SecurityService:

    def __init__(self, secret: str):
        self._secret = secret
        self._failures = {}

    def check(self, request: webabc.Request) -> bool:
        remote, now = request.remote, util.now_millis()
        last_failure = util.get(remote, self._failures)
        if last_failure:
            if (now - last_failure) < 5000:
                self._failures[remote] = now
                raise httpabc.ResponseBody.UNAUTHORISED
            del self._failures[remote]
        secret = HeadersTool(request).get(X_SECRET)
        if secret is None:
            secret = request.cookies.get('secret')
        if secret is None:
            return False
        if secret == self._secret:
            return True
        self._clean_failures(now)
        self._failures[remote] = now
        raise httpabc.ResponseBody.UNAUTHORISED

    def _clean_failures(self, now: int):
        delete_keys = []
        for key, value in self._failures.items():
            if (now - value) >= 5000:
                delete_keys.append(key)
        for key in delete_keys:
            del self._failures[key]


class HeadersTool:

    def __init__(self, request: webabc.Request):
        self._headers = request.headers

    def get(self, key: str) -> str:
        return self._headers.getone(key) if key in self._headers else None

    def get_content_length(self) -> int:
        content_length = self.get(CONTENT_LENGTH)
        return int(content_length) if content_length else None

    def get_content_type(self) -> typing.Optional[httpabc.ContentType]:
        content_type = self.get(CONTENT_TYPE)
        return ContentTypeImpl(content_type) if content_type else None

    def accepts_encoding(self, encoding) -> bool:
        accepts = self.get(ACCEPT_ENCODING)
        return accepts and accepts.find(encoding) != -1


MIME_TEXT_PLAIN = 'text/plain'
MIME_APPLICATION_JSON = 'application/json'
MIME_MULTIPART_FORM_DATA = 'multipart/form-data'
MIME_APPLICATION_BIN = 'application/octet-stream'
_TEXT_TYPES = (MIME_TEXT_PLAIN, MIME_APPLICATION_JSON, 'text/html', 'application/xml',
               'text/css', 'application/javascript', 'application/typescript',
               'image/svg+xml')
_CHARSET = 'charset='
CONTENT_TYPE_TEXT_PLAIN = ContentTypeImpl(MIME_TEXT_PLAIN)
CONTENT_TYPE_TEXT_PLAIN_UTF8 = ContentTypeImpl(MIME_TEXT_PLAIN + '; ' + _CHARSET + UTF8)
CONTENT_TYPE_APPLICATION_JSON = ContentTypeImpl(MIME_APPLICATION_JSON)
CONTENT_TYPE_APPLICATION_BIN = ContentTypeImpl(MIME_APPLICATION_BIN)
_CONTENT_TYPES = {
    'txt': CONTENT_TYPE_TEXT_PLAIN,
    'text': CONTENT_TYPE_TEXT_PLAIN,
    'ini': CONTENT_TYPE_TEXT_PLAIN,
    'log': CONTENT_TYPE_TEXT_PLAIN,
    'lua': CONTENT_TYPE_TEXT_PLAIN,
    'acf': CONTENT_TYPE_TEXT_PLAIN,
    'dat': CONTENT_TYPE_TEXT_PLAIN,
    'json': CONTENT_TYPE_APPLICATION_JSON,
    'html': ContentTypeImpl('text/html'),
    'xml': ContentTypeImpl('application/xml'),
    'css': ContentTypeImpl('text/css'),
    'js': ContentTypeImpl('application/javascript'),
    'ts': ContentTypeImpl('application/typescript'),
    'svg': ContentTypeImpl('image/svg+xml'),
    'ico': ContentTypeImpl('image/x-icon'),
    'gif': ContentTypeImpl('image/gif'),
    'jpg': ContentTypeImpl('image/jpeg'),
    'jpeg': ContentTypeImpl('image/jpeg'),
    'png': ContentTypeImpl('image/png'),
    'webp': ContentTypeImpl('image/webp'),
    'woff': ContentTypeImpl('font/woff'),
    'woff2': ContentTypeImpl('font/woff2'),
    'zip': ContentTypeImpl('application/zip')
}
