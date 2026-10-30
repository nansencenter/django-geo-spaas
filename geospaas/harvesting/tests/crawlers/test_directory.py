import ftplib
import logging
import os
import re
import unittest
import unittest.mock as mock
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import ParseResult

import numpy as np
import requests

import geospaas.harvesting.crawlers.base as crawlers_base
import geospaas.harvesting.crawlers.directory as crawlers_directory


class DirectoryCrawlerTestCase(unittest.TestCase):
    """Tests for the DirectoryCrawler"""

    def test_instantiation(self):
        """Test the correct instantiation of a DirectoryCrawler
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(
            url='https://foo/bar.nc',
            time_range=(
                datetime(2020, 1, 1, tzinfo=timezone.utc),
                datetime(2020, 1, 2, tzinfo=timezone.utc)),
            include='.*')
        crawler.set_initial_state()
        self.assertIsInstance(crawler, crawlers_base.Crawler)
        self.assertEqual(
            crawler.root_url,
            ParseResult(scheme='https', netloc='foo', path='/bar.nc',
                        params='', query='', fragment=''))
        self.assertSequenceEqual(
            crawler.time_range,
            (datetime(2020, 1, 1, tzinfo=timezone.utc),
             datetime(2020, 1, 2, tzinfo=timezone.utc)))
        self.assertListEqual(crawler._to_process, ['/bar.nc'])

    def test_repr(self):
        """Test string representation"""
        self.assertEqual(
            repr(crawlers_directory.DirectoryCrawler.from_kwargs(
                url='https://foo',
                time_range=(datetime(2025, 1, 1), datetime(2025, 1, 2)),
                include='\.nc$',
                username='user',
                password='pass')),
            "DirectoryCrawler("
                "url='https://foo', "
                "include='\.nc$', "
                "time_range=(datetime.datetime(2025, 1, 1, 0, 0, tzinfo=datetime.timezone.utc), "
                            "datetime.datetime(2025, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)), "
                "username='user', "
                "password='******')")

    def test_equality(self):
        """Test equality of two DirectoryCrawler objects"""
        self.assertEqual(
            crawlers_directory.DirectoryCrawler.from_kwargs(
                url='http://foo', time_range=(datetime(2024, 1, 2), datetime(2024, 1, 3)),
                include=r'.*\.nc', username='user', password='pass'),
            crawlers_directory.DirectoryCrawler.from_kwargs(
                url='http://foo', time_range=(datetime(2024, 1, 2), datetime(2024, 1, 3)),
                include=r'.*\.nc', username='user', password='pass'))
        self.assertNotEqual(
            crawlers_directory.DirectoryCrawler.from_kwargs(
                url='http://foo', time_range=(datetime(2024, 1, 2), datetime(2024, 1, 3)),
                include=r'.*\.nc', username='user', password='pass'),
            crawlers_directory.DirectoryCrawler.from_kwargs(
                url='http://foo', time_range=(datetime(2024, 1, 2), datetime(2024, 1, 3)),
                include=r'.*\.nc', username='user', password='password'))

    def test_http_get_with_auth(self):
        """If no username and password are provided, HTTP requests
        should not have an 'auth' parameter
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(
            url='', username='user', password='pass')
        with mock.patch('geospaas.harvesting.crawlers.Crawler._http_get') as mock_get:
            crawler._http_get('http://foo/bar')
            crawler._http_get('http://foo/bar', request_parameters={'quz': 'qux'})
        mock_get.assert_has_calls((
            mock.call('http://foo/bar', request_parameters={'auth': ('user', 'pass')},
                      max_tries=5, wait_time=5),
            mock.call('http://foo/bar', request_parameters={'quz': 'qux', 'auth': ('user', 'pass')},
                      max_tries=5, wait_time=5),
        ))

    def test_http_get_no_auth(self):
        """If no username and password are provided, HTTP requests
        should not have an 'auth' parameter
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(url='')
        with mock.patch('geospaas.harvesting.crawlers.Crawler._http_get') as mock_get:
            crawler._http_get('http://foo/bar')
        mock_get.assert_called_with('http://foo/bar', request_parameters=None,
                                    max_tries=5, wait_time=5)

    def test_abstract_list_folder_contents(self):
        """
        A NotImplementedError should be raised if the _list_folder_contents() method
        is accessed directly on the DirectoryCrawler class
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(url='')
        with self.assertRaises(NotImplementedError):
            crawler._list_folder_contents('')

    def test_is_folder(self):
        """
        A NotImplementedError should be raised if the _is_folder() method
        is accessed directly on the DirectoryCrawler class
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(url='')
        with self.assertRaises(NotImplementedError):
            crawler._is_folder('')

    def test_get_download_url(self):
        """
        The get_download_url() method of the DirectoryCrawler
        should return the resource URL unchanged
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(url='https://foo')
        self.assertEqual(crawler.get_download_url('bar'), 'https://foo/bar')

    def test_base_url(self):
        """The base_url property should return the root_url without path"""
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(url='http://foo/bar')
        self.assertEqual(crawler.base_url, 'http://foo')

    def test_set_initial_state(self):
        """set_initial_state() should set the right values for _urls and _to_process"""
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(url='http://foo/bar')
        crawler._results = None
        crawler._to_process = None
        crawler.set_initial_state()
        self.assertListEqual(crawler._to_process, ['/bar'])

    def test_add_folder_to_process(self):
        """_add_folder_to_process() should add the path of the folder
        if it fits in the time range constraint
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(url='http://foo/bar')
        crawler.logger = mock.Mock()
        crawler._to_process = []
        crawler._add_folder_to_process('/bar/baz')
        self.assertListEqual(crawler._to_process, ['/bar/baz'])

    def test_process_folder_with_file(self):
        """_process_folder() should feed the _urls stack
        with only file paths which are included
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(
            url='http://foo/bar', include='\.nc$')
        crawler.EXCLUDE = re.compile(r'\.h5$')
        crawler.logger = mock.Mock()
        with mock.patch.object(crawler, '_list_folder_contents') as mock_folder_contents, \
                mock.patch.object(crawler, '_is_folder', return_value=False), \
                mock.patch.object(crawler, 'get_raw_attributes', return_value={}):
            mock_folder_contents.return_value = ['/bar/baz.nc', '/bar/qux.gz']
            self.assertSequenceEqual(
                list(crawler._process_folder('')),
                [crawlers_base.DatasetInfo('http://foo/bar/baz.nc')])

    def test_process_folder_with_folder(self):
        """_process_folder() should feed the _to_process stack
        with folder paths which are not excluded
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(
            url='http://foo/bar', include='baz')
        crawler.EXCLUDE = re.compile(r'qux')
        crawler.logger = mock.Mock()
        with mock.patch.object(crawler, '_list_folder_contents') as mock_folder_contents, \
                mock.patch.object(crawler, '_is_folder', return_value=True), \
                mock.patch.object(crawler, '_add_folder_to_process') as mock_add_folder:
            mock_folder_contents.return_value = ['/bar/baz', '/bar/qux']
            list(crawler._process_folder(''))
        mock_add_folder.assert_called_once_with('/bar/baz')

    def test_get_year_folder_coverage(self):
        """Get the correct time range from a year folder"""
        self.assertEqual(
            crawlers_directory.DirectoryCrawler._folder_coverage(
                'https://test-opendap.com/folder/2019/contents.html'),
            (datetime(2019, 1, 1, tzinfo=timezone.utc), datetime(2020, 1, 1, tzinfo=timezone.utc))
        )

    def test_get_month_folder_coverage(self):
        """Get the correct time range from a month folder"""
        self.assertEqual(
            crawlers_directory.DirectoryCrawler._folder_coverage(
                'https://test-opendap.com/folder/2019/02/contents.html'),
            (datetime(2019, 2, 1, tzinfo=timezone.utc), datetime(2019, 3, 1, tzinfo=timezone.utc))
        )
        self.assertEqual(
            crawlers_directory.DirectoryCrawler._folder_coverage(
                'https://test-opendap.com/folder/201902/contents.html'),
            (datetime(2019, 2, 1, tzinfo=timezone.utc), datetime(2019, 3, 1, tzinfo=timezone.utc))
        )

    def test_get_day_of_month_folder_coverage(self):
        """Get the correct time range from a day of month folder"""
        self.assertEqual(
            crawlers_directory.DirectoryCrawler._folder_coverage(
                'https://test-opendap.com/folder/2019/02/14/contents.html'),
            (datetime(2019, 2, 14, tzinfo=timezone.utc), datetime(2019, 2, 15, tzinfo=timezone.utc))
        )
        self.assertEqual(
            crawlers_directory.DirectoryCrawler._folder_coverage(
                'https://test-opendap.com/folder/20190214/contents.html'),
            (datetime(2019, 2, 14, tzinfo=timezone.utc), datetime(2019, 2, 15, tzinfo=timezone.utc))
        )

    def test_get_day_of_year_folder_coverage(self):
        """Get the correct time range from a day of year folder"""
        self.assertEqual(
            crawlers_directory.DirectoryCrawler._folder_coverage(
                'https://test-opendap.com/folder/2019/046/contents.html'),
            (datetime(2019, 2, 15, tzinfo=timezone.utc), datetime(2019, 2, 16, tzinfo=timezone.utc))
        )

    def test_none_when_no_folder_coverage(self):
        """
        The `_folder_coverage` method should return `None` if no time range is inferred from the
        folder's path
        """
        self.assertEqual(
            crawlers_directory.DirectoryCrawler._folder_coverage(
                'https://test-opendap.com/folder/contents.html'), (None, None))
        self.assertEqual(
            crawlers_directory.DirectoryCrawler._folder_coverage(
                'https://test-opendap.com/folder/046/contents.html'),
            (None, None)
        )
        self.assertEqual(
            crawlers_directory.DirectoryCrawler._folder_coverage(
                'https://test-opendap.com/folder/02/contents.html'),
            (None, None)
        )

    def test_intersects_time_range_finite_limits(self):
        """
        Test the behavior of the `_intersects_time_range` method with a finite time range limitation
        `time_range[0]` and `time_range[1]` are the limits defined in the crawler
        `start_time` and `stop_time` are the limits of the time range which is tested against the
        crawler's condition
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(
            url='', time_range=(datetime(2019, 2, 14), datetime(2019, 2, 20)))

        # start_time < time_range[0] < stop_time < time_range[1]
        self.assertTrue(crawler._intersects_time_range(
            datetime(2019, 2, 10, tzinfo=timezone.utc), datetime(2019, 2, 17, tzinfo=timezone.utc)))
        # start_time < time_range[0] == stop_time < time_range[1]
        self.assertTrue(crawler._intersects_time_range(
            datetime(2019, 2, 10, tzinfo=timezone.utc), datetime(2019, 2, 14, tzinfo=timezone.utc)))
        # time_range[0] < start_time < time_range[1] < stop_time
        self.assertTrue(crawler._intersects_time_range(
            datetime(2019, 2, 17, tzinfo=timezone.utc), datetime(2019, 2, 25, tzinfo=timezone.utc)))
        # time_range[0] < start_time == time_range[1] < stop_time
        self.assertTrue(crawler._intersects_time_range(
            datetime(2019, 2, 20, tzinfo=timezone.utc), datetime(2019, 2, 25, tzinfo=timezone.utc)))
        # time_range[0] < start_time < stop_time < time_range[1]
        self.assertTrue(crawler._intersects_time_range(
            datetime(2019, 2, 15, tzinfo=timezone.utc), datetime(2019, 2, 19, tzinfo=timezone.utc)))
        # start_time < time_range[0] < time_range[1] < stop_time
        self.assertTrue(crawler._intersects_time_range(
            datetime(2019, 2, 13, tzinfo=timezone.utc), datetime(2019, 2, 25, tzinfo=timezone.utc)))
        # start_time < stop_time < time_range[0] < time_range[1]
        self.assertFalse(crawler._intersects_time_range(
            datetime(2019, 2, 10, tzinfo=timezone.utc), datetime(2019, 2, 13, tzinfo=timezone.utc)))
        # time_range[0] < time_range[1] < start_time < stop_time
        self.assertFalse(crawler._intersects_time_range(
            datetime(2019, 2, 25, tzinfo=timezone.utc), datetime(2019, 2, 26, tzinfo=timezone.utc)))
        # no start_time < time_range[0] < time_range[1] < stop_time
        self.assertTrue(
            crawler._intersects_time_range(None, datetime(2019, 2, 27, tzinfo=timezone.utc)))
        # no start_time < time_range[0] < stop_time < time_range[1]
        self.assertTrue(
            crawler._intersects_time_range(None, datetime(2019, 2, 17, tzinfo=timezone.utc)))
        # no start_time < stop_time < time_range[0] < time_range[1]
        self.assertFalse(
            crawler._intersects_time_range(None, datetime(2019, 2, 10, tzinfo=timezone.utc)))
        # start_time < time_range[0] < time_range[1] < no stop time
        self.assertTrue(
            crawler._intersects_time_range(datetime(2019, 2, 10, tzinfo=timezone.utc), None))
        # time_range[0] < start_time < time_range[1] < no stop time
        self.assertTrue(
            crawler._intersects_time_range(datetime(2019, 2, 18, tzinfo=timezone.utc), None))
        # time_range[0] < time_range[1] < start_time < no stop time
        self.assertFalse(
            crawler._intersects_time_range(datetime(2019, 2, 21, tzinfo=timezone.utc), None))

    def test_intersects_time_range_no_lower_limit(self):
        """
        Test the behavior of the `_intersects_time_range` method without a lower limit for the
        crawler's time range.
        `time_range[1]` is the upper limit defined in the crawler
        `start_time` and `stop_time` are the limits of the time range which is tested against the
        crawler's condition
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(
            url='', time_range=(None, datetime(2019, 2, 20, tzinfo=timezone.utc)))

        # no lower limit < time_range[1] < start_time < stop_time
        self.assertFalse(crawler._intersects_time_range(
            datetime(2019, 2, 25, tzinfo=timezone.utc), datetime(2019, 2, 26, tzinfo=timezone.utc)))
        # no lower limit < start_time < time_range[1] < stop_time
        self.assertTrue(crawler._intersects_time_range(
            datetime(2019, 2, 18, tzinfo=timezone.utc), datetime(2019, 2, 26, tzinfo=timezone.utc)))
        # no lower limit < start_time < stop_time < time_range[1]
        self.assertTrue(crawler._intersects_time_range(
            datetime(2019, 2, 18, tzinfo=timezone.utc), datetime(2019, 2, 19, tzinfo=timezone.utc)))
        # no lower limit and no start time
        self.assertTrue(
            crawler._intersects_time_range(None, datetime(2019, 2, 21, tzinfo=timezone.utc)))
        # no lower limit and no stop_time, with intersection
        self.assertTrue(
            crawler._intersects_time_range(datetime(2019, 2, 19, tzinfo=timezone.utc), None))
        # no lower limit and no stop_time, without intersection
        self.assertFalse(
            crawler._intersects_time_range(datetime(2019, 2, 21, tzinfo=timezone.utc), None))

    def test_intersects_time_range_no_upper_limit(self):
        """
        Test the behavior of the `_intersects_time_range` method without an upper limit for the
        crawler's time range.
        `time_range[0]` is the upper limit defined in the crawler
        `start_time` and `stop_time` are the limits of the time range which is tested against the
        crawler's condition
        """
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(
            url='', time_range=(datetime(2019, 2, 20), None))

        # start_time < stop_time < time_range[0] < no upper limit
        self.assertFalse(crawler._intersects_time_range(
            datetime(2019, 2, 10, tzinfo=timezone.utc), datetime(2019, 2, 15, tzinfo=timezone.utc)))
        # start_time < time_range[0] < stop_time < no upper limit
        self.assertTrue(crawler._intersects_time_range(
            datetime(2019, 2, 18, tzinfo=timezone.utc), datetime(2019, 2, 26, tzinfo=timezone.utc)))
        # time_range[0] < start_time < stop_time < no upper limit
        self.assertTrue(crawler._intersects_time_range(
            datetime(2019, 2, 21, tzinfo=timezone.utc), datetime(2019, 2, 25, tzinfo=timezone.utc)))
        # no upper limit and no stop_time
        self.assertTrue(
            crawler._intersects_time_range(datetime(2019, 2, 21, tzinfo=timezone.utc), None))
        # no upper limit and no start_time, with intersection
        self.assertTrue(
            crawler._intersects_time_range(None, datetime(2019, 2, 21, tzinfo=timezone.utc)))
        # no upper limit and no start_time, without intersection
        self.assertFalse(
            crawler._intersects_time_range(None, datetime(2019, 2, 19, tzinfo=timezone.utc)))

    def test_crawl(self):
        """Test crawling"""
        crawler = crawlers_directory.DirectoryCrawler.from_kwargs(url='https://foo/bar.nc')

        with mock.patch.object(crawler, '_process_folder') as mock_process_folder:
            mock_process_folder.return_value = ['foo', 'bar']
            generator = crawler.crawl()
            self.assertEqual(next(generator), 'foo')
            self.assertEqual(next(generator), 'bar')
            with self.assertRaises(StopIteration):
                next(generator)
            mock_process_folder.assert_called()


class LocalDirectoryCrawlerTestCase(unittest.TestCase):
    """Tests for LocalDirectoryCrawler"""

    def setUp(self):
        self.crawler = crawlers_directory.LocalDirectoryCrawler.from_kwargs(url='')

    def test_list_folder_contents(self):
        """_list_folder_contents() should return the absolute
        path of all files contained in the folder"""
        with mock.patch('os.listdir', return_value=['foo', 'bar', 'baz']), \
                mock.patch.object(self.crawler, '_is_folder', return_value=True):
            base_dir_name = 'base_dir'
            self.assertListEqual(
                self.crawler._list_folder_contents(base_dir_name),
                [
                    os.path.join(base_dir_name, 'foo'),
                    os.path.join(base_dir_name, 'bar'),
                    os.path.join(base_dir_name, 'baz'),
                ]
            )

    def test_list_folder_contents_file_path(self):
        """When given a file path, _list_folder_contents() should
        return a list containing only this file path
        """
        with mock.patch.object(self.crawler, '_is_folder', return_value=False):
            file_path = '/foo/bar.nc'
            self.assertListEqual(
                self.crawler._list_folder_contents(file_path),
                [file_path]
            )

    def test_is_folder(self):
        """_is_folder() should return True if the
        path points to a folder, False otherwise"""
        with mock.patch('os.path.isdir', return_value=True):
            self.assertTrue(self.crawler._is_folder(''), "_is_folder() should return True")
        with mock.patch('os.path.isdir', return_value=False):
            self.assertFalse(self.crawler._is_folder(''), "_is_folder() should return False")


class HTMLDirectoryCrawlerTestCase(unittest.TestCase):
    """Tests for the HTMLDirectoryCrawler crawler"""

    def test_strip_folder_page(self):
        """_strip_folder_page() should remove the index page from a
        folder path
        """
        self.assertEqual(
            crawlers_directory.HTMLDirectoryCrawler._strip_folder_page('/foo/bar/contents.html'),
            '/foo/bar')
        self.assertEqual(
            crawlers_directory.HTMLDirectoryCrawler._strip_folder_page('/foo/bar/'),
            '/foo/bar')
        self.assertEqual(
            crawlers_directory.HTMLDirectoryCrawler._strip_folder_page('/foo/bar'),
            '/foo/bar')

    def test_get_right_number_of_links(self):
        """Test that the crawler gets the correct number of links from a test page"""
        with open(os.path.join(
                os.path.dirname(__file__), '..', 'data', 'opendap', 'root.html')) as data_file:
            html = data_file.read()
        self.assertEqual(len(crawlers_directory.HTMLDirectoryCrawler._get_links(html)), 4)

        with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'empty.html')) as data_file:
            html = data_file.read()
        self.assertEqual(len(crawlers_directory.HTMLDirectoryCrawler._get_links(html)), 0)

    def test_link_extractor_error(self):
        """In case of error, LinkExtractor must use a logger"""
        parser = crawlers_directory.LinkExtractor()
        with self.assertLogs(parser.logger, level=logging.ERROR):
            parser.error('some message')

    def test_prepend_parent_path(self):
        """
        Should prepend all the paths with the parent_path, except if they already start with it
        """
        parent_path = '/foo'
        paths = ['/foo/bar', 'baz', 'https://external/site']
        self.assertEqual(
            crawlers_directory.HTMLDirectoryCrawler._prepend_parent_path(parent_path, paths),
            ['/foo/bar', '/foo/baz']
        )

    def test_list_folder_contents(self):
        """Test listing a folder's contents"""
        with mock.patch('geospaas.harvesting.crawlers.Crawler._http_get') as mock_http_get:
            mock_http_get.return_value.text = (
                '<html>'
                '<a href="bar/contents.html">folder/</a>'
                '<a href="baz/">folder/</a>'
                '<html/>')
            crawler = crawlers_directory.HTMLDirectoryCrawler.from_kwargs(url='')
            self.assertListEqual(
                crawler._list_folder_contents('/foo/contents.html'),
                ['/foo/bar/contents.html', '/foo/baz/'])

    def test_list_folder_contents_no_auth(self):
        """If no username and password are provided, HTTP requests
        should not have an 'auth' parameter
        """
        with mock.patch('geospaas.harvesting.crawlers.Crawler._http_get') as mock_http_get:
            mock_http_get.return_value.text = '<html><html/>'
            crawler = crawlers_directory.HTMLDirectoryCrawler.from_kwargs(url='http://foo')
            crawler._list_folder_contents('/bar')
            mock_http_get.assert_called_once_with('http://foo/bar', request_parameters={},
                                                  max_tries=5, wait_time=5)

    def test_list_folder_contents_with_auth(self):
        """If a username and password are provided, HTTP requests
        should have an 'auth' parameter
        """
        with mock.patch('geospaas.harvesting.crawlers.Crawler._http_get') as mock_http_get:
            mock_http_get.return_value.text = '<html><html/>'
            crawler = crawlers_directory.HTMLDirectoryCrawler.from_kwargs(
                url='http://foo', username='user', password='pass')
            crawler._list_folder_contents('/bar')
        mock_http_get.assert_called_once_with('http://foo/bar',
                                              request_parameters={'auth': ('user', 'pass')},
                                              max_tries=5, wait_time=5)


