"""Utility functions for geospaas.processing"""
import functools
import gzip
import logging
import math
import os
import os.path
import posixpath
import re
import shutil
import stat
import tarfile
import time
import yaml
import zipfile
from contextlib import contextmanager
from collections.abc import Sequence
from urllib.parse import urlparse

import paramiko
import requests
import scp
try:
    from redis import Redis
except ImportError:  # pragma: no cover
    Redis = None

from geospaas.processing.config import settings

LOGGER = logging.getLogger(__name__)
logging.getLogger('paramiko').setLevel(logging.WARNING)
LOCK_EXPIRE = 3600  # Lock expires in 1 hour
REDIS_HOST = settings.GEOSPAAS_PROCESSING_REDIS_HOST
REDIS_PORT = settings.GEOSPAAS_PROCESSING_REDIS_PORT
DATASET_LOCK_PREFIX = 'lock-'


class CleanUpError(Exception):
    """Error while freeing space"""


class Storage():
    """Represents a storage location"""

    LOCK_PREFIX = 'lock_cleanup_'

    def __init__(self, **kwargs):
        """"""
        self.path = kwargs['path']
        self.block_size = self.get_block_size()

    def get_files_size(self, files):
        """Returns the total size of several files in bytes"""
        return sum(self.get_file_size(file) for file in files)

    def get_file_size(self, file):
        """Get the size of one file in bytes"""
        raise NotImplementedError

    def get_block_size(self):
        """Get the block size of the file system"""
        raise NotImplementedError()

    def get_free_space(self):
        """Get the available space in bytes"""
        raise NotImplementedError()

    def listdir(self, dir_path):
        """
        Get the contents of a directory, as returned by `os.listdir()`.
        The path is relative to `self.path`.
        """
        raise NotImplementedError()

    def stat(self, path):
        """
        Get information about a file, as returned by `os.stat()`.
        The path is relative to `self.path`
        """
        raise NotImplementedError()

    def isfile(self, path):
        """Return True if the file is a regular file. The path is relative to `self.path`"""
        raise NotImplementedError()

    def isdir(self, path):
        """Return True if the file is a directory. The path is relative to `self.path`."""
        raise NotImplementedError()

    def remove(self, path):
        """Remove the target file. The path is relative to `self.path`."""
        raise NotImplementedError()

    def put(self, local_path, storage_path):
        """
        Put the file from the local filesystem located at `local_path` in the Storage.
        `storage_path` is the relative path in the Storage.
        """
        raise NotImplementedError()

    def _get_file_disk_usage(self, file_size):
        """
        Get the space occupied by a file on disk,
        taking into account the block size of the filesystem.
        """
        blocks = math.ceil(float(file_size) / float(self.block_size))
        return blocks * self.block_size

    def _get_removable_files(self):
        """
        Get the characteristics of the files that can be deleted from the directory.
        Returns a list of tuples containing:
            - the file path
            - the file size
            - the time of the last modification
        """
        dirs_to_process = ['']
        depth = 1
        max_depth = 1000
        removable_files = []
        while dirs_to_process and depth < max_depth:
            current_dir = dirs_to_process.pop()
            for file_name in self.listdir(current_dir):
                path = os.path.join(current_dir, file_name)
                if self.isfile(path):
                    try:
                        file_stat = self.stat(path)
                    except FileNotFoundError:
                        LOGGER.warning(
                            "%s has been removed while a cleanup was in progress", path)
                    except IsADirectoryError:
                        LOGGER.warning("%s has somehow been transformed into a directory while a" +
                                       " cleanup was in progress",
                                       path)
                    else:
                        removable_files.append((
                            path,
                            self._get_file_disk_usage(file_stat.st_size),
                            file_stat.st_mtime
                        ))
                elif self.isdir(path):
                    dirs_to_process.append(path)
                    depth += 1
        LOGGER.debug("Contents of %s directory: %s", self.path, removable_files)
        return removable_files

    @staticmethod
    def _sort_by_mtime(files):
        """
        Sorts a list of files by their modification time.
        The list should have the same structure as returned by `_get_removable_files()`
        """
        return sorted(files, key=lambda x: x[2])

    @staticmethod
    def _total_freeable_space(removable_files):
        total = 0
        for file_info in removable_files:
            total += file_info[1]
        return total

    def _delete_files(self, space_to_free, removable_files):
        """
        Deletes files from the removable_files list until enough space has been freed.
        removable_files must be sorted by decreasing priority (the first files in the list
        will be deleted first). space_to_free is in bytes.
        """
        files_to_delete = []
        freed_space = 0

        for file_properties in removable_files:
            files_to_delete.append(file_properties[0])
            freed_space += file_properties[1]
            if freed_space >= space_to_free:
                break

        for file_path in files_to_delete:
            self.remove(file_path)

        return freed_space, files_to_delete

    def free_space(self, new_file_size):
        """
        Removes files from `self.path` until `new_file_size` bytes have been freed,
        starting with the oldest files.
        """
        max_retries = 30
        countdown = 20
        retries = 0
        while retries < max_retries:
            with redis_lock(f"{self.LOCK_PREFIX}{self.path}", '') as acquired:
                if acquired:
                    current_free_space = self.get_free_space()
                    removable_files = self._sort_by_mtime(self._get_removable_files())
                    freeable_space = self._total_freeable_space(removable_files)

                    if new_file_size > freeable_space + current_free_space:
                        raise CleanUpError("Cannot free enough space")
                    elif new_file_size > current_free_space:
                        space_to_free = new_file_size - current_free_space
                        freed_space, deleted_files = self._delete_files(
                            space_to_free, removable_files)
                        LOGGER.info("Freed %d bytes by removing the following files: %s",
                                    freed_space, deleted_files)
                        return freed_space, deleted_files
                    else:
                        return 0, []
                else:
                    LOGGER.info("Waiting for concurrent cleanup to finish")
                    time.sleep(countdown)
                    retries += 1
        raise CleanUpError("Could not acquire cleanup lock")


