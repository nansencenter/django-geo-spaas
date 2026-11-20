"""
Tools for automatic downloading of files referenced in a GeoSPaaS database.

In order to use the locking functionalities (for example limit the number of parallel downloads),
a Redis instance must be available, and the **redis** pip package installed.
The Redis instance hostname and port can be set via the following environment variables:
  - GEOSPAAS_PROCESSING_REDIS_HOST
  - GEOSPAAS_PROCESSING_REDIS_PORT
"""
import errno
import ftplib
import hashlib
import itertools
import logging
import os
import os.path
import pickle
import re
import shutil
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import boto3
import botocore.config
import botocore.exceptions
import oauthlib.oauth2
import oauthlib.oauth2.rfc6749.errors
import pyotp
import requests
import requests.utils
import requests_oauthlib
try:
    from redis import Redis
except ImportError:  # pragma: no cover
    Redis = None

from geospaas.catalog.models import Dataset

import geospaas.processing.utils as utils


LOGGER = logging.getLogger(__name__)


class DownloadError(Exception):
    """Download failed"""


class RetriableDownloadError(Exception):
    """Download failed but might work if retried"""


class ObsoleteURLError(DownloadError):
    """The URL no longer points to a downloadable dataset"""


class DatasetDownloadError(DownloadError):
    """Failed to download a dataset using any of its URLs"""

    def __init__(self, *args, **kwargs):
        self.errors = kwargs.pop('errors', [])
        super().__init__(*args, **kwargs)

    def __str__(self):
        result = super().__str__()
        for error in self.errors:
            result += f"\n  {error.__class__.__name__}: {error}"
        return result


class TooManyDownloadsError(DownloadError):
    """There are already as many downloads in progress as allowed by the provider"""


class Downloader():
    """Base class for downloaders"""

    @staticmethod
    def validate_settings(settings, keys):
        """`settings` is a dictionary, `keys` is a list of strings.
        Checks that all the strings in `keys` are in `settings`,
        otherwise raise a DownloadError.
        """
        missing_keys = []
        for key in keys:
            if not settings.get(key):
                missing_keys.append(key)
        if missing_keys:
            raise DownloadError(
                f"The following keys are missing from provider_settings.yml: {missing_keys}")

    @classmethod
    def get_auth(cls, kwargs):
        """Builds the `auth` argument taken by `requests` methods from
        the keyword arguments. Uses Basic Auth.
        """
        if ('username' in kwargs) and ('password') in kwargs:
            return (kwargs['username'], kwargs['password'])
        return (None, None)

    @classmethod
    def connect(cls, url, auth=(None, None), **kwargs):
        """Connect to the remote repository. This should return an
        object from which the file to download can be read.
        """
        raise NotImplementedError()

    @classmethod
    def close_connection(cls, connection):
        """Closes the open connection. Most objects used as connections
        have a close() method, but it might be necessary to override
        this in child classes.
        """
        connection.close()

    @classmethod
    def get_file_name(cls, url, connection, **kwargs):
        """Returns the name of the file"""
        raise NotImplementedError()

    @classmethod
    def get_file_size(cls, url, connection, auth=(None, None)):
        """Returns the size of the file"""
        raise NotImplementedError()

    @classmethod
    def download_file(cls, file_path, url, connection):
        """Writes the remote file to the file object contained in the
        `file` argument"""
        raise NotImplementedError()

    @classmethod
    def check_and_download_url(cls, url, download_dir, **kwargs):
        """
        Downloads the file from the requested URL. To be implemented
        in child classes. Must call utils.LocalStorage.free_space()
        before downloading, and manage the case where there is no space
        left to write the downloaded file.
        """
        auth = cls.get_auth(kwargs)
        connection = cls.connect(url, auth, **kwargs)
        try:
            file_name = cls.get_file_name(url, connection, **kwargs)
            if not file_name:
                raise DownloadError(f"Could not find file name for '{url}'")
            file_path = os.path.join(download_dir, file_name)

            file_size = cls.get_file_size(url, connection)
            if file_size:
                LOGGER.debug("Checking there is enough free space to download %s bytes", file_size)
                utils.LocalStorage(path=download_dir).free_space(file_size)

            try:
                cls.download_file(file_path, url, connection)
            except OSError as error:
                if error.errno == errno.ENOSPC:
                    # In case of "No space left on device" error,
                    # try to remove the partially downloaded file
                    try:
                        os.remove(file_path)
                    except FileNotFoundError:
                        pass
                raise
            return file_name
        finally:
            cls.close_connection(connection)


