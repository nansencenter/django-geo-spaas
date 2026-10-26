import logging
import os
from datetime import datetime
from pathlib import Path

import unittest
import unittest.mock as mock

import requests
import shapely.geometry

import geospaas.harvesting.crawlers.base as crawlers_base
import geospaas.harvesting.crawlers.erddap as crawlers_erddap


class ERDDAPTableCrawlerTestCase(unittest.TestCase):
    """Tests for ERDDAPTableCrawler"""

    TEST_DATA_PATH = Path(__file__).parent.parent / 'data' / 'erddap'

    def test_repr(self):
        """Test string representation"""
        self.assertEqual(
            repr(crawlers_erddap.ERDDAPTableCrawler.from_kwargs(
                url='http://foo.json',
                id_attrs=['bar'],
                entry_id_prefix='baz_',
                longitude_attr='lon',
                latitude_attr='lat',
                time_attr='time',
                position_qc_attr='position_qc',
                time_qc_attr='time_qc',
                valid_qc_codes=['1', '2'],
                search_terms=['qux=quux'],
                variables=['var1'],
                location='POINT(1 2)',
                time_range=[datetime(2025, 1, 1), datetime(2025, 1, 2)],
                )),
            "ERDDAPTableCrawler("
                "url='http://foo.json', "
                "id_attrs=['bar'], "
                "entry_id_prefix='baz_', "
                "longitude_attr='lon', latitude_attr='lat', time_attr='time', "
                "position_qc_attr='position_qc', time_qc_attr='time_qc', "
                "valid_qc_codes=['1', '2'], "
                "search_terms=["
                    "'qux=quux', "
                    "'lon>=1.0', 'lon<=1.0', 'lat>=2.0', 'lat<=2.0', "
                    "'time>=2025-01-01T00:00:00Z', 'time<=2025-01-02T00:00:00Z'], "
                "variables=['var1'])")

    def test_url_check(self):
        """ERDDAPTableCrawler's url should end with .json"""
        with self.assertRaises(ValueError):
            crawlers_erddap.ERDDAPTableCrawler.from_kwargs(url='http://foo', id_attrs=['bar'])

    def test_equality(self):
        """Test equality of two DirectoryCrawler objects"""
        self.assertEqual(
            crawlers_erddap.ERDDAPTableCrawler.from_kwargs(
                url='http://foo/ArgoFloats.json', id_attrs=['platform_number']),
            crawlers_erddap.ERDDAPTableCrawler.from_kwargs(
                url='http://foo/ArgoFloats.json', id_attrs=['platform_number']))
        self.assertNotEqual(
            crawlers_erddap.ERDDAPTableCrawler.from_kwargs(
                url='http://foo/ArgoFloats.json', id_attrs=['platform_number']),
            crawlers_erddap.ERDDAPTableCrawler.from_kwargs(
                url='http://foo/ArgoFloats.json', id_attrs=['platform_number'],
                longitude_attr='lon', latitude_attr='lat'))

    def test_get_ids(self):
        """Test gettings identifiers which match search terms"""
        response_path = os.path.join(self.TEST_DATA_PATH, 'ids.json')
        response = requests.Response()
        response.status_code = 200
        response.raw = open(response_path, 'rb')
        crawler = crawlers_erddap.ERDDAPTableCrawler.from_kwargs(
            url='http://foo/ArgoFloats.json',
            id_attrs=['platform_number'],
            search_terms=['time>=2024-01-01T00:00:00Z',
                          'time<=2024-01-01T01:00:00Z'])
        with mock.patch.object(crawler, '_http_get', return_value=response):
            ids = crawler.get_ids()
            self.assertListEqual(
                list(ids),
                [["3901480"], ["5905121"], ["5905267"], ["5905498"], ["5905533"], ["5905765"],
                 ["5905878"], ["5906337"], ["5906912"], ["5906993"], ["6902906"], ["6903060"]])
        response.raw.close()

    def test_get_ids_error(self):
        """An error message must be logged if an error happens when
        fetching IDs
        """
        error = requests.HTTPError(response=mock.Mock(content='error message'))
        crawler = crawlers_erddap.ERDDAPTableCrawler.from_kwargs(
            url='http://foo/ArgoFloats.json', id_attrs=['platform_number'])
        with mock.patch.object(crawler, '_http_get', side_effect=error):
            with self.assertLogs(logger=crawler.logger, level=logging.ERROR), \
                 self.assertRaises(requests.HTTPError):
                list(crawler.get_ids())

    def test__make_condition_parameters(self):
        """Check that string parameters get quotes"""
        self.assertDictEqual(
            crawlers_erddap.ERDDAPTableCrawler.from_kwargs(url='url.json', id_attrs=['id_attr'])._make_condition_parameters({
                'a': 'foo',
                'b': 1,
                'c': True
            }),
            {'a': '"foo"', 'b': 1, 'c': True}
        )

    def test_crawl(self):
        """Test the DatasetInfo objects returned by the crawler"""
        ids = [["3901480"], ["5905121"], ["5905267"]]
        coverage = [('2025-05-01T00:00:00Z', '2025-05-02T00:00:00Z'), [(1, 2), (3, 4)]]
        metadata = {'foo': 'bar'}
        expected_trajectory = shapely.geometry.MultiPoint([(1, 2), (3, 4)]).wkt
        crawler = crawlers_erddap.ERDDAPTableCrawler.from_kwargs(
            url='http://foo/ArgoFloats.json', id_attrs=['platform_number'],
            position_qc_attr='position_qc', variables=['foo', 'bar'])
        with mock.patch.object(crawler, 'get_ids', return_value=ids), \
             mock.patch.object(crawler, 'get_coverage', return_value=coverage), \
             mock.patch.object(crawler, 'get_product_metadata', return_value=metadata):
            self.assertListEqual(
                list(crawler.crawl()),
                [
                    crawlers_base.DatasetInfo(
                        'http://foo/ArgoFloats.json?time,longitude,latitude,position_qc,foo,bar'
                        '&platform_number="3901480"',
                        {
                            'entry_id': '3901480',
                            'temporal_coverage': ('2025-05-01T00:00:00Z', '2025-05-02T00:00:00Z'),
                            'trajectory': expected_trajectory,
                            'product_metadata': metadata,
                        }),
                    crawlers_base.DatasetInfo(
                        'http://foo/ArgoFloats.json?time,longitude,latitude,position_qc,foo,bar'
                        '&platform_number="5905121"',
                        {
                            'entry_id': '5905121',
                            'temporal_coverage': ('2025-05-01T00:00:00Z', '2025-05-02T00:00:00Z'),
                            'trajectory': expected_trajectory,
                            'product_metadata': metadata,

                        }),
                    crawlers_base.DatasetInfo(
                        'http://foo/ArgoFloats.json?time,longitude,latitude,position_qc,foo,bar'
                        '&platform_number="5905267"',
                        {
                            'entry_id': '5905267',
                            'temporal_coverage': ('2025-05-01T00:00:00Z', '2025-05-02T00:00:00Z'),
                            'trajectory': expected_trajectory,
                            'product_metadata': metadata,
                        }),
                ])

    def test_check_qc(self):
        """Test the QC validation"""
        crawler = crawlers_erddap.ERDDAPTableCrawler.from_kwargs(url='foo.json', id_attrs=['bar'], valid_qc_codes=('1', '2'))
        self.assertTrue(crawler._check_qc('1'))
        self.assertTrue(crawler._check_qc('2'))
        self.assertFalse(crawler._check_qc('0'))
        self.assertFalse(crawler._check_qc('3'))
        self.assertFalse(crawler._check_qc(1))

    def test_make_coverage_url(self):
        """Test making the URL to get a dataset's temporal and spatial
        coverage
        """
        self.assertEqual(
            crawlers_erddap.ERDDAPTableCrawler.from_kwargs(url='https://foo.json', id_attrs=['id'],
                                        longitude_attr='lon', latitude_attr='lat', time_attr='time',
                                        position_qc_attr='pos_qc',
                                        variables=['bar', 'baz'])._make_coverage_url(),
            'https://foo.json?time,lon,lat,pos_qc&distinct()&orderBy("time")'
        )

    def test_get_coverage(self):
        """Test getting the temporal and spatial coverage for one
        dataset
        """
        crawler = crawlers_erddap.ERDDAPTableCrawler.from_kwargs(url=
            'https://foo.json', id_attrs=['platform_number'],
            longitude_attr='longitude', latitude_attr='latitude',
            time_attr='time',
            position_qc_attr='position_qc', time_qc_attr='time_qc')

        response = requests.Response()
        response.status_code = 200
        response.raw = open(os.path.join(self.TEST_DATA_PATH, 'coverage.json'), 'rb')

        expected_trajectory = [
            (-11.863, -0.126),
            (-13.83, -0.035),
            (-15.744, 0.68),
            (-16.674, 0.76),
            (-17.133, 1.21),
            (-17.74, 1.403),
            (-17.734, 1.263),
            (-17.189, 1.756),
            (-16.437, 1.191),
            (-16.039, 1.409),
            (-15.451, 1.177),
            (-15.075, 1.132),
            (-14.329, 1.182),
            (-13.586, 1.285),
            (-13.488, 1.766),
            (-13.593, 2.086),
            (-14.115, 2.533),
            (-15.016, 2.923),
            (-15.901, 3.11),
            (-16.634, 3.042),
            (-16.874, 3.115),
            (-17.081, 3.125),
            (-17.515, 3.171),
            (-17.623, 3.318),
            (-17.668, 3.358),
            (-17.332, 3.699),
            (-16.714, 3.96),
            (-15.962, 4.15),
            (-15.254, 3.998),
            (-14.585, 4.127),
            (-14.048, 4.175),
            (-13.926, 4.17),
            (-13.769, 4.183),
            (-13.47, 4.276),
            (-13.134, 4.322),
            (-12.887, 4.221),
            (-12.702, 4.292),
            (-12.415, 4.275),
            (-12.116, 4.126),
            (-11.792, 3.997),
            (-11.3, 3.732),
            (-10.925, 3.94),
            (-10.152, 3.852),
            (-9.558, 4.015),
            (-9.756, 4.6),
            (-10.046, 5.203),
            (-9.934, 5.179),
            (-9.612, 4.975),
        ]

        with mock.patch.object(crawler, '_http_get', return_value=response) as mock_http_get:
            self.assertTupleEqual(
                crawler.get_coverage({'platform_number': '13858'}),
                (("1997-07-28T20:26:20Z", "1998-12-27T20:00:25Z"), expected_trajectory))
        mock_http_get.assert_called_once_with(
            crawler._make_coverage_url(),
            request_parameters={'params': {'platform_number': '"13858"'}})
        response.raw.close()

    def test_get_coverage_error(self):
        """`get_coverage` must raise an exception when the coverage
        cannot be determined
        """
        crawler = crawlers_erddap.ERDDAPTableCrawler.from_kwargs(url=
            'https://foo.json', id_attrs=['platform_number'], valid_qc_codes=('1',))
        with mock.patch.object(crawler, '_http_get') as mock_http_get:
            mock_http_get.return_value.json.return_value = {
                'table': {
                    'rows': [
                        ["1997-07-28T20:26:20Z", -11.863, -0.126, "3", "1"],
                        ["1997-08-09T01:52:41Z", -13.83, -0.035, "5", "1"],
                        ["1997-08-19T20:44:44Z", -15.744, 0.68, "3", "1"],
                        ["1997-08-30T20:12:43Z", -16.674, 0.76, "4", "1"],
                        ["1997-09-10T21:03:19Z", -17.133, 1.21, "4", "1"],
                    ]
                }
            }
            with self.assertRaises(RuntimeError):
                crawler.get_coverage({'platform_number': '123456'})

    def test_get_coverage_http_error(self):
        """`get_coverage` must raise an exception when an HTTP error
        happens
        """
        crawler = crawlers_erddap.ERDDAPTableCrawler.from_kwargs(
            url='https://foo.json', id_attrs=['platform_number'])
        error = requests.HTTPError(response=mock.MagicMock())
        with mock.patch.object(crawler, '_http_get', side_effect=error):
            with self.assertRaises(requests.HTTPError), \
                 self.assertLogs(crawler.logger, logging.ERROR):
                crawler.get_coverage({'platform_number': '123456'})

    def test_make_product_metadata_url(self):
        """Test creating the URL to a product's metadata"""
        self.assertEqual(
            crawlers_erddap.ERDDAPTableCrawler.from_kwargs(url=
                'https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.json', id_attrs=['id']
            )._make_product_metadata_url(),
            'https://erddap.ifremer.fr/erddap/info/ArgoFloats/index.json')

        with self.assertRaises(RuntimeError):
            crawlers_erddap.ERDDAPTableCrawler.from_kwargs(url='https://foo.json', id_attrs=['id'])._make_product_metadata_url()

    def test_get_product_metadata(self):
        """Test getting a product's metadata"""
        crawler = crawlers_erddap.ERDDAPTableCrawler.from_kwargs(url=
            'https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.json', id_attrs=['id'])
        with mock.patch.object(crawler, '_http_get') as mock_http_get:
            result = crawler.get_product_metadata()
        self.assertEqual(result, mock_http_get.return_value.json.return_value)
        mock_http_get.assert_called_with(crawler._make_product_metadata_url())

    def test_get_product_metadata_http_error(self):
        """`get_coverage` must raise an exception when an HTTP error
        happens
        """
        crawler = crawlers_erddap.ERDDAPTableCrawler.from_kwargs(url=
            'https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.json', id_attrs=['id'])
        error = requests.HTTPError
        with mock.patch.object(crawler, '_http_get', side_effect=error):
            with self.assertRaises(error), self.assertLogs(crawler.logger, logging.ERROR):
                crawler.get_product_metadata()
