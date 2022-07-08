from __future__ import annotations
import gzip
import typing
from aiohttp import web, streams, abc as webabc, web_exceptions as err
from core.util import util
from core.context import contextsvc
from core.http import httpabc, httpstatics


class HttpService:
    STARTING = 'HttpService.ServerStarting'
    COMPLETE = 'HttpService.ServerComplete'

    def __init__(self, context: contextsvc.Context, callbacks: httpabc.HttpServiceCallbacks):
        self._context = context
        self._callbacks = callbacks
        self._statics = httpstatics.Statics(context)
        self._resources = None
        self._app = web.Application()
        self._app.on_startup.append(self._initialise)
        self._app.on_shutdown.append(self._shutdown)
        self._app.add_routes([
            web.options('/{tail:.*}', self._handle),
            web.get('/{tail:.*}', self._handle),
            web.post('/{tail:.*}', self._handle)])

    def run(self):
        web.run_app(self._app, port=self._context.config('port'), shutdown_timeout=100.0)

    # noinspection PyUnusedLocal
    async def _initialise(self, app: web.Application):
        self._resources = await self._callbacks.initialise()

    # noinspection PyUnusedLocal
    async def _shutdown(self, app: web.Application):
        await self._callbacks.shutdown()

    async def _handle(self, request: webabc.Request) -> web.Response:
        if self._resources is None:
            raise httpabc.ResponseBody.UNAVAILABLE
        handler = _RequestHandler(self._context, self._statics, self._resources, request)
        return await handler.handle()


class _RequestHandler:
    REQUEST_RECEIVED = 'RequestHandler.RequestReceived'

    def __init__(self, context: contextsvc.Context, statics: httpstatics.Statics,
                 resources: httpabc.Resource, request: webabc.Request):
        self._context = context
        self._statics = statics
        self._resources = resources
        self._request = request
        self._headers = httpabc.HeadersTool(request)
        self._secure = context.is_debug() or self._headers.is_secure(context.config('secret'))
        self._method = httpabc.Method.resolve(self._request.method)

    async def handle(self) -> web.Response:
        resource = self._resources.lookup(self._request.path)
        if resource is None:
            if self._method is httpabc.Method.GET:
                return self._statics.handle(self._headers, self._request)
            else:
                raise err.HTTPNotFound
        if not resource.allows(self._method):
            raise err.HTTPMethodNotAllowed(
                str(self._method),
                httpabc.Method.GET.value if self._method is httpabc.Method.POST else httpabc.Method.POST.value)

        # OPTIONS
        if self._method is httpabc.Method.OPTIONS:
            return self._build_options_response(resource)

        # GET
        if self._method is httpabc.Method.GET:
            response_body = await resource.handle_get(self._request.path, self._secure)
            if response_body is None:
                raise err.HTTPNotFound
            return await self._build_response(response_body)

        # POST
        if not self._secure:
            raise httpabc.ResponseBody.UNAUTHORISED
        request_body, mime, encoding = b'{}', httpabc.APPLICATION_JSON, None
        if self._request.can_read_body:
            mime, encoding = self._headers.get_content_type()
            if mime is None or mime not in httpabc.ACCEPTED_MIME_TYPES:
                raise err.HTTPUnsupportedMediaType
            if mime == httpabc.APPLICATION_BIN:
                request_body = _RequestByteStream(self._request.content, self._headers.get_content_length())
            else:
                request_body = await self._request.content.read()
        if mime != httpabc.APPLICATION_BIN:
            encoding = httpabc.UTF8 if encoding is None else encoding
            request_body = request_body.decode(encoding).strip()
            if mime == httpabc.APPLICATION_JSON:
                request_body = util.json_to_dict(request_body)
                if request_body is None:
                    raise err.HTTPBadRequest
        response_body = await resource.handle_post(self._request.path, request_body)
        return await self._build_response(response_body)

    async def _build_response(self, body: httpabc.ABC_RESPONSE) -> web.Response:
        if body in httpabc.ResponseBody.ERRORS:
            raise body
        response = web.StreamResponse() if isinstance(body, httpabc.ByteStream) else web.Response()
        if self._context.is_debug():
            response.headers.add(httpabc.ACCESS_CONTROL_ALLOW_ORIGIN, httpabc.DEBUG_WEB_ORIGIN)
        if body is httpabc.ResponseBody.NO_CONTENT:
            response.set_status(httpabc.ResponseBody.NO_CONTENT.status_code)
            response.headers.add(httpabc.CONTENT_TYPE, httpabc.APPLICATION_JSON)
            response.headers.add(httpabc.CONTENT_LENGTH, '0')
            return response
        content_type = httpabc.APPLICATION_BIN
        if isinstance(body, str):
            content_type = httpabc.TEXT_PLAIN_UTF8
            body = body.encode(httpabc.UTF8)
        if isinstance(body, (dict, tuple, list)):
            content_type = httpabc.APPLICATION_JSON
            body = util.obj_to_json(body)
            body = body.encode(httpabc.UTF8)
        response.headers.add(httpabc.CONTENT_TYPE, content_type)
        if isinstance(body, bytes) and len(body) > 1024 and self._headers.accepts_encoding(httpabc.GZIP):
            body = gzip.compress(body)
            response.headers.add(httpabc.CONTENT_ENCODING, httpabc.GZIP)
        if isinstance(body, httpabc.ByteStream):
            response.headers.add(httpabc.CONTENT_DISPOSITION, 'inline; filename="' + body.name() + '"')
            content_length = await body.content_length()
            if content_length is None:
                response.enable_chunked_encoding(10240)
            else:
                response.headers.add(httpabc.CONTENT_LENGTH, str(content_length))
            await response.prepare(self._request)
            await util.copy_bytes(body, response)
        else:
            response.headers.add(httpabc.CONTENT_LENGTH, str(len(body)))
            response.body = body
        return response

    def _build_options_response(self, resource: httpabc.Resource) -> web.Response:
        response = web.Response()
        methods = httpabc.Method.GET.value + ',' if resource.allows(httpabc.Method.GET) else ''
        methods += httpabc.Method.POST.value + ',' if resource.allows(httpabc.Method.POST) else ''
        methods += httpabc.Method.OPTIONS.value
        response.set_status(httpabc.ResponseBody.NO_CONTENT.status_code)
        response.headers.add(httpabc.ALLOW, methods)
        if self._context.is_debug():
            response.headers.add(httpabc.ACCESS_CONTROL_ALLOW_ORIGIN, httpabc.DEBUG_WEB_ORIGIN)
        response.headers.add(httpabc.ACCESS_CONTROL_ALLOW_METHODS, methods)
        response.headers.add(httpabc.ACCESS_CONTROL_ALLOW_HEADERS, httpabc.CONTENT_TYPE)
        return response