class URLOAuth2(requests_oauthlib.OAuth2):
    """Custom OAuth2 class that places the token as a parameter in the URL"""

    def __init__(self, *args, **kwargs):
        self.token_parameter_name = kwargs.pop('token_parameter_name', 'access_token')
        super().__init__(*args, **kwargs)

    def __call__(self, r):
        """Override default behavior and put the token in the url
        """
        if not oauthlib.oauth2.is_secure_transport(r.url):
            raise oauthlib.oauth2.InsecureTransportError()
        sch, net, path, par, query, fra = urlparse(r.url)
        query_params = parse_qsl(query)
        query_params.append(('token', self._client.access_token))
        query = urlencode(query_params)
        r.url = urlunparse((sch, net, path, par, query, fra))
        return r


class HTTPDownloader(Downloader):
    """Downloader for repositories which work over HTTP, like OpenDAP"""
    CHUNK_SIZE = 1024 * 1024

    @classmethod
    def get_oauth2_token(cls, username, password, token_url, client, totp_secret=None):
        """Try to get a token from Redis. If this fails, fetch one from the URL"""
        token = None

        LOGGER.debug("Attempting to get an OAuth2 token")
        if Redis is not None and utils.REDIS_HOST and utils.REDIS_PORT:  # cache available
            cache = Redis(host=utils.REDIS_HOST, port=utils.REDIS_PORT)
            key_hash = hashlib.sha1(bytes(token_url + username, encoding='utf-8')).hexdigest()
            lock_key = f"lock-{key_hash}"

            LOGGER.debug("Trying to retrieve OAuth2 token from the cache")
            retries = 10
            while retries > 0:
                raw_token = cache.get(key_hash)
                if raw_token is None:  # did not get the token from the cache
                    if cache.setnx(lock_key, 1):  # set a lock to avoid concurrent token fetching
                        cache.expire(lock_key, utils.LOCK_EXPIRE)  # safety precaution

                        # fetch token from the URL
                        token = cls.fetch_oauth2_token(
                            username, password, token_url, client, totp_secret)
                        LOGGER.debug("Got OAuth2 token from URL")

                        # save the token in the cache
                        expires_in = int(token['expires_in'])
                        # remove 1 second from the expiration time to account
                        # for the processing time after the token was issued
                        expiration = expires_in - 1 if expires_in >= 1 else 0
                        cache.set(key_hash, pickle.dumps(token), ex=expiration)
                        LOGGER.debug("Stored Oauth2 token in the cache")
                        cache.delete(lock_key)
                        retries = 0
                    else:  # another process is fetching the token
                        time.sleep(1)
                        retries -= 1
                else:  # successfully got the token from the cache
                    token = pickle.loads(raw_token)
                    LOGGER.debug("Got OAuth2 token from the cache")
                    retries = 0
        else:  # cache not available
            LOGGER.debug("Cache not available, getting OAuth2 token from URL")
            token = cls.fetch_oauth2_token(username, password, token_url, client, totp_secret)

        return token

    @classmethod
    def fetch_oauth2_token(cls, username, password, token_url, client, totp_secret=None):
        """Fetches a new token from the URL"""
        # TOTP passwords are valid for 30 seconds, so we retry a few
        # times in case we get unlucky and the password expires between
        # the generation of the password and the authentication request
        session_args = {
            'token_url': token_url,
            'username': username,
            'password': password,
            'client_id': client.client_id,
        }
        retries = 5
        while retries > 0:
            if totp_secret:
                session_args['totp'] = pyotp.TOTP(totp_secret).now()
            try:
                token = requests_oauthlib.OAuth2Session(client=client).fetch_token(**session_args)
            except oauthlib.oauth2.rfc6749.errors.InvalidGrantError:
                retries -= 1
                if retries > 0:
                    continue
                else:
                    raise
            return token

    @classmethod
    def build_oauth2_authentication(cls, username, password, token_url, client_id,
                                    totp_secret=None, token_placement=None,
                                    token_parameter_name=None):
        """Creates an OAuth2 object usable by `requests` methods"""
        client = oauthlib.oauth2.LegacyApplicationClient(client_id=client_id)
        token = cls.get_oauth2_token(username, password, token_url, client, totp_secret)
        if token_placement is None:
            oauth2 = requests_oauthlib.OAuth2(client_id=client_id, client=client, token=token)
        elif token_placement == 'url':
            oauth2 = URLOAuth2(client_id=client_id, client=client, token=token,
                               token_parameter_name=token_parameter_name)
        else:
            raise DatasetDownloadError(
                f'Unknown token_placement in configuration: {token_placement}')
        return oauth2

    @classmethod
    def get_auth(cls, kwargs):
        """Builds the `auth` argument taken by `requests` methods from
        the keyword arguments. Supports OAuth2 and Basic Auth.
        """
        if kwargs.get('authentication_type') == 'oauth2':
            cls.validate_settings(
                kwargs, ('username', 'password', 'token_url', 'client_id'))

            return cls.build_oauth2_authentication(
                kwargs['username'],
                kwargs['password'],
                kwargs['token_url'],
                kwargs['client_id'],
                totp_secret=kwargs.get('totp_secret'),
                token_placement=kwargs.get('token_placement'),
                token_parameter_name=kwargs.get('token_parameter_name'),
            )
        else:
            return super().get_auth(kwargs)

    @classmethod
    def get_request_parameters(cls, kwargs):
        """Retrieve and check request parameters from kwargs"""
        parameters = kwargs.get('request_parameters', {})
        if isinstance(parameters, dict):
            return parameters
        else:
            raise ValueError(
                "The 'request_parameters' configuration key should contain a dictionary")

    @classmethod
    def check_response(cls, response, kwargs):
        """Check an HTTP response for a status indicating that the URL
        is obsolete
        """
        invalid_status_codes = kwargs.get('invalid_status_codes', {})
        invalid_status_codes.setdefault(404, 'URL does not exist')

        # deal with obsolete URLs
        if response.status_code in invalid_status_codes:
            raise ObsoleteURLError(
                f"{response.url} is not downloadable" +
                f" ({str(response.status_code)}: {invalid_status_codes[response.status_code]})")
        response.raise_for_status()

    @classmethod
    def get_file_name(cls, url, connection, **kwargs):
        """Extracts the file name from the Content-Disposition header
        of an HTTP response
        """
        filename_key = 'filename='
        if 'Content-Disposition' in connection.headers:
            content_disposition = [
                i.strip() for i in connection.headers['Content-Disposition'].split(';')
            ]

            filename_attributes = [a for a in content_disposition if a.startswith(filename_key)]
            filename_attributes_length = len(filename_attributes)
            if filename_attributes_length > 1:
                raise ValueError("Multiple file names found in response Content-Disposition header")
            elif filename_attributes_length == 1:
                return filename_attributes[0].replace(filename_key, '').strip('"')

        elif 'Content-Type' in connection.headers:
            accepted_types = ('/x-netcdf', '/octet-stream')
            url_file_name = url.split('/')[-1]
            content_type = connection.headers['Content-Type'].lower()

            if (any(accepted_type in content_type for accepted_type in accepted_types)
                    and url_file_name.endswith('.nc')):
                return url_file_name

        LOGGER.error("Could not find file name from HTTP response for %s: %s, %s, %s",
                     url, connection.status_code, connection.reason, connection.headers)
        return ''

    @classmethod
    def connect(cls, url, auth=(None, None), **kwargs):
        """For HTTP downloads, the "connection" actually just consists
        of sending a GET request to the download URL and return the
        corresponding Response object
        """
        try:
            response = utils.http_request(
                'GET', url, stream=True, auth=auth, params=cls.get_request_parameters(kwargs))
            cls.check_response(response, kwargs)
        # Raising DownloadError enables to display a clear message in the API response
        except requests.HTTPError as error:
            details = f"{response.status_code} {response.text}"
            response.close()
            raise DownloadError(
                f"Could not download from '{url}'; response: {details}"
            ) from error
        except (requests.ConnectionError, requests.Timeout) as error:
            raise RetriableDownloadError(f"Failed to connect to {url}") from error
        except requests.RequestException as error:
            raise DownloadError(
                f"Could not download from '{url}'"
            ) from error

        return response

    @classmethod
    def close_connection(cls, connection):
        """Nothing to do since there is no connection kept alive"""

    @classmethod
    def get_file_size(cls, url, connection, auth=(None, None)):
        """Try to get the file size from the response Content-Length
        header. If that does not work, try to get it from a HEAD
        request.
        """
        file_size = None
        try:
            file_size = int(connection.headers['Content-Length'])
        except KeyError:
            try:
                file_size = int(
                    utils.http_request('HEAD', connection.url, auth=auth).headers['Content-Length'])
            except KeyError:
                pass
        return file_size

    @classmethod
    def download_file(cls, file_path, url, connection):
        """Download the file using the Response object contained in the
        `connection` argument
        """
        chunk = None
        try:
            with open(file_path, 'wb') as file:
                for chunk in connection.iter_content(chunk_size=cls.CHUNK_SIZE):
                    file.write(chunk)
        except requests.exceptions.ChunkedEncodingError as error:
            raise RetriableDownloadError(f"Download from {url} was interrupted") from error
        if chunk is None:
            raise DownloadError(f"Getting an empty file from '{url}'")


