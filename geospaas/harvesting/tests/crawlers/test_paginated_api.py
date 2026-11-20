import io
import json
import logging
import unittest
import unittest.mock as mock
from datetime import datetime, timezone
from pathlib import Path

import requests
import shapely.geometry

import geospaas.harvesting.crawlers.base as crawlers_base
import geospaas.harvesting.crawlers.paginated_api as crawlers_paginated_api


class HTTPPaginatedAPICrawlerTestCase(unittest.TestCase):
    """Tests for the HTTPPaginatedAPICrawler base class"""

    def test_repr(self):
        """Test string representation"""
        class TestCrawler(crawlers_paginated_api.HTTPPaginatedAPICrawler):
            PAGE_OFFSET_NAME = 'page'
            PAGE_SIZE_NAME = 'page_size'
        self.assertEqual(
            repr(TestCrawler.from_kwargs(
                url='http://foo',
                initial_offset=0,
                time_range=[datetime(2025, 1, 1), datetime(2025, 1, 2)],
                location='POINT(1 2)',
                username='user',
                password='pass',
                page_size=10,)),
            "TestCrawler("
                "url='http://foo', "
                "initial_offset=0, "
                "request_parameters={'params': {'page': 0, 'page_size': 10}})")

    def test_equality(self):
        """Test the equality operator between crawlers"""
        self.assertEqual(
            crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(url='http://foo'),
            crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(url='http://foo'))
        self.assertEqual(
            crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(
                url='http://foo', username='user', password='pass', search_terms={'bar': 'baz'}),
            crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(
                url='http://foo', username='user', password='pass', search_terms={'bar': 'baz'}))
        self.assertNotEqual(
            crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(url='http://foo'),
            crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(url='http://bar'))

    def test_get_page_size(self):
        """Test page_size getter"""
        with mock.patch(
                'geospaas.harvesting.crawlers.paginated_api.HTTPPaginatedAPICrawler.PAGE_SIZE_NAME',
                'size'):
            crawler = crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(
                url='https://foo', page_size=10)
            crawler.set_initial_state()
            self.assertEqual(crawler.page_size, 10)

    def test_get_page_offset(self):
        """Test page_offset getter"""
        crawler = crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(
                url='foo', initial_offset=10)
        crawler.set_initial_state()
        self.assertEqual(crawler.page_offset, 10)

    def test_set_page_offset(self):
        """Test page_offset setter"""
        crawler = crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(url='https://foo')
        crawler.page_offset = 12
        self.assertEqual(crawler.page_offset, 12)

    def test_set_initial_state(self):
        """Test that set_initial_state correctly resets the crawler"""
        crawler = crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(url='https://foo')
        # Set non-default offset and _urls values
        crawler.request_parameters['params'][crawler.PAGE_OFFSET_NAME] = 200
        crawler.page_offset = 15

        crawler.set_initial_state()
        self.assertEqual(
            crawler.request_parameters['params'][crawler.PAGE_OFFSET_NAME], crawler.initial_offset)

    def test_get_next_page(self):
        """_get_next_page() should get the page at the current offset,
        then increment the offset
        """
        crawler = crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(url='https://foo')
        crawler.set_initial_state()
        response = requests.Response()
        response.status_code = 200
        response.raw = io.BytesIO(b'foo')
        with mock.patch.object(crawler, '_http_get', return_value=response), \
                self.assertLogs(crawler.logger, level=logging.DEBUG):
            self.assertEqual(crawler._get_next_page(), 'foo')
            self.assertEqual(crawler.request_parameters['params'][crawler.PAGE_OFFSET_NAME], 1)

    def test_abstract_get_datasets_info(self):
        """_get_datasets_info() should raise a NotImplementedError
        when called directly from HTTPPaginatedAPICrawler
        """
        crawler = crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(url='foo')
        with self.assertRaises(NotImplementedError):
            crawler._get_datasets_info('')

    def test_abstract_get_entries(self):
        """_get_entries() should raise a NotImplementedError
        when called directly from HTTPPaginatedAPICrawler
        """
        crawler = crawlers_paginated_api.HTTPPaginatedAPICrawler.from_kwargs(url='foo')
        with self.assertRaises(NotImplementedError):
            crawler._get_entries('')

    def test_crawl(self):
        """Test the crawling mechanism for HTTP paginated APIs"""
        class TestHTTPAPICrawler(crawlers_paginated_api.HTTPPaginatedAPICrawler):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.ran = False

            def _get_next_page(self):
                if self.ran:
                    return ''
                else:
                    self.ran = True
                    return 'https://foo/bar.nc;https://foo/baz.nc'

            def _get_entries(self, page:str):
                if page:
                    return page.split(';')
                else:
                    return None

            def _get_datasets_info(self, entries):
                return [crawlers_base.DatasetInfo(url) for url in entries]

        crawler = TestHTTPAPICrawler.from_kwargs(url='https://foo')
        self.assertListEqual(
            list(crawler.crawl()),
            [crawlers_base.DatasetInfo('https://foo/bar.nc'),
             crawlers_base.DatasetInfo('https://foo/baz.nc')])


