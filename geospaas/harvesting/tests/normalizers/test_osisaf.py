"""Tests for the OSISAF metadata normalizer"""
import unittest
import unittest.mock as mock

import dateutil
from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class OSISAFMetadataNormalizer(unittest.TestCase):
    """Tests for the OSISAF attributes normalizer"""

    def setUp(self):
        self.normalizer = normalizers.osisaf.OSISAFMetadataNormalizer()

    def test_entry_title(self):
        """Test getting the title"""
        self.assertEqual(self.normalizer.get_entry_title(DatasetInfo('', {'title': 'foo'})), 'foo')

    def test_missing_entry_title(self):
        """A MetadataNormalizationError must be raised when the raw
        title attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_title(DatasetInfo(''))

    def test_get_entry_id(self):
        """Test getting the entry ID from the URL"""
        self.assertEqual(self.normalizer.get_entry_id(DatasetInfo('https://foo/bar/baz.nc')), 'baz')
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo('https://foo/bar/baz.nc.dods')), 'baz')

    def test_get_entry_id_no_url(self):
        """A MetadataNormalizationError must be raised when the raw
        url attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_summary(self):
        """Test getting the summary"""
        dataset_info = DatasetInfo('', {'abstract': 'value_abs'})
        self.assertEqual(self.normalizer.get_summary(dataset_info), 'Description: value_abs')

    def test_get_summary_missing_raw_attributes(self):
        """A MetadataNormalizationError must be raised when any of the
        raw attributes used to build the summary is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_summary(DatasetInfo(''))

    def test_time_coverage_start(self):
        """Test getting the start of the time coverage"""
        dataset_info = DatasetInfo('', {'start_date': '2020-07-12 00:00:00'})
        self.assertEqual(self.normalizer.get_time_coverage_start(dataset_info),
                         dateutil.parser.parse("2020-07-12").replace(tzinfo=tzutc()))

    def test_missing_time_coverage_start(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_start raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_time_coverage_end(self):
        """Test getting the end of the time coverage."""
        dataset_info = DatasetInfo('', {'stop_date': '2020-07-14 00:00:00'})
        self.assertEqual(self.normalizer.get_time_coverage_end(dataset_info),
                         dateutil.parser.parse("2020-07-14").replace(tzinfo=tzutc()))

    def test_missing_time_coverage_end(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_end raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_end(DatasetInfo(''))

    def test_get_platform_lookup(self):
        """Test getting a lookup for the platform"""
        self.assertEqual(
            self.normalizer._get_platform_lookup(DatasetInfo('', {'platform_name': 'foo'})),
            {'kind': 'gcmd_platform', 'data__icontains': 'foo'})
        self.assertEqual(
            self.normalizer._get_platform_lookup(DatasetInfo('', {'platform': 'foo'})),
            {'kind': 'gcmd_platform', 'data__icontains': 'foo'})
        self.assertEqual(
            self.normalizer._get_platform_lookup(DatasetInfo('')),
            {
                'kind': 'gcmd_platform',
                'data__Category': 'Earth Observation Satellites',
                'data__Short_Name': '',
                'data__Long_Name': '',
                'data__Sub_Category': ''
            })

    def test__get_instrument_lookup(self):
        """Test getting a lookup for the instrument"""
        self.assertEqual(
            self.normalizer._get_instrument_lookup(DatasetInfo('', {'instrument_type': 'foo'})),
            {'kind': 'gcmd_instrument', 'data__icontains': 'foo'})
        self.assertEqual(
            self.normalizer._get_instrument_lookup(DatasetInfo('', {'instrument': 'foo'})),
            {'kind': 'gcmd_instrument', 'data__icontains': 'foo'})
        self.assertEqual(
            self.normalizer._get_instrument_lookup(
                DatasetInfo('', {'product_name': 'osi_saf_ice_conc_l3'})),
            {
                'data__Type': 'Spectrometers/Radiometers',
                'data__Class': 'Passive Remote Sensing',
                'data__Subtype': 'Imaging Spectrometers/Radiometers',
                'data__Category': 'Earth Remote Sensing Instruments',
                'data__Long_Name': '',
                'data__Short_Name': ''
            })
        self.assertEqual(
            self.normalizer._get_instrument_lookup(
                DatasetInfo('', {'product_name': 'amsr2ice_conc'})),
            {'kind': 'gcmd_instrument', 'data__icontains': 'AMSR2'})
        self.assertEqual(
            self.normalizer._get_instrument_lookup(
                DatasetInfo('', {'product_name': 'osi_saf_mr_ice_drift'})),
            {'kind': 'gcmd_instrument', 'data__icontains': 'AVHRR'})
        self.assertEqual(
            self.normalizer._get_instrument_lookup(DatasetInfo('')),
            {
                'kind': 'gcmd_instrument',
                'data__Type': '',
                'data__Class': '',
                'data__Subtype': '',
                'data__Category': 'Earth Remote Sensing Instruments',
                'data__Long_Name': '',
                'data__Short_Name': ''
            })

    def test_get_keywords(self):
        """Test getting the keywords"""
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords:
            self.assertEqual(
                self.normalizer.get_keywords(DatasetInfo(url='https://foo')),
                mock_find_keywords.return_value)

    def test_location_geometry(self):
        """Test getting the location_geometry, with and without the
        typo in the "northernmost" attribute
        """
        expected_geometry = ('POLYGON((' +
             '-175.084000 -15.3505001,' +
             '-142.755005 -15.3505001,' +
             '-142.755005 9.47472000,' +
             '-175.084000 9.47472000,' +
             '-175.084000 -15.3505001))')

        self.assertEqual(expected_geometry, self.normalizer.get_location_geometry(DatasetInfo('', {
            'northernsmost_latitude': "9.47472000",
            'southernmost_latitude': "-15.3505001",
            'easternmost_longitude': "-142.755005",
            'westernmost_longitude': "-175.084000"
        })))

        self.assertEqual(expected_geometry, self.normalizer.get_location_geometry(DatasetInfo('', {
            'northernmost_latitude': "9.47472000",
            'southernmost_latitude': "-15.3505001",
            'easternmost_longitude': "-142.755005",
            'westernmost_longitude': "-175.084000"
        })))
