import importlib
import logging
import uuid
from core import httpsvc, httpext, svrsvc, msgext, util, msgftr


class SystemService:
    SERVER_INITIALISED = 'SystemService.ServerInitialised'
    SERVER_DELETED = 'SystemService.ServerDestroyed'
    SERVER_DELETE = 'SystemService.ServerDelete'

    def __init__(self, context):
        self.context = context
        self.modules = {}
        self.home_dir = self.context.config('home')
        self.url = self.context.config('url')
        self.res = httpext.ResourceBuilder(self.url) \
            .push('system') \
            .append('shutdown', _ShutdownHandler(self)) \
            .pop() \
            .append('instances', _InstancesHandler(self)) \
            .build()
        self.instances = self.res.get_resource('instances')
        self.context.register(_Subscriber(self))

    def resources(self):
        return self.res

    async def initialise(self):
        ls = util.directory_list_dict(self.home_dir)
        for directory in iter([o for o in ls if o['type'] == 'directory']):
            identity = directory['name']
            config_file = self.home_dir + '/' + identity + '/instance.json'
            if util.file_exists(config_file):
                configuration = await util.read_file(config_file)
                configuration = util.json_to_dict(configuration)
                configuration.update({
                    'identity': identity,
                    'url': self.url + '/instances/' + identity,
                    'home': self.home_dir + '/' + identity
                })
                self.initialise_instance(configuration)
        return self

    def create_server(self, subcontext):
        module_name = subcontext.config('module')
        module = util.get(module_name, self.modules)
        if not module:
            module = importlib.import_module('servers.{}.server'.format(module_name))
            self.modules.update({module_name: module})
        return module.Server(subcontext)

    def initialise_instance(self, configuration):
        subcontext = self.context.create_subcontext(**configuration)
        subcontext.start()
        subcontext.register(msgext.RelaySubscriber(self.context, _Subscriber.FILTER))
        if subcontext.is_debug():
            subcontext.register(msgext.LoggerSubscriber(level=logging.DEBUG))
        server = self.create_server(subcontext)
        instance = server.resources(subcontext.config('identity'))
        self.instances.append(instance)
        svrsvc.ServerService(subcontext, server).start()
        self.context.post(self, SystemService.SERVER_INITIALISED, subcontext)
        return subcontext

    async def create_instance(self, configuration):
        identity = str(uuid.uuid4())
        home_dir = self.home_dir + '/' + identity
        util.create_directory(home_dir)
        config_file = home_dir + '/' + 'instance.json'
        await util.write_file(config_file, util.obj_to_json(configuration))
        configuration.update({
            'identity': identity,
            'url': self.url + '/instances/' + identity,
            'home': home_dir
        })
        return self.initialise_instance(configuration)

    async def delete_instance(self, subcontext):
        self.instances.remove(subcontext.config('identity'))
        await self.context.destroy_subcontext(subcontext)
        util.delete_directory(subcontext.config('home'))
        self.context.post(self, SystemService.SERVER_DELETED, subcontext)

    async def shutdown(self):
        subcontexts = self.context.subcontexts()
        for subcontext in iter(subcontexts):
            self.instances.remove(subcontext.config('identity'))
        for subcontext in iter(subcontexts):
            await svrsvc.ServerService.shutdown(subcontext, self)
            await self.context.destroy_subcontext(subcontext)
        await self.context.shutdown()
        util.signal_interrupt()


class _Subscriber:
    FILTER = msgftr.NameIs(SystemService.SERVER_DELETE)

    def __init__(self, server):
        self.server = server

    def accepts(self, message):
        return _Subscriber.FILTER.accepts(message)

    async def handle(self, message):
        await self.server.delete_instance(message.get_data())
        return None


class _InstancesHandler:
    def __init__(self, server):
        self.server = server

    async def handle_post(self, resource, data):
        subcontext = await self.server.create_instance(data)
        return {'url': subcontext.config('url')}


class _ShutdownHandler:
    def __init__(self, server):
        self.server = server

    async def handle_post(self, resource, data):
        await self.server.shutdown()
        return httpsvc.ResponseBody.NO_CONTENT
