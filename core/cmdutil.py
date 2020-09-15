from core import util


class CommandLine:

    def __init__(self, command=None, args=None):
        self.args = args if args else {}
        self.command = []
        self.append_command(command)

    def append_command(self, command):
        if not command:
            pass
        elif isinstance(command, (tuple, list)):
            self.command.extend(command)
        elif isinstance(command, dict):
            self.command.append(command)
        else:
            self.command.append(str(command))
        return self

    def build(self, args=None, output=str):
        assert output in (str, list)
        args = {**self.args, **args} if args else self.args
        cmdline = []
        for part in iter(self.command):
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
        if output is list:
            return cmdline
        return ' '.join(cmdline)


class CommandLines:

    def __init__(self, commands, command_key='command'):
        assert isinstance(commands, dict)
        self.commands = commands
        self.command_key = command_key

    def get(self, args, command_key=None):
        if command_key is None:
            command_key = self.command_key
        command = util.get(util.get(command_key, args), self.commands)
        return None if not command else CommandLine(command, args)