class _RequestByteStream(httpabc.ByteStream):

    def __init__(self, stream: streams.StreamReader, content_length: int):
        self._stream = stream
        self._content_length = content_length

    def name(self) -> str:
        return 'RequestByteStream'

    async def content_length(self) -> int:
        return self._content_length

    async def read(self, length: int = -1) -> bytes:
        return await self._stream.read(length)


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
        if resource.kind() in (httpabc.ResourceKind.ARG, httpabc.ResourceKind.ARG_ENCODED) \
                and len(self.children(httpabc.ResourceKind.ARG, httpabc.ResourceKind.ARG_ENCODED)) > 0:
            raise Exception('Only one ARG kind allowed')
        resource._parent = self
        self._children.append(resource)
        return self

    def remove(self, name: str) -> typing.Optional[httpabc.Resource]:
        resource = self.child(name)
        if resource is None:
            return None
        self._children.remove(resource)
        return resource

    def kind(self) -> httpabc.ResourceKind:
        return self._kind

    def name(self) -> str:
        return self._name

    def path(self, args: typing.Optional[typing.Dict[str, str]] = None) -> str:
        return _PathProcessor(self).build_path(args)

    def lookup(self, path: str) -> typing.Optional[httpabc.Resource]:
        return _PathProcessor(self).lookup_resource(path)

    def parent(self) -> typing.Optional[httpabc.Resource]:
        return self._parent

    def child(self, name: str) -> typing.Optional[httpabc.Resource]:
        if name is None:
            return None
        return util.single([c for c in self._children if c.name() == name])

    def children(self, *kinds: httpabc.ResourceKind) -> typing.List[httpabc.Resource]:
        if len(kinds) == 0:
            return self._children.copy()
        results = []
        for kind in iter(kinds):
            results.extend([c for c in self._children if c.kind() is kind])
        return results

    def allows(self, method: httpabc.Method) -> bool:
        if self._handler is None:
            return False
        if method is httpabc.Method.OPTIONS:
            return True
        if method is httpabc.Method.GET:
            return isinstance(self._handler, (httpabc.GetHandler, httpabc.AsyncGetHandler))
        if method is httpabc.Method.POST:
            return isinstance(self._handler, (httpabc.PostHandler, httpabc.AsyncPostHandler))
        return False

    async def handle_get(self, path: str, secure: bool) -> httpabc.ABC_RESPONSE:
        data = _PathProcessor(self).extract_args(path)
        if secure:
            httpabc.make_secure(data)
        if isinstance(self._handler, httpabc.GetHandler):
            return self._handler.handle_get(self, data)
        return await self._handler.handle_get(self, data)

    async def handle_post(self, path: str, body: typing.Union[str, httpabc.ABC_DATA_GET, httpabc.ByteStream]
                          ) -> httpabc.ABC_RESPONSE:
        data = _PathProcessor(self).extract_args(path)
        if isinstance(body, dict):
            data.update(body)
        else:
            data.update({'body': body})
        if isinstance(self._handler, httpabc.PostHandler):
            return self._handler.handle_post(self, data)
        return await self._handler.handle_post(self, data)