class FTPDownloader(Downloader):
    """Downloader for FTP repositories"""

    @classmethod
    def connect(cls, url, auth=(None, None), **kwargs):
        """Connects to the remote FTP repository.
        Returns a ftplib.FTP object.
        """
        try:
            ftp = ftplib.FTP(host=urlparse(url).netloc)
            ftp.login(user=auth[0], passwd=auth[1])
            return ftp
        except ftplib.all_errors as error:
            raise DownloadError(f"Could not download from '{url}': {error.args}") from error

    @classmethod
    def get_file_name(cls, url, connection, **kwargs):
        """Extracts the file name from the URL"""
        return urlparse(url).path.split('/')[-1] or None

    @classmethod
    def get_file_size(cls, url, connection):
        """Get the file size from the remote server"""
        try:
            return connection.size(urlparse(url).path)
        except ftplib.all_errors as error:
            LOGGER.warning("Could not get the size from '%s'", url)
            return None

    @classmethod
    def download_file(cls, file_path, url, connection):
        """Downloads the remote file to the `file` object"""
        path = urlparse(url).path
        if connection.nlst(path):
            with open(file_path, 'wb') as file:
                connection.retrbinary(f"RETR {path}", file.write)
        else:
            raise ObsoleteURLError(f"{url} does not exist")


