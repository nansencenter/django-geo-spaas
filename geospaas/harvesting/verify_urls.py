"""URLs verification module
Usage: verify_urls.py [-h] [-p PROVIDERS_CONF] {check,delete-stale} ...

Check and cleanup dataset URIs.

positional arguments:
  {check,delete-stale}
    check               Check all URIs present in the database. Write the
                        stale URIs to files in the output directory (one file
                        per provider).
    delete-stale        Delete the stale URLs present in the file given as
                        argument. The file should have the same structure as
                        one obtained by running this script with the --check
                        optionBy default, only URLs which return an HTTP error
                        404 are deleted. To override this behaviour and remove
                        URLs which return any kind of error, use the --force
                        option.

optional arguments:
  -h, --help            show this help message and exit
  -p PROVIDERS_CONF, --providers-conf PROVIDERS_CONF
                        Path to the providers configuration file.
"""
import argparse
import concurrent.futures
import ftplib
import logging
import os
import re
import socket
import time
from contextlib import closing
from datetime import datetime
from threading import BoundedSemaphore, Lock
from urllib.parse import urlparse

import django
import oauthlib.oauth2
import requests
import requests.auth
import requests.exceptions
import requests_oauthlib
import yaml

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geospaas.harvesting.settings')
django.setup()
from geospaas.catalog.models import DatasetURI  # pylint: disable=wrong-import-position

import geospaas.harvesting.utils as utils  # pylint: disable=wrong-import-position

logger = logging.getLogger('geospaas.harvesting.verify_urls')
logger.setLevel(logging.INFO)


ABSENT = 'absent'
PRESENT = 'present'


class TooManyRequests(Exception):
    """Exception raised when HTTP error 429 is repeatedly received from
    a provider
    """


class BoundedThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    """A ThreadPoolExecutor which has a limit on the number of jobs
    which can be submitted at once
    """

    def __init__(self, *args, queue_limit=10000, **kwargs):
        self.semaphore = BoundedSemaphore(kwargs.get('max_workers', 0) + queue_limit)
        super().__init__(*args, **kwargs)

    def submit(self, *args, **kwargs):
        func, *args = args
        self.semaphore.acquire()
        try:
            future = super().submit(func, *args, **kwargs)
        except:
            # if anything goes wrong, we need to release the semaphore
            self.semaphore.release()
            raise
        else:
            # release the semaphore once the thread ends
            future.add_done_callback(lambda x: self.semaphore.release())
            return future


class Provider():
    """Base Provider class that defines the interface that provider
    implementations should follow
    """

    def __init__(self, name, config):
        self.name = name
        self.config = config
        self._auth = None

    def __eq__(self, obj):
        return (isinstance(obj, self.__class__)
            and obj.name == self.name
            and obj.config == self.config)

    @property
    def auth(self):
        """Returns the right authentication object based on the current
        configuration
        """
        raise NotImplementedError

    def check_url(self, dataset_uri, **kwargs):
        """Check that the `dataset_uri` refers to a valid URL and
        returns the ABSENT or PRESENT constant
        """
        raise NotImplementedError

    def check_all_urls(self, file_name):
        """Check all the URLs for the current provider and writes to a
        file the problematic URLs
        """
        raise NotImplementedError

    @staticmethod
    def write_stale_url(file_name, url_state, dataset_uri_id, url):
        """Check the `dataset_uri` and write it to the output file if it is
        not valid. This is the function that runs in the checking threads.
        """
        logger.debug("Writing to %s", file_name)
        with open(file_name, 'a') as file_handle:
            file_handle.write(f"{url_state} {dataset_uri_id} {url}{os.linesep}")


