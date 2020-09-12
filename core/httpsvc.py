import asyncio
import logging
import gzip
import uuid

from aiohttp import web
from aiohttp import web_exceptions as h

from core import msgsvc, util


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
ACCEPT_ENCODING = 'Accept-Encoding'

NO_CONTENT_RESPONSE = '{ "response": "OK" }'


class ResponseBody:
    NO_CONTENT = h.HTTPNoContent
    NOT_FOUND = h.HTTPNotFound
    BAD_REQUEST = h.HTTPBadRequest
    UNAVAILABLE = h.HTTPServiceUnavailable
    ERRORS = (NOT_FOUND, BAD_REQUEST, UNAVAILABLE)


class HttpService:
    SERVER_STARTING = 'HttpService.ServerStarting'
    SERVER_COMPLETE = 'HttpService.ServerComplete'

    def __init__(self, mailer, resources):
        self.mailer = mailer
        self.resources = resources
        self.secret = Secret(mailer)
        self.app = None
        self.task = None

    def get_secret(self):
        return self.secret.secret

    def get_base_url(self):
        return self.resources.get_name()

    def start(self):
        self.app = web.Application()
        self.app.add_routes([
            web.get('/{tail:.*}', self._handle),
            web.post('/{tail:.*}', self._handle)])
        self.task = asyncio.create_task(web._run_app(
            self.app, host=self.mailer.get_host(), port=self.mailer.get_port()))
        self.mailer.post((self, HttpService.SERVER_STARTING, self.task))
        return self

    async def stop(self):
        if self.app:
            await self.app.shutdown()
            await self.app.cleanup()
        self.mailer.post((self, HttpService.SERVER_COMPLETE, self.task))

    async def _handle(self, request):
        try:
            handler = RequestHandler(self.mailer, self.resources, self.secret, request)
            return await handler.handle()
        except Exception as e:
            logging.error('HTTP Response failed. raised: %s', e)
            raise e


class RequestHandler:
    REQUEST_RECEIVED = 'RequestHandler.RequestReceived'

    def __init__(self, mailer, resources, secret, request):
        self.mailer = mailer
        self.resources = resources
        self.secret = secret
        self.request = request
        self.method = None
        if self.request.method == GET:
            self.method = GET
        if self.request.method == POST:
            self.method = POST

    async def handle(self):
        path = self.request.path
        resource = self.resources.lookup(path)
        if resource is None:
            raise h.HTTPNotFound
        if not resource.allows(self.method):
            allowed = GET if self.method is POST else POST
            raise h.HTTPMethodNotAllowed(self.method, allowed)

        # GET
        if self.method is GET:
            response_body = await resource.handle_get(path)
            if response_body is None:
                raise h.HTTPNotFound
            if response_body in ResponseBody.ERRORS:
                raise response_body
            return self.build_response(response_body)

        # POST
        headers = HeadersTool(self.request.headers)
        if not self.secret.ask(headers):
            raise h.HTTPUnauthorized
        request_body, mime, encoding = b'{}', APPLICATION_JSON, None
        if self.request.has_body:
            mime, encoding = headers.get_content_type()
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
        response_body = await resource.handle_post(path, request_body)
        if response_body in ResponseBody.ERRORS:
            raise response_body
        return self.build_response(response_body)

    def build_response(self, body):
        response = web.Response(status=200)
        if body is ResponseBody.NO_CONTENT:
            response.headers.add(CONTENT_TYPE, APPLICATION_JSON)
            response.headers.add(CONTENT_LENGTH, str(len(NO_CONTENT_RESPONSE)))
            response.text = NO_CONTENT_RESPONSE
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
        if len(body) > 1024 and HeadersTool(self.request.headers).accepts_encoding(GZIP):
            body = gzip.compress(body)
            response.headers.add(CONTENT_ENCODING, GZIP)
        response.headers.add(CONTENT_LENGTH, str(len(body)))
        response.body = body
        return response


class Secret:
    NAME = 'Secret.Id'
    SECRET = 'X-Secret'

    def __init__(self, mailer):
        identity = str(uuid.uuid4())
        self.secret = identity[:4] + identity[len(identity)-4:]
        mailer.post((self, Secret.NAME, self.secret))

    def ask(self, headers):
        host = headers.get_host()[0]
        if host in ('localhost', '127.0.0.1') or host.startswith('192.168.1.'):   # bypass
            return True
        whisper = headers.get(Secret.SECRET)
        return whisper is not None and whisper == self.secret


class HeadersTool:

    def __init__(self, headers):
        self.headers = headers

    def get(self, key):
        return self.headers.getone(key) if key in self.headers else None

    def get_host(self):
        host = self.get(HOST)
        if host is None:
            return '', None
        result = str(host).split(':')
        if len(result) == 1:
            return result[0], None
        return result[0], int(result[1])

    def get_content_length(self):
        content_length = self.get(CONTENT_LENGTH)
        return int(content_length) if content_length else None

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

    def __init__(self, parent, name='', kind=None, handler=None, children=None):
        assert isinstance(parent, Resource) or parent is None
        self.parent = parent
        self.name = name
        self.kind = kind if kind else Resource.PATH
        self.handler = handler
        self.children = children if children is not None else []

    def append(self, resource):
        if resource.kind is Resource.ARG and self.get_arg_resource() is not None:
            raise Exception('Only one Resource.ARG kind allowed')
        self.children.append(resource)
        return self

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

    async def handle_get(self, path):
        path_dict = PathParser(self, path).get_args()
        return await self.handler.handle_get(self, self.decode(path_dict))

    async def handle_post(self, path, body):
        path_dict = PathParser(self, path).get_args()
        if isinstance(body, dict):
            body = self.decode({**path_dict, **body})
        return await self.handler.handle_post(self, body)


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
