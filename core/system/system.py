from __future__ import annotations
import inspect
import logging
import re
import os
# ALLOW util.* msg.* context.* http.* system.svrabc system.svrsvc
from core.util import util, io, pkg, sysutil, signals, objconv
from core.msg import msgabc, msgext, msgftr, msglog
from core.context import contextsvc, contextext
from core.http import httpabc, httpcnt, httprsc, httpext, httpsubs
from core.system import svrabc, svrsvc, igd

MODULES = ('projectzomboid', 'factorio', 'sevendaystodie', 'unturned', 'starbound')


class SystemService:
    SERVER_INITIALISED = 'SystemService.ServerInitialised'
    SERVER_DELETED = 'SystemService.ServerDestroyed'
    SERVER_FILTER = msgftr.NameIn((SERVER_INITIALISED, SERVER_DELETED))

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._modules = {}
        self._home_dir = context.config('home')
        self._clientfile = contextext.ClientFile(context, util.full_path(self._home_dir, context.config('clientfile')))
        subs = httpsubs.HttpSubscriptionService(context)
        self._resource = httprsc.WebResource()
        httprsc.ResourceBuilder(self._resource) \
            .put('login', httpext.LoginHandler(context.config('secret'))) \
            .put('modules', httpext.StaticHandler(MODULES)) \
            .psh('system') \
            .put('info', _SystemInfoHandler()) \
            .put('shutdown', _ShutdownHandler(self)) \
            .pop() \
            .psh('instances', _InstancesHandler(self)) \
            .put('subscribe', subs.handler(SystemService.SERVER_FILTER, _InstanceEventTransformer())) \
            .pop() \
            .psh(subs.resource(self._resource, 'subscriptions')) \
            .put('{identity}', subs.subscriptions_handler('identity'))
        self._instances = self._resource.child('instances')
        context.register(_DeleteInstanceSubscriber(self))
        context.register(_AutoStartsSubscriber(self._context))

    def resources(self) -> httprsc.WebResource:
        return self._resource

    def instances_info(self, baseurl: str) -> dict:
        result = {}
        for child in self._instances.children():
            subcontext = self._get_subcontext(child.name(), False)
            if subcontext and child.name() == subcontext.config('identity') and not subcontext.config('hidden'):
                result[child.name()] = {'module': subcontext.config('module'), 'url': baseurl + child.path()}
        return result

    def instance_info(self, identity: str) -> dict | None:
        subcontext = self._get_subcontext(identity, True)
        return subcontext.config() if subcontext else None

    async def instance_update(self, identity: str, updates: dict) -> dict | None:
        subcontext = self._get_subcontext(identity, True)
        if not subcontext:
            return None
        auto = util.get('auto', updates)  # Only thing that can be updated
        current = subcontext.config()
        persist = util.filter_dict(current, ('module', 'auto', 'hidden'))
        if auto is None:
            return persist
        persist['auto'] = auto
        await io.write_file(current['home'] + '/instance.json', objconv.obj_to_json(persist))
        subcontext.set_config('auto', auto)
        return persist

    async def initialise(self) -> SystemService:
        igd.initialise(self._context)
        autos, ls = [], await io.directory_list(self._home_dir)
        for identity in [str(o['name']) for o in ls if o['type'] == 'directory']:
            config_file = self._home_dir + '/' + identity + '/instance.json'
            if await io.file_exists(config_file):
                configuration = await io.read_file(config_file)
                configuration = objconv.json_to_dict(configuration)
                await _AutoStartsSubscriber.migrate(config_file, configuration)
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
        for subcontext in subcontexts:
            self._instances.remove(subcontext.config('identity'))
        for subcontext in subcontexts:
            await svrsvc.ServerService.shutdown(subcontext, self)
            await self._context.destroy_subcontext(subcontext)

    async def create_instance(self, configuration: dict) -> contextsvc.Context:
        assert util.get('identity', configuration)
        assert util.get('module', configuration) in MODULES
        identity = configuration.pop('identity')
        home_dir = self._home_dir + '/' + identity
        if await io.directory_exists(home_dir):
            raise Exception('Unable to create instance. Directory already exists.')
        logging.debug('CREATING instance ' + identity)
        await io.create_directory(home_dir)
        await io.write_file(home_dir + '/instance.json', objconv.obj_to_json(configuration))
        configuration.update({'identity': identity, 'home': home_dir})
        return await self._initialise_instance(configuration)

    async def delete_instance(self, subcontext: contextsvc.Context):
        identity = subcontext.config('identity')
        self._instances.remove(identity)
        await self._context.destroy_subcontext(subcontext)
        await io.delete_directory(subcontext.config('home'))
        self._context.post(self, SystemService.SERVER_DELETED, subcontext)
        logging.debug('DELETED instance ' + identity)

    async def _initialise_instance(self, configuration: dict) -> contextsvc.Context:
        subcontext = self._context.create_subcontext(**configuration)
        subcontext.start()
        subcontext.register(msgext.RelaySubscriber(
            self._context, msgftr.Or(igd.IgdService.FILTER, _DeleteInstanceSubscriber.FILTER)))
        if subcontext.is_trace():
            subcontext.register(msglog.LoggerSubscriber(level=logging.DEBUG))
        server = await self._create_server(subcontext)
        await server.initialise()
        resource = httprsc.WebResource(subcontext.config('identity'), handler=_InstanceHandler(self))
        self._instances.append(resource)
        server.resources(resource)
        svrsvc.ServerService(subcontext, server).start()
        self._context.post(self, SystemService.SERVER_INITIALISED, subcontext)
        return subcontext

    async def _create_server(self, subcontext: contextsvc.Context) -> svrabc.Server:
        module_name = subcontext.config('module')
        module = util.get(module_name, self._modules)
        if not module:
            module = await pkg.import_module('servers.' + module_name + '.server')
            self._modules.update({module_name: module})
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member) and svrabc.Server in inspect.getmro(member):
                return member(subcontext)
        raise Exception('Server class implementation not found in module: ' + repr(module))

    def _get_subcontext(self, identity: str, include_hidden: bool) -> contextsvc.Context | None:
        for subcontext in self._context.subcontexts():
            if identity == subcontext.config('identity'):
                if include_hidden or not subcontext.config('hidden'):
                    return subcontext
                return None
        return None


