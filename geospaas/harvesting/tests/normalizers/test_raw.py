"""Tests for the RawMetadataNormalizer"""
import unittest
from datetime import datetime, timezone

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo


class RawMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the raw normalizer"""
    def setUp(self):
        self.normalizer = normalizers.raw.RawMetadataNormalizer()

    def test_get_entry_id(self):
        """Test getting the entry ID from the URL"""
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(url='https://foo/bar/baz.nc')),
            'baz')
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(url='https://foo/bar/baz.nc.gz')),
            'baz')
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(url='https://foo/bar/baz.h5')),
            'baz')
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(url='https://foo/bar/baz.h5.gz')),
            'baz')
        self.assertIsNone(self.normalizer.get_entry_id(DatasetInfo(url='https://foo')))

    def test_get_time_coverage_start(self):
        """Test getting the start of the time coverage"""
        self.assertIsNone(self.normalizer.get_time_coverage_start(DatasetInfo('')))

    def test_get_time_coverage_with_regex(self):
        """Test getting the the time coverage with a regex"""
        n = normalizers.raw.RawMetadataNormalizer(
            time_regex=r'.*/bar_(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2}).nc',
            time_offset='1d')
        self.assertEqual(
            n.get_time_coverage_start(DatasetInfo(url='https://foo/bar_20250502.nc')),
            datetime(2025, 5, 2, tzinfo=timezone.utc))
        self.assertEqual(
            n.get_time_coverage_end(DatasetInfo(url='https://foo/bar_20250502.nc')),
            datetime(2025, 5, 3, tzinfo=timezone.utc))

        n = normalizers.raw.RawMetadataNormalizer(
            time_regex=(r'.*/bar_(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})'
                        r'T(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})Z.nc'),
            time_offset='1h')
        self.assertEqual(
            n.get_time_coverage_start(DatasetInfo(url='https://foo/bar_20250502T095612Z.nc')),
            datetime(2025, 5, 2, 9, 56, 12, tzinfo=timezone.utc))
        self.assertEqual(
            n.get_time_coverage_end(DatasetInfo(url='https://foo/bar_20250502T095612Z.nc')),
            datetime(2025, 5, 2, 10, 56, 12, tzinfo=timezone.utc))

    def test_get_time_coverage_end(self):
        """Test getting the end of the time coverage"""
        self.assertIsNone(self.normalizer.get_time_coverage_end(DatasetInfo('')))

    def test_get_location_geometry(self):
        """Test getting the geometry"""
        self.assertIsNone(self.normalizer.get_location_geometry(DatasetInfo('')))

    def test_get_tags(self):
        """Test getting the tags keyword arguments"""
        self.assertEqual(
            self.normalizer.get_tags(DatasetInfo('', {'foo': 'bar', 'baz': 'qux'})),
            [{'name': 'foo', 'value': 'bar'}, {'name': 'baz', 'value': 'qux'}])
