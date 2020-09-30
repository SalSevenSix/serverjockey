from __future__ import annotations
import inspect
import gzip
import typing
from aiohttp import web, abc as webabc, web_exceptions as h
from core import httpabc, util, blobs, contextsvc

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
CONTENT_TYPE = 'Content-Type'
CONTENT_LENGTH = 'Content-Length'
CONTENT_ENCODING = 'Content-Encoding'
CACHE_CONTROL = 'Cache-Control'
ACCEPT_ENCODING = 'Accept-Encoding'
X_SECRET = 'X-Secret'


class HttpService:
    STARTING = 'HttpService.ServerStarting'
    COMPLETE = 'HttpService.ServerComplete'

    def __init__(self, context: contextsvc.Context, callbacks: httpabc.HttpServiceCallbacks):
        self._context = context
        self._callbacks = callbacks
        self._resources = None
        self._app = web.Application()
        self._app.on_startup.append(self._initialise)
        self._app.on_shutdown.append(self._shutdown)
        self._app.add_routes([
            web.get('/{tail:.*}', self._handle),
            web.post('/{tail:.*}', self._handle)])

    def run(self):
        web.run_app(self._app, port=self._context.config('port'), shutdown_timeout=100.0)

    async def _initialise(self, app: web.Application):
        self._resources = await self._callbacks.initialise()

    async def _shutdown(self, app: web.Application):
        await self._callbacks.shutdown()

    async def _handle(self, request: webabc.Request) -> web.Response:
        if self._resources is None:
            raise httpabc.ResponseBody.UNAVAILABLE
        handler = _RequestHandler(self._context, self._resources, request)
        return await handler.handle()


class _RequestHandler:
    REQUEST_RECEIVED = 'RequestHandler.RequestReceived'

    def __init__(self, context: contextsvc.Context, resources: httpabc.Resource, request: webabc.Request):
        self._resources = resources
        self._request = request
        self._headers = _HeadersTool(request)
        self._secure = context.is_debug() \
            or self._headers.get(X_SECRET) == context.config('secret')
        self._method = httpabc.Method.resolve(self._request.method)

    async def handle(self) -> web.Response:
        resource = self._resources.lookup(self._request.path)
        if resource is None:
            return self._static_response()
        if not resource.allows(self._method):
            raise h.HTTPMethodNotAllowed(
                self._method.value(),
                httpabc.Method.GET.value() if self._method is httpabc.Method.POST else httpabc.Method.POST.value())

        # GET
        if self._method is httpabc.Method.GET:
            response_body = await resource.handle_get(self._request.path, self._secure)
            if response_body is None:
                raise h.HTTPNotFound
            return self._build_response(response_body)

        # POST
        if not self._secure:
            raise httpabc.ResponseBody.UNAUTHORISED
        request_body, mime, encoding = b'{}', APPLICATION_JSON, None
        if self._request.can_read_body:
            mime, encoding = self._headers.get_content_type()
            if mime is None or mime not in ACCEPTED_MIME_TYPES:
                raise h.HTTPUnsupportedMediaType
            request_body = await self._request.content.read()
        if mime != APPLICATION_BIN:
            encoding = UTF8 if encoding is None else encoding
            request_body = request_body.decode(encoding).strip()
            if mime == APPLICATION_JSON:
                request_body = util.json_to_dict(request_body)
                if request_body is None:
                    raise h.HTTPBadRequest
        response_body = await resource.handle_post(self._request.path, request_body)
        return self._build_response(response_body)

    def _build_response(self, body: httpabc.ABC_RESPONSE) -> web.Response:
        if body in httpabc.ResponseBody.ERRORS:
            raise body
        response = web.Response()
        if body is httpabc.ResponseBody.NO_CONTENT:
            response.set_status(httpabc.ResponseBody.NO_CONTENT.status_code)
            response.headers.add(CONTENT_TYPE, APPLICATION_JSON)
            response.headers.add(CONTENT_LENGTH, '0')
            return response
        content_type = APPLICATION_BIN
        if isinstance(body, str):
            content_type = TEXT_PLAIN_UTF8
            body = body.encode(UTF8)
        if isinstance(body, (dict, tuple, list)):
            content_type = APPLICATION_JSON
            body = util.obj_to_json(body)
            body = body.encode(UTF8)
        response.headers.add(CONTENT_TYPE, content_type)
        if len(body) > 1024 and self._headers.accepts_encoding(GZIP):
            body = gzip.compress(body)
            response.headers.add(CONTENT_ENCODING, GZIP)
        response.headers.add(CONTENT_LENGTH, str(len(body)))
        response.body = body
        return response

    def _static_response(self) -> web.Response:
        if self._method is httpabc.Method.POST:
            raise h.HTTPNotFound
        if self._request.path.endswith('favicon.ico'):
            response = web.Response()
            response.headers.add(CONTENT_TYPE, 'image/x-icon')
            response.headers.add(CONTENT_LENGTH, str(len(blobs.FAVICON)))
            response.headers.add(CACHE_CONTROL, 'max-age=315360000')
            response.body = blobs.FAVICON
            return response
        raise h.HTTPNotFound


class _HeadersTool:

    def __init__(self, request: webabc.Request):
        self._headers = request.headers

    def get(self, key: str) -> str:
        return self._headers.getone(key) if key in self._headers else None

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


