import inspect
import os
import signal
import shutil
import logging
import json
import time
import uuid

import aiofiles


SCRIPT_SPECIALS = str.maketrans({
    '#':  r'\#', '$':  r'\$', '=':  r'\=', '[':  r'\[', ']':  r'\]',
    '!': r'\!', '<': r'\<', '>': r'\>', '{': r'\{', '}': r'\}',
    ';': r'\;', '|': r'\|', '~': r'\~', '(': r'\(', ')': r'\)',
    '*': r'\*', '?': r'\?', '&': r'\&'
})


class _JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None or type(obj) in (str, tuple, list, dict):
            return obj
        return obj_to_str(obj)


def script_escape(value):
    if not isinstance(value, str):
        return value
    return value.translate(SCRIPT_SPECIALS)


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


def obj_to_dict(obj):
    if obj is None or isinstance(obj, dict):
        return obj
    if hasattr(obj, 'asdict'):
        return obj.asdict()
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    raise Exception('obj_to_dict() failed converting {} to dict'.format(obj))


def obj_to_json(obj):
    if obj is None:
        return None
    encoder = None if type(obj) is dict else _JsonEncoder
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


async def silently_cleanup(obj):
    if hasattr(obj, 'stop'):
        await silently_call(obj.stop)
    if hasattr(obj, 'close'):
        await silently_call(obj.close)
    if hasattr(obj, 'shutdown'):
        await silently_call(obj.shutdown)
    if hasattr(obj, 'cleanup'):
        await silently_call(obj.cleanup)


async def silently_call(invokable):
    if not callable(invokable):
        return
    try:
        if inspect.iscoroutinefunction(invokable):
            await invokable()
        else:
            invokable()
    except Exception as e:
        logging.debug('silently_call failed: ' + repr(e))


def str_to_b10str(value):
    return ''.join([str(b).zfill(3) for b in value.encode('utf-8')])


def b10str_to_str(value):
    chunks = [value[b:b+3] for b in range(0, len(value), 3)]
    return bytes([int(b) for b in chunks]).decode('utf-8')


def to_text(lines):
    return '\n'.join(lines)


def build_url(host=None, port=80, path=None):
    parts = ['http://', str(host) if host else 'localhost']
    if port != 80:
        parts.append(':')
        parts.append(str(port))
    if path:
        path = str(path)
        if not path.startswith('/'):
            parts.append('/')
        parts.append(path)
    return ''.join(parts)


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


def overridable_full_path(root, path):
    if root is None or path is None or path[0] in ('.', '/'):
        return path
    return root + '/' + path


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
    if not os.path.isdir(path):
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


def wipe_directory(path):
    delete_directory(path)
    create_directory(path)


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
            await silently_cleanup(file)


async def write_file(filename, data, text=True):
    mode = 'w' if text else 'wb'
    async with aiofiles.open(filename, mode=mode) as file:
        try:
            await file.write(data)
        finally:
            await silently_cleanup(file)


async def copy_file(source_file, target_file):
    data = await read_file(source_file, text=False)
    await write_file(target_file, data, text=False)


def left_chop_and_strip(line, keyword):
    index = line.find(keyword)
    if index == -1:
        return line
    return line[index + len(keyword):].strip()


def right_chop_and_strip(line, keyword):
    index = line.find(keyword)
    if index == -1:
        return line
    return line[:index].strip()


def generate_token():
    identity = str(uuid.uuid4())
    return identity[:6] + identity[-6:]


def signal_interrupt(pid=None):
    if pid is None:
        pid = os.getpid()
    os.kill(pid, signal.SIGINT)
