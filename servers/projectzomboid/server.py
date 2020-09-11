import asyncio

from core import proch, msgftr, httpext, svrsvc, util
from servers.projectzomboid import handlers as h, subscribers as s


class Server:
    STARTED_FILTER = msgftr.And((
        proch.Filter.STDOUT_LINE,
        msgftr.DataStrContains('SERVER STARTED')))

    def __init__(self, context):
        self.context = context
        self.deployment = Deployment(context)
        self.pipeinsvc = proch.PipeInLineService(context)
        context.register(s.ServerStateSubscriber(context))
        context.register(s.ServerDetailsSubscriber(context))

    def resources(self):
        conf_pre = self.deployment.config_dir + '/' + self.deployment.world_name
        base_url = 'http://{}:{}'.format(self.context.get_host(), self.context.get_port())
        return httpext.ResourceBuilder(base_url) \
            .push('server', httpext.ServerStatusHandler(self.context)) \
            .append('{command}', httpext.ServerCommandHandler(self.context)) \
            .pop() \
            .push('deployment', h.DeploymentHandler(self.deployment)) \
            .append('{command}', h.DeploymentCommandHandler(self.deployment)) \
            .pop() \
            .push('world') \
            .append('{command}', h.WorldCommandHandler(self.context)) \
            .pop() \
            .push('config') \
            .push('options', h.OptionsHandler(self.context)) \
            .append('reload', h.OptionsReloadHandler(self.context)) \
            .push('{option}') \
            .append('{command}', h.OptionCommandHandler(self.context)) \
            .pop().pop() \
            .append('db', httpext.ReadWriteFileHandler(self.deployment.playerdb_file, text=False)) \
            .append('ini', httpext.ProtectedLineConfigHandler(conf_pre + '.ini', ('^Password=.*', '^DiscordToken.*'))) \
            .append('sandbox', httpext.ReadWriteFileHandler(conf_pre + '_SandboxVars.lua')) \
            .append('spawnpoints', httpext.ReadWriteFileHandler(conf_pre + '_spawnpoints.lua')) \
            .append('spawnregions', httpext.ReadWriteFileHandler(conf_pre + '_spawnregions.lua')) \
            .pop() \
            .append('steamids', h.SteamidsHandler(self.context)) \
            .push('players', h.PlayersHandler(self.context)) \
            .push('{player}') \
            .append('{command}', h.PlayerCommandHandler(self.context)) \
            .pop().pop() \
            .push('whitelist') \
            .append('{command}', h.WhitelistCommandHandler(self.context)) \
            .pop() \
            .push('banlist') \
            .append('{command}', h.BanlistCommandHandler(self.context)) \
            .pop() \
            .append('log', h.ConsoleLogHandler(self.context)) \
            .build()

    async def run(self):
        self.context.post((self, svrsvc.ServerStatus.NOTIFY_DETAILS, {'host': self.context.get_host()}))
        return await proch.ProcessHandler(self.context, self.context.get_executable()) \
            .append_arg('-cachedir=' + self.deployment.world_dir) \
            .use_pipeinsvc(self.pipeinsvc) \
            .wait_for_started(Server.STARTED_FILTER, 100) \
            .run()   # sync

    async def stop(self):
        await proch.PipeInLineService.request(self.context, self, 'quit')


class Deployment:

    def __init__(self, context):
        self.world_name = 'servertest'
        self.home_dir = context.get_home()
        self.runtime_dir = context.relative_path('runtime')
        self.world_dir = context.relative_path('world')
        self.playerdb_dir = self.world_dir + '/db'
        self.playerdb_file = self.playerdb_dir + '/' + self.world_name + '.db'
        self.config_dir = self.world_dir + '/Server'
        self.save_dir = self.world_dir + '/Saves'

    def directory_list(self):
        return util.directory_list_dict(self.home_dir)

    async def install_runtime(self, beta=None, validate=False, wipe=True):
        app_arg = ['+app_update 380870']
        if beta:
            app_arg.append('-beta ' + beta)
        if validate:
            app_arg.append('validate')
        if wipe:
            util.delete_directory(self.runtime_dir)
        process = await asyncio.create_subprocess_exec(
            'steamcmd',
            '+login anonymous',
            '+force_install_dir ' + self.runtime_dir,
            ' '.join(app_arg),
            '+quit',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL)
        stdout, stderr = await process.communicate()
        if stdout:
            return stdout.decode()
        return 'NO STDOUT'

    def backup_runtime(self):
        return util.archive_directory(self.runtime_dir)

    def backup_world(self):
        return util.archive_directory(self.world_dir)

    def wipe_world_all(self):
        util.delete_directory(self.world_dir)
        util.create_directory(self.world_dir)
        util.create_directory(self.playerdb_dir)
        util.create_directory(self.config_dir)
        util.create_directory(self.save_dir)

    def wipe_world_playerdb(self):
        util.delete_directory(self.playerdb_dir)
        util.create_directory(self.playerdb_dir)

    def wipe_world_config(self):
        util.delete_directory(self.config_dir)
        util.create_directory(self.config_dir)

    def wipe_world_save(self):
        util.delete_directory(self.save_dir)
        util.create_directory(self.save_dir)
