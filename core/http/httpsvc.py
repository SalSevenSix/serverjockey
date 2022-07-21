import gzip
from aiohttp import web, streams, abc as webabc, web_exceptions as err
from core.util import util
from core.context import contextsvc
from core.http import httpabc, httpstatics


ACCEPTED_MIME_TYPES = (httpabc.MIME_TEXT_PLAIN, httpabc.MIME_APPLICATION_JSON, httpabc.MIME_APPLICATION_BIN)


class HttpService:

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
        web.run_app(
            self._app,
            host=self._context.config('host'),
            port=self._context.config('port'),
            shutdown_timeout=100.0)

    # noinspection PyUnusedLocal
    async def _initialise(self, app: web.Application):
        self._resources = await self._callbacks.initialise()
        # TODO post message to indicate resources are set

    # noinspection PyUnusedLocal
    async def _shutdown(self, app: web.Application):
        await self._callbacks.shutdown()

    async def _handle(self, request: webabc.Request) -> web.Response:
        if self._resources is None:
            raise httpabc.ResponseBody.UNAVAILABLE
        handler = _RequestHandler(self._context, self._statics, self._resources, request)
        return await handler.handle()


class _RequestHandler:

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
            raise err.HTTPNotFound
        if self._method is not httpabc.Method.OPTIONS and not resource.allows(self._method):
            allowed = [httpabc.Method.OPTIONS.value]
            if resource.allows(httpabc.Method.GET):
                allowed.append(httpabc.Method.GET.value)
            if resource.allows(httpabc.Method.POST):
                allowed.append(httpabc.Method.POST.value)
            raise err.HTTPMethodNotAllowed(str(self._method), allowed)

        # OPTIONS
        if self._method is httpabc.Method.OPTIONS:
            return self._build_options_response(resource)

        # GET
        if self._method is httpabc.Method.GET:
            response_body = await resource.handle_get(self._request.url, self._secure)
            if response_body is None:
                raise err.HTTPNotFound
            return await self._build_response(response_body)

        # POST
        if not self._secure:
            raise httpabc.ResponseBody.UNAUTHORISED
        request_body, content_type = b'{}', httpabc.CONTENT_TYPE_APPLICATION_JSON
        if self._request.can_read_body:
            content_type = self._headers.get_content_type()
            if content_type is None or content_type.mime_type() not in ACCEPTED_MIME_TYPES:
                raise err.HTTPUnsupportedMediaType
            if content_type.mime_type() == httpabc.MIME_APPLICATION_BIN:
                request_body = _RequestByteStream(self._request.content, self._headers.get_content_length())
            else:
                request_body = await self._request.content.read()
        if content_type.mime_type() != httpabc.MIME_APPLICATION_BIN:
            encoding = content_type.encoding() if content_type.encoding() else httpabc.UTF8
            request_body = request_body.decode(encoding).strip()
            if content_type.mime_type() == httpabc.MIME_APPLICATION_JSON:
                request_body = util.json_to_dict(request_body)
                if request_body is None:
                    raise err.HTTPBadRequest
        response_body = await resource.handle_post(self._request.url, request_body)
        return await self._build_response(response_body)

    async def _build_response(self, body: httpabc.ABC_RESPONSE) -> web.Response:
        if body in httpabc.ResponseBody.ERRORS:
            raise body
        response = web.StreamResponse() if isinstance(body, httpabc.ByteStream) else web.Response()
        response.headers.add(httpabc.CACHE_CONTROL, httpabc.CACHE_CONTROL_NO_CACHE)
        if self._context.is_debug():
            response.headers.add(httpabc.ACCESS_CONTROL_ALLOW_ORIGIN, '*')
        elif httpabc.WEBDEV_ORIGIN == self._headers.get(httpabc.ORIGIN):
            response.headers.add(httpabc.ACCESS_CONTROL_ALLOW_ORIGIN, httpabc.WEBDEV_ORIGIN)
        if body is httpabc.ResponseBody.NO_CONTENT:
            response.set_status(httpabc.ResponseBody.NO_CONTENT.status_code)
            response.headers.add(httpabc.CONTENT_TYPE, httpabc.MIME_APPLICATION_JSON)
            response.headers.add(httpabc.CONTENT_LENGTH, '0')
            return response
        content_type = httpabc.CONTENT_TYPE_APPLICATION_BIN
        if isinstance(body, str):
            content_type = httpabc.CONTENT_TYPE_TEXT_PLAIN_UTF8
            body = body.encode(httpabc.UTF8)
        if isinstance(body, (dict, tuple, list)):
            content_type = httpabc.CONTENT_TYPE_APPLICATION_JSON
            body = util.obj_to_json(body)
            body = body.encode(httpabc.UTF8)
        if isinstance(body, bytes) and len(body) > 1024 and self._headers.accepts_encoding(httpabc.GZIP):
            body = gzip.compress(body)
            response.headers.add(httpabc.CONTENT_ENCODING, httpabc.GZIP)
        if isinstance(body, httpabc.ByteStream):
            response.headers.add(httpabc.CONTENT_DISPOSITION, 'inline; filename="' + body.name() + '"')
            response.headers.add(httpabc.CONTENT_TYPE, body.content_type().content_type())
            content_length = await body.content_length()
            if content_length is None:
                response.enable_chunked_encoding(util.DEFAULT_CHUNK_SIZE)
            else:
                response.headers.add(httpabc.CONTENT_LENGTH, str(content_length))
            await response.prepare(self._request)
            await util.copy_bytes(body, response, util.DEFAULT_CHUNK_SIZE)
            return response
        response.headers.add(httpabc.CONTENT_TYPE, content_type.content_type())
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
            response.headers.add(httpabc.ACCESS_CONTROL_ALLOW_ORIGIN, '*')
        elif httpabc.WEBDEV_ORIGIN == self._headers.get(httpabc.ORIGIN):
            response.headers.add(httpabc.ACCESS_CONTROL_ALLOW_ORIGIN, httpabc.WEBDEV_ORIGIN)
        response.headers.add(httpabc.ACCESS_CONTROL_ALLOW_METHODS, methods)
        response.headers.add(httpabc.ACCESS_CONTROL_ALLOW_HEADERS, httpabc.CONTENT_TYPE + ',' + httpabc.X_SECRET)
        return response


class _RequestByteStream(httpabc.ByteStream):

    def __init__(self, stream: streams.StreamReader, content_length: int):
        self._stream = stream
        self._content_length = content_length

    def name(self) -> str:
        return 'RequestByteStream'

    def content_type(self) -> httpabc.ContentType:
        return httpabc.CONTENT_TYPE_APPLICATION_JSON

    async def content_length(self) -> int:
        return self._content_length

    async def read(self, length: int = -1) -> bytes:
        return await self._stream.read(length)