class OpenDAPCrawlerTestCase(unittest.TestCase):
    """Tests for the OpenDAP crawler"""

    TEST_DATA = {
        'root': {
            'urls': ["https://test-opendap.com"],
            'file_path': "../data/opendap/root.html"},
        'root_duplicates': {
            'urls': ["https://test2-opendap.com"],
            'file_path': "../data/opendap/root_duplicates.html"},
        'dataset': {
            'urls': [
                'https://test-opendap.com/dataset.nc',
                'https://test2-opendap.com/dataset.nc',
                'https://test-opendap.com/folder/dataset.nc',
                'https://test-opendap.com/folder/2019/02/14/20190214120000_dataset.nc',
                'https://test-opendap.com/folder/2019/02/14/20190214000000_dataset.nc'
            ],
            'file_path': None},
        'full_ddx': {
            'urls': ["https://opendap.jpl.nasa.gov/opendap/full_dataset.nc.ddx"],
            'file_path': "../data/opendap/full_ddx.xml"},
        'short_ddx': {
            'urls': ["https://test-opendap.com/short_dataset.nc.ddx"],
            'file_path': "../data/opendap/short_ddx.xml"},
        'no_ns_ddx': {
            'urls': ["https://test-opendap.com/no_ns_dataset.nc.ddx"],
            'file_path': "../data/opendap/ddx_no_ns.xml"},
        'folder': {
            'urls': [
                'https://test-opendap.com/folder/contents.html',
                'https://test2-opendap.com/folder/contents.html'
            ],
            'file_path': '../data/opendap/folder/contents.html'},
        'folder_year': {
            'urls': ['https://test-opendap.com/folder/2019/contents.html'],
            'file_path': '../data/opendap/folder/2019/contents.html'},
        'folder_month': {
            'urls': ['https://test-opendap.com/folder/2019/02/contents.html'],
            'file_path': '../data/opendap/folder/2019/02/contents.html'},
        'folder_day_of_month': {
            'urls': ['https://test-opendap.com/folder/2019/02/14/contents.html'],
            'file_path': '../data/opendap/folder/2019/02/14/contents.html'},
        'folder_day_of_year': {
            'urls': ['https://test-opendap.com/folder/2019/046/contents.html'],
            'file_path': '../data/opendap/folder/2019/046/contents.html'},
        'empty': {
            'urls': ['http://empty.com'],
            'file_path': '../data/empty.html'},
        'inexistent': {
            'urls': ['http://random.url'],
            'file_path': None}
    }

    def request_side_effect(self, method, url, **kwargs):
        """Side effect function used to mock calls to requests.get().text"""
        if method != 'GET':
            return None

        data_file_relative_path = None
        for test_data in self.TEST_DATA.values():
            if url in test_data['urls']:
                data_file_relative_path = test_data['file_path']
                break

        response = requests.Response()

        if data_file_relative_path:
            # Open data file as binary stream so it can be used to mock a requests response
            data_file = open(os.path.join(os.path.dirname(__file__), data_file_relative_path), 'rb')
            # Store opened files so they can be closed when the test is finished
            self.opened_files.append(data_file)

            response.status_code = 200
            response.raw = data_file
        else:
            response.status_code = 404

        return response

    def setUp(self):
        # Mock requests.request()
        self.patcher_request = mock.patch('geospaas.harvesting.utils.http_request')
        self.mock_request = self.patcher_request.start()
        self.mock_request.side_effect = self.request_side_effect

        # Initialize a list of opened files which will be closed in tearDown()
        self.opened_files = []

    def tearDown(self):
        self.patcher_request.stop()
        # Close any files opened during the test
        for opened_file in self.opened_files:
            opened_file.close()

    def test_process_folder(self):
        """
        Explore root page and make sure the _url and _to_process attributes of the crawler have the
        right values
        """
        crawler = crawlers_directory.OpenDAPCrawler.from_kwargs(
            url=self.TEST_DATA['root']['urls'][0], include=r'\.nc$')
        crawler.set_initial_state()

        with mock.patch.object(crawler, 'get_raw_attributes', return_value=dict()), \
                self.assertLogs(crawler.logger, level=logging.DEBUG):
            self.assertListEqual(
                list(crawler._process_folder(crawler._to_process.pop())),
                [crawlers_base.DatasetInfo(self.TEST_DATA['dataset']['urls'][0])])
        self.assertListEqual(crawler._to_process, ['/folder/contents.html'])

    def test_process_folder_with_time_restriction(self):
        """
        Process a folder and make sure the _url and _to_process
        attributes of the crawler have the right values according to a
        time restriction.
        Since the precision of the time restriction is limited to the
        folder level for DirectoryCrawlers, all datasets in a folder
        whose time coverage intersects the crawler's time range are
        selected, even if the timestamp of a dataset does not intersect
        the crawler's time range.
        """
        crawler = crawlers_directory.OpenDAPCrawler.from_kwargs(
            url=self.TEST_DATA['folder_day_of_year']['urls'][0],
            include=r'\.nc$',
            time_range=(datetime(2019, 2, 15, 11, 0, 0), datetime(2019, 2, 15, 13, 0, 0)))
        crawler.set_initial_state()
        with mock.patch.object(crawler, 'get_raw_attributes', return_value=dict()), \
                self.assertLogs(crawler.logger, level=logging.DEBUG):
            self.assertListEqual(
                list(crawler._process_folder(crawler._to_process.pop())),
                [
                    crawlers_base.DatasetInfo(
                        'https://test-opendap.com/folder/2019/046/20190215000000_dataset.nc'),
                    crawlers_base.DatasetInfo(
                        'https://test-opendap.com/folder/2019/046/20190215120000_dataset.nc'),
                ]
            )
        self.assertListEqual(crawler._to_process, [])

    def test_get_xml_namespace(self):
        """Get xml namespace from the test data DDX file"""
        test_file_path = os.path.join(
            os.path.dirname(__file__),
            self.TEST_DATA['short_ddx']['file_path'])

        with open(test_file_path, 'rb') as test_file:
            root = ET.parse(test_file).getroot()

        self.assertEqual(
            crawlers_directory.OpenDAPCrawler.from_kwargs(url='')._get_xml_namespace(root),
            'http://xml.opendap.org/ns/DAP/3.2#')

    def test_logging_if_no_xml_namespace(self):
        """A warning must be logged if no namespace has been found, and an empty string returned"""
        test_file_path = os.path.join(
            os.path.dirname(__file__),
            self.TEST_DATA['no_ns_ddx']['file_path'])

        with open(test_file_path, 'rb') as test_file:
            root = ET.parse(test_file).getroot()

        crawler = crawlers_directory.OpenDAPCrawler.from_kwargs(url='')
        with self.assertLogs(crawler.logger, level=logging.WARNING):
            namespace = crawlers_directory.OpenDAPCrawler.from_kwargs(
                url=''
            )._get_xml_namespace(root)
        self.assertEqual(namespace, '')

    def test_extract_global_attributes(self):
        """Get nc_global attributes from the test data DDX file"""
        test_file_path = os.path.join(
            os.path.dirname(__file__),
            self.TEST_DATA['short_ddx']['file_path'])

        with open(test_file_path, 'rb') as test_file:
            root = ET.parse(test_file).getroot()

        self.assertDictEqual(
            crawlers_directory.OpenDAPCrawler.from_kwargs(url='')._extract_attributes(root),
            {
                'Conventions': 'CF-1.7, ACDD-1.3',
                'raw_dataset_parameters': {'latitude'},
                'title': 'VIIRS L2P Sea Surface Skin Temperature'
            }
        )

    def test_get_ddx_url(self):
        """Test utility function which transforms download links into
        metadata links for OpenDAP
        """
        self.assertEqual(
            crawlers_directory.OpenDAPCrawler.get_ddx_url('https://foo/bar.nc.ddx'),
            'https://foo/bar.nc.ddx')
        self.assertEqual(
            crawlers_directory.OpenDAPCrawler.get_ddx_url('https://foo/bar.nc'),
            'https://foo/bar.nc.ddx')
        self.assertEqual(
            crawlers_directory.OpenDAPCrawler.get_ddx_url('https://foo/bar.nc.dods'),
            'https://foo/bar.nc.ddx')

    def test_get_raw_attributes(self):
        """Test getting raw attributes from a URL"""
        crawler = crawlers_directory.OpenDAPCrawler.from_kwargs(url='foo')
        self.assertDictEqual(
            crawler.get_raw_attributes('https://test-opendap.com/short_dataset.nc'),
            {
                'Conventions': 'CF-1.7, ACDD-1.3',
                'title': 'VIIRS L2P Sea Surface Skin Temperature',
                'raw_dataset_parameters': {'latitude'}
            })


