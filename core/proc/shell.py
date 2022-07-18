from __future__ import annotations
import typing
from core.util import util


class Script:

    def __init__(self):
        self._script: typing.Dict[str, typing.Union[str, typing.Collection[str]]] = {}

    def build(self) -> str:
        text = []
        for name, lines in iter(self._script.items()):
            text.append('# ' + name)
            if isinstance(lines, (tuple, list)):
                text.extend(lines)
            else:
                text.append(lines)
        return '\n'.join(text)

    def include(self, name: str, lines: typing.Union[str, typing.Collection[str]]) -> Script:
        if name not in self._script:
            self._script.update({name: lines})
        return self

    def include_find_steamcmd(self) -> Script:
        return self.include('include_find_steamcmd', (
            'find_steamcmd() {',
            '  /usr/games/steamcmd +quit >/dev/null 2>&1 && echo /usr/games/steamcmd && return 0',
            '  ~/Steam/steamcmd.sh +quit >/dev/null 2>&1 && echo ~/Steam/steamcmd.sh && return 0',
            '  echo steamcmd && return 1',
            '}'))

    def include_steamcmd_app_update(self, **kwargs: typing.Union[str, int, float]) -> Script:
        self.include_find_steamcmd()
        line = ['$(find_steamcmd)',
                '+force_install_dir {install_dir}',
                '+login anonymous',
                '+app_update {app_id}']
        if util.get('beta', kwargs):
            line.append('-beta {beta}')
        if util.get('validate', kwargs):
            line.append('validate')
        line.append('+quit')
        return self.include('include_steamcmd_app_update', ' '.join(line).format(**kwargs))

    def include_softlink_steamclient_lib(self, directory: str) -> Script:
        return self.include('include_softlink_steamclient_lib', (
            'SRC_FILE=' + directory + '/steamclient.so',
            'TRG_FILE=$SRC_FILE',
            '[ -f $SRC_FILE ] || SRC_FILE=~/.steam/steamcmd/linux64/steamclient.so',
            '[ -f $SRC_FILE ] || SRC_FILE=~/Steam/linux64/steamclient.so',
            '[ -f $TRG_FILE ] || ln -s $SRC_FILE $TRG_FILE'))
