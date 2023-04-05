import logging
import typing
import argparse
import sys
import os
from . import cmd, comms


def _initialise(args: typing.Collection) -> dict:
    p = argparse.ArgumentParser(description='ServerJockey CLI.', epilog=cmd.epilog())
    p.add_argument('--debug', '-d', action='store_true', help='Debug mode')
    p.add_argument('--logfile', '-l', type=str, help='Log file')
    p.add_argument('--clientfile', '-f', type=str, help='Client file')
    p.add_argument('--instance', '-s', type=str, help='Instance name')
    p.add_argument('--commands', '-c', type=str, nargs='+', help='List of commands')
    args = [] if args is None or len(args) < 2 else args[1:]
    args = p.parse_args(args)
    logfmt, datefmt = '%(asctime)s %(levelname)05s %(message)s', '%Y-%m-%d %H:%M:%S'
    level = logging.DEBUG if args.debug else logging.INFO
    if args.logfile:
        logging.basicConfig(level=level, format=logfmt, datefmt=datefmt, filename=args.logfile, filemode='w')
    else:
        logging.basicConfig(level=level, format=logfmt, datefmt=datefmt, stream=sys.stdout)
    if args.clientfile:
        clientfile = args.clientfile
        if not os.path.isfile(clientfile):
            raise Exception('Clientfile ' + clientfile + ' not found.')
    else:
        clientfile = os.environ['HOME'] + '/serverjockey-client.json'
        if not os.path.isfile(clientfile):
            clientfile = os.environ['HOME'] + '/serverjockey/serverjockey-client.json'
            if not os.path.isfile(clientfile):
                raise Exception(
                    'Unable to find Clientfile. ServerJockey may be down. Or try using --clientfile option.')
    commands = args.commands if args.commands else ['server']
    return {'debug': args.debug, 'clientfile': clientfile, 'instance': args.instance, 'commands': commands}


def main() -> int:
    config = _initialise(sys.argv)
    connection = None
    try:
        logging.info('Processing Commands: ' + repr(config['commands']))
        connection = comms.HttpConnection(config['clientfile'])
        cmd.CommandProcessor(config, connection).process()
        logging.info('Done')
        return 0
    except Exception as e:
        if config['debug']:
            raise e
        logging.error(repr(e))
        return 1
    finally:
        if connection:
            connection.close()
