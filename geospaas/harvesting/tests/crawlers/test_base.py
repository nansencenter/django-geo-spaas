import logging
import unittest
import unittest.mock as mock

import requests

import geospaas.harvesting.crawlers.base as crawlers_base


class DatasetInfoTestCase(unittest.TestCase):
    """Tests for DatasetInfo"""

    def test_instanciation(self):
        """Test the correct creation of a DatasetInfo object"""
        dataset_info = crawlers_base.DatasetInfo('url', metadata={'foo': 'bar'})
        self.assertEqual(dataset_info.url, 'url')
        self.assertDictEqual(dataset_info.metadata, {'foo': 'bar'})

    def test_equality(self):
        """Test equality between two DatasetInfo objects"""
        self.assertEqual(
            crawlers_base.DatasetInfo('foo', {'bar': 'baz'}),
            crawlers_base.DatasetInfo('foo', {'bar': 'baz'}))
        self.assertNotEqual(
            crawlers_base.DatasetInfo('foo', {'bar': 'baz'}),
            crawlers_base.DatasetInfo('foo', {'bar': 'quz'}))

    def test_representation(self):
        """Test string reprensentation of DatasetInfo objects"""
        self.assertEqual(
            repr(crawlers_base.DatasetInfo('https://foo', {'a': 1})),
            "DatasetInfo(url='https://foo', metadata={'a': 1})")


class BaseCrawlerTestCase(unittest.TestCase):
    """Tests for the base Crawler"""

    def test_str(self):
        """Test string conversion"""
        class TestCrawler(crawlers_base.Crawler):
            name = 'test'

        self.assertEqual(
            str(TestCrawler.from_kwargs()),
            'test')

    def test_iter(self):
        """Test iterating over crawler"""
        crawler = crawlers_base.Crawler.from_kwargs()
        crawler.crawl = lambda: ['1', '2']
        self.assertListEqual(
            list(crawler),
            ['1', '2'])

    def test_abstract_crawl(self):
        """The crawl method should raise a NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            crawlers_base.Crawler.from_kwargs().crawl()

    def test_http_get_retry(self):
        """Test that _http_get retries the request when a connection
        error or a server error occurs
        """
        http_500_error = requests.HTTPError()
        http_500_error.response = mock.MagicMock(status_code=500)

        with mock.patch('geospaas.harvesting.utils.http_request') as mock_request, \
                mock.patch('time.sleep') as mock_sleep:
            mock_request.side_effect=(
                requests.ConnectionError,
                requests.ConnectTimeout,
                requests.ReadTimeout,
                http_500_error,
                mock.Mock())
            with self.assertLogs(crawlers_base.Crawler.logger, level=logging.WARNING):
                crawlers_base.Crawler.from_kwargs()._http_get('url', max_tries=5, wait_time=30)

            self.assertEqual(len(mock_request.mock_calls), 5)
            self.assertListEqual(mock_sleep.mock_calls, [mock.call(30 * (2**i)) for i in range(4)])

    def test_http_get_fails_eventually(self):
        """Test that _http_get retries the request when a connection
        error or a server error occurs, then logs an error and returns None
        if the problem persists
        """
        with mock.patch('geospaas.harvesting.utils.http_request') as mock_request, \
                mock.patch('time.sleep') as mock_sleep:
            mock_request.side_effect = requests.ConnectionError

            with self.assertLogs(crawlers_base.Crawler.logger, level=logging.WARNING), \
                 self.assertRaises(RuntimeError):
                crawlers_base.Crawler.from_kwargs()._http_get('url')

            self.assertEqual(len(mock_request.mock_calls), 5)
            self.assertEqual(len(mock_sleep.mock_calls), 5)

    def test_http_get_no_retry_error(self):
        """_http_get should not retry the request if the error is not a
        connection error or a server error
        """
        with mock.patch('geospaas.harvesting.utils.http_request') as mock_request:
            mock_request.side_effect = requests.TooManyRedirects
            with self.assertRaises(requests.RequestException):
                self.assertIsNone(crawlers_base.Crawler.from_kwargs()._http_get('url'))

    def test_http_get_error_on_404_status(self):
        """Test that an exception is raised in case of HTTP error code"""
        response = requests.Response()
        response.status_code = 404
        with mock.patch('geospaas.harvesting.utils.http_request') as mock_request:
            mock_request.side_effect = requests.HTTPError(response=response)
            with self.assertRaises(requests.HTTPError):
                crawlers_base.Crawler.from_kwargs()._http_get('http://foo')
