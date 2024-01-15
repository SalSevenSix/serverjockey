import logging
import typing
import argparse
import asyncio
import sys
import os
# ALLOW util.* msg.* context.* http.* system.svrabc system.system
from core.util import util, idutil, funcutil, sysutil, steamutil, logutil, io, tasks
from core.msg import msglog
from core.context import contextsvc, contextext
from core.http import httpabc, httpsvc
from core.system import system


class _NoTraceFilter(logging.Filter):
    PREFIXES = 'tsk>', 'trs>', 'msg>', 'shl>'

    def filter(self, record):
        message = record.getMessage()
        trace = len(message) > 4 and message[:4] in _NoTraceFilter.PREFIXES
        return not trace


def _stime(home: str) -> float | None:
    pidfile = home + '/.pid'
    return os.stat(pidfile).st_atime if os.path.isfile(pidfile) else None


def _ssl_config(home: str) -> tuple:
    sslcert, sslkey = home + '/serverjockey.crt', home + '/serverjockey.key'
    if os.path.isfile(sslcert) and os.path.isfile(sslkey):
        return 'https', sslcert, sslkey
    return 'http', None, None


def _create_context(args: typing.Collection) -> contextsvc.Context | None:
    p = argparse.ArgumentParser(description='Start ServerJockey game server management system.')
    p.add_argument('--version', action='store_true',
                   help='Show version then exit')
    p.add_argument('--debug', action='store_true',
                   help='Debug mode')
    p.add_argument('--trace', action='store_true',
                   help='Debug mode with detailed logging')
    p.add_argument('--showtoken', action='store_true',
                   help='Print the login token to stdout')
    p.add_argument('--host', type=str,
                   help='Host or IP to bind http service, default is open to all')
    p.add_argument('--port', type=int, default=6164,
                   help='Port for http service, default is 6164')
    p.add_argument('--home', type=str, default='.',
                   help='Home directory to use for server instances, default is current working directory')
    p.add_argument('--tempdir', type=str, default='.tmp',
                   help='Directory to use for temporary files, default is .tmp under home')
    p.add_argument('--clientfile', type=str, default='serverjockey-client.json',
                   help='Filename for client file, relative to "home" unless starts with "/" or "."')
    p.add_argument('--dbfile', type=str, nargs='?', const='serverjockey.db',
                   help='Filename for database file, relative to "home" unless starts with "/" or "."')
    p.add_argument('--logfile', type=str, nargs='?', const='serverjockey.log',
                   help='Optional Log file to use, relative to "home" unless starts with "/" or "."')
    p.add_argument('--noupnp', action='store_true',
                   help='Do not enable UPnP services')
    config = p.parse_args([] if args is None or len(args) < 2 else args[1:])
    if config.version:
        print(sysutil.system_version())
        return None
    home = util.full_path(os.getcwd(), config.home)
    tempdir = util.full_path(home, config.tempdir)
    clientfile = util.full_path(home, config.clientfile)
    dbfile = util.full_path(home, config.dbfile)
    logfile = util.full_path(home, config.logfile)
    scheme, sslcert, sslkey = _ssl_config(home)
    return contextsvc.Context(
        debug=config.debug, trace=config.trace, home=home, tempdir=tempdir,
        stime=_stime(home), secret=idutil.generate_token(10, True), showtoken=config.showtoken,
        scheme=scheme, sslcert=sslcert, sslkey=sslkey, env=os.environ.copy(), python=sys.executable,
        clientfile=clientfile, dbfile=dbfile, logfile=logfile, noupnp=config.noupnp,
        host=None if config.host == '0.0.0.0' else config.host, port=config.port)


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

    async def _log_system_info(self):
        os_name, local_ip, public_ip = await asyncio.gather(sysutil.os_name(), sysutil.local_ip(), sysutil.public_ip())
        logging.info('OS Name: ' + os_name)
        logging.info('Local IPv4: ' + local_ip)
        logging.info('Public IPv4: ' + public_ip)
        if self._context.is_debug() or self._context.config('showtoken'):
            print('URL   : ' + contextext.RootUrl(self._context).build(local_ip))
            print('TOKEN : ' + self._context.config('secret'))

    async def initialise(self) -> httpabc.Resource:
        self._context.start()
        if self._context.is_trace():
            self._context.register(msglog.LoggerSubscriber(level=logging.DEBUG))
        tasks.task_fork(self._log_system_info(), 'log_system_info()')
        await io.create_directories(self._context.config('tempdir'))
        self._syssvc = system.SystemService(self._context)
        await self._syssvc.initialise()
        await steamutil.check_steam(self._context.env('HOME'))
        return self._syssvc.resources()

    async def shutdown(self):
        await funcutil.silently_cleanup(self._syssvc)
        await funcutil.silently_cleanup(self._context)
        tasks.dump()


def main(args: typing.Optional[typing.Collection] = None) -> int:
    context = _create_context(args if args else sys.argv)
    if not context:
        return 0
    _setup_logging(context)
    try:
        logging.info('*** START ServerJockey ***')
        logging.info('Version: ' + sysutil.system_version())
        logging.info('Python3: ' + sys.version)
        logging.info('Paths: ' + str(sys.path))
        httpsvc.HttpService(context, _Callbacks(context)).run()
        return 0
    except Exception as e:
        if context.is_debug():
            raise e
        logging.error('main() raised %s', repr(e))
        return 1
    finally:
        logging.info('*** END ServerJockey ***')
