import logging
import signal
import argparse
import sys
import os
import json
# ALLOW lib.*
from . import util, tsk, cmd, comms

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
    if candidate and candidate.find('.') > -1:  # "user" is a file name
        if os.path.isfile(candidate):
            return candidate
        raise Exception('Clientfile ' + candidate + ' not found. ServerJockey may be down.')
    filename = '/serverjockey-client.json'
    if candidate:  # user is a username
        candidate = '/home/' + user + filename
        if os.path.isfile(candidate):
            return candidate
        raise Exception('Clientfile for user ' + user + ' not found. ServerJockey may be down.')
    home = os.environ['HOME']
    candidates = [home + filename, home + '/serverjockey' + filename, '/home/sjgms' + filename]
    if len(sys.path) > 0 and not sys.path[0].endswith('/serverjockey_cmd.pyz'):  # Running from Source
        home = os.getcwd() + '/../..'
        candidates.extend([home + filename, home + '/..' + filename])
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    raise Exception('Unable to find Clientfile. ServerJockey may be down. Or try using --user option.')


def _load_clientfile(clientfile: str) -> tuple:
    with open(file=clientfile, mode='r') as file:
        data = json.load(file)
        return data['SERVER_URL'], data['SERVER_TOKEN']


def _initialise() -> dict:
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
    url, token = None, None
    if args.commands or not args.tasks:
        url, token = _load_clientfile(_find_clientfile(args.user))
    return dict(out=_OUT, url=url, token=token,
                debug=args.debug, user=args.user,
                tasks=args.tasks, commands=args.commands)


# noinspection PyUnusedLocal
def _terminate(sig, frame):
    logging.info('OK (Ctrl-C)')
    sys.exit(0)


def main() -> int:
    config, connection = None, None
    try:
        config = _initialise()
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
        logging.error(str(e))
        return 1
    finally:
        if connection:
            connection.close()