class ThreddsCrawlerTestCase(unittest.TestCase):
    """Tests for the Thredds crawler"""

    @mock.patch("geospaas.harvesting.crawlers.directory.ThreddsCrawler._http_get")
    @mock.patch("geospaas.harvesting.crawlers.directory.ThreddsCrawler._get_links")
    def test_get_download_url(self, mock_get_link, mock_http_get):
        """
        Test the functionality of "get_download_url" method for OpenDAP crawler of OSISAF project
        """
        mock_get_link.return_value = [
            '/thredds/dodsC/osisaf/met.no/ice/amsr2_conc/2019/11/'
            'ice_conc_nh_polstere-100_amsr2_201911301200.nc.html',
            '/thredds/fileServer/osisaf/met.no/ice/amsr2_conc/2019/11/'
            'ice_conc_nh_polstere-100_amsr2_201911301200.nc'
        ]
        # The value of this variable is not used in this test, it is here for reference
        catalog_url = (
            'https://thredds.met.no/thredds/catalog/osisaf/met.no/ice/amsr2_conc/2019/11/'
            'catalog.html?dataset=osisaf/met.no/ice/amsr2_conc/2019/11/'
            'ice_conc_nh_polstere-100_amsr2_201911301200.nc'
        )
        crawler = crawlers_directory.ThreddsCrawler.from_kwargs(
            url='https://thredds.met.no/thredds/osisaf/osisaf.html')
        request_link = crawler.get_download_url(catalog_url)
        self.assertEqual(
            request_link,
            'https://thredds.met.no/thredds/fileServer/osisaf/met.no/ice/amsr2_conc/2019/11/'
            'ice_conc_nh_polstere-100_amsr2_201911301200.nc'
        )

    @mock.patch("geospaas.harvesting.crawlers.directory.ThreddsCrawler._http_get")
    @mock.patch("geospaas.harvesting.crawlers.directory.ThreddsCrawler._get_links")
    def test_get_download_url_no_direct_download_link(self, mock_get_link, mock_http_get):
        """
        The get_download_url() method of the Thredds crawler
        must return None if no valid download URL is found
        """
        mock_get_link.return_value = ['/thredds/dodsC/osisaf/met.no/ice_conc201911301200.nc.dods']
        self.assertIsNone(crawlers_directory.ThreddsCrawler.from_kwargs(url='').get_download_url("dummy"))

    def test_get_ddx_url(self):
        """Test utility function which transforms download links into
        metadata links for Thredds
        """
        self.assertEqual(
            crawlers_directory.ThreddsCrawler.get_ddx_url(
                'https://thredds.met.no/thredds/fileServer/osisaf/met.no/ice/conc/2023/01/'
                'ice_conc_sh_polstere-100_multi_202301141200.nc'),
            'https://thredds.met.no/thredds/dodsC/osisaf/met.no/ice/conc/2023/01/'
            'ice_conc_sh_polstere-100_multi_202301141200.nc.ddx')

    def test_get_ddx_url_error(self):
        """get_ddx_url() should raise an exception when the provided
        URL is not a Thredds fileserver URL
        """
        with self.assertRaises(ValueError):
            crawlers_directory.ThreddsCrawler.get_ddx_url('https://foo/bar.nc')


