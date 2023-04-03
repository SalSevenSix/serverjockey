#!/usr/bin/env python3

import logging
import typing
import argparse
import sys
import os
import time
import json
import inspect
from http import client


class _HttpConnection:
    GET, POST = 'GET', 'POST'

    def __init__(self, clientfile: str):
        with open(file=clientfile, mode='r') as file:
            data = json.load(file)
        url, self._headers = data['SERVER_URL'], {'X-Secret': data['SERVER_TOKEN']}
        if url.startswith('https'):
            self._connection = client.HTTPSConnection(url[8:])
        else:
            self._connection = client.HTTPConnection(url[7:])

    def get(self, path: str) -> str | None:
        self._connection.request(_HttpConnection.GET, path, headers=self._headers)
        response = self._connection.getresponse()
        try:
            if response.status == 204:
                return None
            if response.status == 200:
                return '/n'.join([line.decode() for line in response.readlines()])
            raise Exception('HTTP GET Status: {} Reason: {}'.format(response.status, response.reason))
        finally:
            response.close()

    def post(self, path: str, body: str = None) -> str | None:
        headers = self._headers.copy()
        headers.update({'Content-Type': 'application/json'})
        self._connection.request(_HttpConnection.POST, path, headers=headers, body=body)
        response = self._connection.getresponse()
        try:
            if response.status == 204:
                return None
            if response.status == 200:
                return '/n'.join([line.decode() for line in response.readlines()])
            raise Exception('HTTP POST Status: {} Reason: {}'.format(response.status, response.reason))
        finally:
            response.close()

    def drain(self, url_dict: dict):
        url = url_dict['url'].split('/')[3:]
        path = '/' + '/'.join(url)
        while True:
            self._connection.request(_HttpConnection.GET, path, headers=self._headers)
            response = self._connection.getresponse()
            try:
                if response.status == 200:
                    for line in response.readlines():
                        logging.info(line.decode().strip())
                elif response.status == 404:
                    return
                elif response.status != 204:
                    raise Exception('HTTP POST Status: {} Reason: {}'.format(response.status, response.reason))
            finally:
                response.close()

    def close(self):
        self._connection.close()


class _CommandProcessor:

    def __init__(self, config: dict, connection: _HttpConnection):
        self._connection = connection
        self._commands = []
        for command in config['commands']:
            argument, index = None, command.find(':')
            if index > 0:
                command, argument = command[:index], command[index + 1:]
            method_name = '_' + command.replace('-', '_')
            if hasattr(_CommandProcessor, method_name):
                method = getattr(_CommandProcessor, method_name)
                if callable(method):
                    if len(inspect.signature(method).parameters.keys()) > 1:
                        self._commands.append({'method': method, 'argument': argument})
                    else:
                        self._commands.append({'method': method})
            else:
                raise Exception('Command {} not found'.format(command))
        instance, instances = config['instance'], json.loads(self._connection.get('/instances'))
        if instance and instance not in instances.keys():
            raise Exception('Instance {} does not exist'.format(instance))
        if not instance and len(instances) == 1:
            instance = list(instances.keys())[0]
        if not instance:
            raise Exception('Unable to identify instance to use. Please use the --instance option.')
        self._path = '/instances/' + instance

    def process(self):
        counter = 0
        for command in self._commands:
            counter += 1
            logging.info(str(counter) + ' : ' + str(command['method']))
            if 'argument' in command:
                result = command['method'](self, command['argument'])
            else:
                result = command['method'](self)
            if not result:
                return

    def _exit_if_down(self) -> bool:
        status = json.loads(self._connection.get(self._path + '/server'))
        if status['running']:
            return True
        logging.info('exit-if-down command found the server down, no more commands will be processed')
        return False

    def _sleep(self, argument: str) -> bool:
        try:
            time.sleep(int(argument))
        except (TypeError, ValueError):
            logging.warning('Invalid argument for sleep command, must be a number, was: ' + str(argument))
        return True

    def _server(self) -> bool:
        logging.info(self._connection.get(self._path + '/server'))
        return True

    def _server_daemon(self) -> bool:
        self._connection.post(self._path + '/server/daemon')
        return True

    def _server_start(self) -> bool:
        self._connection.post(self._path + '/server/start')
        return True

    def _server_restart(self) -> bool:
        self._connection.post(self._path + '/server/restart')
        return True

    def _server_stop(self) -> bool:
        self._connection.post(self._path + '/server/stop')
        return True

    def _world_broadcast(self, argument: str) -> bool:
        self._connection.post(self._path + '/world/broadcast', json.dumps({'message': str(argument)}))
        return True

    def _backup_world(self, argument: str) -> bool:
        prune_hours = 0
        if argument:
            try:
                prune_hours = int(argument)
            except (TypeError, ValueError):
                logging.warning('Invalid argument for prune hours, must be a number, was: ' + str(argument))
        result = self._connection.post(self._path + '/deployment/backup-world', json.dumps({'prunehours': prune_hours}))
        self._connection.drain(json.loads(result))
        return True


def _initialise(args: typing.Collection) -> dict:
    epilog = '''
        COMMANDS: exit-if-down sleep:<duration>
        server-daemon server-start server-restart server-stop
        world-broadcast:"<message>" backup-world:<prunehours>
    '''
    p = argparse.ArgumentParser(description='ServerJockey CLI.', epilog=epilog)
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
                raise Exception('Unable to find Clientfile. System may be down. Or try using --clientfile option.')
    commands = args.commands if args.commands else ['server']
    return {'debug': args.debug, 'clientfile': clientfile, 'instance': args.instance, 'commands': commands}


def main() -> int:
    config = _initialise(sys.argv)
    connection = None
    try:
        logging.info('Processing Commands: ' + repr(config['commands']))
        connection = _HttpConnection(config['clientfile'])
        _CommandProcessor(config, connection).process()
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


if __name__ == '__main__':
    sys.exit(main())