class LocalDownloader(Downloader):
    """Downloader for locally hosted files, so basically a file copier
    """

    @staticmethod
    def get_auth(kwargs):
        return (None, None)

    @classmethod
    def connect(cls, url, auth=(None, None), **kwargs):
        return None

    @classmethod
    def close_connection(cls, connection):
        return None

    @classmethod
    def get_file_name(cls, url, connection, **kwargs):
        return os.path.basename(urlparse(url).path)

    @classmethod
    def get_file_size(cls, url, connection, auth=(None, None)):
        url = urlparse(url).path
        try:
            return os.path.getsize(url)
        except FileNotFoundError as error:
            raise ObsoleteURLError(f"{url} does not exist") from error

    @classmethod
    def download_file(cls, file_path, url, connection):
        shutil.copyfile(urlparse(url).path, file_path)


class S3Downloader(Downloader):
    """Download files from AWS S3"""

    @classmethod
    def get_auth(cls, kwargs):
        if ('access_key' in kwargs) and ('secret_key') in kwargs:
            return (kwargs['access_key'], kwargs['secret_key'])
        return (None, None)

    @classmethod
    def connect(cls, url, auth=(None, None), **kwargs):
        url_components = urlparse(url)
        bucket_name = url_components.netloc
        session = boto3.session.Session(
                aws_access_key_id=auth[0],
                aws_secret_access_key=auth[1],
                region_name=kwargs.get('region_name', 'default'))
        s3 = session.resource(
            's3',
            endpoint_url=kwargs.get('endpoint_url'),
            config=botocore.config.Config(retries={
                'total_max_attempts': 5,
                'mode': 'adaptive'
            }))
        return s3.Bucket(bucket_name)

    @classmethod
    def close_connection(cls, connection):
        """Not necessary"""

    @classmethod
    def get_file_name(cls, url, connection, **kwargs):
        return Path(urlparse(url).path).name

    @classmethod
    def get_file_size(cls, url, connection, auth=(None, None)):
        size = 0
        for file in connection.objects.filter(Prefix=urlparse(url).path.lstrip('/')):
            size += file.size
        return size

    @classmethod
    def download_file(cls, file_path, url, connection):
        try:
            s3_path = Path(urlparse(url).path.lstrip('/'))
            files = connection.objects.filter(Prefix=str(s3_path))
            if not list(files):
                raise DownloadError(f"Could not find any files for {s3_path}")
            dest = Path(file_path)
            for remote_file in files:
                remote_file_path = Path(remote_file.key)
                file_dest = Path(dest, remote_file_path.relative_to(s3_path))
                file_dest.parent.mkdir(parents=True, exist_ok=True)
                if not file_dest.is_dir():
                    if (file_dest.is_file() and file_dest.stat().st_size == remote_file.size):
                        LOGGER.info("Already downloaded, skipping %s", file_dest)
                        continue
                    connection.download_file(remote_file.key, file_dest)
                    downloaded_size = file_dest.stat().st_size
                    if downloaded_size != remote_file.size:
                        raise DownloadError(
                            f"Downloaded file {file_dest} has the wrong size {downloaded_size}")
        except botocore.exceptions.ClientError as error:
            raise RetriableDownloadError("Too many concurrent requests") from error


