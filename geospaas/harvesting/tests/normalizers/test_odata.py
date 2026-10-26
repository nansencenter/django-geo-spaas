"""Tests for the OData API metadata normalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime

from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class ODataMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the STAC API attributes normalizer"""

    def setUp(self):
        self.normalizer = normalizers.odata.ODataMetadataNormalizer()

    def test_entry_title(self):
        """entry_title from ODataMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_entry_title(DatasetInfo('', {'Name': 'foo'})),
            'foo')

    def test_missing_raw_title(self):
        """A MetadataNormalizationError must be raised if the raw title
        attribute is absent
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_title(DatasetInfo(''))

    def test_entry_id(self):
        """entry_id from ODataMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo('', {'Name': 'foo'})),
            'foo')

    def test_entry_id_missing_attribute(self):
        """entry_id method must return None if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_summary_empty(self):
        """summary from ODataMetadataNormalizer"""
        dataset_info = DatasetInfo('', {})
        self.assertEqual(self.normalizer.get_summary(dataset_info), "")

    def test_time_coverage_start(self):
        """time_coverage_start from ODataMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('', {'ContentDate': {'Start': "2026-02-26T12:15:10.127242Z"}})),
            datetime(year=2026, month=2, day=26, hour=12, minute=15, second=10, tzinfo=tzutc()))

    def test_time_coverage_start_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_time_coverage_end(self):
        """time_coverage_end from ODataMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('', {'ContentDate': {'End': "2026-02-26T12:16:04.782454Z"}})),
            datetime(year=2026, month=2, day=26, hour=12, minute=16, second=4, tzinfo=tzutc()))

    def test_time_coverage_end_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_end(DatasetInfo(''))

    def test_get_keywords(self):
        """Test getting the keywords"""
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords:
            self.assertEqual(
                self.normalizer.get_keywords(DatasetInfo('https://foo', {
                    'Attributes': [
                        {'Name': 'platformShortName', 'Value': 'foo', 'ValueType': 'String'},
                        {'Name': 'instrumentShortName', 'Value': 'bar', 'ValueType': 'String'},
                    ]
                })),
                mock_find_keywords.return_value)
            mock_find_keywords.assert_called_once_with([
                {'kind': 'gcmd_platform', 'data__icontains': 'foo'},
                {'kind': 'gcmd_instrument', 'data__icontains': 'bar'},
            ])

    def test_location_geometry(self):
        """location_geometry from ODataMetadataNormalizer"""

        dataset_info = DatasetInfo('', {
            'GeoFootprint': {
                "type": "Polygon",
                "coordinates": [[
                    [-85.371239, 55.501102],
                    [-83.847801, 58.734837],
                    [-91.094086, 59.484203],
                    [-92.010674, 56.223198],
                    [-85.371239, 55.501102],
                ]]
            }
        })

        self.assertEqual(
            self.normalizer.get_location_geometry(dataset_info),
            "POLYGON ((-85.371239 55.501102, -83.847801 58.734837, "
            "-91.094086 59.484203, -92.010674 56.223198, "
            "-85.371239 55.501102))")

    def test_location_geometry_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_location_geometry(DatasetInfo(''))

    def test_get_extra_urls(self):
        """Test getting the S3 URL"""
        self.assertListEqual(
            self.normalizer.get_extra_urls(DatasetInfo('https://foo', {'S3Path': 'bar/baz'})),
            ['s3://bar/baz'])
        self.assertListEqual(
            self.normalizer.get_extra_urls(DatasetInfo('https://foo', {})),
            [])
