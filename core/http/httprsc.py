from __future__ import annotations
import logging
import typing
from yarl import URL
# ALLOW util.* msg*.* context.* http.httpabc http.httpsec
from core.util import util, objconv, io
from core.http import httpabc, httpsec

ARG_KINDS = (httpabc.ResourceKind.ARG, httpabc.ResourceKind.ARG_ENCODED, httpabc.ResourceKind.ARG_TAIL)


class ResourceBuilder:

    def __init__(self, resource: WebResource):
        self._current, self._interceptors = resource, {}

    def reg(self, key: str, builder: httpabc.InterceptorBuilder) -> ResourceBuilder:
        assert key and len(key) == 1
        self._interceptors[key] = builder
        return self

    def psh(self, signature: str, handler: typing.Optional[httpabc.AbcHandler] = None,
            ikeys: str = None) -> ResourceBuilder:
        return self._put(signature, handler, ikeys, True)

    def put(self, signature: str, handler: typing.Optional[httpabc.AbcHandler] = None,
            ikeys: str = None) -> ResourceBuilder:
        return self._put(signature, handler, ikeys, False)

    def pop(self) -> ResourceBuilder:
        parent = self._current.parent()
        if not parent:
            raise Exception('Cannot pop() root')
        self._current = parent
        return self

    def _put(self, signature: str, handler: typing.Optional[httpabc.AbcHandler],
             ikeys: typing.Optional[str], push: bool) -> ResourceBuilder:
        name, kind = ResourceBuilder._unpack(signature)
        resource = self._current.child(name)
        if resource:
            resource.handler(self._wrap(ikeys, handler))
        else:
            resource = WebResource(name, kind, self._wrap(ikeys, handler))
            self._current.append(resource)
        if push:
            self._current = resource
        ResourceBuilder._log_binding(resource, handler)
        return self

    def _wrap(self, ikeys: str, handler: typing.Optional[httpabc.AbcHandler]) -> typing.Optional[httpabc.AbcHandler]:
        if not handler or not ikeys:
            return handler
        for key in ikeys[::-1]:
            builder = util.get(key, self._interceptors)
            if builder:
                handler = builder.wrap(handler)
            else:
                raise Exception(f'ERROR HTTP Interceptor with key "{key}" not registered.')
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
    def _log_binding(resource: httpabc.Resource, handler: typing.Optional[httpabc.AbcHandler]):
        if handler is None:
            return
        allows, path = '', resource.path()
        if resource.allows(httpabc.Method.GET):
            allows += httpabc.Method.GET.value
        if resource.allows(httpabc.Method.POST):
            allows += '|' if allows else ''
            allows += httpabc.Method.POST.value
        if resource.kind() == httpabc.ResourceKind.ARG_TAIL:
            path += '/*'
        logging.debug('trs> BIND %s %s => %s', path, allows, objconv.obj_to_str(handler))


class WebResource(httpabc.Resource):

    def __init__(self, name: str = '',
                 kind: httpabc.ResourceKind = httpabc.ResourceKind.PATH,
                 handler: typing.Optional[httpabc.AbcHandler] = None):
        self._name, self._kind, self._handler = name, kind, handler
        self._parent: typing.Optional[WebResource] = None
        self._children: typing.List[WebResource] = []

    def append(self, resource: WebResource):
        name = resource.name()
        if self.child(name):
            raise Exception(f'Resource "{name}" already exists')
        if self.kind() is httpabc.ResourceKind.ARG_TAIL:
            raise Exception(f'Resource "{name}" type ARG_TAIL cannot have children')
        if resource.kind().is_arg() and len(self.children(*ARG_KINDS)) > 0:
            raise Exception(f'Resource "{name}" type ARG must be singular')
        resource._parent = self
        self._children.append(resource)

    def handler(self, handler: typing.Optional[httpabc.AbcHandler] = None) -> typing.Optional[httpabc.AbcHandler]:
        if handler:
            if self._handler:
                raise Exception(f'Resource {self.path()} already has handler')
            self._handler = handler
        return self._handler

    def remove(self, name: str):
        resource = self.child(name)
        if resource:
            self._children.remove(resource)

    def kind(self) -> httpabc.ResourceKind:
        return self._kind

    def name(self) -> str:
        return self._name

    def path(self, args: typing.Optional[typing.Dict[str, str]] = None) -> str:
        return PathProcessor(self).build_path(args)

    def lookup(self, path: str) -> typing.Optional[WebResource]:
        return PathProcessor(self).lookup_resource(path)

    def parent(self) -> typing.Optional[WebResource]:
        return self._parent

    def child(self, name: str) -> typing.Optional[WebResource]:
        if name is None:
            return None
        return util.single([c for c in self._children if c.name() == name])

    def children(self, *kinds: httpabc.ResourceKind) -> typing.List[WebResource]:
        if len(kinds) == 0:
            return self._children.copy()
        results = []
        for kind in kinds:
            results.extend([c for c in self._children if c.kind() is kind])
        return results

    def allows(self, method: httpabc.Method) -> bool:
        return httpabc.AllowMethod.call(method, self._handler)

    async def handle_get(self, url: URL, secure: bool, subpath: str = '') -> httpabc.AbcResponse:
        data = PathProcessor.extract_args_query(url)
        data.update(PathProcessor(self).extract_args_url(url))
        data['baseurl'] = util.build_url(url.scheme, url.host, url.port, subpath)
        httpsec.make_secure(data, secure)
        return await httpabc.GetHandler.call(self._handler, self, data)

    async def handle_post(self, url: URL,
                          body: typing.Union[str, httpabc.AbcDataGet, io.Readable],
                          subpath: str = '') -> httpabc.AbcResponse:
        data = PathProcessor(self).extract_args_url(url)
        if isinstance(body, dict):
            data.update(body)
        else:
            data['body'] = body
        data['baseurl'] = util.build_url(url.scheme, url.host, url.port, subpath)
        return await httpabc.PostHandler.call(self._handler, self, data)


class PathProcessor:

    def __init__(self, resource: httpabc.Resource):
        self._resource = resource

    def lookup_resource(self, path: str) -> typing.Optional[httpabc.Resource]:
        found, current = False, self._resource
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
    def extract_args_query(url: URL) -> httpabc.AbcDataGet:
        data = {}
        for key, value in url.query.items():
            data[str(key).strip().lower()] = str(value)
        return data

    def extract_args_url(self, url: URL) -> httpabc.AbcDataGet:
        return self.extract_args_path(url.path)

    def extract_args_path(self, path: str) -> httpabc.AbcDataGet:
        path, current, data = PathProcessor._split(path), self._resource, {}
        if self._resource.kind() is httpabc.ResourceKind.ARG_TAIL:
            depth = -2
            while current is not None:
                current = current.parent()
                depth += 1
            data[self._resource.name()] = '/'.join(path[depth:])
            path, current = path[:depth], self._resource.parent()
        path.reverse()
        for element in path:
            if current.kind() is httpabc.ResourceKind.ARG_ENCODED:
                data[current.name()] = util.urlsafe_b64decode(element)
            elif current.kind() is httpabc.ResourceKind.ARG:
                data[current.name()] = element
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
