"""Tests for the resto API metadata normalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime

from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class STACMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the STAC API attributes normalizer"""

    def setUp(self):
        self.normalizer = normalizers.stac.STACMetadataNormalizer()

    def test_entry_title(self):
        """entry_title from STACMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_entry_title(DatasetInfo('', {'id': 'foo'})),
            'foo')

    def test_missing_raw_title(self):
        """A MetadataNormalizationError must be raised if the raw title
        attribute is absent
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_title(DatasetInfo(''))

    def test_entry_id(self):
        """entry_id from STACMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo('', {'id': 'foo'})),
            'foo')

    def test_entry_id_missing_attribute(self):
        """entry_id method must return None if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_summary_description_only(self):
        """summary from STACMetadataNormalizer"""
        dataset_info = DatasetInfo('', {
            'properties': {
                "instruments": ["sar"],
                "platform": "sentinel-1a",
            },
        })
        self.assertEqual(
            self.normalizer.get_summary(dataset_info),
            "Description: platform=sentinel-1a, instruments=['sar']")

    def test_summary_with_processing_level(self):
        """summary from STACMetadataNormalizer with processing level"""
        dataset_info = DatasetInfo('', {
            'properties': {
                "instruments": ["sar"],
                "platform": "sentinel-1a",
                "processing:level": "L1",
            },
        })
        self.assertEqual(
            self.normalizer.get_summary(dataset_info),
            "Description: platform=sentinel-1a, instruments=['sar'];Processing level: 1")

    def test_summary_wrong_processing_level_type(self):
        """Processing level should not be included if it has the wrong
        type in the raw data
        """
        dataset_info = DatasetInfo('', {
            'properties': {
                "instruments": ["sar"],
                "platform": "sentinel-1a",
                "processing:level": 1,
            },
        })
        self.assertEqual(
            self.normalizer.get_summary(dataset_info),
            "Description: platform=sentinel-1a, instruments=['sar']")

    def test_summary_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_summary(DatasetInfo(''))

    def test_time_coverage_start(self):
        """time_coverage_start from STACMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('', {'properties': {'start_datetime': "2026-02-26T12:15:10.127242Z"}})),
            datetime(year=2026, month=2, day=26, hour=12, minute=15, second=10, tzinfo=tzutc()))

    def test_time_coverage_start_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_time_coverage_end(self):
        """time_coverage_end from STACMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('', {'properties': {'end_datetime': "2026-02-26T12:16:04.782454Z"}})),
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
                    'properties': {
                        'platform': 'foo',
                        'instruments': ['bar', 'baz'],
                        'processing:facility': 'qux',
                    }
                })),
                mock_find_keywords.return_value)
            mock_find_keywords.assert_called_once_with([
                {'kind': 'gcmd_platform', 'data__icontains': 'foo'},
                {'kind': 'gcmd_instrument', 'data__icontains': 'bar'},
                {'kind': 'gcmd_instrument', 'data__icontains': 'baz'},
                {'kind': 'gcmd_provider', 'data__icontains': 'qux'},
            ])

    def test_location_geometry(self):
        """location_geometry from STACMetadataNormalizer"""

        dataset_info = DatasetInfo('', {
            'geometry': {
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
        """Test getting the S3 URL from metadata"""
        self.assertListEqual(self.normalizer.get_extra_urls(DatasetInfo('', {})), [])
        self.assertListEqual(self.normalizer.get_extra_urls(DatasetInfo('', {'links': []})), [])
        self.assertListEqual(
            self.normalizer.get_extra_urls(DatasetInfo('', {'links': [{'a': 'b'}]})), [])
        self.assertListEqual(
            self.normalizer.get_extra_urls(DatasetInfo('', {'links': [{'auth:refs': ['s3'],
                                                            'href': 's3://bucket/folder/'}]})),
            ['s3://bucket/folder/'])