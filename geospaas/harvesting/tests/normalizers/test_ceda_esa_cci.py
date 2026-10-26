"""Tests for the ESA CCI normalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime
from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class CEDAESACCIMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the REMSS GMI ftp normalizer"""
    def setUp(self):
        self.normalizer = normalizers.ceda_esa_cci.CEDAESACCIMetadataNormalizer()

    def test_entry_title(self):
        """entry_title from CEDAESACCIMetadataNormalizer """
        self.assertEqual(self.normalizer.get_entry_title(DatasetInfo('')), 'ESA SST CCI OSTIA L4 Climatology')

    def test_entry_id(self):
        """entry_id from CEDAESACCIMetadataNormalizer """
        attributes = DatasetInfo(
            url='ftp://ftp.ceda.ac.uk/neodc/esacci/sst/data/CDR_v2/Climatology/L4/v2.1/'
                'D001-ESACCI-L4_GHRSST-SSTdepth-OSTIA-GLOB_CDR2.1-v02.0-fv01.0.nc')
        self.assertEqual(self.normalizer.get_entry_id(attributes),
                         'D001-ESACCI-L4_GHRSST-SSTdepth-OSTIA-GLOB_CDR2.1-v02.0-fv01.0')

    def test_entry_id_error(self):
        """a MetadataNormalizationError must be raised when an entry_id cannot be found"""
        # wrong file format
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(url='ftp://foo/bar.txt'))
        # no url attribute
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_summary(self):
        """summary from CEDAESACCIMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo('')),
            'Description: This v2.1 SST_cci Climatology Data Record (CDR) consists of Level 4 daily'
            ' climatology files gridded on a 0.05 degree grid.;Processing level: 4;'
            'Product: ESA SST CCI Climatology')

    def test_time_coverage_start(self):
        """time_coverage_start from CEDAESACCIMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                url='ftp://anon-ftp.ceda.ac.uk/neodc/esacci/sst/data/CDR_v2/Climatology/L4/v2.1/'
                    'D365-ESACCI-L4_GHRSST-SSTdepth-OSTIA-GLOB_CDR2.1-v02.0-fv01.0.nc')),
            datetime(year=1982, month=12, day=31, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_time_coverage_end(self):
        """time_coverage_end from CEDAESACCIMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                url='ftp://anon-ftp.ceda.ac.uk/neodc/esacci/sst/data/CDR_v2/Climatology/L4/v2.1/'
                    'D365-ESACCI-L4_GHRSST-SSTdepth-OSTIA-GLOB_CDR2.1-v02.0-fv01.0.nc')),
            datetime(year=2010, month=12, day=31, hour=0, minute=0, second=0, tzinfo=tzutc()))

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
        """geometry from CEDAESACCIMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_location_geometry(DatasetInfo('')),
            'POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))')

    def test_dataset_parameters(self):
        """dataset_parameters from CEDAESACCIMetadataNormalizer """
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list') as mock_get_gcmd_method:
            self.assertEqual(
                self.normalizer.get_dataset_parameters(DatasetInfo('')),
                mock_get_gcmd_method.return_value)
