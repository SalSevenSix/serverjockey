import logging
import inspect
import gzip
from aiohttp import web, web_exceptions as h
from core import util, blobs

UTF8 = 'UTF-8'
GZIP = 'gzip'
REQUEST = 'REQUEST'
GET = 'GET'
POST = 'POST'
RESPONSE = 'RESPONSE'
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

SECURE = '_SECURE'


def is_secure(data):
    return util.get(SECURE, data) is True


class ResponseBody:
    NO_CONTENT = h.HTTPNoContent
    NOT_FOUND = h.HTTPNotFound
    BAD_REQUEST = h.HTTPBadRequest
    UNAVAILABLE = h.HTTPServiceUnavailable
    UNAUTHORISED = h.HTTPUnauthorized
    ERRORS = (NOT_FOUND, BAD_REQUEST, UNAVAILABLE, UNAUTHORISED)


class HttpService:
    STARTING = 'HttpService.ServerStarting'
    COMPLETE = 'HttpService.ServerComplete'

    def __init__(self, context, callbacks):
        self.context = context
        self.callbacks = callbacks
        self.resources = None
        self.app = web.Application()
        self.app.on_startup.append(self._initialise)
        self.app.on_shutdown.append(self._shutdown)
        self.app.add_routes([
            web.get('/{tail:.*}', self._handle),
            web.post('/{tail:.*}', self._handle)])

    def run(self):
        web.run_app(self.app, port=self.context.config('port'), shutdown_timeout=100.0)

    async def _initialise(self, app):
        self.resources = await self.callbacks.initialise()

    async def _shutdown(self, app):
        await self.callbacks.shutdown()

    async def _handle(self, request):
        if self.resources is None:
            raise ResponseBody.UNAVAILABLE
        try:
            handler = RequestHandler(self.context, self.resources, request)
            return await handler.handle()
        except Exception as e:
            logging.error('HTTP Response failed. raised: %s', e)
            raise e


class RequestHandler:
    REQUEST_RECEIVED = 'RequestHandler.RequestReceived'

    def __init__(self, context, resources, request):
        self.resources = resources
        self.request = request
        self.headers = HeadersTool(request.headers)
        self.secure = context.is_debug() \
            or self.headers.get(X_SECRET) == context.config('secret')
        self.method = None
        if self.request.method == GET:
            self.method = GET
        if self.request.method == POST:
            self.method = POST

    async def handle(self):
        resource = self.resources.lookup(self.request.path)
        if resource is None:
            return self.static_response()
        if not resource.allows(self.method):
            raise h.HTTPMethodNotAllowed(self.method, GET if self.method is POST else POST)

        # GET
        if self.method is GET:
            response_body = await resource.handle_get(self.request.path, self.secure)
            if response_body is None:
                raise h.HTTPNotFound
            return self.build_response(response_body)

        # POST
        if not self.secure:
            raise ResponseBody.UNAUTHORISED
        request_body, mime, encoding = b'{}', APPLICATION_JSON, None
        if self.request.has_body:
            mime, encoding = self.headers.get_content_type()
            if mime is None or mime not in ACCEPTED_MIME_TYPES:
                raise h.HTTPUnsupportedMediaType
            request_body = await self.request.content.read()
        if mime != APPLICATION_BIN:
            encoding = UTF8 if encoding is None else encoding
            request_body = request_body.decode(encoding).strip()
            if mime == APPLICATION_JSON:
                request_body = util.json_to_dict(request_body)
                if request_body is None:
                    raise h.HTTPBadRequest
        response_body = await resource.handle_post(self.request.path, request_body)
        return self.build_response(response_body)

    def build_response(self, body):
        if body in ResponseBody.ERRORS:
            raise body
        response = web.Response()
        if body is ResponseBody.NO_CONTENT:
            response.set_status(ResponseBody.NO_CONTENT.status_code)
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
        if len(body) > 1024 and self.headers.accepts_encoding(GZIP):
            body = gzip.compress(body)
            response.headers.add(CONTENT_ENCODING, GZIP)
        response.headers.add(CONTENT_LENGTH, str(len(body)))
        response.body = body
        return response

    def static_response(self):
        if self.method is POST:
            raise h.HTTPNotFound
        if self.request.path.endswith('favicon.ico'):
            response = web.Response()
            response.headers.add(CONTENT_TYPE, 'image/x-icon')
            response.headers.add(CONTENT_LENGTH, str(len(blobs.FAVICON)))
            response.headers.add(CACHE_CONTROL, 'max-age=315360000')
            response.body = blobs.FAVICON
            return response
        raise h.HTTPNotFound


