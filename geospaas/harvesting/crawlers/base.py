"""
A set of crawlers used to explore data provider interfaces and get resources URLs. Each crawler
should inherit from the Crawler class and implement the abstract methods defined in Crawler.
"""

import logging
import time

import requests

import geospaas.harvesting.arguments as arguments
import geospaas.harvesting.utils as utils


logging.getLogger(__name__).addHandler(logging.NullHandler())


class DatasetInfo():
    """Class used to store dataset information coming from crawled repositories
    url is a string, metadata is a dict
    """
    def __init__(self, url, metadata=None):
        self.url = url
        if metadata is None:
            self.metadata = {}
        else:
            self.metadata = metadata

    def __repr__(self):
        return f"DatasetInfo(url='{self.url}', metadata={self.metadata})"

    def __eq__(self, other):
        return self.url == other.url and self.metadata == other.metadata


class Crawler():
    """Base Crawler class"""

    name = None

    logger = logging.getLogger(__name__ + '.Crawler')
    argument_parser = arguments.ArgumentParser([
        arguments.SequenceArgument('time_range',
            contents_type=arguments.DatetimeArgument,
            length=2,
            default=(None, None)),
        arguments.WKTArgument('location', default=None),
        arguments.StringArgument('username', default=None),
        arguments.StringArgument('password', default=None),
    ])

    def __init__(self, **kwargs):
        self.time_range = kwargs['time_range']
        self.location = kwargs['location']
        self.username = kwargs['username']
        self.password = kwargs['password']

    def __str__(self):
        return self.name

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"location={self.location}, "
                f"time_range={self.time_range}, "
                f"username={self.username}, "
                f"password=******"
                ")")

    @classmethod
    def from_config(cls, config: dict):
        """Instantiate a crawler from a configuration dictionary"""
        return cls(**cls.argument_parser.parse(config))

    @classmethod
    def from_kwargs(cls, **kwargs):
        """Instantiate a crawler from a configuration dictionary"""
        return cls(**cls.argument_parser.parse(kwargs))

    # ------------- crawl ------------
    def __iter__(self):
        return iter(self.crawl())

    def crawl(self):
        """Generator which crawls through a dataset repository and yields
        DatasetInfo objects
        """
        raise NotImplementedError()

    def _http_get(self, url, request_parameters=None, max_tries=5, wait_time=5):
        """Sends an HTTP GET request, retry in case of failure"""
        self.logger.debug("Getting page: '%s'", url)

        last_error = None
        for try_index in range(max_tries):
            try:
                response = utils.http_request('GET', url, **request_parameters or {})
                response.raise_for_status()
                return response
            except (requests.ConnectionError, requests.HTTPError, requests.Timeout) as error:
                # retry only for connection errors and HTTP errors 5**
                if (isinstance(error, requests.HTTPError) and
                        (error.response.status_code < 500 or error.response.status_code > 599)):
                    raise
                else:
                    last_error = error
                    self.logger.warning('Error while sending request to %s, %d retries left',
                                        url, max_tries - try_index - 1, exc_info=True)
            time.sleep(wait_time)
            wait_time *= 2
        raise RuntimeError(f"Max retries reached trying to get {url}") from last_error