class FTPCrawlerTestCase(unittest.TestCase):
    """Tests for the FTP crawler"""

    def emulate_cwd_of_ftp(self, name):
        """passes in the case of "", ".." or "folder_name" in order to resemble the behavior of cwd
        of ftplib. Otherwise (encountering a filename) raise the proper exception """
        if name not in ["..", "folder_name", ""]:
            raise ftplib.error_perm

    @mock.patch('ftplib.FTP')
    def test_ftp_correct_navigation(self, mock_ftp):
        """check that file URLs and folders paths are added to the right stacks"""
        test_crawler = crawlers_directory.FTPCrawler.from_kwargs(url='ftp://foo', include='\.gz$')
        test_crawler.set_initial_state()
        test_crawler.ftp.nlst.return_value = ['file1.gz', 'folder_name', 'file3.bb', 'file2.gz', ]
        test_crawler.ftp.cwd.side_effect = self.emulate_cwd_of_ftp
        test_crawler.ftp.host = ''
        with self.assertLogs('geospaas.harvesting.crawlers.directory.FTPCrawler',
                             level=logging.DEBUG):
            self.assertListEqual(
                list(test_crawler._process_folder('')),
                [
                    crawlers_base.DatasetInfo('ftp://foo/file1.gz'),
                    crawlers_base.DatasetInfo('ftp://foo/file2.gz')
                ])
        # folder with 'folder_name' must be in the "_to_process" list
        self.assertCountEqual(['/', 'folder_name'], test_crawler._to_process)

    @mock.patch('ftplib.FTP.login')
    def test_ftp_correct_exception(self, mock_ftp):
        """set_initial_state() should not raise an error in case of
        503 or 230 responses from FTP.login(), but it should for
        other error codes.
        """
        test_crawler = crawlers_directory.FTPCrawler.from_kwargs(
            url='ftp://', username="d", password="d", include='\.gz$')

        mock_ftp.side_effect = ftplib.error_perm("503")
        test_crawler.set_initial_state()

        mock_ftp.side_effect = ftplib.error_perm("230")
        test_crawler.set_initial_state()

        mock_ftp.side_effect = ftplib.error_perm("999")
        with self.assertRaises(ftplib.error_perm):
            test_crawler.set_initial_state()

    def test_ftp_incorrect_entry(self):
        """Shall return 'ValueError' when there is an incorrect entry in ftp address of
        the configuration file """
        with self.assertRaises(ValueError):
            crawlers_directory.FTPCrawler.from_kwargs(url='ft:///')

    def test_retry_on_timeout_decorator_timeout_error(self):
        """The retry_on_timeout decorator should re-create
        the connection when a FTP timeout error occurs, and
        and re-run the method in which the error occurred once
        """
        with mock.patch('ftplib.FTP'):
            crawler = crawlers_directory.FTPCrawler.from_kwargs(url='ftp://foo')
            crawler.set_initial_state()
            crawler.ftp.nlst.side_effect = ftplib.error_temp('421')

            with self.assertRaises(ftplib.error_temp), \
                 self.assertLogs(crawler.logger, level=logging.INFO) as log_cm:
                crawler._list_folder_contents('/')

            self.assertEqual(log_cm.records[0].getMessage(), "Re-initializing the FTP connection")

    def test_retry_on_timeout_decorator_connection_error(self):
        """The retry_on_timeout decorator should try to re-create
        the when a connection error occurs, and re-run the method
        in which the error occurred 5 times
        """
        with mock.patch('ftplib.FTP'):
            crawler = crawlers_directory.FTPCrawler.from_kwargs(url='ftp://foo')
            crawler.set_initial_state()
            for error in (ConnectionError, ConnectionRefusedError, ConnectionResetError):
                crawler.ftp.nlst.side_effect = error

                with mock.patch.object(crawler, 'connect') as mock_connect:
                    with self.assertRaises(error), \
                        self.assertLogs(crawler.logger, level=logging.INFO):
                        crawler._list_folder_contents('/')
                self.assertEqual(mock_connect.call_count, 5)

    def test_no_retry_on_non_timeout_ftp_errors(self):
        """FTP errors other than timeouts should not trigger a retry"""
        with mock.patch('ftplib.FTP'):
            crawler = crawlers_directory.FTPCrawler.from_kwargs(url='ftp://foo')
            crawler.set_initial_state()
            crawler.ftp.nlst.side_effect = ftplib.error_temp('422')

            with mock.patch.object(crawler, 'connect') as mock_connect:
                with self.assertRaises(ftplib.error_temp):
                    crawler._list_folder_contents('/')
                mock_connect.assert_not_called()


