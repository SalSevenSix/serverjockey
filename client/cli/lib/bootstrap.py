import logging
import signal
import typing
import argparse
import sys
import os
import json
from . import util, cmd, comms


class _NoLogFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage().startswith(' ')


class _NoLogFormatter(logging.Formatter):
    def format(self, record):
        if record.msg and len(record.msg) > 4 and record.msg.startswith(' '):
            record.msg = record.msg[4:]
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


def _find_clientfile(clientfile: str | None) -> str:
    if clientfile:
        if not os.path.isfile(clientfile):
            raise Exception('Clientfile ' + clientfile + ' not found.')
        return clientfile
    home, filename = os.environ['HOME'], '/serverjockey-client.json'
    candidates = (home + filename, home + '/serverjockey' + filename, '/home/sjgms' + filename)
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    raise Exception('Unable to find Clientfile. ServerJockey may be down. Or try using --clientfile option.')


def _load_clientfile(clientfile: str) -> tuple:
    with open(file=clientfile, mode='r') as file:
        data = json.load(file)
        return data['SERVER_URL'], data['SERVER_TOKEN']


def _initialise(args: typing.Collection) -> dict:
    p = argparse.ArgumentParser(description='ServerJockey CLI.', epilog=cmd.epilog())
    p.add_argument('--debug', '-d', action='store_true', help='Debug mode')
    p.add_argument('--nolog', '-n', action='store_true', help='Suppress logging, only show output')
    p.add_argument('--clientfile', '-f', type=str, help='Client file')
    p.add_argument('--showtoken', '-t', action='store_true', help='Show webapp url and login token')
    p.add_argument('--commands', '-c', type=str, nargs='+', help='List of commands')
    args = [] if args is None or len(args) < 2 else args[1:]
    args = p.parse_args(args)
    _setup_logging(args.debug, args.nolog)
    url, token = _load_clientfile(_find_clientfile(args.clientfile))
    if args.showtoken:
        logging.info('    URL: ' + url.replace('localhost', util.get_ip()))
        logging.info('    Token: ' + token)
    return {'debug': args.debug, 'url': url, 'token': token, 'commands': args.commands}


def _terminate(sig, frame):
    logging.info('OK (Ctrl-C)')
    sys.exit(0)


def main() -> int:
    config, connection = None, None
    try:
        config = _initialise(sys.argv)
        if config['commands']:
            signal.signal(signal.SIGINT, _terminate)
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
