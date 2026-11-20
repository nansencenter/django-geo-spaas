"""Tests for the amsr2_asi normalizer"""

import unittest
import unittest.mock as mock
from datetime import datetime, timezone

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class AMSR2ASIMetadataNormalizerTests(unittest.TestCase):
    """Tests for AMSR2ASIMetadataNormalizer"""

    def setUp(self):
        self.normalizer = normalizers.amsr2_asi.AMSR2ASIMetadataNormalizer()

    def test_get_entry_title(self):
        """Test getting the title"""
        self.assertEqual(self.normalizer.get_entry_title(DatasetInfo(url='https://foo')),
                         'ASI sea ice concentration from AMSR2')

    def test_get_entry_id(self):
        """Test getting the ID"""
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(
                url='https://data.seaice.uni-bremen.de/amsr2/asi_daygrid_swath/n6250/netcdf/'
                    '2024/asi-AMSR2-n6250-20240101-v5.4.nc')),
            'asi-AMSR2-n6250-20240101-v5.4')

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
            'Description: Sea ice concentration retrieved with the ARTIST Sea Ice (ASI) algorithm '
            '(Spreen et al., 2008) which is applied to microwave radiometer data of the sensor '
            'AMSR2 (Advanced Microwave Scanning Radiometer 2) on the JAXA satellite GCOM-W1.;'
            'Processing level: 3')

    def test_get_time_coverage_start(self):
        """Test getting the start of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                url='https://data.seaice.uni-bremen.de/amsr2/asi_daygrid_swath/n6250/netcdf/'
                    '2024/asi-AMSR2-n6250-20240101-v5.4.nc')),
            datetime(year=2024, month=1, day=1, tzinfo=timezone.utc))

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
                url='https://data.seaice.uni-bremen.de/amsr2/asi_daygrid_swath/n6250/netcdf/'
                    '2024/asi-AMSR2-n6250-20240101-v5.4.nc')),
            datetime(year=2024, month=1, day=2, tzinfo=timezone.utc))

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
                url='https://data.seaice.uni-bremen.de/amsr2/asi_daygrid_swath/n6250/netcdf/'
                    '2024/asi-AMSR2-n6250-20240101-v5.4.nc')),
            'POLYGON((-180 40,180 40,180 90,-180 90,-180 40))')
        self.assertEqual(
            self.normalizer.get_location_geometry(DatasetInfo(
                url='https://data.seaice.uni-bremen.de/amsr2/asi_daygrid_swath/s6250/netcdf/'
                    '2024/asi-AMSR2-s6250-20240101-v5.4.nc')),
            'POLYGON((-180 -40,180 -40,180 -90,-180 -90,-180 -40))')

    def test_location_geometry_error(self):
        """get_location_geometry() should raise an exception when the
        hemisphere can't be determined
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_location_geometry(
                DatasetInfo(url='foo/asi-AMSR2-a6250-20240101-v5.4.nc'))
