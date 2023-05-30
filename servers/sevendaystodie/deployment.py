from xml.dom import minidom
# ALLOW core.* sevendaystodie.messaging
from core.util import io
from core.msg import msgftr, msgtrf, msglog, msgext
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.system import svrsvc
from core.proc import proch, jobh
from core.common import steam, interceptors
from servers.sevendaystodie import messaging as msg


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir = context.config('home')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._settings_def_file = self._runtime_dir + '/serverconfig.xml'
        self._runtime_metafile = self._runtime_dir + '/steamapps/appmanifest_294420.acf'
        self._executable = self._runtime_dir + '/7DaysToDieServer.x86_64'
        self._world_dir = self._home_dir + '/world'
        self._config_dir = self._world_dir + '/config'
        self._save_dir = self._world_dir + '/save'
        self._log_dir = self._save_dir + '/logs'
        self._log_file = self._log_dir + '/server-%Y%m%d-%H%M%S.log'
        self._settings_file = self._config_dir + '/serverconfig.xml'
        self._live_file = self._config_dir + '/serverconfig-live.xml'
        self._admin_file = self._config_dir + '/serveradmin.xml'
        self._env = context.config('env').copy()
        self._env['LD_LIBRARY_PATH'] = self._runtime_dir

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
        self._mailer.register(msglog.LogfileSubscriber(
            self._log_file, msg.CONSOLE_LOG_FILTER,
            msgftr.And(msgftr.NameIs(svrsvc.ServerStatus.NOTIFY_RUNNING), msgftr.DataEquals(False)),
            msgtrf.GetData()))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.psh('logs', httpext.FileSystemHandler(self._log_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._log_dir, 'path'))
        r.pop()
        r.psh('config')
        r.put('settings', httpext.FileSystemHandler(self._settings_file))
        r.put('admin', httpext.FileSystemHandler(self._admin_file))
        r.pop()
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_metafile))
        r.put('install-runtime', steam.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 294420), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('wipe-world-config', httpext.WipeHandler(self._mailer, self._config_dir), 'r')
        r.put('wipe-world-save', httpext.WipeHandler(self._mailer, self._save_dir), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._backups_dir, 'path'), 'm')

    def new_server_process(self) -> proch.ServerProcess:
        return proch.ServerProcess(self._mailer, self._executable) \
            .use_env(self._env) \
            .append_arg('-quit') \
            .append_arg('-batchmode') \
            .append_arg('-nographics') \
            .append_arg('-dedicated') \
            .append_arg('-configfile=' + self._live_file)

    async def build_world(self):
        await io.create_directory(self._backups_dir)
        await io.create_directory(self._world_dir)
        await io.create_directory(self._config_dir)
        await io.create_directory(self._save_dir)
        await io.create_directory(self._log_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        if not await io.file_exists(self._settings_file):
            await io.copy_text_file(self._settings_def_file, self._settings_file)

    async def build_live_config(self):
        subs = {
            'AdminFileName': '../../config/serveradmin.xml',
            'UserDataFolder': self._save_dir,
            'SaveGameFolder': None
        }
        xml = await io.read_file(self._settings_file)
        original = minidom.parseString(xml).firstChild
        live = minidom.Element(original.tagName)
        doc = minidom.Document()
        doc.appendChild(live)
        live.ownerDocument = doc
        for node in original.childNodes:
            if isinstance(node, minidom.Element):
                name = node.getAttribute('name')
                if name in subs:
                    if subs[name] is not None:
                        live_node = minidom.Element(node.tagName)
                        live_node.ownerDocument = doc
                        live_node.setAttribute('name', name)
                        live_node.setAttribute('value', subs[name])
                        live.appendChild(live_node)
                    del subs[name]
                else:
                    live.appendChild(node)
        for name, value in subs.items():
            if value is not None:
                live_node = minidom.Element('property')
                live_node.ownerDocument = doc
                live_node.setAttribute('name', name)
                live_node.setAttribute('value', value)
                live.appendChild(live_node)
        await io.write_file(self._live_file, doc.toxml())