class _AutoStartsSubscriber(msgabc.AbcSubscriber):
    AUTOS = 'AutoStartsSubscriber.Autos'

    @staticmethod
    async def migrate(config_file: str, configuration: dict):
        auto = util.get('auto', configuration)
        if not auto or not isinstance(auto, str):
            return
        configuration['auto'] = 0
        if auto == 'start':
            configuration['auto'] = 1
        if auto == 'daemon':
            configuration['auto'] = 3
        await io.write_file(config_file, objconv.obj_to_json(configuration))

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.Or(
            msgftr.NameIs(_AutoStartsSubscriber.AUTOS),
            msgftr.NameIs(httpcnt.RESOURCES_READY)))
        self._mailer = mailer
        self._autos = []

    async def handle(self, message):
        if message.name() is _AutoStartsSubscriber.AUTOS:
            self._autos = message.data()
            return None
        for subcontext in self._autos:
            if subcontext.config('auto') in (1, 3):
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


class _InstancesHandler(httpabc.GetHandler, httpabc.PostHandler):
    VALIDATOR = re.compile(r'[^a-z0-9_\-]')

    def __init__(self, system: SystemService):
        self._system = system

    def handle_get(self, resource, data):
        return self._system.instances_info(util.get('baseurl', data, ''))

    async def handle_post(self, resource, data):
        module, identity = util.get('module', data), util.get('identity', data)
        if not identity or module not in MODULES:
            return httpabc.ResponseBody.BAD_REQUEST
        identity = identity.replace(' ', '_').lower()
        if _InstancesHandler.VALIDATOR.search(identity):
            return httpabc.ResponseBody.BAD_REQUEST
        subcontext = await self._system.create_instance({'module': module, 'identity': identity})
        return {'url': util.get('baseurl', data, '') + '/instances/' + subcontext.config('identity')}


class _InstanceHandler(httpabc.GetHandler, httpabc.PostHandler):

    def __init__(self, system: SystemService):
        self._system = system

    def handle_get(self, resource, data):
        result = self._system.instance_info(resource.name())
        return result if result else httpabc.ResponseBody.NOT_FOUND

    async def handle_post(self, resource, data):
        auto = util.get('auto', data)
        if auto is not None:
            try:
                auto = int(auto)
            except (TypeError, ValueError):
                return httpabc.ResponseBody.BAD_REQUEST
            if auto not in (0, 1, 2, 3):
                return httpabc.ResponseBody.BAD_REQUEST
            data['auto'] = auto
        result = await self._system.instance_update(resource.name(), data)
        return result if httpabc.ResponseBody.NO_CONTENT else httpabc.ResponseBody.NOT_FOUND


class _SystemInfoHandler(httpabc.GetHandler):

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
        signals.interrupt(os.getpid())
        return httpabc.ResponseBody.NO_CONTENT


class _InstanceEventTransformer(msgabc.Transformer):

    def transform(self, message):
        event = 'created' if message.name() is SystemService.SERVER_INITIALISED else 'deleted'
        return {'event': event, 'instance': objconv.obj_to_dict(message.data())}