class EarthdataCMRCrawlerTestCase(unittest.TestCase):
    """Tests for EarthdataCMRCrawler"""

    def setUp(self):
        self.crawler = crawlers_paginated_api.EarthDataCMRCrawler.from_kwargs(
            url='foo',
            search_terms={'short_name': 'COLLECTION', 'platform': 'value1', 'instrument': 'value2'})

    def test_build_request_parameters_no_argument(self):
        """Test building the request parameters without specifying any argument"""
        self.assertDictEqual(self.crawler._build_request_parameters(), {
            'params': {
                'page_size': 100,
                'page_num': 1,
                'sort_key': '+start_date',
            }
        })

    def test_build_request_parameters_no_time_range(self):
        """Test building the request parameters without time range"""
        self.assertDictEqual(
            self.crawler._build_request_parameters(
                {'short_name': 'COLLECTION', 'platform': 'value1', 'instrument': 'value2'}),
            {
                'params': {
                    'platform': 'value1',
                    'instrument': 'value2',
                    'short_name': 'COLLECTION',
                    'page_size': 100,
                    'page_num': 1,
                    'sort_key': '+start_date'
                }
            })

    def test_build_request_parameters_with_time_range(self):
        """Test building the request parameters without time range"""
        time_range = (
            datetime(2020, 2, 1, tzinfo=timezone.utc),
            datetime(2020, 2, 2, tzinfo=timezone.utc)
        )

        self.assertDictEqual(
            self.crawler._build_request_parameters(
                {'short_name': 'COLLECTION', 'platform': 'value1', 'instrument': 'value2'},
                time_range),
            {
                'params': {
                    'platform': 'value1',
                    'instrument': 'value2',
                    'short_name': 'COLLECTION',
                    'page_size': 100,
                    'page_num': 1,
                    'sort_key': '+start_date',
                    'temporal': '2020-02-01T00:00:00+00:00,2020-02-02T00:00:00+00:00'
                }
            }
        )

    def test_build_request_parameters_with_time_range_start_only(self):
        """Test building the request parameters without time range"""
        time_range = (datetime(2020, 2, 1, tzinfo=timezone.utc), None)

        self.assertDictEqual(
            self.crawler._build_request_parameters(
                {'short_name': 'COLLECTION', 'platform': 'value1', 'instrument': 'value2'},
                time_range),
            {
                'params': {
                    'platform': 'value1',
                    'instrument': 'value2',
                    'short_name': 'COLLECTION',
                    'page_size': 100,
                    'page_num': 1,
                    'sort_key': '+start_date',
                    'temporal': '2020-02-01T00:00:00+00:00,'
                }
            })

    def test_build_request_parameters_with_time_range_end_only(self):
        """Test building the request parameters without time range"""
        time_range = (None, datetime(2020, 2, 2, tzinfo=timezone.utc))

        self.assertDictEqual(
            self.crawler._build_request_parameters(
                {'short_name': 'COLLECTION', 'platform': 'value1', 'instrument': 'value2'},
                time_range),
            {
                'params': {
                    'platform': 'value1',
                    'instrument': 'value2',
                    'short_name': 'COLLECTION',
                    'page_size': 100,
                    'page_num': 1,
                    'sort_key': '+start_date',
                    'temporal': ',2020-02-02T00:00:00+00:00'
                }
            })

    def test_build_request_parameters_with_polygon(self):
        """Test building the request parameters with a polygon location
        """
        self.assertDictEqual(
            self.crawler._build_request_parameters({'short_name': 'COLLECTION'},
                location=shapely.geometry.Polygon(((1, 90), (180, 90), (180, 3), (1, 3), (1, 90)))),
            {
                'params': {
                    'short_name': 'COLLECTION',
                    'page_size': 100,
                    'page_num': 1,
                    'sort_key': '+start_date',
                    'polygon[]': '1.0,89.99,179.99,89.99,179.99,3.0,1.0,3.0,1.0,89.99'
                }
            })

    def test_build_request_parameters_with_line(self):
        """Test building the request parameters with a line location
        """
        self.assertDictEqual(
            self.crawler._build_request_parameters({'short_name': 'COLLECTION'},
                location=shapely.geometry.LineString(((1, 2), (3, 4), (5, 6)))),
            {
                'params': {
                    'short_name': 'COLLECTION',
                    'page_size': 100,
                    'page_num': 1,
                    'sort_key': '+start_date',
                    'line[]': '1.0,2.0,3.0,4.0,5.0,6.0'
                }
            })

    def test_build_request_parameters_with_point(self):
        """Test building the request parameters with a point location
        """
        self.assertDictEqual(
            self.crawler._build_request_parameters({'short_name': 'COLLECTION'},
                location=shapely.geometry.Point((1, 2))),
            {
                'params': {
                    'short_name': 'COLLECTION',
                    'page_size': 100,
                    'page_num': 1,
                    'sort_key': '+start_date',
                    'point': '1.0,2.0'
                }
            })

    def test_build_request_parameters_with_bbox(self):
        """Test building the request parameters with a bounding box
        location
        """
        self.assertDictEqual(
            self.crawler._build_request_parameters({'short_name': 'COLLECTION'},
                location='bounding_box[]=-10,-5,10,5'),
            {
                'params': {
                    'short_name': 'COLLECTION',
                    'page_size': 100,
                    'page_num': 1,
                    'sort_key': '+start_date',
                    'bounding_box[]': '-10,-5,10,5'
                }
            })

    def test_build_request_parameters_location_error(self):
        """Test building the request parameters with a bounding box
        location
        """
        with self.assertRaises(ValueError):
            self.crawler._build_request_parameters({'short_name': 'COLLECTION'}, location=1)

    def test_find_download_url(self):
        """Test finding a download URL in an entry"""
        entry = {
            'umm': {
                'RelatedUrls': [
                    {'URL': 'https://foo/bar.json', 'Type': 'EXTENDED METADATA'},
                    {'URL': 'https://foo/bar.nc', 'Type': 'GET DATA'},
                    {'URL': 'https://baz/bar.nc', 'Type': 'GET DATA'},
                    {'URL': 'https://foo/qux.png', 'Type': 'DIRECT DOWNLOAD'},
                ]
            }
        }
        self.assertEqual(self.crawler._find_download_url(entry), 'https://foo/bar.nc')

    def test_find_download_url_no_get_data(self):
        """Test finding a download URL in an entry when no GET DATA type is available"""
        entry = {
            'umm': {
                'RelatedUrls': [
                    {'URL': 'https://foo/bar.nc', 'Type': 'DOWNLOAD'},
                    {'URL': 'https://baz/bar.nc', 'Type': 'DOWNLOAD'},
                ]
            }
        }
        self.assertEqual(self.crawler._find_download_url(entry), 'https://foo/bar.nc')

    def test_get_datasets_info(self):
        """_get_datasets_info() should extract datasets information
        from a response page
        """
        data_file_path = str(Path(__file__).parent.parent / 'data/earthdata_cmr/result_page.json')

        with open(data_file_path, 'r') as f_h:
            page = f_h.read()

        expected_entry = crawlers_base.DatasetInfo(
            'https://oceandata.sci.gsfc.nasa.gov/cmr/getfile/V2012002205400.L2_SNPP_OC.nc',
            metadata=json.loads(page)['items'][0])

        dataset_infos = self.crawler._get_datasets_info(self.crawler._get_entries(page))
        self.assertEqual(next(dataset_infos), expected_entry)


