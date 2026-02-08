import logging
import pathlib
import time
import os
import pwd
import inspect
import shutil
import subprocess
import zipfile
# ALLOW lib.util, lib.ddns
from . import util, cxt, ddns


def _checkroot(args: str):
    if not os.path.isfile('/usr/local/bin/serverjockey_cmd.pyz'):  # All root tasks are for service deployment
        raise Exception('Task not applicable when running from Source')
    script = util.get_resource('checkroot.sh').format(args=args)
    result = subprocess.run(script, shell=True, capture_output=True)
    _dump_to_log(result.stdout, result.stderr)
    if result.returncode != 0:
        raise Exception('Task not run')


def _extract_user_and_port(argument: str):
    user, port = util.split_argument(argument, 2)
    return user if user else util.DEFAULT_USER, int(port) if port else util.DEFAULT_PORT


def _dump_to_log(*data: str | bytes) -> bool:
    if data:
        for item in data:
            text = item.decode() if isinstance(item, bytes) else item
            if text:
                for line in text.strip().split('\n'):
                    logging.info(util.OUT + line)
    return True


class TaskProcessor:

    def __init__(self, context: cxt.Context):
        self._context, self._tasks = context, []
        for task in context.tasks():
            argument, index = None, task.find(':')
            if index > 0:
                task, argument = task[:index], task[index + 1:]
            method_name = '_' + task.replace('-', '_')
            if hasattr(TaskProcessor, method_name):
                method = getattr(TaskProcessor, method_name)
                if callable(method):
                    entry = dict(name=task, method=method)
                    if len(inspect.signature(method).parameters.keys()) > 1:
                        entry['argument'] = argument
                    self._tasks.append(entry)
            else:
                raise Exception(f'Task {task} not found')

    def process(self):
        for task in self._tasks:
            name, method = task['name'], task['method']
            if 'argument' in task:
                argument: str = task['argument']
                logging.info('--> ' + name + (':' + argument if argument else ''))
                result = method(self, argument)
            else:
                logging.info('--> ' + name)
                result = method(self)
            if not result:
                return

    # noinspection PyMethodMayBeStatic
    def _sysdsvc(self, argument: str) -> bool:
        assert argument
        resource = util.get_resource('serverjockey.service')
        return _dump_to_log(resource.format(user=argument))

    # noinspection PyMethodMayBeStatic
    def _pteroegg(self, argument: str) -> bool:
        assert argument
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()) + '+00:00'
        resource = util.get_resource('pteroegg.json')
        resource = resource.replace('{version}', argument).replace('{timestamp}', timestamp)
        return _dump_to_log(resource)

    # noinspection PyMethodMayBeStatic
    def _pufferpaneltemplate(self) -> bool:
        return _dump_to_log(util.get_resource('pufferpaneltemplate.json'))

    # noinspection PyMethodMayBeStatic
    def _ddwrapper(self, argument) -> bool:
        ddexe, outfile = util.split_argument(argument, 2)
        assert ddexe
        # see https://github.com/SteamRE/DepotDownloader
        resource = util.get_resource('ddwrapper.sh').replace('{ddexe}', ddexe)
        if not outfile:
            return _dump_to_log(resource)
        with open(outfile, 'w') as f:
            f.write(resource)
        return True

    # noinspection PyMethodMayBeStatic
    def _upgrade(self) -> bool:
        _checkroot('upgrade')
        script = util.get_resource('upgrade.sh')
        result = subprocess.run(script, shell=True, capture_output=True)
        _dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Upgrade task failed')
        return True

    # noinspection PyMethodMayBeStatic
    def _uninstall(self) -> bool:
        _checkroot('uninstall')
        script = util.get_resource('uninstall.sh').replace('{userdef}', util.DEFAULT_USER)
        result = subprocess.run(script, shell=True, capture_output=True)
        if result.returncode != 0:
            _dump_to_log(result.stdout, result.stderr)
            raise Exception('Uninstall task failed')
        return False

    # noinspection PyMethodMayBeStatic
    def _adduser(self, argument: str) -> bool:
        _checkroot('adduser:<name>,<port>')
        user, port = _extract_user_and_port(argument)
        if user == util.DEFAULT_SERVICE:
            raise Exception('User name not allowed')
        script = util.get_resource('adduser.sh')
        script = script.replace('{userdef}', util.DEFAULT_USER).replace('{user}', user)
        script = script.replace('{portdef}', str(util.DEFAULT_PORT)).replace('{port}', str(port))
        result = subprocess.run(script, shell=True, capture_output=True)
        _dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('New user task failed')
        return True

    # noinspection PyMethodMayBeStatic
    def _userdel(self, argument: str) -> bool:
        _checkroot('userdel:<name>')
        user = _extract_user_and_port(argument)[0]
        if user == util.DEFAULT_USER:
            raise Exception('Cannot delete default user. Use uninstall task instead.')
        script = util.get_resource('userdel.sh').replace('{user}', user)
        result = subprocess.run(script, shell=True, capture_output=True)
        _dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Delete user task failed')
        return True

    def _export(self, argument: str) -> bool:
        if not argument:
            raise Exception('<zipfile> required')
        _checkroot('export:<zipfile>')
        user, file = self._context.user(), argument if argument.endswith('.zip') else argument + '.zip'
        if os.path.isfile(file) or os.path.isdir(file):
            raise Exception(f'Zipfile elready exists: {file}')
        logging.info(f'Exporting ServerJockey service user {user} to {file}')
        home, svcname = pathlib.Path('/home/' + user), util.DEFAULT_SERVICE if user == util.DEFAULT_USER else user
        if not home.is_dir():
            raise Exception(f'ServerJockey home not found: {home}')
        logging.info(f'Stopping ServerJockey service name {svcname}')
        subprocess.run(util.get_resource('systemctl.sh').format(args=f'stop {svcname}'), shell=True)
        with zipfile.ZipFile(file, 'w', zipfile.ZIP_DEFLATED) as f:
            for abspath in home.rglob('*'):
                relpath = str(abspath.relative_to(home))
                dozip = not relpath.startswith('.') and (relpath.find('/') > -1 or not relpath.endswith('.log'))
                dozip = dozip and not abspath.is_dir() and not abspath.is_symlink()
                if dozip:
                    logging.info(f'DEFLATE {abspath}')
                    f.write(abspath, relpath)
        suser = os.getenv('SUDO_USER')
        if suser:
            pwnam = pwd.getpwnam(suser)
            os.chown(file, pwnam.pw_uid, pwnam.pw_gid)
        return True

    def _import(self, argument: str) -> bool:
        if not argument:
            raise Exception('<zipfile> required')
        _checkroot('import:<zipfile>')
        user, file = self._context.user(), argument if argument.endswith('.zip') else argument + '.zip'
        if not os.path.isfile(file):
            raise Exception(f'Zipfile not found: {file}')
        home, pwnam = '/home/' + user, pwd.getpwnam(user)
        if not os.path.isdir(home):
            raise Exception(f'ServerJockey home not found: {home}')
        svcname = util.DEFAULT_SERVICE if user == util.DEFAULT_USER else user
        logging.info(f'Stopping ServerJockey service name {svcname}')
        subprocess.run(util.get_resource('systemctl.sh').format(args=f'stop {svcname}'), shell=True)
        with zipfile.ZipFile(file, 'r') as f:
            alldirs, rootdirs, uid, gid = [home], [home], pwnam.pw_uid, pwnam.pw_gid
            for member in f.infolist():
                relpath, pos = member.filename, member.filename.find('/')
                if pos == -1:  # root file
                    abspath = home + '/' + relpath
                    if os.path.isfile(abspath):
                        logging.info(f'RMFILE  {abspath}')
                        os.remove(abspath)
                elif relpath.count('/') == 1:  # root directory
                    abspath = home + '/' + relpath[:pos]
                    if abspath not in rootdirs:
                        rootdirs.append(abspath)
                        if os.path.isdir(abspath):
                            logging.info(f'RMDIR   {abspath}')
                            shutil.rmtree(abspath)
                abspath = f.extract(member, home)
                logging.info(f'UNPACK  {abspath}')
                dirpath = os.path.dirname(abspath)
                if dirpath not in alldirs:
                    alldirs.append(dirpath)
                    logging.info(f'CHODIR  {dirpath}')
                    os.chown(dirpath, uid, gid)
                os.chown(abspath, uid, gid)
        return True

    def _service(self, argument: str) -> bool:
        _checkroot('service:<command>')
        user = self._context.user()
        args = argument if argument else 'status'
        args += ' '
        args += util.DEFAULT_SERVICE if user == util.DEFAULT_USER else user
        script = util.get_resource('systemctl.sh').format(args=args)
        result = subprocess.run(script, shell=True, capture_output=True)
        _dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Service ' + argument + ' task failed')
        return True

    def _wait(self, argument: str) -> bool:
        retries = util.to_int(argument, 0)
        if retries <= 0:
            return True
        while True:
            try:
                assert self._context.find_clientfile()  # just try find it first
                time.sleep(1.0)  # grace period
                assert self._context.credentials()  # now load to pre cache
                return True
            except Exception as e:
                if retries <= 0:
                    raise e
            retries -= 1
            time.sleep(1.0)

    # noinspection PyMethodMayBeStatic
    def _ddns(self, argument: str) -> bool:
        if not argument:
            return _dump_to_log(util.get_resource('ddnshelp.text'))
        provider, = util.split_argument(argument, 1)
        if provider == 'duck':
            ddns.update_duck(*util.split_argument(argument, 3))
        elif provider == 'pork':
            ddns.update_pork(*util.split_argument(argument, 5))
        else:
            raise Exception('Unknown DDNS Service Provider')
        return True
