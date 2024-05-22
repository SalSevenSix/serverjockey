from __future__ import annotations
import logging
import typing
from yarl import URL
# ALLOW const.* util.* msg*.* context.* http.httpabc http.httpcnt
from core.util import util, objconv, io
from core.http import httpabc, httpcnt

ARG_KINDS = (httpabc.ResourceKind.ARG, httpabc.ResourceKind.ARG_ENCODED, httpabc.ResourceKind.ARG_TAIL)


class ResourceBuilder:

    def __init__(self, resource: httpabc.Resource):
        self._interceptors = {}
        self._current = resource

    def reg(self, key: str, builder: httpabc.InterceptorBuilder) -> ResourceBuilder:
        assert key and len(key) == 1
        self._interceptors[key] = builder
        return self

    def psh(self, signature: str,
            handler: typing.Optional[httpabc.ABC_HANDLER] = None, ikeys: str = None) -> ResourceBuilder:
        name, kind = ResourceBuilder._unpack(signature)
        resource = self._current.child(name)
        if resource is None:
            resource = WebResource(name, kind, self._wrap(ikeys, handler))
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

    def put(self, signature: str,
            handler: typing.Optional[httpabc.ABC_HANDLER] = None, ikeys: str = None) -> ResourceBuilder:
        name, kind = ResourceBuilder._unpack(signature)
        resource = WebResource(name, kind, self._wrap(ikeys, handler))
        self._current.append(resource)
        ResourceBuilder._log_binding(resource, handler)
        return self

    def _wrap(self, ikeys: str, handler: typing.Optional[httpabc.ABC_HANDLER]) -> typing.Optional[httpabc.ABC_HANDLER]:
        if not handler or not ikeys:
            return handler
        for key in ikeys[::-1]:
            builder = util.get(key, self._interceptors)
            if builder:
                handler = builder.wrap(handler)
            else:
                raise Exception('ERROR HTTP Interceptor with key "' + key + '" not registered.')
        return handler

    @staticmethod
    def _unpack(signature: str) -> typing.Tuple[str, httpabc.ResourceKind]:
        if signature.endswith('}'):
            if signature.startswith('{'):
                return signature[1:-1], httpabc.ResourceKind.ARG
            if signature.startswith('x{'):
                return signature[2:-1], httpabc.ResourceKind.ARG_ENCODED
            if signature.startswith('*{'):
                return signature[2:-1], httpabc.ResourceKind.ARG_TAIL
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
        logging.debug('trs> BIND {} {} => {}'.format(resource.path(), allows, objconv.obj_to_str(handler)))


class WebResource(httpabc.Resource):

    def __init__(self, name: str = '',
                 kind: httpabc.ResourceKind = httpabc.ResourceKind.PATH,
                 handler: typing.Optional[httpabc.ABC_HANDLER] = None):
        self._name, self._kind, self._handler = name, kind, handler
        self._parent: typing.Optional[httpabc.Resource] = None
        self._children: typing.List[httpabc.Resource] = []

    def append(self, resource: httpabc.Resource) -> httpabc.Resource:
        if self.kind() is httpabc.ResourceKind.ARG_TAIL:
            raise Exception('ARG_TAIL resource cannot have children')
        if resource.kind().is_arg() and len(self.children(*ARG_KINDS)) > 0:
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
        for kind in kinds:
            results.extend([c for c in self._children if c.kind() is kind])
        return results

    def allows(self, method: httpabc.Method) -> bool:
        return httpabc.AllowMethod.call(method, self._handler)

    async def handle_get(self, url: URL, secure: bool) -> httpabc.ABC_RESPONSE:
        data = PathProcessor.extract_args_query(url)
        data.update(PathProcessor(self).extract_args_url(url))
        httpcnt.make_secure(data, secure)
        return await httpabc.GetHandler.call(self._handler, self, data)

    async def handle_post(
            self, url: URL, body: typing.Union[str, httpabc.ABC_DATA_GET, io.Readable]) -> httpabc.ABC_RESPONSE:
        data = PathProcessor(self).extract_args_url(url)
        if isinstance(body, dict):
            data.update(body)
        else:
            data.update({'body': body})
        return await httpabc.PostHandler.call(self._handler, self, data)


class PathProcessor:

    def __init__(self, resource: httpabc.Resource):
        self._resource = resource

    def lookup_resource(self, path: str) -> typing.Optional[httpabc.Resource]:
        found, tail, current = False, False, self._resource
        for element in PathProcessor._split(path):
            found_path, found_arg = False, False
            for path_resource in current.children(httpabc.ResourceKind.PATH):
                if not found_path and element == path_resource.name():
                    found, found_path, current = True, True, path_resource
            if not found_path:
                arg_resource = util.single(current.children(*ARG_KINDS))
                if arg_resource is not None:
                    found, found_arg, current = True, True, arg_resource
                    if arg_resource.kind() is httpabc.ResourceKind.ARG_TAIL:
                        return arg_resource
            if not (found_path or found_arg):
                return None
        return current if found else None

    def build_path(self, args: typing.Optional[typing.Dict[str, str]] = None) -> str:
        parent, name, kind = self._resource.parent(), self._resource.name(), self._resource.kind()
        looping, path, args = True, [], args if args else {}
        while looping:
            if kind.is_path():
                path.append(name)
            elif name in args and kind in (httpabc.ResourceKind.ARG, httpabc.ResourceKind.ARG_TAIL):
                path.append(args[name])
            elif name in args and kind is httpabc.ResourceKind.ARG_ENCODED:
                path.append(util.urlsafe_b64encode(args[name]))
            elif name not in args and kind is not httpabc.ResourceKind.ARG_TAIL:
                path.append(name)
            if parent is None:
                looping = False
            else:
                parent, name, kind = parent.parent(), parent.name(), parent.kind()
        path.reverse()
        return '/'.join(path)

    @staticmethod
    def extract_args_query(url: URL) -> httpabc.ABC_DATA_GET:
        data = {}
        for key, value in url.query.items():
            data[str(key).strip().lower()] = str(value)
        return data

    def extract_args_url(self, url: URL) -> httpabc.ABC_DATA_GET:
        data = self.extract_args_path(url.path)
        data.update({'baseurl': util.build_url(url.scheme, url.host, url.port)})
        return data

    def extract_args_path(self, path: str) -> httpabc.ABC_DATA_GET:
        path, current, data = PathProcessor._split(path), self._resource, {}
        if self._resource.kind() is httpabc.ResourceKind.ARG_TAIL:
            depth = -2
            while current is not None:
                current = current.parent()
                depth += 1
            data.update({self._resource.name(): '/'.join(path[depth:])})
            path, current = path[:depth], self._resource.parent()
        path.reverse()
        for element in path:
            if current.kind() is httpabc.ResourceKind.ARG_ENCODED:
                data.update({current.name(): util.urlsafe_b64decode(element)})
            elif current.kind() is httpabc.ResourceKind.ARG:
                data.update({current.name(): element})
            current = current.parent()
            if current is None:
                raise Exception('Resource should never be None')
        return data

    @staticmethod
    def _split(path: str) -> typing.List[str]:
        path = path.split('/')
        if path[0] == '':
            path.remove(path[0])
        return path