class DownloadLock():
    """Context manager used to prevent too many simultaneous downloads"""

    CURRENT_DOWNLOADS_KEY = 'current_downloads'

    # Lua scripts to be run on the Redis server for atomic operations
    # Increments or initializes downloads count. Returns nil if the maximum
    # number of downloads has been reached
    # /!\ This is not unit tested for now, BE CAREFUL AND TEST LOCALLY if you modify it /!\
    INCREMENT_SCRIPT = """local d = tonumber(redis.call('hget', KEYS[1], ARGV[1]))
    local limit = tonumber(ARGV[2])
    if(d) then
        if(d < limit) then return redis.call('hincrby', KEYS[1], ARGV[1], 1) end
    else if(limit >= 1) then return redis.call('hset', KEYS[1], ARGV[1], 1) end
    end
    return nil
    """
    # Decrements downloads count, with 0 as the minimum value
    DECREMENT_SCRIPT = """if(tonumber(redis.call('hget', KEYS[1], ARGV[1])) > 0) then
        return redis.call('hincrby', KEYS[1], ARGV[1], -1)
    end
    """

    def __init__(self, base_url, max_downloads, redis_host=None, redis_port=None):
        self.base_url = base_url
        self.max_downloads = max_downloads
        self.acquired = True

        if Redis and redis_host and redis_port:
            self.redis = Redis(redis_host, redis_port)
        else:
            self.redis = None

    def __enter__(self):
        """
        If no Redis instance is defined, returns True.
        Otherwise:
        Checks whether the number of downloads in progress is inferior to `max_downloads`.
        If the number of downloads is inferior to the maximum allowed, it will be incremented in
        Redis and this method returns True.
        If not, it returns False.
        """
        if self.max_downloads and self.redis:
            # Increment or initialize downloads count
            LOGGER.debug("Incrementing downloads count for %s", self.base_url)
            incremented_current_downloads = self.redis.eval(
                self.INCREMENT_SCRIPT, 1, self.CURRENT_DOWNLOADS_KEY,
                self.base_url, self.max_downloads
            )
            # The max number of downloads has already been reached
            if incremented_current_downloads is None:
                LOGGER.debug(
                    "The maximum number of parallel downloads for %s has already been reached",
                    self.base_url
                )
                self.acquired = False
            else:
                LOGGER.debug("Current number of parallel downloads for %s: %s",
                             self.base_url, int(incremented_current_downloads))
        return self.acquired

    def __exit__(self, *args):
        """Decrements the number of downloads if necessary"""
        if self.redis and self.max_downloads and self.acquired:
            LOGGER.debug("Decrementing downloads count for %s", self.base_url)
            self.redis.eval(self.DECREMENT_SCRIPT, 1, self.CURRENT_DOWNLOADS_KEY, self.base_url)


