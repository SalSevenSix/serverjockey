import logging
import argparse
import sys
from core import contextsvc, httpsvc, msgext, system, util

LOG_FORMAT = '%(asctime)s %(levelname)05s %(message)s'
DATE_FORMAT = '%Y%m%d%H%M%S'


def create_context(args):
    p = argparse.ArgumentParser(description='Start serverjockey.')
    p.add_argument('home', type=str,
                   help='Home directory to use for server instances')
    p.add_argument('--debug', action='store_true',
                   help='Debug mode')
    p.add_argument('--host', type=str, default='localhost',
                   help='Host name to use, default is "localhost"')
    p.add_argument('--port', type=int, default=80,
                   help='Port number to use, default is 80')
    p.add_argument('--logfile', type=str, default='./serverjockey.log',
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


class Callbacks:

    def __init__(self, context):
        self.context = context

    async def initialise(self):
        if self.context.is_debug():
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            logging.getLogger().addHandler(stdout_handler)
        self.context.start()
        if self.context.is_debug():
            self.context.register(msgext.LoggerSubscriber(level=logging.DEBUG))
        self.context.post(self, 'Logging.File', self.context.config('logfile'))
        syssvc = system.SystemService(self.context)
        await syssvc.initialise()
        return syssvc.resources()

    async def shutdown(self):
        # shutting down the context here doesn't work
        # because the stupid aiohttp webserver cancels
        # all the tasks before calling this!
        pass


def main(args=None):
    context = create_context(args if args else sys.argv)
    logging.basicConfig(
        level=logging.DEBUG if context.is_debug() else logging.INFO,
        filename=context.config('logfile'), filemode='w',
        format=LOG_FORMAT, datefmt=DATE_FORMAT)
    try:
        logging.info('*** START Serverjockey ***')
        httpsvc.HttpService(context, Callbacks(context)).run()
        return 0
    except Exception as e:
        if context.is_debug():
            raise e
        logging.error('main() raised %s', repr(e))
        return 1
    finally:
        logging.info('*** END Serverjockey ***')
