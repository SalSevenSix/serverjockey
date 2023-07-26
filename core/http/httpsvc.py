import logging
import re
import ssl
import aiohttp
from aiohttp import web, streams, abc as webabc, web_exceptions as err
# ALLOW util.* msg.* context.* http.httpabc http.httpcnt http.httpstatics
from core.util import pack, io, objconv
from core.context import contextsvc
from core.http import httpabc, httpcnt, httpstatics

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
        self._context = context
        self._callbacks = callbacks
        self._security = httpcnt.SecurityService(context.config('secret'))
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
        access_logger = logging.getLogger('aiohttp.access')
        access_logger.addFilter(_AccessLogFilter())
        ssl_context = None
        if self._context.config('scheme') == 'https':
            # noinspection PyTypeChecker
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self._context.config('sslcert'), self._context.config('sslkey'))
        web.run_app(
            self._app,
            host=self._context.config('host'),
            port=self._context.config('port'),
            access_log=access_logger,
            ssl_context=ssl_context,
            shutdown_timeout=100.0)

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
        handler = _RequestHandler(self._context, self._security, self._statics, self._resources, request)
        return await handler.handle()


class _RequestHandler:

    def __init__(self, context: contextsvc.Context, security: httpcnt.SecurityService, statics: httpstatics.Statics,
                 resources: httpabc.Resource, request: webabc.Request):
        self._context = context
        self._security = security
        self._statics = statics
        self._request = request
        self._method = httpabc.Method.resolve(request.method)
        self._resource = resources.lookup(request.path)

    async def handle(self) -> web.Response:
        # Static response
        if self._resource is None:
            if self._method is httpabc.Method.GET:
                return await self._statics.handle(self._request)
            raise err.HTTPNotFound

        # Check method allowed
        if self._method is not httpabc.Method.OPTIONS and not self._resource.allows(self._method):
            raise self._build_error_method_not_allowed()

        # OPTIONS
        if self._method is httpabc.Method.OPTIONS:
            return self._build_response_options()

        # GET
        secure = self._security.check(self._request)
        if self._method is httpabc.Method.GET:
            response_body = await self._resource.handle_get(self._request.url, secure)
            if response_body is None:
                raise err.HTTPNotFound
            return await self._build_response(response_body)

        # POST
        if not secure:
            raise err.HTTPUnauthorized
        headers = httpcnt.HeadersTool(self._request)
        request_body, content_type = b'{}', httpcnt.CONTENT_TYPE_APPLICATION_JSON
        if self._request.can_read_body:
            content_type = headers.get_content_type()
            if content_type is None or content_type.mime_type() not in _ACCEPTED_MIME_TYPES:
                raise err.HTTPUnsupportedMediaType
            if content_type.mime_type() == httpcnt.MIME_MULTIPART_FORM_DATA:
                request_body = _MultipartFormByteStream(self._request.content, self._request.headers)
            elif content_type.mime_type() == httpcnt.MIME_APPLICATION_BIN:
                request_body = _RequestByteStream(self._request.content, headers.get_content_length())
            else:
                request_body = await self._request.content.read()
        if content_type.mime_type() in _TEXT_MIME_TYPES:
            encoding = content_type.encoding() if content_type.encoding() else httpcnt.UTF8
            request_body = request_body.decode(encoding).strip()
            if content_type.mime_type() == httpcnt.MIME_APPLICATION_JSON:
                request_body = objconv.json_to_dict(request_body)
                if request_body is None:
                    raise err.HTTPBadRequest
        response_body = await self._resource.handle_post(self._request.url, request_body)
        return await self._build_response(response_body)

    async def _build_response(self, body: httpabc.ABC_RESPONSE) -> web.Response:
        if body in httpabc.ResponseBody.ERRORS:
            raise body
        headers = httpcnt.HeadersTool(self._request)
        response = web.StreamResponse() if isinstance(body, httpabc.ByteStream) else web.Response()
        response.headers.add(httpcnt.CACHE_CONTROL, httpcnt.CACHE_CONTROL_NO_CACHE)
        if self._context.is_debug():
            response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_ORIGIN, '*')
        elif httpcnt.WEBDEV_ORIGIN == headers.get(httpcnt.ORIGIN):
            response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_ORIGIN, httpcnt.WEBDEV_ORIGIN)
        if body == self._context.config('secret'):
            response.set_cookie('secret', body, max_age=36000, httponly=True, samesite='Lax')
            body = httpabc.ResponseBody.NO_CONTENT
        if body is httpabc.ResponseBody.NO_CONTENT:
            response.set_status(httpabc.ResponseBody.NO_CONTENT.status_code)
            response.headers.add(httpcnt.CONTENT_TYPE, httpcnt.MIME_APPLICATION_JSON)
            response.headers.add(httpcnt.CONTENT_LENGTH, '0')
            return response
        content_type = httpcnt.CONTENT_TYPE_APPLICATION_BIN
        if isinstance(body, str):
            content_type = httpcnt.CONTENT_TYPE_TEXT_PLAIN_UTF8
            body = body.encode(httpcnt.UTF8)
        if isinstance(body, (dict, tuple, list)):
            content_type = httpcnt.CONTENT_TYPE_APPLICATION_JSON
            body = objconv.obj_to_json(body)
            body = body.encode(httpcnt.UTF8)
        if isinstance(body, bytes) and len(body) > 512 and headers.accepts_encoding(httpcnt.GZIP):
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

    def _build_response_options(self) -> web.Response:
        response = web.Response()
        methods = httpabc.Method.GET.value + ',' if self._resource.allows(httpabc.Method.GET) else ''
        methods += httpabc.Method.POST.value + ',' if self._resource.allows(httpabc.Method.POST) else ''
        methods += httpabc.Method.OPTIONS.value
        response.set_status(httpabc.ResponseBody.NO_CONTENT.status_code)
        response.headers.add(httpcnt.ALLOW, methods)
        if self._context.is_debug():
            response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_ORIGIN, '*')
        elif httpcnt.WEBDEV_ORIGIN == httpcnt.HeadersTool(self._request).get(httpcnt.ORIGIN):
            response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_ORIGIN, httpcnt.WEBDEV_ORIGIN)
        response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_METHODS, methods)
        response.headers.add(httpcnt.ACCESS_CONTROL_ALLOW_HEADERS, httpcnt.CONTENT_TYPE + ',' + httpcnt.X_SECRET)
        return response

    def _build_error_method_not_allowed(self) -> err.HTTPMethodNotAllowed:
        allowed = [str(httpabc.Method.OPTIONS.value)]
        if self._resource.allows(httpabc.Method.GET):
            allowed.append(str(httpabc.Method.GET.value))
        if self._resource.allows(httpabc.Method.POST):
            allowed.append(str(httpabc.Method.POST.value))
        return err.HTTPMethodNotAllowed(str(self._method), allowed)


