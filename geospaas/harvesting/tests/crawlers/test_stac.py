import unittest
import unittest.mock as mock
from datetime import datetime

from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.crawlers.stac import STACCrawler


class STACCrawlerTestCase(unittest.TestCase):
    """Tests for STACCrawler"""

    def setUp(self):
        self.mock_client = mock.Mock()
        self.client_patcher = mock.patch('pystac_client.Client.open', return_value=self.mock_client)
        self.client_patcher.start()

        self.crawler = STACCrawler(
            url='http://foo',
            collections=['bar', 'baz'],
            time_range=[datetime(2025, 1, 1), datetime(2025, 1, 2)],
            location='POINT(0 1)',
            username=None,
            password=None,
            filter=None,
            limit=100)

    def tearDown(self):
        self.client_patcher.stop()
        self.mock_client = None

    def test_instantiation(self):
        """Test that a pystac client is created"""
        self.assertEqual(self.crawler._client, self.mock_client)

    def test_crawl(self):
        """Test crawling"""
        self.mock_client.search.return_value.items_as_dicts.return_value = [
            {'assets': {'product': {'href': 'https://foo'}}, 'bar': 'baz'},
            {'assets': {'Product': {'href': 'https://qux'}}, 'quux': 'corge'},
        ]
        self.assertListEqual(
            list(self.crawler.crawl()),
            [
                DatasetInfo(
                    url='https://foo',
                    metadata={'assets': {'product': {'href': 'https://foo'}}, 'bar': 'baz'}),
                DatasetInfo(
                    url='https://qux',
                    metadata={'assets': {'Product': {'href': 'https://qux'}}, 'quux': 'corge'}),
            ]
        )

    def test_crawl_no_url(self):
        """An exception must be raised if no URL is found"""
        self.mock_client.search.return_value.items_as_dicts.return_value = [
            {'assets': {'data_product': {'href': 'https://foo'}}, 'bar': 'baz'},
            {'assets': {'Product': {'href': 'https://qux'}}, 'quux': 'corge'},
        ]
        with self.assertRaises(ValueError):
            list(self.crawler.crawl())
