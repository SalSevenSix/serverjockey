import logging
import typing
import argparse
import sys
import os
import json
from . import util, cmd, comms


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


def _setup_logging(debug: bool, logfile: str | None):
    logfmt, datefmt = '%(asctime)s %(levelname)05s %(message)s', '%Y-%m-%d %H:%M:%S'
    level = logging.DEBUG if debug else logging.INFO
    if logfile:
        logging.basicConfig(level=level, format=logfmt, datefmt=datefmt, filename=logfile, filemode='w')
    else:
        logging.basicConfig(level=level, format=logfmt, datefmt=datefmt, stream=sys.stdout)


def _initialise(args: typing.Collection) -> dict:
    p = argparse.ArgumentParser(description='ServerJockey CLI.', epilog=cmd.epilog())
    p.add_argument('--debug', '-d', action='store_true', help='Debug mode')
    p.add_argument('--logfile', '-l', type=str, help='Log file')
    p.add_argument('--clientfile', '-f', type=str, help='Client file')
    p.add_argument('--showtoken', '-t', action='store_true', help='Show webapp url and login token')
    p.add_argument('--commands', '-c', type=str, nargs='+', help='List of commands')
    args = [] if args is None or len(args) < 2 else args[1:]
    args = p.parse_args(args)
    _setup_logging(args.debug, args.logfile)
    url, token = _load_clientfile(_find_clientfile(args.clientfile))
    if args.showtoken:
        logging.info('Webapp URL  : ' + url.replace('localhost', util.get_ip()))
        logging.info('Login Token : ' + token)
    return {'debug': args.debug, 'url': url, 'token': token, 'commands': args.commands}


def main() -> int:
    config, connection = None, None
    try:
        config = _initialise(sys.argv)
        if config['commands']:
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
