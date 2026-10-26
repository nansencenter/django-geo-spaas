"""Tests for the nextsim normalizer"""

import unittest
import unittest.mock as mock
from datetime import datetime, timezone

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class DownscaledECMWFMetadataNormalizerTests(unittest.TestCase):
    """Tests for DownscaledECMWFMetadataNormalizer"""

    def setUp(self):
        self.normalizer = normalizers.downscaled_ecmwf.DownscaledECMWFMetadataNormalizer()

    def test_get_entry_title(self):
        """Test getting the title"""
        self.assertEqual(self.normalizer.get_entry_title(DatasetInfo('')),
                         'Downscaled ECMWF seasonal forecast')

    def test_get_entry_id(self):
        """Test getting the ID"""
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo('/foo/bar/Seasonal_Nov23_SDA_n15.nc')),
            'Seasonal_Nov23_SDA_n15')
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo('/foo/bar/Seasonal_Nov23_SAT_n15.nc')),
            'Seasonal_Nov23_SAT_n15')

    def test_entry_id_error(self):
        """A MetadataNormalizationError should be raised if the url
        attribute is missing or the ID is not found
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo('foo'))

    def test_summary(self):
        """Test getting the summary"""
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo('')),
            "Downscaled version of ECMWF's seasonal forecasts")

    def test_get_time_coverage_start(self):
        """Test getting the start of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('', {'date': '2023-11-14 13:21:08'})),
            datetime(year=2023, month=11, day=1, tzinfo=timezone.utc))

    def test_missing_time_coverage_start(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_start raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_get_time_coverage_end(self):
        """Test getting the end of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo('', {'date': '2023-11-14 13:21:08'})),
            datetime(year=2024, month=5, day=1, tzinfo=timezone.utc))

    def test_missing_time_coverage_end(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_end raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_end(DatasetInfo(''))

    def test_get_keywords(self):
        """Test getting the keywords"""
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords:
            self.assertEqual(
                self.normalizer.get_keywords(DatasetInfo(url='https://foo')),
                mock_find_keywords.return_value)

    def test_get_location_geometry(self):
        """get_location_geometry() should return the location
        of the dataset
        """
        self.assertEqual(self.normalizer.get_location_geometry(DatasetInfo('')), '')