class NansatCrawlerTestCase(unittest.TestCase):
    """Tests for NansatCrawler"""

    def setUp(self):
        patcher_nansat = mock.patch('geospaas.harvesting.crawlers.directory.Nansat')
        self.mock_nansat = patcher_nansat.start()
        self.addCleanup(mock.patch.stopall)

    def test_get_raw_attributes(self):
        """Test the ingestion of a netcdf file using nansat"""
        crawler = crawlers_directory.NansatCrawler.from_kwargs(url='foo')
        self.assertEqual(
            crawler.get_raw_attributes(''),
            self.mock_nansat.return_value.get_metadata.return_value)

    def test_get_raw_attributes_ftp_error(self):
        """Nansat does not support remote FTP files"""
        with self.assertRaises(ValueError):
            crawlers_directory.NansatCrawler.from_kwargs(url='').get_raw_attributes('ftp://foo')

    def test_get_raw_attributes_gcps(self):
        """Test the ingestion of a netcdf file using nansat, with GCP
        reprojection
        """
        crawler = crawlers_directory.NansatCrawler.from_kwargs(url='foo')
        self.mock_nansat.return_value.vrt.dataset.GetGCPs.return_value = True
        self.assertEqual(
            crawler.get_raw_attributes(''),
            self.mock_nansat.return_value.get_metadata.return_value)
        self.mock_nansat.return_value.reproject_gcps.assert_called_once()


