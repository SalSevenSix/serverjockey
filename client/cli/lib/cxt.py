import sys
import os
import json
# ALLOW lib.*
from . import util


def _load_clientfile(clientfile: str) -> tuple:
    with open(file=clientfile, mode='r') as file:
        data = json.load(file)
        return data['SERVER_URL'], data['SERVER_TOKEN']


class Context:

    def __init__(self, debug, user, tasks, commands):
        self._debug = True if debug else False
        self._user = user if user else None
        self._tasks = tuple(tasks) if tasks else ()
        self._commands = tuple(commands) if commands else ()
        self._credentials = None

    def is_debug(self) -> bool:
        return self._debug

    def user(self):
        return self._user if self._user else util.DEFAULT_USER

    def has_tasks(self) -> bool:
        return len(self._tasks) > 0

    def tasks(self) -> tuple:
        return self._tasks

    def has_commands(self) -> bool:
        return len(self._commands) > 0

    def commands(self) -> tuple:
        return self._commands

    def credentials(self) -> tuple:
        if not self._credentials:
            self._credentials = _load_clientfile(self.find_clientfile())
        return self._credentials

    def find_clientfile(self) -> str:
        candidate, filename = self._user, '/serverjockey-client.json'
        if candidate and candidate.endswith(filename[1:]):  # candidate is a client file
            if os.path.isfile(candidate):
                return candidate
            raise Exception('Clientfile ' + candidate + ' not found. ServerJockey may be down.')
        if candidate:  # candidate is a username
            candidate = '/home/' + self._user + filename
            if os.path.isfile(candidate):
                return candidate
            raise Exception('Clientfile for user ' + self._user + ' not found. ServerJockey may be down.')
        home = os.environ['HOME']
        candidates = [home + filename, home + '/serverjockey' + filename, '/home/sjgms' + filename]
        if len(sys.path) > 0 and not sys.path[0].endswith('/serverjockey_cmd.pyz'):  # running from source
            home = os.getcwd() + '/../..'
            candidates.extend([home + filename, home + '/..' + filename])
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
        raise Exception('Unable to find Clientfile. ServerJockey may be down. Or try using --user option.')
