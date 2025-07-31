from __future__ import annotations
import typing
# ALLOW util.* msg*.* context.* http.* system.* proc.*
from core.util import aggtrf, cmdutil
from core.msg import msgabc, msglog, msgftr, msgtrf, msgext, msgpack
from core.msgc import mc
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.system import svrext
from core.proc import jobh, prcext
from core.common import steam, playerstore, interceptors, portmapper, rconsvc

_SEND_COMMAND = cmdutil.CommandLines(dict(send='{line}'))


class MessagingInitHelper:

    def __init__(self, context: contextsvc.Context):
        self._context = context

    def init_state(self, job_start_filter: msgabc.Filter = None,
                   job_done_filter: msgabc.Filter = None) -> MessagingInitHelper:
        self._context.register(prcext.ServerStateSubscriber(self._context))
        self._context.register(svrext.MaintenanceStateSubscriber(
            self._context,
            msgftr.Or(job_start_filter if job_start_filter else jobh.JobProcess.FILTER_STARTED,
                      msgpack.Archiver.FILTER_START, msgpack.Unpacker.FILTER_START),
            msgftr.Or(job_done_filter if job_done_filter else jobh.JobProcess.FILTER_DONE,
                      msgpack.Archiver.FILTER_DONE, msgpack.Unpacker.FILTER_DONE)))
        return self

    def init_players(self) -> MessagingInitHelper:
        self._context.register(playerstore.PlayersSubscriber(self._context))
        return self


class DeploymentInitHelper:

    def __init__(self, context: contextsvc.Context, build_world: typing.Callable):
        self._context, self._build_world = context, build_world
        self._rebuild_filters = [httpext.WipeHandler.FILTER_DONE]

    def init_ports(self) -> DeploymentInitHelper:
        self._context.register(portmapper.PortMapperService(self._context))
        return self

    def init_jobs(self, no_rebuild: bool = False) -> DeploymentInitHelper:
        self._context.register(jobh.JobProcess(self._context))
        if not no_rebuild:
            self._rebuild_filters.append(jobh.JobProcess.FILTER_DONE)
        return self

    def init_archiving(self, tempdir: str) -> DeploymentInitHelper:
        self._context.register(
            msgext.SyncWrapper(self._context, msgpack.Archiver(self._context, tempdir), msgext.SyncReply.AT_START))
        self._context.register(
            msgext.SyncWrapper(self._context, msgpack.Unpacker(self._context, tempdir), msgext.SyncReply.AT_START))
        self._rebuild_filters.append(msgpack.Unpacker.FILTER_DONE)
        return self

    def init_logging(self, logs_dir: str, log_filter: msgabc.Filter) -> DeploymentInitHelper:
        roll_filter = msgftr.Or(mc.ServerStatus.RUNNING_FALSE_FILTER, msgftr.And(
            httpext.WipeHandler.FILTER_DONE, msgftr.DataStrStartsWith(logs_dir, invert=True)))
        self._context.register(msglog.LogfileSubscriber(
            logs_dir + '/%Y%m%d-%H%M%S.log', log_filter, roll_filter, msgtrf.GetData()))
        return self

    def done(self):
        self._context.register(msgext.CallableSubscriber(msgftr.Or(*self._rebuild_filters), self._build_world))


class ServerResourceBuilder:

    def __init__(self, context: contextsvc.Context, resource: httprsc.WebResource):
        self._context, self._resource = context, resource
        self._httpsubs, self._builder = httpsubs.HttpSubscriptionService(context), httprsc.ResourceBuilder(resource)
        self._builder.reg('m', interceptors.block_maintenance_only(context))

    def psh(self, signature, handler=None, ikeys=None) -> ServerResourceBuilder:
        self._builder.psh(signature, handler, ikeys)
        return self

    def put(self, signature, handler=None, ikeys=None) -> ServerResourceBuilder:
        self._builder.put(signature, handler, ikeys)
        return self

    def pop(self) -> ServerResourceBuilder:
        self._builder.pop()
        return self

    def put_server(self, additional_commands: typing.Dict[str, typing.Callable] = None) -> ServerResourceBuilder:
        self.psh('server', svrext.ServerStatusHandler(self._context))
        self.put('subscribe', self._httpsubs.handler(mc.ServerStatus.UPDATED_FILTER))
        self.put('{command}', svrext.ServerCommandHandler(self._context, additional_commands), 'm')
        return self.pop()

    def put_players(self, no_list: bool = False) -> ServerResourceBuilder:
        self.psh('players', None if no_list else playerstore.PlayersHandler(self._context))
        self.put('subscribe', self._httpsubs.handler(mc.PlayerStore.EVENT_FILTER, mc.PlayerStore.EVENT_TRF))
        return self.pop()

    def put_log(self, log_filter: msgabc.Filter) -> ServerResourceBuilder:
        self.psh('log')
        self.put('tail', httpext.RollingLogHandler(self._context, log_filter))
        self.put('subscribe', self._httpsubs.handler(log_filter, aggtrf.StrJoin('\n')))
        return self.pop()

    def put_subs(self) -> ServerResourceBuilder:
        self.psh(self._httpsubs.resource(self._resource, 'subscriptions'))
        self.put('{identity}', self._httpsubs.subscriptions_handler('identity'))
        return self.pop()


