"""Tests for the REMSS GMI normalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime
from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class REMSSGMIMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the REMSS GMI ftp normalizer"""
    def setUp(self):
        self.normalizer = normalizers.remss_gmi.REMSSGMIMetadataNormalizer()

    def test_entry_title(self):
        """entry_title from REMSSGMIMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_entry_title(DatasetInfo('')),
            'Atmosphere parameters from Global Precipitation Measurement Microwave Imager')

    def test_entry_id(self):
        """entry_id from REMSSGMIMetadataNormalizer """
        dataset_info = DatasetInfo(
            'ftp://ftp.remss.com/gmi/bmaps_v08.2/y2014/m06/f35_20140603v8.2.gz')
        self.assertEqual(self.normalizer.get_entry_id(dataset_info),
                         'f35_20140603v8.2')

    def test_entry_id_error(self):
        """a MetadataNormalizationError must be raised when an entry_id cannot be found"""
        # wrong file format
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo('ftp://foo/bar.txt'))
        # no url attribute
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_summary(self):
        """summary from REMSSGMIMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo('')),
            'Description: GMI is a dual-polarization, multi-channel, conical-scanning, passive '
            'microwave radiometer with frequent revisit times.;Processing level: 3')

    def test_time_coverage_start_month_file(self):
        """shall return the propert starting time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('ftp://ftp.remss.com/gmi/bmaps_v08.2/y2014/m06/f35_201406v8.2.gz')),
            datetime(year=2014, month=6, day=1, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_single_day_file(self):
        """shall return the propert starting time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('ftp://ftp.remss.com/gmi/bmaps_v08.2/y2014/m06/f35_20140604v8.2.gz')),
            datetime(year=2014, month=6, day=4, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_week_file(self):
        """shall return the propert starting time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('ftp://ftp.remss.com/gmi/bmaps_v08.2/weeks/f35_20140614v8.2.gz')),
            datetime(year=2014, month=6, day=8, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_3d3_file(self):
        """shall return the propert starting time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'ftp://ftp.remss.com/gmi/bmaps_v08.2/y2014/m06/f35_20140630v8.2_d3d.gz')),
            datetime(year=2014, month=6, day=28, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_time_coverage_end_single_day_file(self):
        """shall return the propert end time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('ftp://ftp.remss.com/gmi/bmaps_v08.2/y2014/m06/f35_20140620v8.2.gz')),
            datetime(year=2014, month=6, day=21, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_end_month_file(self):
        """shall return the propert end time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('ftp://ftp.remss.com/gmi/bmaps_v08.2/y2014/m06/f35_201406v8.2.gz')),
            datetime(year=2014, month=7, day=1, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_end_week_file(self):
        """shall return the propert end time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('ftp://ftp.remss.com/gmi/bmaps_v08.2/weeks/f35_20140614v8.2.gz')),
            datetime(year=2014, month=6, day=15, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_end_3d3_file(self):
        """shall return the propert end time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'ftp://ftp.remss.com/gmi/bmaps_v08.2/y2014/m06/f35_20140630v8.2_d3d.gz')),
            datetime(year=2014, month=7, day=1, hour=0, minute=0, second=0, tzinfo=tzutc()))

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
        """geometry from REMSSGMIMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_location_geometry(DatasetInfo('')),
            'POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))')

    def test_dataset_parameters(self):
        """dataset_parameters from CEDAESACCIMetadataNormalizer """
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list') as mock_get_gcmd_method:
            self.assertEqual(
                self.normalizer.get_dataset_parameters(DatasetInfo('')),
                mock_get_gcmd_method.return_value)
