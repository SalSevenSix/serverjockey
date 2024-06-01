import logging
import re
import aiohttp
from yarl import URL
from aiohttp import web, abc as webabc, web_exceptions as err
# ALLOW util.* msg*.* context.* http.httpabc http.httpcnt http.httpstatics
from core.util import gc, pack, io, objconv
from core.context import contextsvc
from core.http import httpabc, httpcnt, httpstatics, httpssl

_ACCEPTED_MIME_TYPES = (
    httpcnt.MIME_TEXT_PLAIN,
    httpcnt.MIME_APPLICATION_JSON,
    httpcnt.MIME_MULTIPART_FORM_DATA,
    httpcnt.MIME_APPLICATION_BIN)
_TEXT_MIME_TYPES = (
    httpcnt.MIME_TEXT_PLAIN,
    httpcnt.MIME_APPLICATION_JSON)


class HttpService:

    def __init__(self, context: contextsvc.Context, callbacks: httpabc.HttpServiceCallbacks):
        self._context, self._callbacks = context, callbacks
        self._security = httpcnt.SecurityService(context.config('secret'))
        self._statics = httpstatics.Statics()
        self._resources = None
        self._app = web.Application()
        self._app.on_startup.append(self._initialise)
        self._app.on_shutdown.append(self._shutdown)
        self._app.add_routes([
            web.options('/{tail:.*}', self._handle),
            web.get('/{tail:.*}', self._handle),
            web.post('/{tail:.*}', self._handle)])

    def run(self):
        access_logger = logging.getLogger('aiohttp.access')
        access_logger.addFilter(_AccessLogFilter(self._context.is_trace()))
        ssl_context = httpssl.SslTool(self._context).ssl_context()
        web.run_app(
            self._app, host=self._context.config('host'), port=self._context.config('port'),
            access_log=access_logger, ssl_context=ssl_context, shutdown_timeout=100.0)

    # noinspection PyUnusedLocal
    async def _initialise(self, app: web.Application):
        self._resources = await self._callbacks.initialise()
        self._context.post(self, httpcnt.RESOURCES_READY)

    # noinspection PyUnusedLocal
    async def _shutdown(self, app: web.Application):
        self._resources = None
        await self._callbacks.shutdown()

    async def _handle(self, request: webabc.Request) -> web.Response:
        if self._resources is None:
            raise err.HTTPServiceUnavailable
        method = httpabc.Method.resolve(request.method)
        resource = self._resources.lookup(request.path)
        if resource is None:
            if method is httpabc.Method.GET:
                return await self._statics.handle(request)
            raise err.HTTPNotFound
        return await _RequestHandler(self._context, self._security, method, request, resource).handle()


