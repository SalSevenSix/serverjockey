import logging
import asyncio
import re
# ALLOW util.* msg*.* context.* http.* system.svrabc system.svrsvc
from core.util import util, dtutil, io, sysutil, signals, objconv, funcutil
from core.msg import msgabc, msgftr, msglog, msgext
from core.msgc import mc
from core.context import contextsvc, contextext
from core.http import httpabc, httpcnt, httpsec, httprsc, httpext, httpsubs, httpssl
from core.system import svrmodules, svrsvc, sysstore, sysmetrics, mprof, steamapi, igd

_NO_LOG = 'NO FILE LOGGING. STDOUT ONLY.'


class SystemService:
    _INSTANCE_EVENT_FILTER = msgftr.Or(mc.SystemService.SERVER_FILTER, mc.ServerStatus.UPDATED_FILTER)

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir = context.config('home')
        self._pidfile = _PidFileSubscriber(context)
        self._clientfile = contextext.ClientFile(context, tokenfile=True)
        self._modules = svrmodules.Modules(context)
        self._sysstoresvc = sysstore.SystemStoreService(context)
        self._resource = self._build_resources()
        self._instances = self._resource.child('instances')

    def _build_resources(self) -> httprsc.WebResource:
        subs, logfile = httpsubs.HttpSubscriptionService(self._context), self._context.config('logfile')
        resource = httprsc.WebResource()
        self._sysstoresvc.resources(resource)
        steamapi.resources(resource)
        r = httprsc.ResourceBuilder(resource)
        r.put('login', httpext.LoginHandler())
        r.put('modules', httpext.StaticHandler(self._modules.names()))
        r.put('ssl', httpssl.SslHandler(self._context))
        r.put('metrics', sysmetrics.MetricsHandler())
        r.put('mprof', mprof.MemoryProfilingHandler())
        r.psh('system')
        r.put('info', _SystemInfoHandler())
        r.put('log', httpext.FileSystemHandler(logfile) if logfile else httpext.StaticHandler(_NO_LOG))
        r.put('shutdown', _ShutdownHandler())
        r.pop()
        r.psh('instances', _InstancesHandler(self, self._modules))
        r.put('subscribe', subs.handler(SystemService._INSTANCE_EVENT_FILTER, _InstanceEventTransformer()))
        r.pop()
        r.psh(subs.resource(resource, 'subscriptions'))
        r.put('{identity}', subs.subscriptions_handler('identity'))
        return resource

    async def initialise(self):
        self._context.register(self._pidfile)
        igd.initialise(self._context, self)
        self._sysstoresvc.initialise()
        self._context.register(_DeleteInstanceSubscriber(self))
        self._context.register(_AutoStartsSubscriber())
        await self._initialise_instances()
        await self._clientfile.write()

    async def _initialise_instances(self):
        autos, ls = [], await io.directory_list(self._home_dir)
        for identity in [str(o['name']) for o in ls if o['type'] == 'directory']:
            config_file = self._home_dir + '/' + identity + '/instance.json'
            if await io.file_exists(config_file):
                configuration = objconv.json_to_dict(await io.read_file(config_file))
                configuration.update({'identity': identity, 'home': self._home_dir + '/' + identity})
                subcontext = await self._initialise_instance(configuration)
                if subcontext.config('auto'):
                    autos.append(subcontext)
        self._context.post(self, _AutoStartsSubscriber.AUTOS, autos)

    def resources(self) -> httprsc.WebResource:
        return self._resource

    async def shutdown(self):
        shutdowns, destroys = [self._clientfile.delete(), self._pidfile.shutdown()], []
        for subcontext in self._context.subcontexts():
            self._instances.remove(subcontext.config('identity'))
            shutdowns.append(svrsvc.ServerService.shutdown(subcontext, self))
            destroys.append(self._context.destroy_subcontext(subcontext))
        await asyncio.gather(*shutdowns)
        await asyncio.gather(*destroys)

    async def instances_info(self, baseurl: str) -> dict:
        result = {}
        for child in self._instances.children():
            subcontext = self._get_subcontext(child.name(), False)
            if subcontext and child.name() == subcontext.config('identity') and not subcontext.config('hidden'):
                status = await svrsvc.ServerStatus.get_status(subcontext, self)
                result[child.name()] = {
                    'running': status['running'],
                    'module': subcontext.config('module'),
                    'url': baseurl + child.path()}
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

    async def create_instance(self, configuration: dict) -> contextsvc.Context:
        assert util.get('identity', configuration)
        assert self._modules.valid(util.get('module', configuration))
        identity = configuration.pop('identity')
        home_dir = self._home_dir + '/' + identity
        if await io.directory_exists(home_dir):
            raise Exception('Unable to create instance. Directory already exists.')
        try:
            logging.debug('CREATING instance ' + identity)
            await io.create_directory(home_dir)
            await io.write_file(home_dir + '/instance.json', objconv.obj_to_json(configuration))
            configuration.update({'identity': identity, 'home': home_dir})
            return await self._initialise_instance(configuration)
        except Exception as e:
            await funcutil.silently_call(io.delete_directory(home_dir))
            raise e

    async def delete_instance(self, subcontext: contextsvc.Context):
        identity, home_dir = subcontext.config('identity'), subcontext.config('home')
        self._instances.remove(identity)
        await self._context.destroy_subcontext(subcontext)
        await io.delete_directory(home_dir)
        self._context.post(self, mc.SystemService.SERVER_DELETED, subcontext)
        logging.debug('DELETED instance ' + identity)

    async def _initialise_instance(self, configuration: dict) -> contextsvc.Context:
        subcontext = self._context.create_subcontext(**configuration)
        subcontext.start()
        if subcontext.is_trace():
            subcontext.register(msglog.LoggerSubscriber(level=logging.DEBUG))
        subcontext.register(msgext.RelaySubscriber(self._context, mc.ServerStatus.UPDATED_FILTER))
        self._sysstoresvc.initialise_instance(subcontext)
        await sysmetrics.initialise_instance(subcontext)
        server = await self._modules.create_server(subcontext)
        await server.initialise()
        resource = httprsc.WebResource(subcontext.config('identity'), handler=_InstanceHandler(self))
        self._instances.append(resource)
        server.resources(resource)
        svrsvc.ServerService(subcontext, server).start()
        self._context.post(self, mc.SystemService.SERVER_INITIALISED, subcontext)
        return subcontext

    def _get_subcontext(self, identity: str, include_hidden: bool) -> contextsvc.Context | None:
        for subcontext in self._context.subcontexts():
            if identity == subcontext.config('identity'):
                if include_hidden or not subcontext.config('hidden'):
                    return subcontext
                return None
        return None


