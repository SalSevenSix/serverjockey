from __future__ import annotations
import typing
import importlib
import inspect
import logging
import uuid
from core.util import util, io, sysutil, signals
from core.msg import msgabc, msgext, msgftr
from core.context import contextsvc, contextext
from core.http import httpabc, httpcnt, httprsc, httpext, httpsubs
from core.system import svrabc, svrsvc


class SystemService:
    SERVER_INITIALISED = 'SystemService.ServerInitialised'
    SERVER_DELETED = 'SystemService.ServerDestroyed'
    SERVER_FILTER = msgftr.NameIn((SERVER_INITIALISED, SERVER_DELETED))

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._modules = {}
        self._home_dir = context.config('home')
        self._clientfile = contextext.ClientFile(
            context, util.overridable_full_path(context.config('home'), context.config('clientfile')))
        subs = httpsubs.HttpSubscriptionService(context)
        self._resource = httprsc.WebResource()
        httprsc.ResourceBuilder(self._resource) \
            .push('system') \
            .append('info', _SystemInfoHandler()) \
            .append('shutdown', _ShutdownHandler(self)) \
            .pop() \
            .append('login', httpext.LoginHandler(context.config('secret'))) \
            .push('instances', _InstancesHandler(self)) \
            .append('subscribe', subs.handler(SystemService.SERVER_FILTER, _InstanceEventTransformer())) \
            .pop() \
            .push(subs.resource(self._resource, 'subscriptions')) \
            .append('{identity}', subs.subscriptions_handler('identity'))
        self._instances = self._resource.child('instances')
        context.register(_DeleteInstanceSubscriber(self))
        context.register(_AutoStartsSubscriber(self._context))

    def resources(self):
        return self._resource

    def instances_dict(self, baseurl: str) -> typing.Dict:
        result = {}
        for child in self._instances.children():
            for subcontext in self._context.subcontexts():
                if child.name() == subcontext.config('identity') and not subcontext.config('hidden'):
                    result[child.name()] = {'module': subcontext.config('module'), 'url': baseurl + child.path()}
        return result

    async def initialise(self) -> SystemService:
        autos, ls = [], await io.directory_list_dict(self._home_dir)
        for directory in iter([o for o in ls if o['type'] == 'directory']):
            identity = directory['name']
            config_file = self._home_dir + '/' + identity + '/instance.json'
            if await io.file_exists(config_file):
                configuration = await io.read_file(config_file)
                configuration = util.json_to_dict(configuration)
                configuration.update({'identity': identity, 'home': self._home_dir + '/' + identity})
                subcontext = await self._initialise_instance(configuration)
                if subcontext.config('auto'):
                    autos.append(subcontext)
        await self._clientfile.write()
        self._context.post(self, _AutoStartsSubscriber.AUTOS, autos)
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
        await io.create_directory(home_dir)
        config_file = home_dir + '/' + 'instance.json'
        await io.write_file(config_file, util.obj_to_json(configuration))
        configuration.update({'identity': identity, 'home': home_dir})
        return await self._initialise_instance(configuration)

    async def delete_instance(self, subcontext: contextsvc.Context):
        self._instances.remove(subcontext.config('identity'))
        await self._context.destroy_subcontext(subcontext)
        await io.delete_directory(subcontext.config('home'))
        self._context.post(self, SystemService.SERVER_DELETED, subcontext)

    async def _initialise_instance(self, configuration: typing.Dict[str, str]) -> contextsvc.Context:
        subcontext = self._context.create_subcontext(**configuration)
        subcontext.start()
        subcontext.register(msgext.RelaySubscriber(self._context, _DeleteInstanceSubscriber.FILTER))
        if subcontext.is_debug():
            subcontext.register(msgext.LoggerSubscriber(level=logging.DEBUG))
        server = self._create_server(subcontext)
        await server.initialise()
        resource = httprsc.WebResource(subcontext.config('identity'), handler=_InstanceHandler(configuration))
        self._instances.append(resource)
        server.resources(resource)
        svrsvc.ServerService(subcontext, server).start()
        self._context.post(self, SystemService.SERVER_INITIALISED, subcontext)
        return subcontext

    def _create_server(self, subcontext: contextsvc.Context) -> svrabc.Server:
        module_name = subcontext.config('module')
        module = util.get(module_name, self._modules)
        if not module:
            module = importlib.import_module('servers.{}.server'.format(module_name))  # TODO blocking io
            self._modules.update({module_name: module})
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member) and svrabc.Server in inspect.getmro(member):
                return member(subcontext)
        raise Exception('Server class implementation not found in module: ' + repr(module))


class _AutoStartsSubscriber(msgabc.AbcSubscriber):
    AUTOS = 'AutoStartsSubscriber.Autos'

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.Or(
            msgftr.NameIs(_AutoStartsSubscriber.AUTOS),
            msgftr.NameIs(httpcnt.RESOURCES_READY)
        ))
        self._mailer = mailer
        self._autos = None

    async def handle(self, message):
        if message.name() is _AutoStartsSubscriber.AUTOS:
            self._autos = message.data()
            return None
        for subcontext in iter(self._autos):
            if subcontext.config('auto') == 'daemon':
                svrsvc.ServerService.signal_daemon(subcontext, self)
            if subcontext.config('auto') == 'start':
                svrsvc.ServerService.signal_start(subcontext, self)
        return True


class _DeleteInstanceSubscriber(msgabc.AbcSubscriber):
    FILTER = msgftr.NameIs(svrsvc.ServerService.DELETE_ME)

    def __init__(self, system: SystemService):
        super().__init__(_DeleteInstanceSubscriber.FILTER)
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
        return self._system.instances_dict(util.get('baseurl', data, ''))

    async def handle_post(self, resource, data):
        module, identity = util.get('module', data), util.get('identity', data)
        if not module:
            return httpabc.ResponseBody.BAD_REQUEST
        subcontext = await self._system.create_instance({'module': module, 'identity': identity})
        return {'url': util.get('baseurl', data, '') + '/instances/' + subcontext.config('identity')}


class _SystemInfoHandler(httpabc.AsyncGetHandler):
    def __init__(self):
        self._start_time = util.now_millis()

    async def handle_get(self, resource, data):
        info = await sysutil.system_info()
        info.update({'uptime': util.now_millis() - self._start_time})
        return info


class _ShutdownHandler(httpabc.PostHandler):

    def __init__(self, system: SystemService):
        self._system = system

    def handle_post(self, resource, data):
        signals.interrupt()
        return httpabc.ResponseBody.NO_CONTENT


class _InstanceEventTransformer(msgabc.Transformer):

    def transform(self, message):
        event = 'created' if message.name() is SystemService.SERVER_INITIALISED else 'deleted'
        return {'event': event, 'instance': util.obj_to_dict(message.data())}
