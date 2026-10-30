"""Tests for the Radarsat 2 CSV normalizer"""
import datetime as dt
import unittest
import unittest.mock as mock

from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError

class Radarsat2CSVNormalizerTests(unittest.TestCase):
    """Tests for the well known attributes normalizer"""

    def setUp(self):
        self.dataset_info = DatasetInfo('', {
            'Result Number': '1',
            'Satellite': 'RADARSAT-2',
            'Date': '2020-07-16 02:14:27 GMT',
            'Beam Mode': 'ScanSAR Wide A (W1 W2 W3 S7)',
            'Polarization': 'HH HV',
            'Type': 'SGF',
            'Image Id': '831163',
            'Image Info': ('"{""headers"":[""Product Type"" ""LUT Applied"" ""Sampled Pixel ' +
            'Spacing (Panchromatic)"" ""Product Format"" ""Geodetic Terrain Height""] ""' +
            'relatedProducts"":[{""values"":[""SGF"" ""Ice"" ""100.0"" ""GeoTIFF"" ""0.00186""' +
            ']}] ""collectionID"":""Radarsat2"" ""imageID"":""7337877""}"'),
            'Metadata': 'dummy value',
            'Reason': '',
            'Sensor Mode': 'ScanSAR Wide',
            'Orbit Direction': 'Ascending',
            'Order Key': 'RS2_OK121511_PK1076349_DK1021326_SCWA_20200716_021427_HH_HV_SGF',
            'SIP Size (MB)': '84',
            'Service UUID': 'SERVICE-RSAT2_001-000000000000000000',
            'Footprint': ('-146.008396 73.905427 -143.459486 72.212173 -127.936480 73.451549'+
            ' -128.875274 75.249738 -146.008396 73.905427 '),
            'Look Orientation': 'Right',
            'Band': 'C',
            'Title': 'rsat2_20200716_N7370W13656',
            'Options': '',
            'Absolute Orbit': '65706',
            'Orderable': 'TRUE'})

        self.normalizer = normalizers.radarsat2_csv.Radarsat2CSVMetadataNormalizer()

    def test_get_entry_title(self):
        """ shall return title composed of several fields """
        self.assertEqual(
            self.normalizer.get_entry_title(self.dataset_info),
            'rsat2_20200716_N7370W13656 HH HV ScanSAR Wide A (W1 W2 W3 S7)')

    def test_missing_entry_title(self):
        """A MetadataNormalizationError must be raised when the raw
        attributes used to generate the title are missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_title(DatasetInfo(''))

    def test_get_entry_id(self):
        """ shall return RS2 image name """
        self.assertEqual(
            self.normalizer.get_entry_id(self.dataset_info),
            'RS2_OK121511_PK1076349_DK1021326_SCWA_20200716_021427_HH_HV_SGF')

    def test_missing_entry_id(self):
        """A MetadataNormalizationError must be raised when the raw
        Order Key attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_get_time_coverage_start(self):
        """shall return the proper starting time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_start(self.dataset_info),
            dt.datetime(year=2020, month=7, day=16, hour=2, minute=14, second=27, tzinfo=tzutc()))

    def test_missing_time_coverage_start(self):
        """A MetadataNormalizationError must be raised when the
        Date raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_get_time_coverage_end(self):
        """shall return the proper starting time for hardcoded normalizer """
        self.assertEqual(
            self.normalizer.get_time_coverage_end(self.dataset_info),
            dt.datetime(year=2020, month=7, day=16, hour=2, minute=19, second=27, tzinfo=tzutc()))

    def test_missing_time_coverage_end(self):
        """A MetadataNormalizationError must be raised when the
        Date raw attribute is missing
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
        """ shall return POLYGON """
        self.assertEqual(
            self.normalizer.get_location_geometry(self.dataset_info),
            ('POLYGON((-146.008396 73.905427, -143.459486 72.212173, -127.936480 73.451549, '+
             '-128.875274 75.249738, -146.008396 73.905427))'))

    def test_missing_geometry(self):
        """A MetadataNormalizationError must be raised when the
        Footprint raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_location_geometry(DatasetInfo(''))

    def test_dataset_parameters(self):
        """dataset_parameters from CEDAESACCIMetadataNormalizer """
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list') as mock_get_gcmd_method:
            self.assertEqual(
                self.normalizer.get_dataset_parameters(DatasetInfo('')),
                mock_get_gcmd_method.return_value)