class LocalStorage(Storage):
    """Represents a storage location on a local disk"""

    def get_file_size(self, file):
        return os.path.getsize(os.path.join(self.path, file))

    def get_block_size(self):
        return self.stat('').st_blksize

    def get_free_space(self):
        return shutil.disk_usage(self.path).free

    def listdir(self, dir_path):
        return os.listdir(os.path.join(self.path, dir_path))

    def stat(self, path):
        return os.stat(os.path.join(self.path, path))

    def isfile(self, path):
        return os.path.isfile(os.path.join(self.path, path))

    def isdir(self, path):
        return os.path.isdir(os.path.join(self.path, path))

    def remove(self, path):
        os.remove(os.path.join(self.path, path))

    def put(self, local_path, storage_path):
        shutil.copy(local_path, os.path.join(self.path, storage_path))


class RemoteStorage(Storage):
    """Represents a storage location on a remote Linux host accessible by SSH"""

    def __init__(self, **kwargs):
        self.host = kwargs['host']
        host_config = self.get_ssh_config()

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client.connect(self.host, host_config['port'], host_config['user'],
                                key_filename=host_config['identityfile'][0])

        self.sftp_client = self.ssh_client.open_sftp()

        super().__init__(**kwargs)

    def __del__(self):
        self.ssh_client.close()

    def get_ssh_config(self):
        """Read SSH configuration from ~/.ssh/config"""
        config = paramiko.SSHConfig.from_path(
            os.path.join(os.path.expanduser('~'), '.ssh', 'config'))
        return config.lookup(self.host)

    def get_file_size(self, file):
        absolute_path = posixpath.join(self.path, file)
        _, stdout, _ = self.ssh_client.exec_command(f"du --bytes '{absolute_path}' | cut -f1")
        return int(stdout.read())

    def get_block_size(self):
        _, stdout, _ = self.ssh_client.exec_command(f"stat -f --printf '%S' '{self.path}'")
        return int(stdout.read())

    def get_free_space(self):
        _, stdout, _ = self.ssh_client.exec_command(f"df -B 1 -P '{self.path}'")
        return int(stdout.readlines()[1].split()[3])

    def listdir(self, dir_path):
        return self.sftp_client.listdir(os.path.join(self.path, dir_path))

    def stat(self, path):
        full_path = os.path.join(self.path, path)
        return self.sftp_client.stat(full_path)

    def isfile(self, path):
        mode = self.stat(path).st_mode
        return stat.S_ISREG(mode)

    def isdir(self, path):
        mode = self.stat(path).st_mode
        return stat.S_ISDIR(mode)

    def remove(self, path):
        self.sftp_client.remove(os.path.join(self.path, path))

    def put(self, local_path, storage_path):
        remote_path = os.path.join(self.path, storage_path)
        # Create the directory where the files will be copied on the remote server
        _, stdout, _ = self.ssh_client.exec_command(f"mkdir -p {os.path.dirname(remote_path)}")
        stdout.channel.recv_exit_status() # wait for the command to finish executing
        #Copy the files
        with scp.SCPClient(self.ssh_client.get_transport()) as scp_client:
            scp_client.put(local_path, recursive=True, remote_path=remote_path)


@contextmanager
def redis_lock(lock_key, lock_value):
    """
    Context manager to set a lock in a cache. Pretty much copied from:
    https://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html#ensuring-a-task-is-only-executed-one-at-a-time
    """
    if Redis is not None and REDIS_HOST and REDIS_PORT:
        cache = Redis(host=REDIS_HOST, port=REDIS_PORT)
        timeout_at = time.monotonic() + LOCK_EXPIRE
        status = cache.setnx(lock_key, lock_value)
        cache.expire(lock_key, LOCK_EXPIRE)
        try:
            yield status
        finally:
            if time.monotonic() < timeout_at and status:
                cache.delete(lock_key)
    else:
        # if the redis lib is not available or no connection information is provided,
        # always acquire the lock
        yield True