class NetCDFCrawlerTestCase(unittest.TestCase):
    """Test the NetCDFCrawler"""

    def  setUp(self):
        self.crawler = crawlers_directory.NetCDFCrawler.from_kwargs(
            url='/foo',
            longitude_attribute='LONGITUDE',
            latitude_attribute='LATITUDE')
    class MockVariable(mock.Mock):
        """Mock netCDF variable"""
        def __init__(self, data, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._data = np.array(data)
            self.shape = self._data.shape
            self.dimensions = kwargs.get('dimensions', {})

        def __iter__(self):
            """Make the class iterable"""
            return iter(self._data)

        def __getitem__(self, i):
            """Make the class subscriptable"""
            return self._data[i]

        def __array__(self, *args, **kwargs):
            """Make the class numpy-array-like"""
            return self._data
    class MaskedMockVariable(MockVariable):
        """Mock netCDF variable with masked values"""
        def __init__(self, data, *args, **kwargs):
            super().__init__(data, *args, **kwargs)
            self._data = np.ma.masked_values(data, 1e10)

    def test_get_raw_attributes(self):
        """Test reading raw attributes from a netCDF file"""
        attributes = {
            'attr1': 'value1',
            'attr2': 'value2'
        }
        with mock.patch('netCDF4.Dataset') as mock_dataset, \
             mock.patch.object(self.crawler, '_get_parameter_names', return_value=['param']), \
             mock.patch.object(self.crawler, '_get_geometry_wkt', return_value='wkt'):
            mock_dataset.return_value.__dict__ = attributes

            self.assertDictEqual(
                self.crawler.get_raw_attributes('/foo/bar'),
                {
                    **attributes,
                    'raw_dataset_parameters': ['param'],
                    'location_geometry': 'wkt',
                })

    def test_repr(self):
        """Test string representation"""
        self.assertEqual(
            repr(crawlers_directory.NetCDFCrawler.from_kwargs(
                url='https://foo',
                time_range=(datetime(2025, 1, 1), datetime(2025, 1, 2)),
                include='\.nc$',
                username='user',
                password='pass',
                longitude_attribute='longitude',
                latitude_attribute='latitude')),
            "NetCDFCrawler("
                "url='https://foo', "
                "include='\.nc$', "
                "longitude_attribute='longitude', "
                "latitude_attribute='latitude', "
                "time_range=(datetime.datetime(2025, 1, 1, 0, 0, tzinfo=datetime.timezone.utc), "
                            "datetime.datetime(2025, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)), "
                "username='user', "
                "password='******')")

    def test_get_parameter_names(self):
        """_get_parameter_names() should return the names of the
        variables of the dataset
        """
        mock_variable1 = mock.Mock()
        mock_variable1.standard_name = 'standard_name_1'

        mock_dataset = mock.Mock()
        mock_dataset.variables = {
            'var1': mock_variable1,
            'var2': 'variable2' # does not have a "standard_name" attribute
        }

        self.assertListEqual(self.crawler._get_parameter_names(mock_dataset), ['standard_name_1'])

    def test_get_trajectory(self):
        """Test getting a trajectory from a netCDF dataset"""
        mock_dataset = mock.Mock()
        mock_dataset.dimensions = {}
        mock_dataset.variables = {
            'LONGITUDE': self.MaskedMockVariable((1, 3, 1e10, 5)),
            'LATITUDE': self.MaskedMockVariable((2, 4, 1e10, 6))
        }
        self.assertEqual(
            self.crawler._get_geometry_wkt(mock_dataset),
            'LINESTRING (1 2, 5 6)')

    def test_get_point(self):
        """Test getting a WKT point when the shape of the latitude and
        longitude is (1,)"""
        mock_dataset = mock.Mock()
        mock_dataset.dimensions = {}
        mock_dataset.variables = {
            'LONGITUDE': self.MockVariable((1,)),
            'LATITUDE': self.MockVariable((2,))
        }
        self.assertEqual(
            self.crawler._get_geometry_wkt(mock_dataset),
            'POINT (1 2)'
        )

    def test_get_deduplicated_point(self):
        """Test getting a WKT point when that point is referenced
        multiple times in the dataset
        """
        mock_dataset = mock.Mock()
        mock_dataset.dimensions = {}
        mock_dataset.variables = {
            'LONGITUDE': self.MockVariable((1, 1, 1)),
            'LATITUDE': self.MockVariable((2, 2, 2))
        }
        self.assertEqual(
            self.crawler._get_geometry_wkt(mock_dataset),
            'POINT (1 2)'
        )

    def test_get_polygon_from_coordinates_lists(self):
        """Test getting a polygonal coverage from a dataset when the
        latitude and longitude are multi-dimensional and of the same
        shape
        """
        mock_dataset = mock.Mock()
        mock_dataset.dimensions = {}
        mock_dataset.variables = {
            'LONGITUDE': self.MockVariable((
                (1, 1, 2),
                (2, 0, 3),
            )),
            'LATITUDE': self.MockVariable((
                (1, 2, 3),
                (4, 0, 4),
            ))
        }
        self.assertEqual(
            self.crawler._get_geometry_wkt(mock_dataset),
            'POLYGON ((0 0, 2 4, 3 4, 1 1, 0 0))'
        )

    @mock.patch('geospaas.harvesting.crawlers.directory.np.ma.isMaskedArray', return_value=True)
    def test_get_polygon_from_coordinates_lists_with_masked_array(self, mock_isMaskedArray):
        """Test getting a polygonal coverage from a dataset when the
        latitude and longitude are multi-dimensional masked_array
        """
        mock_dataset = mock.Mock()
        mock_dataset.dimensions = {}
        mock_dataset.variables = {
            'LONGITUDE': self.MaskedMockVariable((
                (1, 1e10, 1e10),
                (2, 0, 3),
            )),
            'LATITUDE': self.MaskedMockVariable((
                (1, 1e10, 1e10),
                (4, 0, 4),
            ))
        }
        self.assertEqual(
            self.crawler._get_geometry_wkt(mock_dataset),
            'POLYGON ((0 0, 2 4, 3 4, 1 1, 0 0))'
        )

    @mock.patch('geospaas.harvesting.crawlers.directory.np.ma.isMaskedArray', return_value=True)
    def test_get_polygon_from_coordinates_lists_with_masked_array_1d_case(self, mock_isMaskedArray):
        """Test getting a polygonal coverage from a dataset when the
        latitude and longitude are 1d masked_array as an abstracted
        version of 2d lon and lat values
        """
        mock_dataset = mock.Mock()
        mock_dataset.dimensions = {}
        mock_dataset.variables = {
            'LONGITUDE': self.MaskedMockVariable(
                (1, 1e10, 1e10, 2, 0, 3, 1), dimensions=['LONGITUDE','LATITUDE']),
            'LATITUDE': self.MaskedMockVariable(
                (1, 1e10, 1e10, 4, 0, 4, 1), dimensions=['LONGITUDE','LATITUDE']),
        }
        self.assertEqual(
            self.crawler._get_geometry_wkt(mock_dataset),
            'POLYGON ((0 0, 0 4, 3 4, 3 0, 0 0))'
        )

    def test_get_polygon_from_1d_lon_lat(self):
        """Test getting a polygonal coverage from a dataset when the
        latitude and longitude are one-dimensional and of different
        shapes
        """
        mock_dataset = mock.Mock()
        mock_dataset.dimensions = {}
        mock_dataset.variables = {
            'LONGITUDE': self.MockVariable((1, 2, 3)),
            'LATITUDE': self.MockVariable((1, 2)),
            'DATA': self.MockVariable('some_data', dimensions=('LONGITUDE', 'LATITUDE'))
        }
        self.assertEqual(
            self.crawler._get_geometry_wkt(mock_dataset),
            'POLYGON ((1 1, 1 2, 3 2, 3 1, 1 1))'
        )

    def test_error_on_unsupported_case(self):
        """An error should be raised if the dataset has longitude and
        latitude arrays of different lengths and no variable is
        dependent on latitude and longitude
        """
        mock_dataset = mock.Mock()
        mock_dataset.dimensions = {}
        mock_dataset.variables = {
            'LONGITUDE': self.MockVariable((1, 1, 1, 1)),
            'LATITUDE': self.MockVariable((2, 2, 2))
        }
        with self.assertRaises(ValueError):
            self.crawler._get_geometry_wkt(mock_dataset)
