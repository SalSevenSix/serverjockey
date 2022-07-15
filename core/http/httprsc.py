from __future__ import annotations
import logging
import typing
from yarl import URL
from core.util import util
from core.http import httpabc


class ResourceBuilder:

    def __init__(self, resource: httpabc.Resource):
        self._current = resource

    def push(self, signature: str, handler: typing.Optional[httpabc.ABC_HANDLER] = None) -> ResourceBuilder:
        name, kind = ResourceBuilder._unpack(signature)
        resource = self._current.child(name)
        if resource is None:
            resource = WebResource(name, kind, handler)
        self._current.append(resource)
        self._current = resource
        ResourceBuilder._log_binding(resource, handler)
        return self

    def pop(self) -> ResourceBuilder:
        parent = self._current.parent()
        if not parent:
            raise Exception('Cannot pop() root')
        self._current = parent
        return self

    def append(self, signature: str, handler: typing.Optional[httpabc.ABC_HANDLER] = None) -> ResourceBuilder:
        name, kind = ResourceBuilder._unpack(signature)
        resource = WebResource(name, kind, handler)
        self._current.append(resource)
        ResourceBuilder._log_binding(resource, handler)
        return self

    @staticmethod
    def _unpack(signature: str) -> typing.Tuple[str, httpabc.ResourceKind]:
        if signature.endswith('}'):
            if signature.startswith('{'):
                return signature[1:-1], httpabc.ResourceKind.ARG
            if signature.startswith('x{'):
                return signature[2:-1], httpabc.ResourceKind.ARG_ENCODED
        return signature, httpabc.ResourceKind.PATH

    @staticmethod
    def _log_binding(resource: httpabc.Resource, handler: typing.Optional[httpabc.ABC_HANDLER]):
        if handler is None:
            return
        allows = ''
        if resource.allows(httpabc.Method.GET):
            allows += httpabc.Method.GET.value
        if resource.allows(httpabc.Method.POST):
            allows += '|' if allows else ''
            allows += httpabc.Method.POST.value
        logging.debug('trs> BIND {} {} => {}'.format(resource.path(), allows, util.obj_to_str(handler)))


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
        return PathProcessor(self).build_path(args)

    def lookup(self, path: str) -> typing.Optional[httpabc.Resource]:
        return PathProcessor(self).lookup_resource(path)

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

    async def handle_get(self, url: URL, secure: bool) -> httpabc.ABC_RESPONSE:
        data = PathProcessor(self).extract_args(url)
        if secure:
            httpabc.make_secure(data)
        if isinstance(self._handler, httpabc.GetHandler):
            return self._handler.handle_get(self, data)
        return await self._handler.handle_get(self, data)

    async def handle_post(self, url: URL, body: typing.Union[str, httpabc.ABC_DATA_GET, httpabc.ByteStream]
                          ) -> httpabc.ABC_RESPONSE:
        data = PathProcessor(self).extract_args(url)
        if isinstance(body, dict):
            data.update(body)
        else:
            data.update({'body': body})
        if isinstance(self._handler, httpabc.PostHandler):
            return self._handler.handle_post(self, data)
        return await self._handler.handle_post(self, data)


class PathProcessor:

    def __init__(self, resource: httpabc.Resource):
        self._resource = resource

    def build_path(self, args: typing.Optional[typing.Dict[str, str]] = None) -> str:
        return PathProcessor._build(self._resource, args if args else {})

    def extract_args(self, url: URL) -> httpabc.ABC_DATA_GET:
        data = PathProcessor._extract(self._resource, PathProcessor._split(url.path), {})
        data.update({'baseurl': util.build_url(url.host, url.port)})
        return data

    def lookup_resource(self, path: str) -> typing.Optional[httpabc.Resource]:
        return PathProcessor._lookup(self._resource, PathProcessor._split(path), 0)

    @staticmethod
    def _build(resource: httpabc.Resource, args: typing.Dict[str, str]) -> str:
        parent, name, kind = resource.parent(), resource.name(), resource.kind()
        path, has_arg = [], name in args
        if parent is not None:
            path.append(PathProcessor._build(parent, args))
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
        return PathProcessor._extract(resource.parent(), path, args)

    @staticmethod
    def _lookup(resource: httpabc.Resource,
                path: typing.List[str], index: int) -> typing.Optional[httpabc.Resource]:
        stop = index == len(path) - 1
        for path_resource in iter(resource.children(httpabc.ResourceKind.PATH)):
            if path_resource.name() == path[index]:
                return path_resource if stop else PathProcessor._lookup(path_resource, path, index + 1)
        arg_resource = util.single(resource.children(httpabc.ResourceKind.ARG, httpabc.ResourceKind.ARG_ENCODED))
        if arg_resource is not None:
            return arg_resource if stop else PathProcessor._lookup(arg_resource, path, index + 1)
        return None

    @staticmethod
    def _split(path: str) -> typing.List[str]:
        path = path.split('/')
        if path[0] == '':
            path.remove(path[0])
        return path