class _MultipartFormByteStream(httpabc.ByteStream):

    def __init__(self, stream: streams.StreamReader, headers):
        self._reader = aiohttp.MultipartReader(headers, stream)
        self._part = None

    def name(self) -> str:
        raise NotImplemented()

    def content_type(self) -> httpabc.ContentType:
        return httpcnt.CONTENT_TYPE_APPLICATION_BIN

    async def content_length(self) -> int:
        return -1

    async def read(self, length: int = -1) -> bytes:
        if not self._part:
            self._part = await self._reader.next()
        chunk = await self._part.read_chunk(length)
        if io.end_of_stream(chunk):
            while self._part is not None:  # Drain remaining parts if any
                self._part = await self._reader.next()
        return chunk


class _RequestByteStream(httpabc.ByteStream):

    def __init__(self, stream: streams.StreamReader, content_length: int):
        self._stream = stream
        self._content_length = content_length

    def name(self) -> str:
        raise NotImplemented()

    def content_type(self) -> httpabc.ContentType:
        return httpcnt.CONTENT_TYPE_APPLICATION_BIN

    async def content_length(self) -> int:
        return self._content_length

    async def read(self, length: int = -1) -> bytes:
        return await self._stream.read(length)


class _AccessLogFilter(logging.Filter):
    REGEX = re.compile(r'.*(GET|POST|OPTIONS) /.*HTTP/1.1" (200|204|404|409).*')

    def filter(self, record):
        return _AccessLogFilter.REGEX.match(record.getMessage()) is None
