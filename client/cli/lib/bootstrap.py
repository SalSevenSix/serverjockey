import logging
import signal
import typing
import argparse
import sys
import os
import json
# ALLOW lib.*
from . import tsk, cmd, comms, helptext

_OUT = '    '


class _NoLogFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage().startswith(_OUT)


class _NoLogFormatter(logging.Formatter):
    def format(self, record):
        if record.msg and record.msg.startswith(_OUT):
            record.msg = record.msg[len(_OUT):]
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


def _find_clientfile(user: str | None) -> str:
    candidate = user
    if candidate and candidate.find('.') > 0:  # user is a file name
        if not os.path.isfile(candidate):
            raise Exception('Clientfile ' + candidate + ' not found. ServerJockey may be down.')
        return candidate
    filename = '/serverjockey-client.json'
    if candidate:  # user is a username
        candidate = '/home/' + user + filename
        if not os.path.isfile(candidate):
            raise Exception('Clientfile for user ' + user + ' not found. ServerJockey may be down.')
        return candidate
    home = os.environ['HOME']
    candidates = (home + filename, home + '/serverjockey' + filename, '/home/sjgms' + filename)
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    raise Exception('Unable to find Clientfile. ServerJockey may be down. Or try using --user option.')


def _load_clientfile(clientfile: str) -> tuple:
    with open(file=clientfile, mode='r') as file:
        data = json.load(file)
        return data['SERVER_URL'], data['SERVER_TOKEN']


def _initialise(args: typing.Collection) -> dict:
    p = argparse.ArgumentParser(
        description='ServerJockey CLI.',
        epilog=helptext.epilog(),
        formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('--debug', '-d', action='store_true', help='Debug mode')
    p.add_argument('--nolog', '-n', action='store_true', help='Suppress logging, only show output')
    p.add_argument('--user', '-u', type=str, help='Specify user or client file')
    p.add_argument('--tasks', '-t', type=str, nargs='+', help='List of tasks to run')
    p.add_argument('--commands', '-c', type=str, nargs='+', help='List of commands to process')
    args = [] if args is None or len(args) < 2 else args[1:]
    args = p.parse_args(args)
    _setup_logging(args.debug, args.nolog)
    url, token = None, None
    if args.commands or not args.tasks:
        url, token = _load_clientfile(_find_clientfile(args.user))
    return {'out': _OUT, 'debug': args.debug, 'url': url, 'token': token,
            'tasks': args.tasks, 'commands': args.commands}


# noinspection PyUnusedLocal
def _terminate(sig, frame):
    logging.info('OK (Ctrl-C)')
    sys.exit(0)


def main() -> int:
    config, connection = None, None
    try:
        config = _initialise(sys.argv)
        tasks, commands = config['tasks'], config['commands']
        if tasks or commands:
            signal.signal(signal.SIGINT, _terminate)
        if tasks:
            tsk.TaskProcessor(config).process()
        if commands:
            connection = comms.HttpConnection(config)
            cmd.CommandProcessor(config, connection).process()
        logging.info('OK')
        return 0
    except Exception as e:
        if config and config['debug']:
            raise e
        logging.error(repr(e))
        return 1
    finally:
        if connection:
            connection.close()
