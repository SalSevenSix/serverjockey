# ALLOW core.* starbound.messaging
from core.util import util, io, objconv
from core.msg import msgext, msgftr, msglog
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.proc import proch, jobh
from core.common import steam, rconsvc, interceptors
from servers.starbound import messaging as msg

# STARBOUND https://starbounder.org/Guide:LinuxServerSetup


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir = context.config('home')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._config_file = self._world_dir + '/starbound_server.config'

    async def initialise(self):
        await self.build_world()
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE, jobh.JobProcess.FILTER_DONE),
            self.build_world))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer), msgext.SyncReply.AT_START))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.put('log', httpext.FileSystemHandler(self._world_dir + '/starbound_server.log'))
        r.psh('logs', httpext.FileSystemHandler(self._world_dir, ls_filter=_logfiles))
        r.put('*{path}', httpext.FileSystemHandler(self._world_dir, 'path'), 'r')
        r.pop()
        r.psh('config')
        r.put('settings', httpext.FileSystemHandler(self._config_file), 'm')
        r.pop()
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_dir + '/steamapps/appmanifest_211820.acf'))
        r.put('install-runtime', steam.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 211820, anon=False), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('wipe-world-save', httpext.WipeHandler(self._mailer, self._world_dir + '/universe'), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        r.pop()
        r.psh('steamcmd')
        r.put('login', steam.SteamCmdLoginHandler(self._mailer))
        r.put('input', steam.SteamCmdInputHandler(self._mailer))
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(
            self._backups_dir, 'path',
            read_tracker=msglog.IntervalTracker(self._mailer, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._mailer)), 'm')

    async def new_server_process(self):
        await self._rcon_config()
        await self._link_mods()
        bin_dir = self._runtime_dir + '/linux'
        return proch.ServerProcess(self._mailer, bin_dir + '/starbound_server').use_cwd(bin_dir)

    async def build_world(self):
        await io.create_directory(self._backups_dir)
        await io.create_directory(self._world_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        storage_dir = self._runtime_dir + '/storage'
        if not await io.symlink_exists(storage_dir):
            await io.create_symlink(storage_dir, self._world_dir)

    async def _rcon_config(self):
        if not await io.file_exists(self._config_file):
            return
        config = objconv.json_to_dict(await io.read_file(self._config_file))
        port, password = util.get('rconServerPort', config), util.get('rconServerPassword', config)
        if not port:
            port = 21026
        if not password:
            password = util.generate_token(10)
        rconsvc.RconService.set_config(self._mailer, self, port, password)
        config['rconServerPort'], config['rconServerPassword'] = port, password
        config['runRconServer'] = True
        await io.write_file(self._config_file, objconv.obj_to_json(config, pretty=True))

    async def _link_mods(self):
        self._mailer.post(self, msg.DEPLOYMENT_MSG, 'INFO  Including subscribed workshop mods...')
        workshop_files, workshop_dir = [], self._runtime_dir + '/steamapps/workshop/content/211820'
        if await io.directory_exists(workshop_dir):
            workshop_files = await io.directory_list(workshop_dir)
        workshop_items, mods_dir = [], self._runtime_dir + '/mods'
        for workshop_item in [str(o['name']) for o in workshop_files if o['type'] == 'directory']:
            pack_file = workshop_dir + '/' + workshop_item + '/contents.pak'
            if await io.file_exists(pack_file):
                self._mailer.post(self, msg.DEPLOYMENT_MSG, 'INFO  Adding   ' + workshop_item)
                workshop_items.append(workshop_item + '.pak')
                link_file = mods_dir + '/' + workshop_item + '.pak'
                if not await io.symlink_exists(link_file):
                    await io.create_symlink(link_file, pack_file)
            else:
                self._mailer.post(self, msg.DEPLOYMENT_MSG,
                                  'ERROR Adding   ' + workshop_item + ' because contents.pak not found')
        mod_files = await io.directory_list(mods_dir)
        for mod_file in [o['name'] for o in mod_files if o['type'] == 'link']:
            if mod_file not in workshop_items:
                self._mailer.post(self, msg.DEPLOYMENT_MSG, 'INFO  Removing ' + mod_file[:-4])
                await io.delete_file(mods_dir + '/' + mod_file)


def _logfiles(entry) -> bool:
    return entry['type'] == 'file' and entry['name'].startswith('starbound_server.log')