def redis_any_lock(lock_key_prefix='lock'):
    """Returns True if any lock is set in Redis.
    Returns False if no lock is set or if Redis is not available.
    """
    if Redis is not None and REDIS_HOST and REDIS_PORT:
        cache = Redis(host=REDIS_HOST, port=REDIS_PORT)
        for key in cache.keys():
            if key.startswith(bytes(lock_key_prefix, 'utf-8')):
                return True
    return False


def lock_dataset_files(function):
    """
    Decorator that locks a dataset's files. Works with tasks that take either
    a dataset ID as argument, or a tuple which first argument is a dataset ID.
    """
    @functools.wraps(function)
    def redis_lock_wrapper(*args, **kwargs):
        retries_wait = 15
        retries_count = 60
        task = args[0]
        if 'args' in kwargs:
            task_args = kwargs.pop('args')
        else:
            task_args = args[1]
        dataset_id = task_args[0]
        lock_id = f"{DATASET_LOCK_PREFIX}{dataset_id}"
        with redis_lock(lock_id, task.request.id or 'local') as acquired:
            if acquired:
                return function(task, task_args, **kwargs)
            else:
                LOGGER.info("Another task is in progress on dataset %s, retrying", dataset_id)
                task.retry((task_args,), countdown=retries_wait, max_retries=retries_count)
    return redis_lock_wrapper


def gunzip(archive_path, out_dir):
    """Extracts the gzip archive contents to `out_dir`"""
    file_name = re.sub(r'\.gz$', '', os.path.basename(archive_path))
    with gzip.open(archive_path, 'rb') as archive_file:
        with open(os.path.join(out_dir, file_name), 'wb') as output_file:
            shutil.copyfileobj(archive_file, output_file)


shutil.register_unpack_format('gz', ['.gz'], gunzip)


def unarchive(in_file):
    """Extract contents if `in_file` is an archive. Supported format
    are those supported by shutil's unpack_archive(), plus gzip.
    The files are extracted in a folder name like the archive, minus
    the extension.
    Returns None if the given file is not an archive (or in an
    unsupported archive format)
    """
    extract_dir = None

    match = re.match(
        (r'(.*)\.('
         r'tar'
         r'|tar\.gz|tgz'
         r'|tar\.bz2|tbz2'
         r'|tar\.xz|txz'
         r'|zip'
         r'|(?<!tar\.)gz)$'),
        in_file)
    if match:
        extract_dir = match.group(1)
        os.makedirs(extract_dir, exist_ok=True)

        try:
            shutil.unpack_archive(in_file, extract_dir)
        except shutil.ReadError:
            shutil.rmtree(extract_dir)
            raise

    return extract_dir

def is_gzipfile(file_path):
    """Test if a file is a gzip archive by checking the magic number
    """
    with open(file_path, 'rb') as file_handler:
        return file_handler.read(2) == b'\x1f\x8b'

def tar_gzip(file_path, force=False):
    """Makes the file a tar archive compressed with gzip if the file is not one already"""
    if os.path.isfile(file_path) and (tarfile.is_tarfile(file_path) or
                                      zipfile.is_zipfile(file_path) or
                                      is_gzipfile(file_path)):
        return file_path

    archive_path = f"{file_path}.tar.gz"
    if os.path.isfile(archive_path):
        if force:
            os.remove(archive_path)
        else:
            return archive_path

    with tarfile.open(archive_path, 'w:gz') as archive:
        archive.add(file_path, arcname=os.path.basename(file_path))

    return archive_path


def yaml_env_safe_load(stream):
    """Parses a YAML string with support for the !ENV tag.
    A string tagged with !ENV is replaced by the value of the
    environment variable whose name is that string.
    """
    yaml.SafeLoader.add_constructor('!ENV', lambda loader, node: os.getenv(node.value))
    return yaml.safe_load(stream)


class TrustDomainSession(requests.Session):
    """Session class which allows keeping authentication headers in
    case of redirection to the same domain
    """

    def should_strip_auth(self, old_url, new_url):
        """Keep the authentication header when redirecting to a
        different host in the same domain, for example from
        "scihub.copernicus.eu" to "apihub.copernicus.eu".
        If not in this case, defer to the parent class.
        """
        old_split_hostname = urlparse(old_url).hostname.split('.')
        new_split_hostname = urlparse(new_url).hostname.split('.')
        if (len(old_split_hostname) > 2
                and len(new_split_hostname) > 2
                and old_split_hostname[-2:] == new_split_hostname[-2:]):
            return False
        else:
            return super().should_strip_auth(old_url, new_url)


def http_request(http_method, *args, **kwargs):
    """Wrapper around requests.request() which runs the HTTP request
    inside a TrustDomainSession if authentication is provided. This
    makes it possible to follow redirections inside the same domain.
    """
    auth = kwargs.pop('auth', (None, None))
    if ((isinstance(auth, Sequence) and any(i is not None for i in auth))
            or (not isinstance(auth, Sequence) and auth)):
        with TrustDomainSession() as session:
            session.auth = auth
            return session.request(http_method, *args, **kwargs)
    else:
        return requests.request(http_method, *args, **kwargs)
