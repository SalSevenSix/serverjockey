import logging
import re
import aiohttp
from aiohttp import web, abc as webabc, web_exceptions as err
# ALLOW util.* msg*.* context.* http.httpabc http.httpcnt http.httpstatics
from core.util import gc, util, pack, io, objconv
from core.msgc import mc
from core.context import contextsvc
from core.http import httpabc, httpcnt, httpsec, httpstatics, httpssl

_ACCEPTED_MIME_TYPES = (httpcnt.MIME_TEXT_PLAIN, httpcnt.MIME_APPLICATION_JSON,
                        httpcnt.MIME_MULTIPART_FORM_DATA, httpcnt.MIME_APPLICATION_BIN)
_TEXT_MIME_TYPES = (httpcnt.MIME_TEXT_PLAIN, httpcnt.MIME_APPLICATION_JSON)


class HttpService:

    def __init__(self, context: contextsvc.Context, callbacks: httpabc.HttpServiceCallbacks):
        self._context, self._callbacks = context, callbacks
        self._security = httpsec.SecurityService(context.config('secret'))
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
    # pylint: disable=unused-argument
    async def _initialise(self, app: web.Application):
        self._resources = await self._callbacks.initialise()
        self._context.post(self, mc.WebResource.READY)

    # noinspection PyUnusedLocal
    # pylint: disable=unused-argument
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
        if self._context.is_trace():
            httpcnt.dump_request(request)
        return await _RequestHandler(self._context, self._security, method, request, resource).handle()


class _RequestHandler:

    def __init__(self, context: contextsvc.Context, security: httpsec.SecurityService,
                 method: httpabc.Method, request: webabc.Request, resource: httpabc.Resource):
        self._context, self._security = context, security
        self._method, self._request = method, request
        self._headers = httpcnt.HeadersTool(request)
        self._resource = resource

    # pylint: disable=too-many-branches
    async def handle(self) -> web.Response:
        # Check method allowed
        if self._method is not httpabc.Method.OPTIONS and not self._resource.allows(self._method):
            raise self._build_error_method_not_allowed()

        # OPTIONS
        if self._method is httpabc.Method.OPTIONS:
            return self._build_response_options()

        # GET
        secure = self._security.check(self._request)
        request_url, request_subpath = self._request_url(), self._request_subpath()
        if self._method is httpabc.Method.GET:
            response_body = await self._resource.handle_get(request_url, secure, request_subpath)
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
        response_body = await self._resource.handle_post(request_url, request_body, request_subpath)
        return await self._build_response(response_body)

    def _request_url(self):
        url, scheme = self._request.url, self._headers.get(httpcnt.X_FORWARDED_PROTO)
        if scheme:
            assert scheme in gc.HTTP_PROTOCALS
            url = url.with_scheme(scheme)
        return url

    def _request_subpath(self) -> str:
        subpath = self._headers.get(httpcnt.X_FORWARDED_SUBPATH)
        if subpath:
            assert subpath == util.script_escape(subpath)
            subpath = subpath.strip('/')
        return subpath if subpath else ''

    async def _build_response(self, body: httpabc.AbcResponse) -> web.Response:
        if body in httpabc.ResponseBody.ERRORS:
            # noinspection PyCallingNonCallable
            response = body()  # it will be callable, trust me bro
            self._add_allow_origin(response)
            raise response
        if isinstance(body, Exception):
            raise body
        response = web.StreamResponse() if isinstance(body, httpabc.ByteStream) else web.Response()
        response.headers.add(httpcnt.CACHE_CONTROL, httpcnt.CACHE_CONTROL_NO_STORE)
        self._add_allow_origin(response)
        if isinstance(body, httpsec.LoginResponse):
            self._security.set_cookie(response)
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
        if isinstance(body, httpabc.ResponseBody):
            content_type = body.content_type()
            body = body.body()
        if self._headers.accepts_encoding(gc.GZIP) and isinstance(body, bytes) and len(body) > 512:
            body = await pack.gzip_compress(body)
            response.headers.add(httpcnt.CONTENT_ENCODING, gc.GZIP)
        if isinstance(body, httpabc.ByteStream):
            response.headers.add(httpcnt.CONTENT_DISPOSITION, 'inline; filename="' + body.name() + '"')
            response.headers.add(httpcnt.CONTENT_TYPE, body.content_type().content_type())
            content_length = body.content_length()
            if content_length is None:
                response.enable_chunked_encoding()
                if self._headers.accepts_encoding(gc.DEFLATE):
                    response.enable_compression()
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
        response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_HEADERS,
                             httpcnt.CONTENT_TYPE + ',' + httpcnt.AUTHORIZATION + ',' + httpcnt.X_SECRET)
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
