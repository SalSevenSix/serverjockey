import logging
import argparse
import sys
import typing
from core.util import util
from core.msg import msgext
from core.context import contextsvc
from core.http import httpabc, httpsvc
from core.system import system


def _create_context(args: typing.Collection) -> contextsvc.Context:
    p = argparse.ArgumentParser(description='Start serverjockey.')
    p.add_argument('home', type=str,
                   help='Home directory to use for server instances')
    p.add_argument('--debug', action='store_true',
                   help='Debug mode')
    p.add_argument('--host', type=str, default='localhost',
                   help='Host name to use, default is "localhost"')
    p.add_argument('--port', type=int, default=6164,
                   help='Port number to use, default is 6164')
    p.add_argument('--logfile', type=str,
                   help='Log file to use, relative to "home" unless starts with "/" or "."')
    p.add_argument('--clientfile', type=str,
                   help='Filename for client file, relative to instance dir unless starts with "/" or "."')
    args = [] if args is None or len(args) < 2 else args[1:]
    args = p.parse_args(args)
    return contextsvc.Context(
        secret=util.generate_token(),
        home=args.home, debug=args.debug,
        logfile=args.logfile, clientfile=args.clientfile,
        url=util.build_url(args.host, args.port),
        host=args.host, port=args.port)


def _setup_logging(context: contextsvc.Context):
    logfmt = '%(asctime)s %(levelname)05s %(message)s'
    datefmt = '%Y%m%d%H%M%S'
    level = logging.DEBUG if context.is_debug() else logging.INFO
    filename = context.config('logfile')
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

    async def initialise(self) -> httpabc.Resource:
        self._context.start()
        if self._context.is_debug():
            self._context.register(msgext.LoggerSubscriber(level=logging.DEBUG))
        self._context.post(self, 'Logging.File', self._context.config('logfile'))
        syssvc = system.SystemService(self._context)
        await syssvc.initialise()
        return syssvc.resources()

    async def shutdown(self):
        # shutting down the context here doesn't work
        # because the stupid aiohttp webserver cancels
        # all the tasks before calling this!
        pass


def main(args: typing.Optional[typing.Collection] = None) -> int:
    context = _create_context(args if args else sys.argv)
    _setup_logging(context)
    try:
        logging.info('*** START Serverjockey ***')
        logging.info('Secret {}'.format(context.config('secret')))
        httpsvc.HttpService(context, _Callbacks(context)).run()
        return 0
    except Exception as e:
        if context.is_debug():
            raise e
        logging.error('main() raised %s', repr(e))
        return 1
    finally:
        logging.info('*** END Serverjockey ***')
