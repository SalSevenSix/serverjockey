import logging
import argparse
import sys
import os
import typing
import secrets
from core.util import util, funcutil
from core.msg import msgext
from core.context import contextsvc
from core.http import httpabc, httpsvc
from core.system import system


def _get_token() -> str:
    token = secrets.token_hex(5)
    path = '/tmp/serverjockey.token'
    if not os.path.exists(path):
        return token
    with open(path) as file:
        token = file.readline().strip()
    return token


def _create_context(args: typing.Collection) -> contextsvc.Context:
    p = argparse.ArgumentParser(description='Start serverjockey.')
    p.add_argument('--debug', action='store_true',
                   help='Debug mode')
    p.add_argument('--host', type=str,
                   help='Host or IP to bind http service, default is open to all')
    p.add_argument('--port', type=int, default=6164,
                   help='Port for http service, default is 6164')
    p.add_argument('--home', type=str, default='.',
                   help='Home directory to use for server instances, default is current working directory')
    p.add_argument('--clientfile', type=str, default='serverjockey-client.json',
                   help='Filename for client file, relative to "home" unless starts with "/" or "."')
    p.add_argument('--logfile', type=str,
                   help='Log file to use, relative to "home" unless starts with "/" or "."')
    args = [] if args is None or len(args) < 2 else args[1:]
    args = p.parse_args(args)
    return contextsvc.Context(
        debug=args.debug, secret=_get_token(),
        home=os.getcwd() if args.home == '.' else args.home,
        logfile=args.logfile, clientfile=args.clientfile,
        host=None if args.host == '0.0.0.0' else args.host, port=args.port)


def _setup_logging(context: contextsvc.Context):
    logfmt, datefmt = '%(asctime)s %(levelname)05s %(message)s', '%Y%m%d%H%M%S'
    level = logging.DEBUG if context.is_debug() else logging.INFO
    filename = util.overridable_full_path(context.config('home'), context.config('logfile'))
    if filename:
        logging.basicConfig(level=level, format=logfmt, datefmt=datefmt, filename=filename, filemode='w')
        if context.is_debug():
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(logging.Formatter(logfmt, datefmt))
            logging.getLogger().addHandler(stdout_handler)
    else:
        logging.basicConfig(level=level, format=logfmt, datefmt=datefmt, stream=sys.stdout)


class _Callbacks(httpabc.HttpServiceCallbacks):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._syssvc = None

    async def initialise(self) -> httpabc.Resource:
        self._context.start()
        if self._context.is_debug():
            self._context.register(msgext.LoggerSubscriber(level=logging.DEBUG))
        self._context.post(self, 'Logging.File', self._context.config('logfile'))
        self._syssvc = system.SystemService(self._context)
        await self._syssvc.initialise()
        return self._syssvc.resources()

    async def shutdown(self):
        await funcutil.silently_cleanup(self._syssvc)
        await funcutil.silently_cleanup(self._context)


def main(args: typing.Optional[typing.Collection] = None) -> int:
    context = _create_context(args if args else sys.argv)
    _setup_logging(context)
    try:
        logging.info('*** START Serverjockey ***')
        httpsvc.HttpService(context, _Callbacks(context)).run()
        return 0
    except Exception as e:
        if context.is_debug():
            raise e
        logging.error('main() raised %s', repr(e))
        return 1
    finally:
        logging.info('*** END Serverjockey ***')
