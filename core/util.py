import os
import shutil
import logging
import json
import time
import aiofiles


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None or type(obj) in (str, tuple, list, dict):
            return obj
        return obj_to_str(obj)


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
                if is_format(part_str):
                    cmdline.append(part_str.format(**args))
                else:
                    cmdline.append(part_str)
            elif isinstance(part, dict):
                for arg_key, arg_format in iter(part.items()):
                    arg_format = str(arg_format).replace('%s', '{}')
                    if is_format(arg_format):
                        value = get(arg_key, args)
                        if isinstance(value, list):
                            cmdline.append(arg_format.format(*value))
                        elif value:
                            cmdline.append(arg_format.format(value))
                    elif arg_key in args:
                        cmdline.append(arg_format)
        if output is list:
            return cmdline
        return ' '.join(cmdline)


class DictionaryCoder:

    def __init__(self, coders=None, deep=False):
        self.coders = coders if coders else {}
        if deep:
            raise Exception('Unsupported')

    def append(self, key, coder):
        self.coders.update({key: coder})
        return self

    def process(self, dictionary):
        result = {}
        for key, value in iter(dictionary.items()):
            if key in self.coders:
                coder = self.coders[key]
                if callable(coder):
                    result.update({key: coder(value)})
                elif hasattr(coder, 'encode') and callable(coder.encode):
                    result.update({key: coder.encode(value)})
                elif hasattr(coder, 'decode') and callable(coder.decode):
                    result.update({key: coder.decode(value)})
            else:
                result.update({key: value})
        return result


# TODO this needs improvement, look for builtin support
def is_format(text):
    open_index = text.count('{')
    close_index = text.count('}')
    if open_index == 0 and close_index == 0:
        return False
    return open_index == close_index


def timestamp(value=None):
    if value is None:
        value = time.time()
    return str(int(value * 10000000))


def obj_to_str(obj):
    return repr(obj).replace(' object at ', ':')


def obj_to_json(obj):
    if obj is None:
        return None
    encoder = None if type(obj) is dict else JsonEncoder
    if hasattr(obj, '__dict__'):
        obj = obj.__dict__
    try:
        return json.dumps(obj, cls=encoder)
    except Exception as e:
        logging.warning('Not serializable to JSON. raised: %s', e)
        return None


def json_to_dict(text):
    if text is None or text == '':
        return None
    try:
        return json.loads(text)
    except Exception as e:
        logging.warning('Text is not valid JSON. raised: %s', e)
        return None


def attr_dict(obj, names):
    result = {}
    for name in iter(names):
        if hasattr(obj, name):
            result.update({name: getattr(obj, name)})
    return result


def str_to_b10str(value):
    return ''.join([str(b).zfill(3) for b in value.encode('utf-8')])


def b10str_to_str(value):
    chunks = [value[b:b+3] for b in range(0, len(value), 3)]
    return bytes([int(b) for b in chunks]).decode('utf-8')


def get(key, dictionary):
    if key and dictionary and isinstance(dictionary, dict) and key in dictionary:
        return dictionary[key]
    return None


def iterable(obj):
    try:
        iter(obj)
    except Exception:
        return False
    return True


def file_exists(file):
    if not file:
        return False
    return os.path.isfile(file)


def insert_filename_suffix(filename, suffix):
    index = filename.rfind('.')
    if index == -1 or filename.rfind('/') > index:
        return filename + suffix
    return filename[:index] + suffix + filename[index:]


def directory_list_dict(path):
    if not path.endswith('/'):
        path = path + '/'
    result = []
    for name in iter(os.listdir(path)):
        file = path + name
        ftype = 'unknown'
        if os.path.isfile(file):
            ftype = 'file'
        elif os.path.isdir(file):
            ftype = 'directory'
        elif os.path.islink(file):
            ftype = 'link'
        updated = time.ctime(os.path.getmtime(file))
        result.append({'type': ftype, 'name': name, 'updated': updated})
    return result


def create_directory(path):
    os.mkdir(path)


def archive_directory(path):
    parts = path.split('/')
    if parts[-1] == '':
        del parts[-1]   # chop trailing '/'
    root_dir = '/'.join(parts)
    file = []
    for part in iter(parts):
        file.append(part)
    file.append('..')
    file.append(parts[-1] + '-' + timestamp())
    file = '/'.join(file)
    shutil.make_archive(file, 'zip', root_dir=root_dir)
    return file


def delete_directory(path):
    shutil.rmtree(path, ignore_errors=True)


def delete_file(file):
    if file is not None and file_exists(file):
        os.remove(file)


async def read_file(filename, text=True):
    mode = 'r' if text else 'rb'
    async with aiofiles.open(filename, mode=mode) as file:
        try:
            return await file.read()
        finally:
            await file.close()


async def write_file(filename, data, text=True):
    mode = 'w' if text else 'wb'
    async with aiofiles.open(filename, mode=mode) as file:
        try:
            await file.write(data)
        finally:
            await file.close()


async def copy_file(source_file, target_file):
    data = await read_file(source_file, text=False)
    await write_file(target_file, data, text=False)