class _PathProcessor:

    def __init__(self, resource: httpabc.Resource):
        self._resource = resource

    def build_path(self, args: typing.Optional[typing.Dict[str, str]] = None) -> str:
        return _PathProcessor._build(self._resource, args if args else {})

    def extract_args(self, path: str) -> httpabc.ABC_DATA_GET:
        return _PathProcessor._extract(self._resource, _PathProcessor._split(path), {})

    def lookup_resource(self, path: str) -> typing.Optional[httpabc.Resource]:
        return _PathProcessor._lookup(self._resource, _PathProcessor._split(path), 0)

    @staticmethod
    def _build(resource: httpabc.Resource, args: typing.Dict[str, str]) -> str:
        parent, name, kind = resource.parent(), resource.name(), resource.kind()
        path, has_arg = [], name in args
        if parent is not None:
            path.append(_PathProcessor._build(parent, args))
        if has_arg and kind is httpabc.ResourceKind.ARG:
            name = args[name]
        elif has_arg and kind is httpabc.ResourceKind.ARG_ENCODED:
            name = util.str_to_b10str(args[name])
        path.append(name)
        return '/'.join(path)

    @staticmethod
    def _extract(resource: httpabc.Resource,
                 path: typing.List[str],
                 args: typing.Dict[str, str]) -> httpabc.ABC_DATA_GET:
        index = len(path) - 1
        kind = resource.kind()
        if kind in (httpabc.ResourceKind.ARG, httpabc.ResourceKind.ARG_ENCODED):
            if kind is httpabc.ResourceKind.ARG_ENCODED:
                args.update({resource.name(): util.b10str_to_str(path[index])})
            else:
                args.update({resource.name(): path[index]})
        if index == 0:
            return args
        path.remove(path[index])
        return _PathProcessor._extract(resource.parent(), path, args)

    @staticmethod
    def _lookup(resource: httpabc.Resource,
                path: typing.List[str], index: int) -> typing.Optional[httpabc.Resource]:
        stop = index == len(path) - 1
        for path_resource in iter(resource.children(httpabc.ResourceKind.PATH)):
            if path_resource.name() == path[index]:
                return path_resource if stop else _PathProcessor._lookup(path_resource, path, index + 1)
        arg_resource = util.single(resource.children(httpabc.ResourceKind.ARG, httpabc.ResourceKind.ARG_ENCODED))
        if arg_resource is not None:
            return arg_resource if stop else _PathProcessor._lookup(arg_resource, path, index + 1)
        return None

    @staticmethod
    def _split(path: str) -> typing.List[str]:
        path = path.split('/')
        if path[0] == '':
            path.remove(path[0])
        return path
