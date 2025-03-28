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


unpack_tarxz = funcutil.to_async(_sync_unpack_tarxz)
gzip_compress = funcutil.to_async(gzip.compress)
gzip_decompress = funcutil.to_async(gzip.decompress)
make_archive = funcutil.to_async(shutil.make_archive)
unpack_archive = funcutil.to_async(shutil.unpack_archive)