class DeploymentResourceBuilder:

    def __init__(self, context: contextsvc.Context, resource: httprsc.WebResource):
        self._context, self._builder = context, httprsc.ResourceBuilder(resource)
        self._builder.reg('r', interceptors.block_running_or_maintenance(context))
        self._builder.reg('m', interceptors.block_maintenance_only(context))

    def psh(self, signature, handler=None, ikeys=None) -> DeploymentResourceBuilder:
        self._builder.psh(signature, handler, ikeys)
        return self

    def put(self, signature, handler=None, ikeys=None) -> DeploymentResourceBuilder:
        self._builder.put(signature, handler, ikeys)
        return self

    def pop(self) -> DeploymentResourceBuilder:
        self._builder.pop()
        return self

    def psh_deployment(self) -> DeploymentResourceBuilder:
        return self.psh('deployment')

    def put_meta(self, runtime_meta: str, world_meta: httpabc.GetHandler) -> DeploymentResourceBuilder:
        self.put('runtime-meta', httpext.FileSystemHandler(runtime_meta))
        self.put('world-meta', world_meta)
        return self

    def put_installer(self, handler: httpabc.PostHandler) -> DeploymentResourceBuilder:
        return self.put('install-runtime', handler, 'r')

    def put_installer_steam(self, runtime_dir: str, app_id: str, anon: bool = True) -> DeploymentResourceBuilder:
        return self.put_installer(steam.SteamCmdInstallHandler(self._context, runtime_dir, app_id, anon))

    def put_wipes(self, runtime_dir: str, world_dirs: dict) -> DeploymentResourceBuilder:
        self.put('wipe-runtime', httpext.WipeHandler(self._context, runtime_dir), 'r')
        for key, value in world_dirs.items():
            if isinstance(value, dict):
                handler = httpext.WipeHandler(self._context, value['path'], value['ls_filter'])
            else:
                handler = httpext.WipeHandler(self._context, value)
            self.put('wipe-world-' + key, handler, 'r')
        return self

    def put_archiving(
            self, home_dir: str, backups_dir: str, runtime_dir: str, world_dir: str) -> DeploymentResourceBuilder:
        self.put('backup-runtime', httpext.ArchiveHandler(self._context, backups_dir, runtime_dir), 'r')
        self.put('backup-world', httpext.ArchiveHandler(self._context, backups_dir, world_dir), 'r')
        self.put('restore-backup', httpext.UnpackerHandler(self._context, backups_dir, home_dir), 'r')
        return self

    def put_log(self, log_file: str) -> DeploymentResourceBuilder:
        return self.put('log', httpext.FileSystemHandler(log_file))

    def put_logs(self, logs_dir: str, ls_filter: typing.Callable = None) -> DeploymentResourceBuilder:
        self.psh('logs', httpext.FileSystemHandler(logs_dir, ls_filter=ls_filter))
        self.put('*{path}', httpext.FileSystemHandler(logs_dir, 'path'), 'r')
        return self.pop()

    def put_backups(self, tempdir: str, backups_dir: str) -> DeploymentResourceBuilder:
        self.psh('backups', httpext.FileSystemHandler(backups_dir))
        self.put('*{path}', httpext.FileSystemHandler(
            backups_dir, 'path', tempdir=tempdir,
            read_tracker=msglog.IntervalTracker(self._context, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._context)), 'm')
        return self.pop()

    def put_config(self, config_files: dict) -> DeploymentResourceBuilder:
        self.psh('config')
        for key in config_files.keys():
            self.put(key, httpext.FileSystemHandler(config_files[key]), 'm')
        return self.pop()

    def put_steamcmd(self) -> DeploymentResourceBuilder:
        self.psh('steamcmd')
        self.put('login', steam.SteamCmdLoginHandler(self._context))
        self.put('input', steam.SteamCmdInputHandler(self._context))
        return self.pop()


class ConsoleResourceBuilder:

    def __init__(self, mailer: msgabc.MulticastMailer, resource: httprsc.WebResource):
        self._mailer, self._builder = mailer, httprsc.ResourceBuilder(resource)
        self._builder.reg('s', interceptors.block_not_started(mailer))

    def psh(self, signature, handler=None, ikeys=None) -> ConsoleResourceBuilder:
        self._builder.psh(signature, handler, ikeys)
        return self

    def put(self, signature, handler=None, ikeys=None) -> ConsoleResourceBuilder:
        self._builder.put(signature, handler, ikeys)
        return self

    def psh_console(self) -> ConsoleResourceBuilder:
        return self.psh('console')

    def put_help(self, text: str) -> ConsoleResourceBuilder:
        return self.put('help', httpext.StaticHandler(text))

    def put_send_rcon(self) -> ConsoleResourceBuilder:
        return self.put('send', rconsvc.RconHandler(self._mailer), 's')

    def put_send_pipein(self) -> ConsoleResourceBuilder:
        return self.put('{command}', prcext.ConsoleCommandHandler(self._mailer, _SEND_COMMAND), 's')

    def put_say_pipein(self, template: str) -> ConsoleResourceBuilder:
        return self.put('say', prcext.SayHandler(self._mailer, template), 's')
