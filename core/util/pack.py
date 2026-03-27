import shutil
import lzma
import tarfile
import gzip
# ALLOW util.*
from core.util import funcutil


def _sync_unpack_tarxz(file_path: str, target_directory: str):
    with lzma.open(file_path) as fd:
        with tarfile.open(fileobj=fd) as tar:
            tar.extractall(target_directory)


def _sync_unpack_tarbz(file_path: str, target_directory: str):
    with tarfile.open(file_path, 'r:bz2') as tar:
        tar.extractall(target_directory)


def _sync_unpack_targz(file_path: str, target_directory: str):
    with tarfile.open(file_path, 'r:gz') as tar:
        tar.extractall(target_directory)


unpack_tarxz = funcutil.to_async(_sync_unpack_tarxz)
unpack_tarbz = funcutil.to_async(_sync_unpack_tarbz)
unpack_targz = funcutil.to_async(_sync_unpack_targz)
unpack_archive = funcutil.to_async(shutil.unpack_archive)
gzip_compress = funcutil.to_async(gzip.compress)
gzip_decompress = funcutil.to_async(gzip.decompress)


def make_archive_script(archive_file: str, unpacked_dir: str) -> str:
    return f'''import logging
import pathlib
import sys
import zipfile
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
    unpacked_dir = pathlib.Path('{unpacked_dir}')
    with zipfile.ZipFile('{archive_file}', 'w', zipfile.ZIP_DEFLATED) as f:
        for abspath in unpacked_dir.rglob('*'):
            if not abspath.is_symlink():
                logging.info('DEFLATE ' + str(abspath))
                f.write(abspath, str(abspath.relative_to(unpacked_dir)))
'''


def unpack_archive_script(archive_file: str, unpacked_dir: str) -> str:
    return f'''import logging
import os
import sys
import zipfile
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
    with zipfile.ZipFile('{archive_file}', 'r') as f:
        for member in f.infolist():
            abspath = str(f.extract(member, '{unpacked_dir}'))
            logging.info('UNPACKED ' + abspath)
            filename = os.path.basename(abspath)
            if filename.find('.') == -1 or filename.endswith('.sh') or filename.endswith('.x86_64'):
                os.chmod(abspath, 0o774)
'''
