"""Tests for the nextsim normalizer"""

import unittest
import unittest.mock as mock
from datetime import datetime, timezone

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class NextsimMetadataNormalizerTests(unittest.TestCase):
    """Tests for NextsimMetadataNormalizer"""

    def setUp(self):
        self.normalizer = normalizers.nextsim.NextsimMetadataNormalizer()

    def test_get_entry_title(self):
        """Test getting the title"""
        self.assertEqual(self.normalizer.get_entry_title(DatasetInfo('', {'title': 'foo'})), 'foo')

    def test_missing_title(self):
        """A MetadataNormalizationError should be raised if the raw title
        is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_title(DatasetInfo(''))

    def test_get_entry_id(self):
        """Test getting the ID"""
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(
                '/foo/bar/20210823_hr-nersc-MODEL-nextsimf-ARC-b20210817-fv00.0.nc')),
            '20210823_hr-nersc-MODEL-nextsimf-ARC-b20210817-fv00.0')

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
            'Description: The Arctic Sea Ice Analysis and Forecast system uses the neXtSIM '
            'stand-alone sea ice model running the Brittle-Bingham-Maxwell sea ice rheology on an '
            'adaptive triangular mesh of 10 km average cell length.;'
            'Processing level: 4;'
            'Product: ARCTIC_ANALYSISFORECAST_PHY_ICE_002_011')

    def test_get_time_coverage_start(self):
        """Test getting the start of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo('', {'field_date': '2021-08-23'})),
            datetime(year=2021, month=8, day=23, tzinfo=timezone.utc))

    def test_missing_time_coverage_start(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_start raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_get_time_coverage_end(self):
        """Test getting the end of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo('', {'field_date': '2021-08-23'})),
            datetime(year=2021, month=8, day=24, tzinfo=timezone.utc))

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
        self.assertEqual(
            self.normalizer.get_location_geometry(DatasetInfo('')),
            'POLYGON((-180 62,180 62,180 90,-180 90,-180 62))')