class _AutoStartsSubscriber(msgabc.AbcSubscriber):
    AUTOS = 'AutoStartsSubscriber.Autos'

    def __init__(self):
        super().__init__(msgftr.Or(
            msgftr.NameIs(_AutoStartsSubscriber.AUTOS),
            msgftr.NameIs(httpcnt.RESOURCES_READY)))
        self._autos = []

    def handle(self, message):
        if message.name() is _AutoStartsSubscriber.AUTOS:
            self._autos = message.data()
            return None
        for subcontext in self._autos:
            if subcontext.config('auto') in (1, 3):
                svrsvc.ServerService.signal_start(subcontext, self)
        return True


class _DeleteInstanceSubscriber(msgabc.AbcSubscriber):

    def __init__(self, system: SystemService):
        super().__init__(msgftr.NameIs(svrsvc.ServerService.DELETE_ME))
        self._system = system

    async def handle(self, message):
        await self._system.delete_instance(message.data())
        return None


class _InstancesHandler(httpabc.GetHandler, httpabc.PostHandler):
    VALIDATOR = re.compile(r'[^a-z0-9_\-]')

    def __init__(self, system: SystemService, modules: svrmodules.Modules):
        self._system, self._modules, = system, modules

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        return await self._system.instances_info(util.get('baseurl', data, ''))

    async def handle_post(self, resource, data):
        module, identity = util.get('module', data), util.get('identity', data)
        if not identity or not self._modules.valid(module):
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
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
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
        return result if result else httpabc.ResponseBody.NOT_FOUND


class _SystemInfoHandler(httpabc.GetHandler):

    def __init__(self):
        self._startmillis = dtutil.now_millis()

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        info = await sysutil.system_info()
        info['startmillis'] = self._startmillis
        info['uptime'] = dtutil.now_millis() - self._startmillis
        return info


class _PidFileSubscriber(msgabc.AbcSubscriber):

    def __init__(self, context: contextsvc.Context):
        super().__init__(msgftr.AcceptAll())
        self._pid, self._pidfile = str(signals.pid_self()), context.config('home') + '/.pid'
        self._running, self._last = True, None

    async def handle(self, message):
        if not self._running:
            return True
        now = message.created()
        if not self._last:
            await funcutil.silently_call(io.write_file(self._pidfile, self._pid))
            self._last = now
        elif now - self._last > 300.0:  # 5 minutes
            await funcutil.silently_call(io.touch_file(self._pidfile))
            self._last = now
        return None

    async def shutdown(self):
        self._running = False
        await funcutil.silently_call(io.write_file(self._pidfile, self._pid))


class _ShutdownHandler(httpabc.PostHandler):

    def handle_post(self, resource, data):
        signals.interrupt_self()
        return httpabc.ResponseBody.NO_CONTENT


class _InstanceEventTransformer(msgabc.Transformer):

    def transform(self, message):
        if mc.ServerStatus.UPDATED_FILTER.accepts(message):
            status = message.data()
            return {'event': 'running', 'instance': status['instance'], 'running': status['running']}
        if mc.SystemService.SERVER_FILTER.accepts(message):
            event = 'created' if message.name() is mc.SystemService.SERVER_INITIALISED else 'deleted'
            return {'event': event, 'instance': objconv.obj_to_dict(message.data())}
        return None
