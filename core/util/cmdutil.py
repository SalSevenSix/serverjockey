from __future__ import annotations
import typing
from core.util import util


class CommandLine:

    def __init__(self, command: typing.Any = None, args: typing.Optional[dict] = None):
        self._args = args if args else {}
        self._command = []
        self.append(command)

    def append(self, command: typing.Any) -> CommandLine:
        if isinstance(command, (tuple, list)):
            self._command.extend(command)
        elif isinstance(command, dict):
            self._command.append(command)
        else:
            self._command.append(str(command))
        return self

    def build_list(self, args: typing.Optional[dict] = None) -> list:
        args = {**self._args, **args} if args else self._args
        cmdline = []
        for part in iter(self._command):
            if isinstance(part, (str, int, float)):
                part_str = str(part)
                if util.is_format(part_str):
                    cmdline.append(part_str.format(**args))
                else:
                    cmdline.append(part_str)
            elif isinstance(part, dict):
                for arg_key, arg_format in iter(part.items()):
                    arg_format = str(arg_format).replace('%s', '{}')
                    if util.is_format(arg_format):
                        value = util.get(arg_key, args)
                        if isinstance(value, list):
                            cmdline.append(arg_format.format(*value))
                        elif value:
                            cmdline.append(arg_format.format(value))
                    elif arg_key in args:
                        cmdline.append(arg_format)
        return cmdline

    def build_str(self, args: typing.Optional[dict] = None) -> str:
        return ' '.join(self.build_list(args))

    def build(self, args: typing.Optional[dict] = None) -> str:
        return self.build_str(args)


class CommandLines:

    def __init__(self, commands: dict, command_key: str = 'command'):
        self._commands = commands
        self._command_key = command_key

    def get(self, args: dict, command_key: typing.Optional[str] = None) -> CommandLine:
        if command_key is None:
            command_key = self._command_key
        command = util.get(util.get(command_key, args), self._commands)
        return None if not command else CommandLine(command, args)