class WebResource(httpabc.Resource):

    def __init__(self,
                 name: str = '',
                 kind: httpabc.ResourceKind = httpabc.ResourceKind.PATH,
                 handler: typing.Optional[httpabc.ABC_HANDLER] = None):
        self._parent: typing.Optional[httpabc.Resource] = None
        self._children: typing.List[httpabc.Resource] = []
        self._name = name
        self._kind = kind
        self._handler = handler

    def append(self, resource: httpabc.Resource) -> httpabc.Resource:
        if resource.is_arg() and self.get_arg_resource() is not None:
            raise Exception('Only one ARG kind allowed')
        resource._parent = self
        self._children.append(resource)
        return self

    def remove(self, name: str) -> typing.Optional[httpabc.Resource]:
        resource = self.get_resource(name)
        if resource is None:
            return None
        self._children.remove(resource)
        return resource

    def is_path(self) -> bool:
        return self._kind is httpabc.ResourceKind.PATH

    def is_arg(self) -> bool:
        return self._kind is httpabc.ResourceKind.ARG

    def get_name(self) -> str:
        return self._name

    def get_path(self) -> str:
        return PathBuilder(self).build()

    def lookup(self, path: str) -> typing.Optional[httpabc.Resource]:
        return _PathParser(self, path).lookup()

    def get_parent_resource(self) -> typing.Optional[httpabc.Resource]:
        return self._parent

    def get_resource(self, name: str) -> typing.Optional[httpabc.Resource]:
        if name is None:
            return None
        result = [c for c in self._children if c.get_name() == name]
        return util.single(result)

    def get_path_resources(self) -> typing.Tuple[httpabc.Resource]:
        return tuple([c for c in self._children if c.is_path()])

    def get_path_resource(self, name: str) -> typing.Optional[httpabc.Resource]:
        result = [c for c in self._children if c.is_path() and c.get_name() == name]
        return util.single(result)

    def get_arg_resource(self) -> typing.Optional[httpabc.Resource]:
        result = [c for c in self._children if c.is_arg()]
        return util.single(result)

    def allows(self, method: httpabc.Method.GET) -> bool:
        if self._handler is None:
            return False
        if method is httpabc.Method.GET:
            return hasattr(self._handler, 'handle_get')
        if method is httpabc.Method.POST:
            return hasattr(self._handler, 'handle_post')
        return False

    def _decode(self, data: httpabc.ABC_DATA_GET) -> httpabc.ABC_DATA_GET:
        decoder = None
        if hasattr(self._handler, 'decoder'):
            decoder = self._handler.decoder()
        if decoder:
            return decoder.process(data)
        return data

    async def handle_get(self, path: str, secure: bool = False) -> httpabc.ABC_RESPONSE:
        data = _PathParser(self, path).get_args()
        data = self._decode(data)
        if secure:
            httpabc.make_secure(data)
        if inspect.iscoroutinefunction(self._handler.handle_get):
            return await self._handler.handle_get(self, data)
        return self._handler.handle_get(self, data)

    async def handle_post(self, path: str, body: httpabc.ABC_DATA_POST) -> httpabc.ABC_RESPONSE:
        if isinstance(body, dict):
            data = _PathParser(self, path).get_args()
            body = self._decode({**data, **body})
        if inspect.iscoroutinefunction(self._handler.handle_post):
            return await self._handler.handle_post(self, body)
        return self._handler.handle_post(self, body)


class PathBuilder:   # TODO make this private, use get_path() only

    def __init__(self, resource: httpabc.Resource, name: typing.Optional[str] = None):
        self._resource = resource.get_resource(name) if name else resource
        self._args: typing.Dict[str, str] = {}

    def append(self, name: str, arg: str) -> PathBuilder:
        self._args.update({name: arg})
        return self

    def build(self) -> str:
        return PathBuilder._rbuild(self._resource, self._args)

    @staticmethod
    def _rbuild(resource: httpabc.Resource, args: typing.Dict[str, str]) -> str:
        path = []
        parent = resource.get_parent_resource()
        if parent:
            path.append(PathBuilder._rbuild(parent, args))
        name = resource.get_name()
        if resource.is_arg():
            name = args[name] if name in args else '{' + name + '}'
        path.append(name)
        return '/'.join(path)


class _PathParser:

    def __init__(self, resource: httpabc.Resource, path: str):
        self._resource = resource
        path = path.split('/')
        if path[0] == '':
            path.remove(path[0])
        self._path: typing.List[str] = path

    def get_args(self) -> httpabc.ABC_DATA_GET:
        return _PathParser._rgather(self._resource, self._path.copy(), {})

    @staticmethod
    def _rgather(resource: httpabc.Resource,
                 path: typing.List[str],
                 args: typing.Dict[str, str]) -> httpabc.ABC_DATA_GET:
        index = len(path) - 1
        if resource.is_arg():
            args.update({resource.get_name(): path[index]})
        if index == 0:
            return args
        path.remove(path[index])
        return _PathParser._rgather(resource.get_parent_resource(), path, args)

    def lookup(self) -> typing.Optional[httpabc.Resource]:
        return _PathParser._rlookup(self._resource, self._path.copy(), 0)

    @staticmethod
    def _rlookup(resource: httpabc.Resource, path: typing.List[str], index: int) -> typing.Optional[httpabc.Resource]:
        stop = index == len(path) - 1
        for path_resource in iter(resource.get_path_resources()):
            if path_resource.get_name() == path[index]:
                return path_resource if stop else _PathParser._rlookup(path_resource, path, index + 1)
        arg_resource = resource.get_arg_resource()
        if arg_resource is not None:
            return arg_resource if stop else _PathParser._rlookup(arg_resource, path, index + 1)
        return None
