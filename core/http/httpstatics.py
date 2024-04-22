from __future__ import annotations
import logging
import typing
from aiohttp import web, abc as webabc, web_exceptions as err
# ALLOW util.* msg.* context.* http.httpabc http.httpcnt
from core.util import util, pack, pkg
from core.context import contextsvc
from core.http import httpabc, httpcnt


class Statics:

    def __init__(self, context: contextsvc.Context):
        self._loader = _Loader() if context.is_debug() else _CacheLoader()

    async def handle(self, request: webabc.Request) -> web.Response:
        resource = await self._loader.load(request.path)
        if resource is None:
            raise err.HTTPNotFound
        response, content_type = web.Response(), resource.content_type()
        response.headers.add(httpcnt.CONTENT_TYPE, content_type.content_type())
        cache_control = 'private, max-age=3600' if content_type.is_text_type() else 'public, max-age=2592000'
        response.headers.add(httpcnt.CACHE_CONTROL, cache_control)
        if httpcnt.HeadersTool(request).accepts_encoding(httpcnt.GZIP) and await resource.compress():
            response.headers.add(httpcnt.CONTENT_ENCODING, httpcnt.GZIP)
            body = resource.compressed()
        else:
            body = await resource.uncompressed()
        length = len(body)
        if length > 524288:  # Half a Megabyte
            logging.warning('Large static file ' + request.path + ' (' + str(length) + ' bytes)')
        response.headers.add(httpcnt.CONTENT_LENGTH, str(length))
        response.body = body
        return response


class _CacheLoader:

    def __init__(self):
        self._loader = _Loader()
        self._cache = {}

    async def load(self, path: str) -> typing.Optional[_Resource]:
        resource = util.get(path, self._cache)
        if resource is not None:
            return resource
        resource = await self._loader.load(path)
        if resource is None:
            return None
        if resource.content_type().is_text_type():
            self._cache[path] = resource
        return resource


class _Loader:

    async def load(self, path: str) -> typing.Optional[_Resource]:
        if path is None or path == '':
            path = '/'
        if path[-1] == '/':
            path += 'index.html'
        try:
            data = await pkg.pkg_load('web', path)
            return _Resource(httpcnt.ContentTypeImpl.lookup(path), data) if data else None
        except (IsADirectoryError, FileNotFoundError, OSError):
            if path.endswith('/index.html'):
                return await self.load('/'.join(path.split('/')[:-1]) + '.html')
            if path.endswith('.html'):
                return None
            return await self.load(path + '/')


class _Resource:

    def __init__(self, content_type: httpabc.ContentType, data: typing.Any):
        self._content_type, self._data = content_type, data
        self._compressed = None

    def content_type(self) -> httpabc.ContentType:
        return self._content_type

    async def compress(self) -> bool:
        if self._compressed is not None:
            return self._compressed
        if not self._content_type.is_text_type():
            self._compressed = False
            return False
        data = await pack.gzip_compress(self._data)
        if len(self._data) < len(data):
            self._compressed = False
        else:
            self._data = data
            self._compressed = True
        return self._compressed

    def compressed(self) -> typing.Any:
        assert self._compressed is True
        return self._data

    async def uncompressed(self) -> typing.Any:
        if self._compressed:
            return await pack.gzip_decompress(self._data)
        return self._data
