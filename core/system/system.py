from __future__ import annotations
import typing
import importlib
import inspect
import logging
import uuid
from core.util import util, signals
from core.msg import msgabc, msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httpsvc, httpext
from core.system import svrabc, svrsvc, svrext


class SystemService:
    SERVER_INITIALISED = 'SystemService.ServerInitialised'
    SERVER_DELETED = 'SystemService.ServerDestroyed'

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._modules = {}
        self._home_dir = context.config('home')
        self._url = context.config('url')
        self._clientfile = svrext.ClientFile(
            context, util.overridable_full_path(context.config('home'), context.config('clientfile')))
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

    def instances_dict(self) -> typing.Dict:
        result = {}
        for child in self._instances.children():
            for subcontext in self._context.subcontexts():
                if child.name() == subcontext.config('identity') and not subcontext.config('hidden'):
                    result[child.name()] = {'module': subcontext.config('module'), 'url': child.path()}
        return result

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
        await self._clientfile.write()
        return self

    async def shutdown(self):
        await self._clientfile.delete()
        subcontexts = self._context.subcontexts()
        for subcontext in iter(subcontexts):
            self._instances.remove(subcontext.config('identity'))
        for subcontext in iter(subcontexts):
            await svrsvc.ServerService.shutdown(subcontext, self)
            await self._context.destroy_subcontext(subcontext)

    async def create_instance(self, configuration: typing.Dict[str, str]) -> contextsvc.Context:
        identity = util.get('identity', configuration)
        if identity:
            configuration.pop('identity')
        else:
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

    async def _initialise_instance(self, configuration: typing.Dict[str, str]) -> contextsvc.Context:
        subcontext = self._context.create_subcontext(**configuration)
        subcontext.start()
        subcontext.register(msgext.RelaySubscriber(self._context, _Subscriber.FILTER))
        if subcontext.is_debug():
            subcontext.register(msgext.LoggerSubscriber(level=logging.DEBUG))
        server = self._create_server(subcontext)
        await server.initialise()
        resource = httpsvc.WebResource(subcontext.config('identity'), handler=_InstanceHandler(configuration))
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


class _Subscriber(msgabc.AbcSubscriber):
    FILTER = msgftr.NameIs(svrsvc.ServerService.DELETE_ME)

    def __init__(self, system: SystemService):
        super().__init__(_Subscriber.FILTER)
        self._system = system

    async def handle(self, message):
        await self._system.delete_instance(message.data())
        return None


class _InstanceHandler(httpabc.GetHandler):

    def __init__(self, configuration: typing.Dict[str, str]):
        self._configuration = configuration.copy()

    def handle_get(self, resource, data):
        return self._configuration


class _InstancesHandler(httpabc.GetHandler, httpabc.AsyncPostHandler):

    def __init__(self, system: SystemService):
        self._system = system

    def handle_get(self, resource, data):
        return self._system.instances_dict()

    async def handle_post(self, resource, data):
        subcontext = await self._system.create_instance(data)
        return {'url': subcontext.config('url')}


class _ShutdownHandler(httpabc.AsyncPostHandler):

    def __init__(self, system: SystemService):
        self._system = system

    async def handle_post(self, resource, data):
        signals.interrupt()
        return httpabc.ResponseBody.NO_CONTENT
