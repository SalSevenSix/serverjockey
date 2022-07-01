from __future__ import annotations
import typing
import pkgutil
import gzip
from aiohttp import web, abc as webabc, web_exceptions as err
from core.util import util
from core.http import httpabc
from core.context import contextsvc


MIMES = {
    'txt': httpabc.TEXT_PLAIN_UTF8,
    'text': httpabc.TEXT_PLAIN_UTF8,
    'json': httpabc.APPLICATION_JSON,
    'html': 'text/html',
    'xml': 'application/xml',
    'css': 'text/css',
    'js': 'text/javascript',
    'ico': 'image/x-icon',
    'gif': 'image/gif',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'svg': 'image/svg+xml',
    'webp': 'image/webp',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
    'zip': 'application/zip'
}


class Statics:

    def __init__(self, context: contextsvc.Context):
        self._loader = _Loader() if context.is_debug() else _CacheLoader()

    def handle(self, headers: httpabc.HeadersTool, request: webabc.Request) -> web.Response:
        resource = self._loader.load(request.path)
        if resource is None:
            raise err.HTTPNotFound
        response = web.Response()
        response.headers.add(httpabc.CONTENT_TYPE, resource.content_type())
        response.headers.add(httpabc.CACHE_CONTROL, 'max-age=315360000')
        if headers.accepts_encoding(httpabc.GZIP) and resource.compress():
            response.headers.add(httpabc.CONTENT_ENCODING, httpabc.GZIP)
            body = resource.compressed()
        else:
            body = resource.uncompressed()
        response.headers.add(httpabc.CONTENT_LENGTH, str(len(body)))
        response.body = body
        return response


class _CacheLoader:

    def __init__(self):
        self._loader = _Loader()
        self._cache = {}

    def load(self, path: str) -> typing.Optional[_Resource]:
        resource = util.get(path, self._cache)
        if resource is not None:
            return resource
        resource = self._loader.load(path)
        if resource is None:
            return None
        self._cache[path] = resource
        return resource


class _Loader:

    def load(self, path: str) -> typing.Optional[_Resource]:
        if path[-1] == '/':
            path += 'index.html'
        content_type = util.get(path.split('.')[-1], MIMES, httpabc.APPLICATION_BIN)
        try:
            return _Resource(content_type, pkgutil.get_data('web', path))
        except IsADirectoryError:
            return self.load(path + '/')
        except FileNotFoundError:
            return None


class _Resource:

    def __init__(self, content_type: str, data: typing.Any):
        self._content_type = content_type
        self._data = data
        self._compressed = None

    def content_type(self) -> str:
        return self._content_type

    def compress(self) -> bool:
        if self._compressed is not None:
            return self._compressed
        compressed = gzip.compress(self._data)
        if len(self._data) < len(compressed):
            self._compressed = False
        else:
            self._data = compressed
            self._compressed = True
        return self._compressed

    def compressed(self) -> typing.Any:
        assert self._compressed is True
        return self._data

    def uncompressed(self) -> typing.Any:
        if self._compressed:
            return gzip.decompress(self._data)
        return self._data
