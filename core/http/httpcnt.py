from __future__ import annotations
import typing
import re
import time
from aiohttp import abc as webabc
# ALLOW util.* msg.* context.* http.httpabc
from core.util import util
from core.http import httpabc

_SECURE = '_SECURE'
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
WEBDEV_ORIGIN = 'http://localhost:5173'


def make_secure(data: httpabc.ABC_DATA_GET, secure: bool):
    if _SECURE in data:
        del data[_SECURE]
    if secure:
        data[_SECURE] = True


def is_secure(data: httpabc.ABC_DATA_GET) -> bool:
    return util.get(_SECURE, data, False) is True


class ContentTypeImpl(httpabc.ContentType):
    _STAMP_REGEX = re.compile(r'^[0-9_-]+$')

    def __init__(self, content_type: str):
        self._content_type = content_type
        self._mime_type, self._encoding = ContentTypeImpl._parse(content_type)
        self._text_type = self._mime_type in _TEXT_TYPES or self._encoding

    @staticmethod
    def lookup(path: str) -> httpabc.ContentType:
        parts = path.split('.')
        size = len(parts)
        if size < 2:
            return CONTENT_TYPE_APPLICATION_BIN
        extension = parts[-1].lower()
        extension_type = util.get(extension, _CONTENT_TYPES, CONTENT_TYPE_APPLICATION_BIN)
        if size < 3 or extension_type.is_text_type():
            return extension_type
        prextion = parts[-2].lower()
        prextion_type = util.get(prextion, _CONTENT_TYPES, CONTENT_TYPE_APPLICATION_BIN)
        if not prextion_type.is_text_type():
            return extension_type
        if extension.startswith('prev') or extension.startswith('back'):
            return prextion_type
        if ContentTypeImpl._STAMP_REGEX.match(extension):
            return prextion_type
        return extension_type

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
    _TIMOUT = 5.0

    def __init__(self, secret: str):
        self._secret = secret
        self._failures = {}

    def check(self, request: webabc.Request) -> bool:
        remote, now = request.remote, time.time()
        last_failure = util.get(remote, self._failures)
        if last_failure:
            if (now - last_failure) < SecurityService._TIMOUT:
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

    def _clean_failures(self, now: float):
        delete_keys = []
        for key, value in self._failures.items():
            if (now - value) >= SecurityService._TIMOUT:
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


MIME_APPLICATION_BIN = 'application/octet-stream'
MIME_MULTIPART_FORM_DATA = 'multipart/form-data'
MIME_TEXT_PLAIN = 'text/plain'
MIME_TEXT_HTML = 'text/html'
MIME_TEXT_CSS = 'text/css'
MIME_APPLICATION_JSON = 'application/json'
MIME_APPLICATION_XML = 'application/xml'
MIME_APPLICATION_JAVASCRIPT = 'application/javascript'
MIME_APPLICATION_TYPESCRIPT = 'application/typescript'
MIME_IMAGE_SVGXML = 'image/svg+xml'

_TEXT_TYPES = (
    MIME_TEXT_PLAIN, MIME_TEXT_HTML, MIME_TEXT_CSS, MIME_APPLICATION_JSON, MIME_APPLICATION_XML,
    MIME_APPLICATION_JAVASCRIPT, MIME_APPLICATION_TYPESCRIPT, MIME_IMAGE_SVGXML
)

_CHARSET = 'charset='
CONTENT_TYPE_TEXT_PLAIN_UTF8 = ContentTypeImpl(MIME_TEXT_PLAIN + '; ' + _CHARSET + UTF8)
CONTENT_TYPE_TEXT_PLAIN = ContentTypeImpl(MIME_TEXT_PLAIN)
CONTENT_TYPE_APPLICATION_JSON = ContentTypeImpl(MIME_APPLICATION_JSON)
CONTENT_TYPE_APPLICATION_BIN = ContentTypeImpl(MIME_APPLICATION_BIN)

_CONTENT_TYPES = {
    'txt': CONTENT_TYPE_TEXT_PLAIN,
    'text': CONTENT_TYPE_TEXT_PLAIN,
    'ini': CONTENT_TYPE_TEXT_PLAIN,
    'config': CONTENT_TYPE_TEXT_PLAIN,
    'cfg': CONTENT_TYPE_TEXT_PLAIN,
    'log': CONTENT_TYPE_TEXT_PLAIN,
    'lua': CONTENT_TYPE_TEXT_PLAIN,
    'acf': CONTENT_TYPE_TEXT_PLAIN,
    'dat': CONTENT_TYPE_TEXT_PLAIN,
    'json': CONTENT_TYPE_APPLICATION_JSON,
    'html': ContentTypeImpl(MIME_TEXT_HTML),
    'xml': ContentTypeImpl(MIME_APPLICATION_XML),
    'css': ContentTypeImpl(MIME_TEXT_CSS),
    'js': ContentTypeImpl(MIME_APPLICATION_JAVASCRIPT),
    'ts': ContentTypeImpl(MIME_APPLICATION_TYPESCRIPT),
    'svg': ContentTypeImpl(MIME_IMAGE_SVGXML),
    'ico': ContentTypeImpl('image/x-icon'),
    'gif': ContentTypeImpl('image/gif'),
    'jpg': ContentTypeImpl('image/jpeg'),
    'jpeg': ContentTypeImpl('image/jpeg'),
    'png': ContentTypeImpl('image/png'),
    'webp': ContentTypeImpl('image/webp'),
    'woff': ContentTypeImpl('font/woff'),
    'woff2': ContentTypeImpl('font/woff2'),
    'ttf': ContentTypeImpl('font/ttf'),
    'zip': ContentTypeImpl('application/zip')
}
