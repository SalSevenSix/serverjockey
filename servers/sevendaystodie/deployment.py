from xml.dom import minidom
# ALLOW core.* sevendaystodie.messaging
from core.util import util, objconv, io
from core.msg import msgftr, msgtrf, msglog, msgext
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.system import svrsvc
from core.proc import proch, jobh
from core.common import steam, interceptors, portmapper
from servers.sevendaystodie import messaging as msg


def _default_cmdargs():
    return {
        '_comment_server_upnp': 'Try to automatically redirect server ports on home network using UPnP',
        'server_upnp': True,
        '_comment_console_upnp': 'Try to automatically redirect web console port on home network using UPnP',
        'console_upnp': False,
        '_comment_telnet_upnp': 'Try to automatically redirect telnet port on home network using UPnP',
        'telnet_upnp': False
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir, self._tmp_dir = context.config('home'), context.config('tmpdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._settings_def_file = self._runtime_dir + '/serverconfig.xml'
        self._runtime_metafile = self._runtime_dir + '/steamapps/appmanifest_294420.acf'
        self._executable = self._runtime_dir + '/7DaysToDieServer.x86_64'
        self._world_dir = self._home_dir + '/world'
        self._config_dir = self._world_dir + '/config'
        self._save_dir = self._world_dir + '/save'
        self._log_dir = self._save_dir + '/logs'
        self._cmdargs_file = self._config_dir + '/cmdargs.json'
        self._settings_file = self._config_dir + '/serverconfig.xml'
        self._live_file = self._config_dir + '/serverconfig-live.xml'
        self._admin_file = self._config_dir + '/serveradmin.xml'
        self._env = context.config('env').copy()
        self._env['LD_LIBRARY_PATH'] = '.'

    async def initialise(self):
        await self.build_world()
        self._mailer.register(portmapper.PortMapperService(self._mailer))
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE, jobh.JobProcess.FILTER_DONE),
            self.build_world))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer, self._tmp_dir), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer, self._tmp_dir), msgext.SyncReply.AT_START))
        self._mailer.register(msglog.LogfileSubscriber(
            self._log_dir + '/%Y%m%d-%H%M%S.log', msg.CONSOLE_LOG_FILTER,
            svrsvc.ServerStatus.RUNNING_FALSE_FILTER, msgtrf.GetData()))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.psh('logs', httpext.FileSystemHandler(self._log_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._log_dir, 'path'), 'r')
        r.pop()
        r.psh('config')
        r.put('cmdargs', httpext.FileSystemHandler(self._cmdargs_file), 'm')
        r.put('settings', httpext.FileSystemHandler(self._settings_file), 'm')
        r.put('admin', httpext.FileSystemHandler(self._admin_file), 'm')
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
        r.put('*{path}', httpext.FileSystemHandler(
            self._backups_dir, 'path', tmp_dir=self._tmp_dir,
            read_tracker=msglog.IntervalTracker(self._mailer, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._mailer)), 'm')

    async def new_server_process(self) -> proch.ServerProcess:
        if not await io.file_exists(self._executable):
            raise FileNotFoundError('7D2D game server not installed. Please Install Runtime first.')
        config = await self._build_live_config()
        await self._map_ports(config)
        return proch.ServerProcess(self._mailer, self._executable) \
            .use_env(self._env) \
            .use_cwd(self._runtime_dir) \
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
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))
        if not await io.file_exists(self._settings_file):
            await io.copy_text_file(self._settings_def_file, self._settings_file)

    async def _build_live_config(self) -> dict:
        live_dict = {}
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
                        live_dict[name] = subs[name]
                    del subs[name]
                else:
                    live.appendChild(node)
                    live_dict[name] = node.getAttribute('value')
        for name, value in subs.items():
            if value is not None:
                live_node = minidom.Element('property')
                live_node.ownerDocument = doc
                live_node.setAttribute('name', name)
                live_node.setAttribute('value', value)
                live.appendChild(live_node)
                live_dict[name] = value
        await io.write_file(self._live_file, doc.toxml())
        return live_dict

    async def _map_ports(self, config: dict):
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        if util.get('server_upnp', cmdargs, True):
            server_port = int(util.get('ServerPort', config, 26900))
            portmapper.map_port(self._mailer, self, server_port, portmapper.TCP, '7D2D TCP server')
            portmapper.map_port(self._mailer, self, server_port, portmapper.UDP, '7D2D UDP server')
            portmapper.map_port(self._mailer, self, server_port + 1, portmapper.UDP, '7D2D aux1')
            portmapper.map_port(self._mailer, self, server_port + 2, portmapper.UDP, '7D2D aux2')
            portmapper.map_port(self._mailer, self, server_port + 3, portmapper.UDP, '7D2D aux3')
        if util.get('console_upnp', cmdargs, False) and objconv.to_bool(util.get('WebDashboardEnabled', config)):
            console_port = int(util.get('WebDashboardPort', config, 8080))
            portmapper.map_port(self._mailer, self, console_port, portmapper.TCP, '7D2D web console')
        if util.get('telnet_upnp', cmdargs, False) and objconv.to_bool(util.get('TelnetEnabled', config)):
            telnet_port = int(util.get('TelnetPort', config, 8081))
            portmapper.map_port(self._mailer, self, telnet_port, portmapper.TCP, '7D2D telnet')
