import logging
import time
import json
import inspect
from . import util, comms


def epilog() -> str:
    return '''
        COMMANDS: exit-if-down exit-if-up sleep:<duration> server server-daemon server-start server-restart server-stop
        console-send:"<cmd>" world-broadcast:"<message>" backup-world:<prunehours> backup-runtime:<prunehours> log-tail
    '''


def _get_prune_hours(argument: str) -> int:
    prune_hours = 0
    if argument:
        prune_hours = util.to_int(argument)
        if prune_hours is None:
            prune_hours = 0
            logging.warning('Invalid argument for prune hours, must be a number, was: ' + str(argument))
    return prune_hours


class CommandProcessor:

    def __init__(self, config: dict, connection: comms.HttpConnection):
        self._connection = connection
        self._commands = []
        for command in config['commands']:
            argument, index = None, command.find(':')
            if index > 0:
                command, argument = command[:index], command[index + 1:]
            method_name = '_' + command.replace('-', '_')
            if hasattr(CommandProcessor, method_name):
                method = getattr(CommandProcessor, method_name)
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
            method = command['method']
            logging.info(str(counter) + ' : ' + str(method))
            if 'argument' in command:
                result = method(self, command['argument'])
            else:
                result = method(self)
            if not result:
                return

    def _exit_if_down(self) -> bool:
        status = json.loads(self._connection.get(self._path + '/server'))
        if status['running']:
            return True
        logging.info('exit-if-down command found the server down, no more commands will be processed')
        return False

    def _exit_if_up(self) -> bool:
        status = json.loads(self._connection.get(self._path + '/server'))
        if not status['running']:
            return True
        logging.info('exit-if-up command found the server up, no more commands will be processed')
        return False

    # noinspection PyMethodMayBeStatic
    def _sleep(self, argument: str) -> bool:
        seconds = util.to_int(argument)
        if seconds:
            time.sleep(seconds)
        else:
            logging.warning('Invalid argument for sleep command, must be a number > 0, was: ' + str(argument))
        return True

    def _server(self) -> bool:
        logging.info(self._connection.get(self._path + '/server'))
        return True

    def _log_tail(self) -> bool:
        result = self._connection.get(self._path + '/log/tail')
        result = [o[2:] if o.startswith('/n') else o for o in result.split('\n')]
        logging.info('LOG TAIL\n' + '\n'.join(result))
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

    def _console_send(self, argument: str) -> bool:
        self._connection.post(self._path + '/console/send', json.dumps({'line': str(argument)}))
        return True

    def _world_broadcast(self, argument: str) -> bool:
        self._connection.post(self._path + '/world/broadcast', json.dumps({'message': str(argument)}))
        return True

    def _backup_world(self, argument: str) -> bool:
        result = self._connection.post(
            self._path + '/deployment/backup-world',
            json.dumps({'prunehours': _get_prune_hours(argument)}))
        self._connection.drain(json.loads(result))
        return True

    def _backup_runtime(self, argument: str) -> bool:
        result = self._connection.post(
            self._path + '/deployment/backup-runtime',
            json.dumps({'prunehours': _get_prune_hours(argument)}))
        self._connection.drain(json.loads(result))
        return True
