import logging
import sys
import argparse
import signal

# ALLOW lib.*
from . import util, cxt, comms, tsk, cmd


class _NoLogFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage().startswith(util.OUT)


class _NoLogFormatter(logging.Formatter):
    def format(self, record):
        if record.msg and record.msg.startswith(util.OUT):
            record.msg = record.msg[len(util.OUT):]
        return super(_NoLogFormatter, self).format(record)


def _setup_logging(debug: bool, nolog: bool):
    handler = logging.StreamHandler(sys.stdout)
    if nolog:
        handler.setFormatter(_NoLogFormatter())
    else:
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)05s %(message)s', '%Y-%m-%d %H:%M:%S'))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(handler)
    if nolog:
        logger.addFilter(_NoLogFilter())


def _initialise() -> cxt.Context:
    p = argparse.ArgumentParser(
        description='ServerJockey CLI.',
        epilog=util.get_resource('help.text'),
        formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('--debug', '-d', action='store_true', help='Debug mode')
    p.add_argument('--nolog', '-n', action='store_true', help='Suppress logging, only show output')
    p.add_argument('--user', '-u', type=str, help='Specify alternate user')
    p.add_argument('--tasks', '-t', type=str, nargs='+', help='List of tasks to run')
    p.add_argument('--commands', '-c', type=str, nargs='+', help='List of commands to process')
    args = p.parse_args(sys.argv[1:])
    _setup_logging(args.debug, args.nolog)
    return cxt.Context(args.debug, args.user, args.tasks, args.commands)


# noinspection PyUnusedLocal
def _terminate(sig, frame):
    logging.info('OK (Ctrl-C)')
    sys.exit(0)


def main() -> int:
    context, connection = None, None
    try:
        context = _initialise()
        if context.has_tasks() or context.has_commands():
            signal.signal(signal.SIGINT, _terminate)
        else:
            assert context.credentials()  # just check service is started
        if context.has_tasks():
            tsk.TaskProcessor(context).process()
        if context.has_commands():
            connection = comms.HttpConnection(context)
            cmd.CommandProcessor(context, connection).process()
        logging.info('OK')
        return 0
    except Exception as e:
        if not context or context.is_debug():
            raise e
        logging.error(repr(e))
        return 1
    finally:
        if connection:
            connection.close()
