from __future__ import annotations
import typing
import importlib
import inspect
import logging
import uuid
from core.util import util
from core.msg import msgabc, msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httpsvc, httpext
from core.system import svrabc, svrsvc


class SystemService:
    SERVER_INITIALISED = 'SystemService.ServerInitialised'
    SERVER_DELETED = 'SystemService.ServerDestroyed'

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._modules = {}
        self._home_dir = context.config('home')
        self._url = context.config('url')
        self._resource = httpsvc.WebResource(self._url)
        httpext.ResourceBuilder(self._resource) \
            .push('system') \
            .append('shutdown', _ShutdownHandler(self)) \
            .pop() \
            .append('instances', _InstancesHandler(self))
        self._instances = self._resource.child('instances')
        context.register(_Subscriber(self))

    def resources(self):
        return self._resource

    async def initialise(self) -> SystemService:
        ls = await util.directory_list_dict(self._home_dir)
        for directory in iter([o for o in ls if o['type'] == 'directory']):
            identity = directory['name']
            config_file = self._home_dir + '/' + identity + '/instance.json'
            if await util.file_exists(config_file):
                configuration = await util.read_file(config_file)
                configuration = util.json_to_dict(configuration)
                configuration.update({
                    'identity': identity,
                    'url': self._url + '/instances/' + identity,
                    'home': self._home_dir + '/' + identity
                })
                await self._initialise_instance(configuration)
        return self

    async def create_instance(self, configuration: typing.Dict[str, str]) -> contextsvc.Context:
        identity = str(uuid.uuid4())
        home_dir = self._home_dir + '/' + identity
        await util.create_directory(home_dir)
        config_file = home_dir + '/' + 'instance.json'
        await util.write_file(config_file, util.obj_to_json(configuration))
        configuration.update({
            'identity': identity,
            'url': self._url + '/instances/' + identity,
            'home': home_dir
        })
        return await self._initialise_instance(configuration)

    async def delete_instance(self, subcontext: contextsvc.Context):
        self._instances.remove(subcontext.config('identity'))
        await self._context.destroy_subcontext(subcontext)
        await util.delete_directory(subcontext.config('home'))
        self._context.post(self, SystemService.SERVER_DELETED, subcontext)

    async def shutdown(self):
        subcontexts = self._context.subcontexts()
        for subcontext in iter(subcontexts):
            self._instances.remove(subcontext.config('identity'))
        for subcontext in iter(subcontexts):
            await svrsvc.ServerService.shutdown(subcontext, self)
            await self._context.destroy_subcontext(subcontext)
        await self._context.shutdown()
        util.signal_interrupt()

    async def _initialise_instance(self, configuration: typing.Dict[str, str]) -> contextsvc.Context:
        subcontext = self._context.create_subcontext(**configuration)
        subcontext.start()
        subcontext.register(msgext.RelaySubscriber(self._context, _Subscriber.FILTER))
        if subcontext.is_debug():
            subcontext.register(msgext.LoggerSubscriber(level=logging.DEBUG))
        server = self._create_server(subcontext)
        await server.initialise()
        resource = httpsvc.WebResource(subcontext.config('identity'))
        server.resources(resource)
        self._instances.append(resource)
        svrsvc.ServerService(subcontext, server).start()
        self._context.post(self, SystemService.SERVER_INITIALISED, subcontext)
        return subcontext

    def _create_server(self, subcontext: contextsvc.Context) -> svrabc.Server:
        module_name = subcontext.config('module')
        module = util.get(module_name, self._modules)
        if not module:
            module = importlib.import_module('servers.{}.server'.format(module_name))
            self._modules.update({module_name: module})
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member) and svrabc.Server in inspect.getmro(member):
                return member(subcontext)
        raise Exception('Server class implementation not found in module: ' + repr(module))


class _Subscriber(msgabc.Subscriber):
    FILTER = msgftr.NameIs(svrsvc.ServerService.DELETE_ME)

    def __init__(self, system: SystemService):
        self._system = system

    def accepts(self, message):
        return _Subscriber.FILTER.accepts(message)

    async def handle(self, message):
        await self._system.delete_instance(message.data())
        return None


class _InstancesHandler(httpabc.AsyncPostHandler):
    def __init__(self, system: SystemService):
        self._system = system

    async def handle_post(self, resource, data):
        subcontext = await self._system.create_instance(data)
        return {'url': subcontext.config('url')}


class _ShutdownHandler(httpabc.AsyncPostHandler):
    def __init__(self, system: SystemService):
        self._system = system

    async def handle_post(self, resource, data):
        await self._system.shutdown()
        return httpabc.ResponseBody.NO_CONTENT
