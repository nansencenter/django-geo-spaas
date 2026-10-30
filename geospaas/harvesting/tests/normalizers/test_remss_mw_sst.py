"""Tests for the REMSS MW SST normalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime
from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class REMSSMWSSTMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the REMSS MW SST ftp normalizer"""
    def setUp(self):
        self.normalizer = normalizers.remss_mw_sst.REMSSMWSSTMetadataNormalizer()

    def test_entry_title(self):
        """entry_title from REMSSMWSSTMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_entry_title(DatasetInfo('')),
            'Sea surface temperature from passive microwave sensors')

    def test_entry_id(self):
        """entry_id from REMSSMWSSTMetadataNormalizer """
        dataset_info = DatasetInfo(
            'https://data.remss.com/SST/daily/mw/v05.1/netcdf/2024/'
            '20240108120000-REMSS-L4_GHRSST-SSTfnd-MW_OI-GLOB-v02.0-fv05.1.nc')
        self.assertEqual(self.normalizer.get_entry_id(dataset_info),
                         '20240108120000-REMSS-L4_GHRSST-SSTfnd-MW_OI-GLOB-v02.0-fv05.1')

    def test_entry_id_error(self):
        """a MetadataNormalizationError must be raised when an entry_id cannot be found"""
        # wrong file format
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo('ftp://foo/bar.txt'))
        # no url attribute
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_summary(self):
        """summary from REMSSMWSSTMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo('')),
            'Description: Sea surface temperature from TMI, AMSR-E, AMSR2, WindSat, GMI;'
            'Processing level: 4')

    def test_time_coverage_start(self):
        """shall return the propert starting time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://data.remss.com/SST/daily/mw/v05.1/netcdf/2024/'
                '20240108120000-REMSS-L4_GHRSST-SSTfnd-MW_OI-GLOB-v02.0-fv05.1.nc')),
            datetime(year=2024, month=1, day=8, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_time_coverage_end(self):
        """shall return the propert end time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://data.remss.com/SST/daily/mw/v05.1/netcdf/2024/'
                '20240108120000-REMSS-L4_GHRSST-SSTfnd-MW_OI-GLOB-v02.0-fv05.1.nc')),
            datetime(year=2024, month=1, day=9, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_end_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_end(DatasetInfo(''))

    def test_get_keywords(self):
        """Test getting the keywords"""
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords:
            self.assertEqual(
                self.normalizer.get_keywords(DatasetInfo(url='https://foo')),
                mock_find_keywords.return_value)

    def test_location_geometry(self):
        """geometry from REMSSMWSSTMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_location_geometry(DatasetInfo('')),
            'POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))')

    def test_dataset_parameters(self):
        """dataset_parameters from CEDAESACCIMetadataNormalizer """
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list') as mock_get_gcmd_method:
            self.assertEqual(
                self.normalizer.get_dataset_parameters(DatasetInfo('')),
                mock_get_gcmd_method.return_value)