class DownloadManager():
    """Downloads datasets based on some criteria, using the right downloaders"""

    # the order defines the priority of Downloaders.
    # if a local URL is present, it will be tried first, etc.
    DOWNLOADERS = {
        'file': LocalDownloader,
        's3': S3Downloader,
        'https': HTTPDownloader,
        'ftp': FTPDownloader,
        'http': HTTPDownloader,
    }

    def __init__(self, download_directory='.', provider_settings_path=None, max_downloads=100,
                 save_path=False, **criteria):
        """
        `criteria` accepts the same keyword arguments as Django's `filter()` method.
        When filtering on time coverage, it is preferable to use timezone aware datetimes.
        `download_directory` should contain a pattern for the destination directory which is
        readable by 'strftime' of python.
        """
        self.max_downloads = max_downloads
        self.datasets = Dataset.objects.filter(**criteria)
        if not self.datasets:
            raise DownloadError("No dataset matches the search criteria")
        self.download_folder = download_directory
        self.save_path = save_path
        LOGGER.debug("Found %d datasets", self.datasets.count())
        if self.datasets.count() > self.max_downloads:
            raise ValueError("Too many datasets to download")

        provider_settings_path = provider_settings_path or os.path.join(
            os.path.dirname(__file__), 'provider_settings.yml')
        with open(provider_settings_path, 'rb') as file_handler:
            self.provider_settings = utils.yaml_env_safe_load(file_handler)

        self._downloaders_priorities =  {
            protocol: (priority, downloader)
            for priority, (protocol, downloader) in enumerate(self.DOWNLOADERS.items())
        }

    def get_provider_settings(self, url_prefix):
        """Finds and returns the settings for the provider matching the `url_prefix`"""
        for prefix in self.provider_settings:
            if prefix.startswith(url_prefix):
                return self.provider_settings[prefix]
        return {}

    @staticmethod
    def get_dataset_directory(dataset):
        """Get the directory where a dataset should be downloaded from
        its entry_id, splitting on potential path separators
        """
        return os.path.join(*re.split(r'/|\\', dataset.entry_id))

    @classmethod
    def already_downloaded(cls, dataset_directory):
        """Check if a dataset has already been downloaded"""
        if os.path.isdir(dataset_directory):
            dir_contents = os.listdir(dataset_directory)
            if len(dir_contents) == 1:
                return True
        return False

    def _download_from_uri(self, dataset_uri, downloader, directory):
        """Download the file(s) from `dataset_uri` to `directory`"""
        # Get the extra settings for the provider
        dataset_uri_prefix = "://".join(requests.utils.urlparse(dataset_uri.uri)[0:2])
        # Find provider settings
        extra_settings = self.get_provider_settings(dataset_uri_prefix)
        if extra_settings:
            LOGGER.debug("Loaded extra settings for provider %s: %s",
                         dataset_uri_prefix, extra_settings)
        # Launch download if the maximum number of parallel downloads has not been reached
        with DownloadLock(dataset_uri_prefix,
                          extra_settings.get('max_parallel_downloads'),
                          utils.REDIS_HOST, utils.REDIS_PORT) as acquired:
            if not acquired:
                raise TooManyDownloadsError(
                    f"Too many downloads in progress for {dataset_uri_prefix}")

            LOGGER.debug("Attempting to download from '%s'", dataset_uri.uri)
            file_name = None
            download_error = None
            try:
                file_name = downloader.check_and_download_url(
                    url=dataset_uri.uri, download_dir=directory,
                    **extra_settings)
            except DownloadError as error:
                LOGGER.warning(
                    ("Failed to download dataset %s from %s. "
                     "Another URL will be tried if possible"),
                    dataset_uri.dataset.pk, dataset_uri.uri, exc_info=True)
                download_error = error
                shutil.rmtree(directory, ignore_errors=True)
            except (FileNotFoundError, IsADirectoryError) as error:
                shutil.rmtree(directory, ignore_errors=True)
                raise DownloadError(
                    f"Could not write the downloaded file to {error.filename}") from error

            return file_name, download_error

    def sort_uris(self, uris):
        """Returns a list of tuples (DatasetURI, Downloader) sorted by
        priority. Priorities are defined by the order of Downloaders in
        self.DOWNLOADERS. URIs with the highest priority come first.
        """
        urls_by_priority = {i: [] for i in range(len(self.DOWNLOADERS))}
        for u in uris:
            protocol = urlparse(u.uri).scheme
            try:
                priority, downloader = self._downloaders_priorities[protocol]
            except KeyError:
                LOGGER.error("No downloader found for %s", u.uri, exc_info=True)
                continue
            urls_by_priority[priority].append((u, downloader))

        sorted_uris = list(itertools.chain.from_iterable(urls_by_priority.values()))
        if uris and not sorted_uris:
            raise RuntimeError(f'Could not find downloader for any of {uris}')
        return sorted_uris

    def download_dataset(self, dataset, download_directory):
        """
        Attempt to download a dataset by trying its URIs one by one. For each `DatasetURI`, it
        selects the appropriate Dowloader based on the URL scheme.
        Returns the downloaded file path if the download succeeds, an empty string otherwise.
        """
        errors = []
        dataset_directory = self.get_dataset_directory(dataset)  # relative to the download dir
        full_dataset_directory = os.path.join(download_directory,
                                              self.get_dataset_directory(dataset))
        file_name = None

        if self.already_downloaded(full_dataset_directory):
            file_name = os.listdir(full_dataset_directory)[0]
            dataset_path = os.path.join(dataset_directory, file_name)
            LOGGER.debug("Dataset %d is already present at %s",
                         dataset.pk, dataset_path)
        else:
            os.makedirs(full_dataset_directory, exist_ok=True)

            for dataset_uri, downloader in self.sort_uris(dataset.dataseturi_set.all()):
                file_name, download_error = self._download_from_uri(dataset_uri,
                                                                    downloader,
                                                                    full_dataset_directory)
                if file_name:
                    dataset_path = os.path.join(dataset_directory, file_name)
                    LOGGER.info("Successfully downloaded dataset %d to %s",
                                dataset_uri.dataset.pk, dataset_path)
                    break
                if download_error:
                    errors.append(download_error)

        if file_name:
            if self.save_path:
                dataset.dataseturi_set.get_or_create(
                    dataset=dataset,
                    uri='file://'+os.path.join(os.path.realpath(full_dataset_directory), file_name))
            return dataset_path
        else:
            shutil.rmtree(full_dataset_directory, ignore_errors=True)
            raise DatasetDownloadError(f"Failed to download dataset {dataset.pk}", errors=errors)

    def download(self):
        """Attempt to download all datasets (matching the criteria if any criteria defined). """
        files = []
        for dataset in self.datasets:
            appropriate_download_directory = dataset.time_coverage_start.strftime(
                str(self.download_folder))
            os.makedirs(appropriate_download_directory, exist_ok=True)
            files.append(self.download_dataset(dataset, appropriate_download_directory))
        return files

    def remove(self):
        """Remove downloaded dataset files"""
        removed = []
        for dataset in self.datasets:
            relative_download_dir = self.get_dataset_directory(dataset)
            download_dir = os.path.join(
                self.download_folder,
                relative_download_dir)
            if os.path.isdir(download_dir):
                shutil.rmtree(download_dir, ignore_errors=True)
                removed.append(relative_download_dir)
        return removed
