import logging
import argparse
import asyncio
import sys
import os
# ALLOW util.* msg.* context.* http.* system.svrabc system.system
from core.util import util, idutil, funcutil, sysutil, steamutil, logutil, io, tasks, objconv
from core.msg import msglog
from core.context import contextsvc, contextext
from core.http import httpabc, httpsvc, httpssl
from core.system import system


class _NoTraceFilter(logging.Filter):
    PREFIXES = 'tsk>', 'trs>', 'msg>', 'shl>', 'net>'

    def filter(self, record):
        message = record.getMessage()
        trace = len(message) > 4 and message[:4] in _NoTraceFilter.PREFIXES
        return not trace


def _stime(home: str) -> float | None:
    file = home + '/.pid'
    return os.stat(file).st_atime if os.path.isfile(file) else None


def _load_cmdargs(home: str) -> dict:
    file = home + '/serverjockey.json'
    if not os.path.isfile(file):
        return {}
    with open(file) as fd:
        result = objconv.json_to_dict(fd.read())
    if not result:
        raise Exception('Invalid JSON file: ' + file)
    result = util.get('cmdargs', result, {})
    assert isinstance(result, dict)
    return result


def _argument_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Start ServerJockey game server management system.')
    p.add_argument('--version', action='store_true', help='Show version and exit')
    p.add_argument('--home', type=str,
                   help='Home directory to use for server instances, default is current working directory')
    p.add_argument('--logfile', type=str, nargs='?', const='serverjockey.log',
                   help='Optional log file to use, relative to home unless starts with "/" or "."')
    p.add_argument('--tempdir', type=str, help='Directory to use for temporary files, default is .tmp under home')
    p.add_argument('--host', type=str, help='Comma delimited IPs to bind http service, default is all')
    p.add_argument('--port', type=int, help='Port for http service, default is 6164')
    p.add_argument('--showtoken', action='store_true', help='Print the login token to stdout')
    p.add_argument('--noupnp', action='store_true', help='Do not enable UPnP services')
    p.add_argument('--nostore', action='store_true', help='Do not use database to store activity')
    p.add_argument('--debug', action='store_true', help='Debug mode logging')
    p.add_argument('--trace', action='store_true', help='Debug mode with more logging')
    return p


def _create_context() -> contextsvc.Context | None:
    args = _argument_parser().parse_args(sys.argv[1:])
    if args.version:
        print(sysutil.system_version())
        return None
    home = util.full_path(os.getcwd(), args.home if args.home else '.')
    cfg = _load_cmdargs(home)
    logfile = args.logfile if args.logfile else util.get('logfile', cfg)
    logfile = 'serverjockey.log' if objconv.to_bool(logfile) and not isinstance(logfile, str) else logfile
    logfile = util.full_path(home, logfile)
    tempdir = args.tempdir if args.tempdir else util.get('tempdir', cfg, '.tmp')
    tempdir = util.full_path(home, tempdir)
    host = args.host if args.host else util.get('host', cfg)
    host = tuple(host.split(',')) if host else None
    port = args.port if args.port else util.get('port', cfg, 6164)
    showtoken = True if args.showtoken else objconv.to_bool(util.get('showtoken', cfg))
    noupnp = True if args.noupnp else objconv.to_bool(util.get('noupnp', cfg))
    nostore = True if args.nostore else objconv.to_bool(util.get('nostore', cfg))
    dbfile = None if nostore else util.full_path(home, 'serverjockey.db')
    debug = True if args.debug else objconv.to_bool(util.get('debug', cfg))
    trace = True if args.trace else objconv.to_bool(util.get('trace', cfg))
    secret = util.get('secret', cfg, idutil.generate_token(10, True))
    return contextsvc.Context(dict(
        home=home, logfile=logfile, tempdir=tempdir, host=host, port=port, showtoken=showtoken,
        noupnp=noupnp, dbfile=dbfile, debug=debug, trace=trace, secret=secret, python=sys.executable,
        stime=_stime(home), scheme=httpssl.sync_get_scheme(home), env=os.environ.copy()))


def _setup_logging(context: contextsvc.Context):
    logfmt, datefmt = '%(asctime)s %(levelname)05s %(message)s', '%Y-%m-%d %H:%M:%S'
    level = logging.DEBUG if context.is_debug() else logging.INFO
    filename = context.config('logfile')
    if filename:
        filename_prev = logutil.prev_logname(filename)
        if os.path.isfile(filename):
            if os.path.isfile(filename_prev):
                os.remove(filename_prev)
            os.rename(filename, filename_prev)
        logging.basicConfig(level=level, format=logfmt, datefmt=datefmt, filename=filename, filemode='w')
        if context.is_debug():
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(logging.Formatter(logfmt, datefmt))
            logging.getLogger().addHandler(stdout_handler)
    else:
        logging.basicConfig(level=level, format=logfmt, datefmt=datefmt, stream=sys.stdout)
    if context.is_debug() and not context.is_trace():
        logging.getLogger().addFilter(_NoTraceFilter())


class _Callbacks(httpabc.HttpServiceCallbacks):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._syssvc = None

    async def initialise(self) -> httpabc.Resource:
        self._context.start()
        if self._context.is_trace():
            self._context.register(msglog.LoggerSubscriber(level=logging.DEBUG))
        tasks.task_fork(self._log_system_info(), 'log_system_info()')
        tasks.task_fork(steamutil.ensure_steamcmd(self._context.env('HOME')), 'ensure_steamcmd()')
        await self._create_tempdir()
        self._syssvc = system.SystemService(self._context)
        await self._syssvc.initialise()
        return self._syssvc.resources()

    async def shutdown(self):
        await funcutil.silently_cleanup(self._syssvc)
        await funcutil.silently_cleanup(self._context)
        tasks.dump()

    async def _create_tempdir(self):
        tempdir = self._context.config('tempdir')
        if tempdir.startswith(self._context.config('home')):
            await io.delete_any(tempdir)
        await io.create_directories(tempdir)

    async def _log_system_info(self):
        cpu_info, os_name, local_ip, public_ip = await asyncio.gather(
            sysutil.cpu_info(), sysutil.os_name(), sysutil.local_ip(), sysutil.public_ip())
        logging.info('CPU: %s | %s | %s', cpu_info['arch'], cpu_info['vendor'], cpu_info['modelname'])
        logging.info('OS Name: %s', os_name)
        logging.info('Local IPv4: %s', local_ip)
        logging.info('Public IPv4: %s', public_ip)
        if self._context.is_debug() or self._context.config('showtoken'):
            print('URL   : ' + contextext.RootUrl(self._context).build(local_ip), flush=True)
            print('TOKEN : ' + self._context.config('secret'), flush=True)


def main() -> int:
    if sys.version_info.major != 3 or sys.version_info.minor not in (10, 11, 12, 13):
        raise Exception('Unsupported python3 version, 3.10 or 3.11 or 3.12 required.')
    context = _create_context()
    if not context:
        return 0
    _setup_logging(context)
    try:
        logging.info('*** START ServerJockey ***')
        logging.info('Version: %s', sysutil.system_version())
        logging.info('Python3: %s', sys.version)
        logging.info('PID: %s', os.getpid())
        logging.info('Home: %s', context.config('home'))
        logging.info('Paths: %s', str(sys.path))
        httpsvc.HttpService(context, _Callbacks(context)).run()
        return 0
    except Exception as e:
        if context.is_debug():
            raise e
        logging.error('main() raised %s', repr(e))
        return 1
    finally:
        logging.info('*** END ServerJockey ***')
