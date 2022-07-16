from __future__ import annotations
import typing
import pkgutil
import gzip
from aiohttp import web, abc as webabc, web_exceptions as err
from core.util import util
from core.http import httpabc
from core.context import contextsvc


class Statics:

    def __init__(self, context: contextsvc.Context):
        self._loader = _Loader() if context.is_debug() else _CacheLoader()

    def handle(self, headers: httpabc.HeadersTool, request: webabc.Request) -> web.Response:
        resource = self._loader.load(request.path)
        if resource is None:
            raise err.HTTPNotFound
        response = web.Response()
        response.headers.add(httpabc.CONTENT_TYPE, resource.content_type().content_type())
        response.headers.add(httpabc.CACHE_CONTROL, httpabc.CACHE_CONTROL_MAXIMUM)
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
        if resource.content_type().is_text_type():
            self._cache[path] = resource
        return resource


class _Loader:

    def load(self, path: str) -> typing.Optional[_Resource]:
        if path is None or path == '':
            path = '/'
        if path[-1] == '/':
            path += 'index.html'
        try:
            data = pkgutil.get_data('web', path)
            return _Resource(httpabc.ContentType.lookup(path), data) if data else None
        except IsADirectoryError:
            if not path.endswith('.html'):
                return self.load(path + '/')
            return None
        except FileNotFoundError:
            if path.endswith('/index.html'):
                return self.load('/'.join(path.split('/')[:-1]) + '.html')
            return None
        except OSError:
            if path.endswith('/index.html'):
                return self.load('/'.join(path.split('/')[:-1]) + '.html')
            if path.endswith('.html'):
                return None
            return self.load(path + '/')


class _Resource:

    def __init__(self, content_type: httpabc.ContentType, data: typing.Any):
        self._content_type = content_type
        self._data = data
        self._compressed = None

    def content_type(self) -> httpabc.ContentType:
        return self._content_type

    def compress(self) -> bool:
        if self._compressed is not None:
            return self._compressed
        if not self._content_type.is_text_type():
            self._compressed = False
            return False
        data = gzip.compress(self._data)
        if len(self._data) < len(data):
            self._compressed = False
        else:
            self._data = data
            self._compressed = True
        return self._compressed

    def compressed(self) -> typing.Any:
        assert self._compressed is True
        return self._data

    def uncompressed(self) -> typing.Any:
        if self._compressed:
            return gzip.decompress(self._data)
        return self._data
