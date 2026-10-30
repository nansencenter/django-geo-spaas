"""Tests for the amsr2_asi normalizer"""

import unittest
import unittest.mock as mock
from datetime import datetime, timezone

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class MarineHeatWavesMetadataNormalizerTests(unittest.TestCase):
    """Tests for MarineHeatWavesMetadataNormalizer"""

    def setUp(self):
        self.normalizer = normalizers.marine_heatwaves.MarineHeatWavesMetadataNormalizer()

    def test_get_entry_title(self):
        """Test getting the title"""
        self.assertEqual(self.normalizer.get_entry_title(DatasetInfo(url='https://foo')),
                         'NOAA marine heatwaves')

    def test_get_entry_id(self):
        """Test getting the ID"""
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(
                url='https://www.star.nesdis.noaa.gov/pub/socd/mecb/crw/data/marine_heatwave/v1.0.1/category/nc/2025/noaa-crw_mhw_v1.0.1_category_20250101.nc')),
            'noaa-crw_mhw_v1.0.1_category_20250101')

    def test_entry_id_error(self):
        """A MetadataNormalizationError should be raised if the url
        attribute is missing or the ID is not found
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(url='https://foo'))
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(url='foo'))

    def test_summary(self):
        """Test getting the summary"""
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(url='https://foo')),
            'Marine heatwaves product derived by applying the Marine Heatwave algorithm of '
            'Hobday et al. (2018)1 to the CRW daily global 5km CoralTemp satellite SST data '
            'product')

    def test_get_time_coverage_start(self):
        """Test getting the start of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                url='https://www.star.nesdis.noaa.gov/pub/socd/mecb/crw/data/marine_heatwave/v1.0.1/'
                    'category/nc/2025/noaa-crw_mhw_v1.0.1_category_20250101.nc')),
            datetime(year=2025, month=1, day=1, tzinfo=timezone.utc))

    def test_missing_time_coverage_start(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_start raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(url='https://foo'))

    def test_get_time_coverage_end(self):
        """Test getting the end of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                url='https://www.star.nesdis.noaa.gov/pub/socd/mecb/crw/data/marine_heatwave/v1.0.1/'
                    'category/nc/2025/noaa-crw_mhw_v1.0.1_category_20250101.nc')),
            datetime(year=2025, month=1, day=2, tzinfo=timezone.utc))

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
                self.normalizer.get_keywords(DatasetInfo(url='https://foo')),
                mock_find_keywords.return_value)

    def test_get_location_geometry(self):
        """get_location_geometry() should return the location
        of the dataset
        """
        self.assertEqual(
            self.normalizer.get_location_geometry(DatasetInfo(
                url='https://foo')),
            'POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))')

    def test_dataset_parameters(self):
        """No standard parameters"""
        self.assertListEqual(self.normalizer.get_dataset_parameters(DatasetInfo('https://foo')),
                             [])