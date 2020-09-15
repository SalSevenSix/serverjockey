import logging
import argparse
import sys
from core import contextsvc, httpsvc, svrsvc, msgext


def configure_logging(context):
    log_level = logging.DEBUG if context.is_debug() else logging.INFO
    log_formatter = logging.Formatter('%(asctime)s %(levelname)05s %(message)s', '%Y%m%d%H%M%S')
    logging.basicConfig(
        level=log_level,
        filename=context.get_logfile(), filemode='w',
        format=log_formatter._fmt, datefmt=log_formatter.datefmt)
    if context.is_debug():
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(log_formatter)
        logging.getLogger().addHandler(stdout_handler)
        context.register(msgext.LoggerSubscriber(level=logging.DEBUG))


class ContextFactory:

    def __init__(self):
        p = argparse.ArgumentParser(description='Start serverjockey.')
        p.add_argument('module', type=str,
                       help='Module to dynamically load for server handling')
        p.add_argument('home', type=str,
                       help='Home directory of the server deployment')
        p.add_argument('executable', type=str,
                       help='Server executable to launch server, relative to "home" unless starts with "/" or "."')
        p.add_argument('--logfile', type=str, default='./serverjockey.log',
                       help='Log file to use, relative to "home" unless starts with "/" or "."')
        p.add_argument('--clientfile', type=str, default=None,
                       help='File to write config for clients, relative to "home" unless starts with "/" or "."')
        p.add_argument('--debug', action='store_true',
                       help='Debug mode')
        p.add_argument('--host', type=str, default='localhost',
                       help='Restrictive host name for HTTP service, default is localhost')
        p.add_argument('--port', type=int, default=80,
                       help='Port for HTTP service, default is 80')
        self.parser = p

    def create(self, args):
        args = [] if args is None or len(args) < 2 else args[1:]
        args = self.parser.parse_args(args)
        context = contextsvc.Context(
            args.module,
            args.home,
            args.executable,
            logfile=args.logfile,
            clientfile=args.clientfile,
            debug=args.debug,
            host=args.host,
            port=args.port)
        return context


async def main(args):
    httpsvr, context = None, None
    try:
        context = ContextFactory().create(args)
        configure_logging(context)
        logging.info('*** START Serverjockey ***')
        server = context.create_server()
        httpsvr = await httpsvc.HttpService(context, server.resources()).start()
        return await svrsvc.ServerService(context, server).run()
    except Exception as e:
        if context and context.is_debug():
            raise e
        logging.error('main() raised %s', repr(e))
        return 9
    finally:
        if context:
            await context.shutdown()
        if httpsvr:
            await httpsvr.stop()
        logging.info('*** END Serverjockey ***')
