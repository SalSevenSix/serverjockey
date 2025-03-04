import logging
import inspect
import time
import ssl
import json
import smtplib
import email.utils
from email.message import EmailMessage
# ALLOW lib.util, lib.comms
from . import util, cxt, comms


def _dump_to_log(data: dict | str | list | tuple) -> bool:
    data = util.repr_dict(data).strip() if isinstance(data, dict) else data
    data = data.split('\n') if isinstance(data, str) else data
    for line in data:
        logging.info(util.OUT + line)
    return True


class CommandProcessor:

    def __init__(self, context: cxt.Context, connection: comms.HttpConnection):
        self._url, self._token = context.credentials()
        self._instances: dict = connection.get('/instances')
        self._connection, self._commands, self._instance = connection, [], None
        for command in context.commands():
            argument, index = None, command.find(':')
            if index > 0:
                command, argument = command[:index], command[index + 1:]
            method_name = '_' + command.replace('-', '_')
            if hasattr(CommandProcessor, method_name):
                method = getattr(CommandProcessor, method_name)
                if callable(method):
                    entry = dict(name=command, method=method)
                    if len(inspect.signature(method).parameters.keys()) > 1:
                        entry['argument'] = argument
                    self._commands.append(entry)
            else:
                raise Exception(f'Command {command} not found')

    def process(self):
        counter = 0
        for command in self._commands:
            counter += 1
            name, method = command['name'], command['method']
            prefix = '{:02d}> '.format(counter) if counter < 100 else '--> '
            if 'argument' in command:
                argument: str = command['argument']
                logging.info(prefix + name + (':' + argument if argument else ''))
                result = method(self, argument)
            else:
                logging.info(prefix + name)
                result = method(self)
            if not result:
                return

    def _instance_path(self, command_path: str = '') -> str:
        if not self._instance:
            if not self._use(None):
                raise Exception('_instance_path() was unable to find instance to use.')
        return '/instances/' + self._instance + command_path

    # noinspection PyMethodMayBeStatic
    def _help(self) -> bool:
        printing = False
        for line in util.get_resource('help.text').split('\n'):
            if printing:
                logging.info(util.OUT + line[2:])
            else:
                printing = line == 'commands:'
        return True

    def _metrics(self) -> bool:
        return _dump_to_log(self._connection.get('/metrics'))

    def _mprof(self) -> bool:
        return _dump_to_log(self._connection.get('/mprof'))

    def _modules(self) -> bool:
        return _dump_to_log(self._connection.get('/modules'))

    def _instances(self) -> bool:
        identities = self._instances.keys()
        if len(identities) == 0:
            logging.info('No instances found.')
            return True
        for identity in identities:
            logging.info(util.OUT + identity + ' ' + self._instances[identity]['module'])
        return True

    def _use(self, argument: str | None) -> bool:
        if argument:
            if argument == self._instance:
                return True
            if argument == 'serverlink' or argument in self._instances.keys():
                self._instance = argument
                logging.info('Instance set to: ' + self._instance)
                return True
            logging.error('Instance %s does not exist. No more commands will be processed.', argument)
            return False
        if len(self._instances) > 0:
            self._instance = list(self._instances.keys())[0]
            logging.info('Instance defaulted to: ' + self._instance)
            return True
        logging.error('No instances found. No more commands will be processed.')
        return False

    def _create(self, argument: str | None) -> bool:
        instance, module = util.split_argument(argument, 2)
        if not instance or not module:
            logging.error('Instance name and module required. No more commands will be processed.')
            return False
        if instance in self._instances.keys():
            logging.error('Instance already exists. No more commands will be processed.')
            return False
        if module not in self._connection.get('/modules'):
            logging.error('Module not found. No more commands will be processed.')
            return False
        logging.info('Creating instance: ' + instance + ' (' + module + ')')
        self._connection.post('/instances', dict(module=module, identity=instance))
        self._instances[instance] = dict(module=module)
        self._use(instance)
        return True

    def _runtime_meta(self) -> bool:
        return _dump_to_log(self._connection.get(self._instance_path('/deployment/runtime-meta'), 'Runtime Not Found'))

    def _world_meta(self) -> bool:
        return _dump_to_log(self._connection.get(self._instance_path('/deployment/world-meta')))

    def _install_runtime(self, argument: str | None) -> bool:
        body = dict(wipe=False, validate=True)
        if argument:
            body['beta'] = argument
        result = self._connection.post(self._instance_path('/deployment/install-runtime'), body)
        if result:
            self._connection.drain(result)
        return True

    def _wipe_runtime(self) -> bool:
        self._connection.post(self._instance_path('/deployment/wipe-runtime'))
        return True

    def _wipe_world(self, argument: str | None) -> bool:
        if not argument:
            logging.error('wipe-world requires an argument e.g. wipe-world:all')
            return False
        self._connection.post(self._instance_path('/deployment/wipe-world-' + argument.lower()))
        return True

    def _wipe_world_all(self) -> bool:
        logging.warning('depricated: use wipe-world:all')
        return self._wipe_world('all')

    def _wipe_world_save(self) -> bool:
        logging.warning('depricated: use wipe-world:save')
        return self._wipe_world('save')

    def _delete(self) -> bool:
        if not self._instance:
            logging.error('Instance must be explicitly set to delete. No more commands will be processed.')
            return False
        self._connection.post(self._instance_path('/server/delete'))
        logging.info('Deleted instance: ' + self._instance)
        del self._instances[self._instance]
        self._instance = None
        return True

    def _exit_down(self) -> bool:
        status = self._connection.get(self._instance_path('/server'))
        if status['running']:
            return True
        logging.info('exit-down found the server down, no more commands will be processed')
        return False

    def _exit_up(self) -> bool:
        status = self._connection.get(self._instance_path('/server'))
        if not status['running']:
            return True
        logging.info('exit-up found the server up, no more commands will be processed')
        return False

    def _exit_ut_gt(self, argument: str) -> bool:
        status = self._connection.get(self._instance_path('/server'))
        uptime = status['uptime'] if 'uptime' in status else 0
        if int(uptime / 1000) > util.to_int(argument, 0):
            logging.info('exit-ut-gt found uptime over threshold, no more commands will be processed')
            return False
        return True

    def _exit_ut_lt(self, argument: str) -> bool:
        status = self._connection.get(self._instance_path('/server'))
        uptime = status['uptime'] if 'uptime' in status else 0
        if int(uptime / 1000) <= util.to_int(argument, 0):
            logging.info('exit-ut-lt found uptime under threshold, no more commands will be processed')
            return False
        return True

    def _exit_pl_gt(self, argument: str) -> bool:
        count = len(self._connection.get(self._instance_path('/players')))
        if count > util.to_int(argument, 0):
            logging.info('exit-pl-gt found players over threshold, no more commands will be processed')
            return False
        return True

    def _exit_pl_lt(self, argument: str) -> bool:
        count = len(self._connection.get(self._instance_path('/players')))
        if count <= util.to_int(argument, 0):
            logging.info('exit-pl-lt found players under threshold, no more commands will be processed')
            return False
        return True

    # noinspection PyMethodMayBeStatic
    def _sleep(self, argument: str) -> bool:
        seconds = util.to_int(argument, 0)
        if seconds > 0:
            time.sleep(seconds)
        else:
            logging.warning('Invalid argument for sleep command, must be a number > 0, was: %s', argument)
        return True

    # noinspection PyMethodMayBeStatic
    def _print(self, argument: str) -> bool:
        logging.info(util.OUT + argument if argument else '')
        return True

    def _welcome(self) -> bool:
        logging.info(util.OUT)
        logging.info(util.OUT)
        logging.info(util.OUT + ' ===========================================================')
        logging.info(util.OUT + ' =                    WELCOME TO ZOMBOX                    =')
        logging.info(util.OUT + ' ===========================================================')
        logging.info(util.OUT)
        logging.info(util.OUT + ' Open the webapp then login with the token.')
        logging.info(util.OUT)
        logging.info(util.OUT + ' Address   ' + self._url.replace('localhost', util.get_local_ip4()))
        logging.info(util.OUT + ' Token     ' + self._token)
        logging.info(util.OUT)
        logging.info(util.OUT + ' (hit ENTER key to show login prompt)')
        return True

    # https://blogs.oracle.com/cloud-infrastructure/post/step-by-step-instructions-to-send-email-with-oci-email-delivery
    def _emailtoken(self, argument: str | None) -> bool:
        with open(file=argument if argument else 'emailtoken.json', mode='r') as file:
            cfg = json.load(file)
        msg = EmailMessage()
        msg['Subject'] = cfg['subject']
        msg['From'] = email.utils.formataddr((cfg['sender']['name'], cfg['sender']['email']))
        msg['To'] = cfg['recipient']['email']
        msg.set_content(cfg['content'].format(
            url=self._url.replace('localhost', util.get_local_ip4()), token=self._token))
        server = smtplib.SMTP(cfg['smtp']['host'], cfg['smtp']['port'])
        try:
            server.ehlo()
            server.starttls(context=ssl.create_default_context(
                purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None))
            server.ehlo()
            server.login(cfg['smtp']['login'], cfg['smtp']['password'])
            server.sendmail(cfg['sender']['email'], cfg['recipient']['email'], msg.as_string())
        finally:
            server.close()
        return True

    def _showtoken(self) -> bool:
        logging.info(util.OUT + 'URL: ' + self._url.replace('localhost', util.get_local_ip4()))
        logging.info(util.OUT + 'Token: ' + self._token)
        return True

    def _server(self, argument: str | None) -> bool:
        if argument and argument != 'status':
            self._connection.post(self._instance_path('/server/' + argument))
            return True
        return _dump_to_log(self._connection.get(self._instance_path('/server')))

    def _auto(self, argument: str | None) -> bool:
        self._connection.post(self._instance_path(), dict(auto=util.to_int(argument, -1)))
        return True

    def _players(self) -> bool:
        result: list = self._connection.get(self._instance_path('/players'))
        for player in result:
            line = util.OUT
            line += str(player['startmillis']) if 'startmillis' in player else '0'
            line += ' '
            line += str(player['uptime']) if 'uptime' in player else '0'
            line += ' '
            steamid = player['steamid'] if 'steamid' in player else None
            if steamid:
                line += steamid
            else:
                line += 'NONE' if steamid is None else 'CONNECTED'
            line += ' ' + player['name']
            logging.info(line)
        return True

    def _system(self) -> bool:
        return _dump_to_log(self._connection.get('/system/info'))

    def _report(self) -> bool:
        identities = self._instances.keys()
        if len(identities) == 0:
            return True
        original = self._instance
        for identity in identities:
            self._instance = identity
            result = self._connection.get(self._instance_path('/server'))
            del result['instance']
            for line in util.repr_dict(result, identity).strip().split('\n'):
                logging.info(util.OUT + line)
        self._instance = original
        return True

    def _log_tail(self, argument: str | None) -> bool:
        lines = util.to_int(argument, 100)
        if lines <= 0:
            lines = 100
            logging.warning('Invalid argument for log-tail command, must be a number > 0')
        result = self._connection.get(self._instance_path('/log/tail'))
        result = result.strip().split('\n')
        if len(result) > 0 and lines < 100:
            result = result[-lines:]
        return _dump_to_log(result)

    def _log_tail_f(self) -> bool:
        self._log_tail('10')
        result = self._connection.post(self._instance_path('/log/subscribe'))
        self._connection.drain(result)
        return True

    def _console_help(self) -> bool:
        return _dump_to_log(self._connection.get(self._instance_path('/console/help')))

    def _console_send(self, argument: str) -> bool:
        result = self._connection.post(self._instance_path('/console/send'), dict(line=str(argument)))
        if not result:
            return True
        result = util.repr_dict(result) if isinstance(result, dict) else str(result)
        return _dump_to_log(result.strip())

    def _world_broadcast(self, argument: str) -> bool:
        self._connection.post(self._instance_path('/world/broadcast'), dict(message=str(argument)))
        return True

    def _backup_world(self, argument: str | None) -> bool:
        result = self._connection.post(
            self._instance_path('/deployment/backup-world'),
            dict(prunehours=util.to_int(argument, 0)))
        self._connection.drain(result)
        return True

    def _backup_runtime(self, argument: str | None) -> bool:
        result = self._connection.post(
            self._instance_path('/deployment/backup-runtime'),
            dict(prunehours=util.to_int(argument, 0)))
        self._connection.drain(result)
        return True

    def _https(self, argument: str | None) -> bool:
        argument = argument.lower() if argument else ''
        enabled = None
        if argument == 'true':
            enabled = True
        elif argument == 'false':
            enabled = False
        if enabled is None:
            logging.error('Invalid argument, use https:true or https:false')
            return False
        self._connection.post('/ssl', dict(enabled=enabled))
        return True

    def _shutdown(self) -> bool:
        self._connection.post('/system/shutdown')
        return False
