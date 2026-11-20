"""Tests for the NansatMetadataNormalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime, timezone

import shapely.geometry

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class NansatMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the nansat normalizer"""
    def setUp(self):
        self.normalizer = normalizers.nansat.NansatMetadataNormalizer()

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
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(url='', metadata={'entry_id': 'baz'})),
            'baz')
        self.assertIsNone(self.normalizer.get_entry_id(DatasetInfo(url='https://foo')))

    def test_get_entry_title(self):
        """Test getting the title"""
        self.assertEqual(
            self.normalizer.get_entry_title(DatasetInfo('', {'entry_title': 'foo'})),
            'foo')

    def test_get_summary(self):
        """Test getting the summary"""
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo('', {'summary': 'lorem ipsum'})),
            'lorem ipsum')

    def test_get_time_coverage_start(self):
        """Test getting the start of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('', {'time_coverage_start': "20200101T000001"})),
            datetime(year=2020, month=1, day=1, hour=0, minute=0, second=1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('', {'time_coverage_start': "20200101T000001Z"})),
            datetime(year=2020, month=1, day=1, hour=0, minute=0, second=1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('', {'time_coverage_start': "2020-01-01T00:00:01"})),
            datetime(year=2020, month=1, day=1, hour=0, minute=0, second=1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('', {'time_coverage_start': "2020-01-01T00:00:01Z"})),
            datetime(year=2020, month=1, day=1, hour=0, minute=0, second=1, tzinfo=timezone.utc))

    def test_missing_time_coverage_start(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_start raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(url='https://foo'))

    def test_get_time_coverage_end(self):
        """Test getting the end of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('', {'time_coverage_end': "20200101T000559"})),
            datetime(year=2020, month=1, day=1, hour=0, minute=5, second=59, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('', {'time_coverage_end': "20200101T000559Z"})),
            datetime(year=2020, month=1, day=1, hour=0, minute=5, second=59, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('', {'time_coverage_end': "2020-01-01T00:05:59"})),
            datetime(year=2020, month=1, day=1, hour=0, minute=5, second=59, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('', {'time_coverage_end': "2020-01-01T00:05:59Z"})),
            datetime(year=2020, month=1, day=1, hour=0, minute=5, second=59, tzinfo=timezone.utc))

    def test_missing_time_coverage_end(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_end raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_end(DatasetInfo(url='https://foo'))

    def test_get_keywords(self):
        """Test getting the keywords"""
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords:
            self.assertEqual(
                self.normalizer.get_keywords(DatasetInfo(
                    url='https://foo',
                    metadata={
                        'platform': 'platform1',
                        'instrument': 'instrument1',
                        'provider': 'provider1',
                        'gcmd_location': 'gcmd_location1',
                        'ISO_topic_category': 'category1'
                    })),
                mock_find_keywords.return_value)
            mock_find_keywords.assert_called_with([
                {'kind': 'gcmd_platform', 'data__icontains': 'platform1'},
                {'kind': 'gcmd_instrument', 'data__icontains': 'instrument1'},
                {'kind': 'gcmd_provider', 'data__icontains': 'provider1'},
                {'kind': 'gcmd_location', 'data__icontains': 'gcmd_location1'},
                {'kind': 'iso19115_topic_category', 'data__icontains': 'category1'},
            ])

    def test_get_location_geometry(self):
        """Test getting the geometry"""
        self.assertEqual(
            self.normalizer.get_location_geometry(
                DatasetInfo('', {'location_geometry': shapely.geometry.Point(1, 1)})),
            'POINT (1 1)')

    def test_missing_geometry(self):
        """An empty string must be returned when the geometry raw
        attribute is missing
        """
        self.assertEqual(self.normalizer.get_location_geometry(DatasetInfo(url='https://foo')), '')

    def test_get_dataset_parameters(self):
        """Test getting dataset parameters"""
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list'
                        ) as mock_create_parameter_list:
            self.normalizer.get_dataset_parameters(
                DatasetInfo(url='https://foo', metadata={'dataset_parameters': ['foo', 'bar']}))
            mock_create_parameter_list.assert_called_with(['foo', 'bar'])

        self.assertListEqual(
            self.normalizer.get_dataset_parameters(DatasetInfo(url='https://foo')),
            [])