class HTTPProvider(Provider):
    """Provider class that deals with FTP repositories"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._auth_start = None

    @staticmethod
    def build_oauth2(username, password, token_url, client_id):
        """Creates an OAuth2 object usable by requests.get()"""
        client = oauthlib.oauth2.LegacyApplicationClient(client_id=client_id)
        token = requests_oauthlib.OAuth2Session(client=client).fetch_token(
            token_url=token_url,
            username=username,
            password=password,
            client_id=client_id,
        )
        return requests_oauthlib.OAuth2(client_id=client_id, client=client, token=token)

    @property
    def auth(self):
        auth_renew = self.config.get('auth_renew')
        current_time = time.monotonic()
        if not self._auth or (auth_renew and current_time - self._auth_start >= auth_renew):
            self._auth_start = current_time
            if set(('username', 'password', 'token_url', 'client_id')).issubset(self.config):
                self._auth = self.build_oauth2(
                    self.config['username'], self.config['password'],
                    self.config['token_url'], self.config['client_id'],
                )
            elif set(('username', 'password')).issubset(self.config):
                self._auth = requests.auth.HTTPBasicAuth(
                    self.config['username'], self.config['password'])
        return self._auth

    def check_url(self, dataset_uri, **kwargs):
        throttle = self.config.get('throttle', 0)
        tries = kwargs.get('tries', 5)
        logger.debug("Sending HEAD request to %s", dataset_uri.uri)
        while tries > 0:
            try:
                with closing(utils.http_request(
                        'HEAD', dataset_uri.uri, allow_redirects=True, auth=self.auth)) as response:
                    status_code = response.status_code
                    headers = response.headers
            except requests.exceptions.ConnectionError:
                tries -= 1
                if tries <= 0:
                    raise
                else:
                    logger.error("Error when connecting to %s", dataset_uri.uri, exc_info=True)
                    time.sleep(5)
                    continue

            logger.debug("%d %s", status_code, dataset_uri.uri)

            # Too Many Requests: wait and retry
            if status_code == 429:
                tries -= 1
                if tries <= 0:
                    raise TooManyRequests(dataset_uri.uri)
                else:
                    logger.warning(
                        "Error 429 received from '%s'; retries left: %d", dataset_uri.uri, tries)
                    time.sleep(headers.get('Retry-After', 60))
            # other errors: return False
            elif status_code < 200 or status_code > 299:
                tries = 0
                if status_code == 404:
                    url_state = ABSENT
                else:
                    url_state = f"http_{status_code}"
            # no error: return True
            else:
                tries = 0
                url_state = PRESENT

        time.sleep(throttle)
        return url_state

    def check_and_write_stale_url(self, lock, file_name, dataset_uri):
        """Check the `dataset_uri` and write it to the output file if it is
        not valid. This is the function that runs in the checking threads.
        """
        url_state = self.check_url(dataset_uri)

        if url_state != PRESENT:
            logger.debug("Waiting for file lock")
            with lock:
                self.write_stale_url(file_name, url_state, dataset_uri.id, dataset_uri.uri)

    def check_all_urls(self, file_name):
        url_prefix = self.config['url']
        throttle = self.config.get('throttle', 0)
        max_workers = 1 if throttle else 50
        lock = Lock()
        futures = {}

        logger.info("Starting to check %s URLs", url_prefix)

        with BoundedThreadPoolExecutor(max_workers=max_workers,
                                       queue_limit=2000) as thread_executor:
            for dataset_uri in DatasetURI.objects.filter(uri__startswith=url_prefix).iterator():
                futures[thread_executor.submit(
                    self.check_and_write_stale_url,
                    lock,
                    file_name,
                    dataset_uri)] = dataset_uri.uri

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                finally:
                    del futures[future]
        logger.info("Finished checking %s URLs", url_prefix)


class FTPProvider(Provider):
    """Provider class that deals with FTP repositories"""

    network_errors = (
        ConnectionResetError,
        socket.gaierror,
        socket.herror,
        socket.timeout,
        EOFError
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ftp_client = None

    @property
    def auth(self):
        if not self._auth:
            if set(('username', 'password')).issubset(self.config):
                self._auth = {'user': self.config['username'], 'passwd': self.config['password']}
            else:
                self._auth = {'user': '', 'passwd': ''}
        return self._auth

    @property
    def ftp_client(self):
        """Initialize an FTP client if necessary, or return the
        existing one
        """
        if not self._ftp_client:
            self._ftp_client = ftplib.FTP()
            self.ftp_connect()
        return self._ftp_client

    def ftp_connect(self, timeout=5, retries=5):
        """Connect to the remote FTP host. This should be used
        directly only when the connection needs to be re-established
        after a problem
        """
        host = urlparse(self.config['url']).netloc
        wait = 5
        while retries > 0:
            try:
                self.ftp_client.connect(host, timeout=timeout)
                self.ftp_client.login(**self.auth)
                retries = 0
            except self.network_errors:
                retries -= 1
                if retries <= 0:
                    logger.error("Could not connect to %s", host, exc_info=True)
                    raise
                else:
                    time.sleep(wait)
                    wait += 1

    def check_url(self, dataset_uri, **kwargs):
        logger.debug('Checking %s', dataset_uri.uri)
        remote_path = urlparse(dataset_uri.uri).path
        retries = 5
        while retries > 0:
            try:
                path_list = self.ftp_client.nlst(remote_path)
                retries = 0
            except self.network_errors:
                retries -= 1
                if retries <= 0:
                    logger.error("Could not execute NLST command", exc_info=True)
                    raise
                else:
                    time.sleep(5)
                    self.ftp_connect()

        if path_list and path_list[0] == remote_path:
            return PRESENT
        else:
            return ABSENT

    def check_all_urls(self, file_name):
        url_prefix = self.config['url']
        logger.info("Starting to check %s URLs", url_prefix)
        for dataset_uri in DatasetURI.objects.filter(uri__startswith=url_prefix).iterator():
            url_state = self.check_url(dataset_uri)
            if url_state != PRESENT:
                logger.debug("%s is not valid", dataset_uri.uri)
                self.write_stale_url(file_name, url_state, dataset_uri.id, dataset_uri.uri)


def check_providers(output_directory, providers):
    """Check the URLs for each provider in a separate process"""
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {}
        for provider in providers:
            results_file_name = os.path.join(
                output_directory,
                f"{provider.name}_stale_urls_{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}.txt"
            )
            futures[executor.submit(
                provider.check_all_urls,
                results_file_name
            )] = provider.config['url']

        success = True
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except:  # pylint: disable=bare-except
                success = False
                logger.error("An error occurred while checking '%s'",
                             futures[future], exc_info=True)
        return success


def find_provider(urls_file_path, providers):
    """Find the provider given the name of a file resulting from the
    'check' action
    """
    provider_name_match = re.match(
        r'^(.*)_stale_urls_\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.txt$',
        os.path.basename(urls_file_path))
    if provider_name_match:
        provider_name = provider_name_match.group(1)
        for provider in providers:
            if provider.name == provider_name:
                return provider
    return None


def remove_dataset_uri(dataset_uri):
    """Remove a DatasetURI and the corresponding Dataset, if it has no
    URIs anymore
    """
    removed_uri = removed_dataset = False

    logger.debug("Removing dataset URI %d, %s", dataset_uri.id, dataset_uri.uri)
    removed_uri = dataset_uri.delete()[0] == 1

    dataset = dataset_uri.dataset
    remove_dataset = not dataset.dataseturi_set.all()  # .all() is needed to refresh the queryset
    if remove_dataset:
        logger.debug("Removing dataset %d", dataset.id)
        removed_dataset = dataset.delete()[0] == 1

    return (removed_uri, removed_dataset)


def delete_stale_urls(urls_file_path, providers, force=False):
    """Re-check the URLs contained in a file issued from the checking
    step, then remove them.
    """
    provider = find_provider(urls_file_path, providers)

    deleted_uris_count = 0
    deleted_datasets_count = 0
    with open(urls_file_path, 'r') as urls_file:
        for line in urls_file:
            _, dataset_uri_id, _ = line.split()
            dataset_uri_queryset = DatasetURI.objects.filter(id=int(dataset_uri_id))
            if dataset_uri_queryset:
                dataset_uri = dataset_uri_queryset[0]
                url_state = provider.check_url(dataset_uri)
                if url_state != PRESENT and (url_state == ABSENT or force):
                    removed_uri, removed_dataset = remove_dataset_uri(dataset_uri)
                    if removed_uri:
                        deleted_uris_count += 1
                    if removed_dataset:
                        deleted_datasets_count += 1
            else:
                logger.warning("Could not remove DatasetURI with ID %s",
                               dataset_uri_id, exc_info=True)
    return (deleted_uris_count, deleted_datasets_count)


def get_provider(name, config):
    """Instantiate the right type of provider for the given config"""
    if config['url'].startswith('ftp'):
        return FTPProvider(name, config)
    elif config['url'].startswith('http'):
        return HTTPProvider(name, config)
    else:
        raise ValueError("Unknown type of provider")


def read_config(config_path):
    """Read the configuration file and builds a list of providers
    """
    yaml.SafeLoader.add_constructor('!ENV', lambda loader, node: os.getenv(node.value))
    with open(config_path, 'r') as config_file:
        providers_config = yaml.safe_load(config_file)

    providers = []
    for name, config in providers_config.items():
        providers.append(get_provider(name, config))

    return providers


def parse_cli_arguments():
    """Parse the arguments given on the command line"""
    parser = argparse.ArgumentParser(description='Check and cleanup dataset URIs.')
    parser.add_argument(
        '-p', '--providers-conf',
        default=os.path.join(os.path.dirname(__file__), 'check.yml'),
        help='Path to the providers configuration file.')

    sub_parsers = parser.add_subparsers(dest='action', required=True)

    check_parser = sub_parsers.add_parser(
        'check',
        help=('Check all URIs present in the database. Write the stale URIs to files in the '
              'output directory (one file per provider).'))
    check_parser.add_argument(
        '-o', '--output-directory',
        default='.',
        help='Path to the directory where the output files will be created')

    delete_parser = sub_parsers.add_parser(
        'delete-stale',
        help=('Delete the stale URLs present in the file given as argument. The file should have '
              'the same structure as one obtained by running this script with the --check option'
              'By default, only URLs which return an HTTP error 404 are deleted. To override this '
              'behaviour and remove URLs which return any kind of error, use the --force option.'))
    delete_parser.add_argument(
        'urls_file',
        help='Path to the file containing the URls to delete.')
    delete_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Remove URLs which return any error, not just 404')

    return parser.parse_args()


def main():
    """Runs one process per provider, which checks the URLs for this
    provider
    """
    args = parse_cli_arguments()
    providers = read_config(args.providers_conf)

    if args.action == 'check':
        if check_providers(args.output_directory, providers):
            logger.info("Finished checking all URLs")
    elif args.action == 'delete-stale':
        logger.info("Deleting URLs from %s", args.urls_file)
        deleted_counts = delete_stale_urls(args.urls_file, providers)
        logger.info("Deleted %d URIs and %d datasets", *deleted_counts)


if __name__ == '__main__':
    main()  # pragma: no cover