class RestoCrawlerTestCase(unittest.TestCase):
    """Tests for RestoCrawler"""
    def setUp(self):
        self.crawler = crawlers_paginated_api.RestoCrawler.from_kwargs(
            url='foo', collection='COLLECTION',
            search_terms={'param1': 'value1', 'param2': 'value2'})

    def test_build_request_parameters_no_argument(self):
        """Test building the request parameters without specifying any argument"""
        self.assertDictEqual(self.crawler._build_request_parameters(), {
            'params': {
                'maxRecords': 100,
                'page': 1,
                'sortOrder': 'ascending',
                'sortParam': 'published'
            }
        })

    def test_build_request_parameters_no_time_range(self):
        """Test building the request parameters without time range"""
        self.assertDictEqual(
            self.crawler._build_request_parameters(
                {'param1': 'value1', 'param2': 'value2'}),
            {
                'params': {
                    'param1': 'value1',
                    'param2': 'value2',
                    'maxRecords': 100,
                    'page': 1,
                    'sortOrder': 'ascending',
                    'sortParam': 'published'
                }
            })

    def test_build_request_parameters_with_time_range(self):
        """Test building the request parameters with time range"""
        time_range = (
            datetime(2020, 2, 1, tzinfo=timezone.utc),
            datetime(2020, 2, 2, tzinfo=timezone.utc)
        )

        self.assertDictEqual(
            self.crawler._build_request_parameters(
                    {'param1': 'value1', 'param2': 'value2'},
                    time_range),
            {
                'params': {
                    'param1': 'value1',
                    'param2': 'value2',
                    'maxRecords': 100,
                    'page': 1,
                    'sortOrder': 'ascending',
                    'sortParam': 'published',
                    'startDate': '2020-02-01T00:00:00Z',
                    'completionDate': '2020-02-02T00:00:00Z'
                }
            }
        )

    def test_build_request_parameters_with_time_range_start_only(self):
        """Test building the request parameters with time start only
        """
        time_range = (datetime(2020, 2, 1, tzinfo=timezone.utc), None)

        self.assertDictEqual(
            self.crawler._build_request_parameters(
                {'param1': 'value1', 'param2': 'value2'},
                time_range),
            {
                'params': {
                    'param1': 'value1',
                    'param2': 'value2',
                    'maxRecords': 100,
                    'page': 1,
                    'sortOrder': 'ascending',
                    'sortParam': 'published',
                    'startDate': '2020-02-01T00:00:00Z'
                }
            })

    def test_build_request_parameters_with_location(self):
        """Test building the request parameters with location"""
        time_range = (datetime(2020, 2, 1, tzinfo=timezone.utc), None)

        self.assertDictEqual(
            self.crawler._build_request_parameters(
                {'param1': 'value1', 'param2': 'value2'},
                location=shapely.geometry.Polygon(((1, 2), (1, 3), (2, 3), (1, 2)))),
            {
                'params': {
                    'param1': 'value1',
                    'param2': 'value2',
                    'maxRecords': 100,
                    'page': 1,
                    'sortOrder': 'ascending',
                    'sortParam': 'published',
                    'geometry': 'POLYGON ((1 2, 1 3, 2 3, 1 2))'
                }
            })

    def test_build_request_parameters_with_time_range_end_only(self):
        """Test building the request parameters without time range"""
        time_range = (None, datetime(2020, 2, 2, tzinfo=timezone.utc))

        self.assertDictEqual(
            self.crawler._build_request_parameters(
                {'param1': 'value1', 'param2': 'value2'}, time_range),
            {
                'params': {
                    'param1': 'value1',
                    'param2': 'value2',
                    'maxRecords': 100,
                    'page': 1,
                    'sortOrder': 'ascending',
                    'sortParam': 'published',
                    'completionDate': '2020-02-02T00:00:00Z'
                }
            })

    def test_get_datasets_info(self):
        """_get_datasets_info() should extract datasets information from a response page"""
        data_file_path = str(
            Path(__file__).parent.parent / 'data/creodias_eofinder/result_page.json')

        with open(data_file_path, 'r', encoding='utf-8') as f_h:
            page = f_h.read()

        expected_entry = json.loads(page)['features'][0]

        expected_result_metadata = expected_entry['properties'].copy()
        expected_result_metadata['geometry'] = json.dumps(expected_entry['geometry'])
        expected_result = crawlers_base.DatasetInfo(
            'https://zipper.creodias.eu/download/c6ff8061-df12-53b7-8dd8-fb834b998f5b',
            expected_result_metadata)

        dataset_infos = self.crawler._get_datasets_info(self.crawler._get_entries(page))
        self.assertEqual(next(dataset_infos), expected_result)