class HeadersTool:

    def __init__(self, headers):
        self.headers = headers

    def get(self, key):
        return self.headers.getone(key) if key in self.headers else None

    def get_content_type(self):
        content_type = self.get(CONTENT_TYPE)
        if content_type is None:
            return None, None
        content_type = str(content_type).replace(' ', '')
        result = str(content_type).split(CHARSET_STRING)
        if len(result) == 1:
            return result[0], None
        return tuple(result)

    def accepts_encoding(self, encoding):
        accepts = self.get(ACCEPT_ENCODING)
        return accepts is not None and accepts.find(encoding) != -1


class Resource:
    PATH = 'PATH'
    ARG = 'ARG'

    def __init__(self, name='', kind=None, handler=None, children=None):
        self.parent = None
        self.name = name
        self.kind = kind if kind else Resource.PATH
        self.handler = handler
        self.children = children if children is not None else []

    def append(self, resource):
        if resource.kind is Resource.ARG and self.get_arg_resource() is not None:
            raise Exception('Only one Resource.ARG kind allowed')
        resource.parent = self
        self.children.append(resource)
        return self

    def remove(self, name):
        resource = self.get_resource(name)
        if resource is None:
            return None
        self.children.remove(resource)
        return resource

    def is_path(self):
        return self.kind is Resource.PATH

    def is_arg(self):
        return self.kind is Resource.ARG

    def get_name(self):
        return self.name

    def get_path(self):
        return PathBuilder(self).build()

    def lookup(self, path):
        return PathParser(self, path).lookup()

    def get_parent_resource(self):
        return self.parent

    def get_resource(self, name):
        if name is None:
            return None
        result = [c for c in self.children if c.name == name]
        return None if len(result) == 0 else result[0]

    def get_path_resources(self):
        return [c for c in self.children if c.is_path()]

    def get_path_resource(self, name):
        result = [c for c in self.children if c.is_path() and c.name == name]
        return None if len(result) == 0 else result[0]

    def get_arg_resource(self, name=None):
        result = [c for c in self.children if c.is_arg()]
        if len(result) == 0:
            return None
        if name is None or name == result[0].name:
            return result[0]
        return None

    def allows(self, method):
        if self.handler is None:
            return False
        if method is GET:
            return hasattr(self.handler, 'handle_get')
        if method is POST:
            return hasattr(self.handler, 'handle_post')
        return False

    def decode(self, data):
        if not hasattr(self.handler, 'get_decoder'):
            return data
        return self.handler.get_decoder().process(data)

    async def handle_get(self, path, secure=False):
        data = PathParser(self, path).get_args()
        if secure:
            data.update({SECURE: secure})
        data = self.decode(data)
        if inspect.iscoroutinefunction(self.handler.handle_get):
            return await self.handler.handle_get(self, data)
        return self.handler.handle_get(self, data)

    async def handle_post(self, path, body):
        if isinstance(body, dict):
            data = PathParser(self, path).get_args()
            body = self.decode({**data, **body})
        if inspect.iscoroutinefunction(self.handler.handle_post):
            return await self.handler.handle_post(self, body)
        return self.handler.handle_post(self, body)


class PathBuilder:

    def __init__(self, resource, name=None):
        self.resource = resource
        self.name = name
        self.args = {}

    def append(self, name, identity):
        self.args.update({name: identity})
        return self

    def build(self):
        resource = self.resource.get_resource(self.name)
        if not resource:
            resource = self.resource
        return PathBuilder.rbuild(resource, self.args)

    @staticmethod
    def rbuild(resource, identities):
        path = []
        parent = resource.get_parent_resource()
        if parent:
            path.append(PathBuilder.rbuild(parent, identities))
        name = resource.get_name()
        if resource.is_arg():
            name = identities[name] if name in identities else '{' + name + '}'
        path.append(name)
        return '/'.join(path)


class PathParser:

    def __init__(self, resource, path):
        self.resource = resource
        self.path = path
        if self.path:
            self.path = path.split('/')
            if self.path[0] == '':
                self.path.remove(self.path[0])

    def get_args(self):
        if self.path is None:
            return {}
        return PathParser.rgather(self.resource, self.path, {})

    @staticmethod
    def rgather(resource, path, args):
        index = len(path) - 1
        if resource.is_arg():
            args.update({resource.get_name(): path[index]})
        if index == 0:
            return args
        path.remove(path[index])
        return PathParser.rgather(resource.get_parent_resource(), path, args)

    def lookup(self):
        if self.path is None:
            return self.resource
        return PathParser.rlookup(self.resource, self.path, 0)

    @staticmethod
    def rlookup(resource, path, index):
        stop = index == len(path) - 1
        for path_resource in iter(resource.get_path_resources()):
            if path_resource.name == path[index]:
                return path_resource if stop else PathParser.rlookup(path_resource, path, index + 1)
        arg_resource = resource.get_arg_resource()
        if arg_resource is not None:
            return arg_resource if stop else PathParser.rlookup(arg_resource, path, index + 1)
        return None