class _RequestHandler:

    def __init__(self, context: contextsvc.Context, security: httpcnt.SecurityService,
                 method: httpabc.Method, request: webabc.Request, resource: httpabc.Resource):
        self._context, self._security = context, security
        self._method, self._request = method, request
        self._headers = httpcnt.HeadersTool(request)
        self._resource = resource

    async def handle(self) -> web.Response:
        # Check method allowed
        if self._method is not httpabc.Method.OPTIONS and not self._resource.allows(self._method):
            raise self._build_error_method_not_allowed()

        # OPTIONS
        if self._method is httpabc.Method.OPTIONS:
            return self._build_response_options()

        # GET
        request_url, secure = self._request_url(), self._security.check(self._request)
        if self._method is httpabc.Method.GET:
            response_body = await self._resource.handle_get(request_url, secure)
            if response_body is None:
                raise err.HTTPNotFound
            return await self._build_response(response_body)

        # POST
        if not secure:
            raise err.HTTPUnauthorized
        request_body, content_type = b'{}', httpcnt.CONTENT_TYPE_APPLICATION_JSON
        if self._request.can_read_body:
            content_type = self._headers.get_content_type()
            if content_type is None or content_type.mime_type() not in _ACCEPTED_MIME_TYPES:
                raise err.HTTPUnsupportedMediaType
            if content_type.mime_type() == httpcnt.MIME_MULTIPART_FORM_DATA:
                request_body = _ReadableMultipartForm(self._request)
            elif content_type.mime_type() == httpcnt.MIME_APPLICATION_BIN:
                request_body = _ReadableRequest(self._request)
            else:
                request_body = await self._request.content.read()
        if content_type.mime_type() in _TEXT_MIME_TYPES:
            encoding = content_type.encoding() if content_type.encoding() else gc.UTF_8
            request_body = request_body.decode(encoding).strip()
            if content_type.mime_type() == httpcnt.MIME_APPLICATION_JSON:
                request_body = objconv.json_to_dict(request_body)
                if request_body is None:
                    raise err.HTTPBadRequest
        response_body = await self._resource.handle_post(request_url, request_body)
        return await self._build_response(response_body)

    def _request_url(self) -> URL:
        url, proto = self._request.url, self._headers.get(httpcnt.X_FORWARDED_PROTO)
        if proto and proto in gc.HTTP_PROTOCALS:
            url = url.with_scheme(proto)
        return url

    async def _build_response(self, body: httpabc.ABC_RESPONSE) -> web.Response:
        if body in httpabc.ResponseBody.ERRORS:
            # noinspection PyCallingNonCallable
            response = body()
            self._add_allow_origin(response)
            raise response
        if isinstance(body, Exception):
            raise body
        response = web.StreamResponse() if isinstance(body, httpabc.ByteStream) else web.Response()
        response.headers.add(httpcnt.CACHE_CONTROL, httpcnt.CACHE_CONTROL_NO_STORE)
        self._add_allow_origin(response)
        if isinstance(body, httpcnt.LoginResponse):
            response.set_cookie('secret', self._security.secret(), max_age=86400, httponly=True, samesite='Lax')
            body = httpabc.ResponseBody.NO_CONTENT
        if body is httpabc.ResponseBody.NO_CONTENT:
            response.set_status(httpabc.ResponseBody.NO_CONTENT.status_code)
            response.headers.add(httpcnt.CONTENT_TYPE, httpcnt.MIME_APPLICATION_JSON)
            response.headers.add(httpcnt.CONTENT_LENGTH, '0')
            return response
        content_type = httpcnt.CONTENT_TYPE_APPLICATION_BIN
        if isinstance(body, str):
            content_type = httpcnt.CONTENT_TYPE_TEXT_PLAIN_UTF8
            body = body.encode(gc.UTF_8)
        if isinstance(body, (dict, tuple, list)):
            content_type = httpcnt.CONTENT_TYPE_APPLICATION_JSON
            body = objconv.obj_to_json(body)
            body = body.encode(gc.UTF_8)
        allow_gzip = self._headers.accepts_encoding(httpcnt.GZIP)
        if allow_gzip and isinstance(body, bytes) and len(body) > 512:
            body = await pack.gzip_compress(body)
            response.headers.add(httpcnt.CONTENT_ENCODING, httpcnt.GZIP)
        if isinstance(body, httpabc.ByteStream):
            response.headers.add(httpcnt.CONTENT_DISPOSITION, 'inline; filename="' + body.name() + '"')
            response.headers.add(httpcnt.CONTENT_TYPE, body.content_type().content_type())
            content_length = await body.content_length()
            if content_length is None:
                response.enable_chunked_encoding(io.DEFAULT_CHUNK_SIZE)
            else:
                response.headers.add(httpcnt.CONTENT_LENGTH, str(content_length))
            await response.prepare(self._request)
            await io.copy_bytes(body, response, io.DEFAULT_CHUNK_SIZE)
            return response
        response.headers.add(httpcnt.CONTENT_TYPE, content_type.content_type())
        response.headers.add(httpcnt.CONTENT_LENGTH, str(len(body)))
        response.body = body
        return response

    def _build_error_method_not_allowed(self) -> err.HTTPMethodNotAllowed:
        allowed = [str(httpabc.Method.OPTIONS.value)]
        if self._resource.allows(httpabc.Method.GET):
            allowed.append(str(httpabc.Method.GET.value))
        if self._resource.allows(httpabc.Method.POST):
            allowed.append(str(httpabc.Method.POST.value))
        return err.HTTPMethodNotAllowed(str(self._method), allowed)

    def _build_response_options(self) -> web.Response:
        methods = httpabc.Method.GET.value + ',' if self._resource.allows(httpabc.Method.GET) else ''
        methods += httpabc.Method.POST.value + ',' if self._resource.allows(httpabc.Method.POST) else ''
        methods += httpabc.Method.OPTIONS.value
        response = web.Response()
        response.set_status(httpabc.ResponseBody.NO_CONTENT.status_code)
        response.headers.add(httpcnt.ALLOW, methods)
        self._add_allow_origin(response)
        response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_METHODS, methods)
        response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_HEADERS, httpcnt.CONTENT_TYPE + ',' + httpcnt.X_SECRET)
        response.headers.add(httpcnt.ACCESS_CONTROL_MAX_AGE, '600')  # 10 minutes
        return response

    def _add_allow_origin(self, response):
        if self._context.is_debug():
            response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_ORIGIN, httpcnt.ORIGIN_ALL)
            return
        origin = self._headers.get(httpcnt.ORIGIN)
        if not origin:
            return
        if origin == httpcnt.ORIGIN_WEBDEV or origin.startswith(httpcnt.ORIGIN_EXT_PREFIX):
            response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_ORIGIN, origin)


class _ReadableMultipartForm(io.Readable):

    def __init__(self, request: webabc.Request):
        self._reader = aiohttp.MultipartReader(request.headers, request.content)
        self._part = None

    async def read(self, length: int = -1) -> bytes:
        if not self._part:
            self._part = await self._reader.next()
        chunk = await self._part.read_chunk(length)
        if io.end_of_stream(chunk):
            while self._part is not None:  # Drain remaining parts if any
                self._part = await self._reader.next()
        return chunk


class _ReadableRequest(io.Readable):

    def __init__(self, request: webabc.Request):
        self._stream = request.content

    async def read(self, length: int = -1) -> bytes:
        return await self._stream.read(length)


class _AccessLogFilter(logging.Filter):

    def __init__(self, trace: bool = False):
        super().__init__('HttpAccessLogFilter')
        if trace:
            self._regex = re.compile(
                r'.*GET.*/(subscriptions|assets|_app)/.*HTTP/1.1" (204|200).*|.*OPTIONS.*HTTP/1.1" 204.*')
        else:
            self._regex = re.compile(r'.*(GET|POST|OPTIONS) /.*HTTP/1.1" (200|204|404|409).*')

    def filter(self, record):
        return self._regex.match(record.getMessage()) is None