class ODataCrawlerTestCase(unittest.TestCase):
    """Tests for the ODataCrawler"""

    def test_init(self):
        """Test initialisation"""
        with mock.patch.object(crawlers_paginated_api.ODataCrawler,
                               '_build_request_parameters') as mock_build_params:
            crawler = crawlers_paginated_api.ODataCrawler.from_kwargs(
                url='https://foo/',
                collection='COLLECTION',
                time_range=[datetime(2026, 4, 1), datetime(2026, 4, 2)],
                location='POLYGON((-180 90,180 90,180 60,-180 60,-180 90))',
                search_terms={'param1': 'value1', 'param2': 2})

        self.assertEqual(crawler.root_url, 'https://foo')
        self.assertEqual(crawler.collection, 'COLLECTION')
        self.assertIsNone(crawler._collection_attributes)
        self.assertEqual(crawler.initial_offset, 0)
        self.assertEqual(crawler.request_parameters, mock_build_params.return_value)

    def test_url_property(self):
        """Test URL property"""
        crawler = crawlers_paginated_api.ODataCrawler.from_kwargs(
            url='https://foo/',
            collection='bar')
        self.assertEqual(crawler.url, 'https://foo/Products')

    def test_collection_attributes_property(self):
        """Test that the collection_attributes property fetches the """
        mock_response = mock.Mock()
        mock_response.json.return_value = [
            {'Name':'attr1', 'ValueType':'String'},
            {'Name':'attr2',  'ValueType':'Integer'}]
        with mock.patch.object(crawlers_paginated_api.ODataCrawler, '_http_get',
                               return_value=mock_response):
            crawler = crawlers_paginated_api.ODataCrawler.from_kwargs(
                url='https://foo/', collection='bar', search_terms={'attr1': 'baz', 'attr2': 'qux'})
            self.assertDictEqual(crawler.collection_attributes,
                                 {'attr1': 'String', 'attr2': 'Integer'})

    def test_build_request_parameters(self):
        """Test builsding requests parameters"""
        self.maxDiff = None
        with mock.patch.object(crawlers_paginated_api.ODataCrawler, '_build_attributes_filters',
                               return_value=['attribute_filter']):
            crawler = crawlers_paginated_api.ODataCrawler.from_kwargs(
                url='https://foo/',
                collection='COLLECTION',
                time_range=[datetime(2026, 4, 1), datetime(2026, 4, 2)],
                location='POINT(0 1)',
                search_terms={'param1': 'value1'},
                page_size=100,
            )
        self.assertDictEqual(
            crawler.request_parameters,
            {
                'params': {
                    '$skip': 0,
                    '$top': 100,
                    '$orderby': 'ContentDate/Start asc',
                    '$expand': 'Attributes',
                    '$filter': (
                        "Collection/Name eq 'COLLECTION' and attribute_filter and "
                        "ContentDate/End gt 2026-04-01T00:00:00Z and "
                        "ContentDate/Start lt 2026-04-02T00:00:00Z and "
                        "OData.CSC.Intersects(area=geography'SRID=4326;POINT (0 1)')")
                }
            }
        )

    def test_increment_offset(self):
        """Test incrementing the results offset"""
        crawler = crawlers_paginated_api.ODataCrawler.from_kwargs(
            url='https://foo/', collection='COLLECTION', page_size=100)
        self.assertEqual(crawler.page_offset, 0)
        crawler.increment_offset()
        self.assertEqual(crawler.page_offset, 100)

    def test_build_attributes_filters(self):
        """Test building attributes filters"""
        with mock.patch.object(crawlers_paginated_api.ODataCrawler,'collection_attributes',
                               new_callable=mock.PropertyMock) as mock_collection_attributes:
            crawler = crawlers_paginated_api.ODataCrawler.from_kwargs(
                url='https://foo/', collection='COLLECTION')
            mock_collection_attributes.return_value = {'key1': 'String', 'key2': 'Integer'}

            with self.assertLogs(crawler.logger, logging.WARNING):
                self.assertEqual(
                    crawler._build_attributes_filters({'key1': 'value1', 'key2': '2', 'key3': '3'}),
                    [
                        "Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'key1' and "
                            "att/OData.CSC.StringAttribute/Value eq 'value1')",
                        "Attributes/OData.CSC.IntegerAttribute/any(att:att/Name eq 'key2' and "
                            "att/OData.CSC.IntegerAttribute/Value eq '2')"
                    ])

    def test_get_entries(self):
        """Test retrieving dataset entries from the API response"""
        crawler = crawlers_paginated_api.ODataCrawler.from_kwargs(
            url='https://foo/', collection='COLLECTION')
        self.assertListEqual(
            crawler._get_entries(
                '{"@odata.context":"$metadata#Products(Attributes())","value":["d1", "d2"]}'),
            ['d1', 'd2'])

    def test_get_download_url(self):
        """Test getting the download URL for a dataset given its ID"""
        crawler_1 = crawlers_paginated_api.ODataCrawler.from_kwargs(
            url='https://foo/', collection='COLLECTION')
        self.assertEqual(
            crawler_1.get_download_url('bar'),
            "https://foo/Products(bar)/$value")
        crawler_2 = crawlers_paginated_api.ODataCrawler.from_kwargs(
            url='https://catalog.foo',
            download_url='https://download.foo/',
            collection='COLLECTION', )
        self.assertEqual(
            crawler_2.get_download_url('bar'),
            "https://download.foo/Products(bar)/$value")

    def test_get_datasets_info(self):
        """Test getting DatasetInfo objects from API entries
        """
        crawler = crawlers_paginated_api.ODataCrawler.from_kwargs(
            url='https://catalog.foo/',
            download_url='https://download.foo',
            collection='COLLECTION', )
        entries = [
            {'Id': 'id1', 'GeoFootprint': [[1, 2]]},
            {'Id': 'id2', 'attr1': 'value1', 'GeoFootprint': [[3, 4]]}]
        self.assertListEqual(
            list(crawler._get_datasets_info(entries)),
            [
                crawlers_base.DatasetInfo(
                    url='https://download.foo/Products(id1)/$value',
                    metadata={
                        'Id': 'id1',
                        'GeoFootprint': [[1, 2]],
                    }),
                crawlers_base.DatasetInfo(
                    url='https://download.foo/Products(id2)/$value',
                    metadata={
                        'Id': 'id2',
                        'attr1': 'value1',
                        'GeoFootprint': [[3, 4]],
                    }),
            ]
        )
