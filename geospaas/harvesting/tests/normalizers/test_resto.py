"""Tests for the resto API metadata normalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime

from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class RestoAPIMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the resto API attributes normalizer"""

    def setUp(self):
        self.normalizer = normalizers.resto.RestoAPIMetadataNormalizer()

    def test_entry_title(self):
        """entry_title from RestoAPIMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_entry_title(DatasetInfo('', {'title': 'foo'})),
            'foo')

    def test_missing_raw_title(self):
        """A MetadataNormalizationError must be raised if the raw title
        attribute is absent
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_title(DatasetInfo(''))

    def test_entry_id(self):
        """entry_id from RestoAPIMetadataNormalizer """
        dataset_info = DatasetInfo('', {
            'url': "https://zipper.creodias.eu/foo",
            'title': 'id_value'
        })
        self.assertEqual(self.normalizer.get_entry_id(dataset_info), 'id_value')

    def test_entry_id_missing_attribute(self):
        """entry_id method must return None if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_summary_description_only(self):
        """summary from RestoAPIMetadataNormalizer"""
        dataset_info = DatasetInfo('', {
            'startDate': '2018-04-18T01:02:03Z',
            'instrument': 'instrument_value',
            'sensorMode': 'mode_value',
            'platform': 'platform_value'
        })
        self.assertEqual(
            self.normalizer.get_summary(dataset_info),
            'Description: sensorMode=mode_value, platform=platform_value, ' +
            'instrument=instrument_value, startDate=2018-04-18T01:02:03Z')

    def test_summary_with_processing_level(self):
        """summary from RestoAPIMetadataNormalizer with processing level"""
        dataset_info = DatasetInfo('', {
            'startDate': '2018-04-18T01:02:03Z',
            'instrument': 'instrument_value',
            'sensorMode': 'mode_value',
            'platform': 'platform_value',
            'processingLevel': 'LEVEL2'
        })
        self.assertEqual(
            self.normalizer.get_summary(dataset_info),
            'Description: sensorMode=mode_value, platform=platform_value, ' +
            'instrument=instrument_value, startDate=2018-04-18T01:02:03Z;Processing level: 2')

    def test_summary_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_summary(DatasetInfo(''))

    def test_time_coverage_start(self):
        """time_coverage_start from RestoAPIMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('', {'startDate': "2020-12-15T11:40:38.211Z"})),
            datetime(year=2020, month=12, day=15, hour=11, minute=40, second=38, tzinfo=tzutc()))

    def test_time_coverage_start_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_time_coverage_end(self):
        """time_coverage_end from RestoAPIMetadataNormalizer"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('', {'completionDate': "2020-12-15T11:43:38.211Z"})),
            datetime(year=2020, month=12, day=15, hour=11, minute=43, second=38, tzinfo=tzutc()))

    def test_time_coverage_end_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_end(DatasetInfo(''))

    def test_get_platform_lookup(self):
        """Test getting a lookup for the platform"""
        self.assertEqual(
            self.normalizer._get_platform_lookup(DatasetInfo('', {'platform': 'foo'})),
            {'kind': 'gcmd_platform', 'data__icontains': 'foo'})
        self.assertEqual(
            self.normalizer._get_platform_lookup(DatasetInfo('', {'platform': 'S1A'})),
            {'kind': 'gcmd_platform', 'data__icontains': 'SENTINEL-1A'})
        self.assertIsNone(self.normalizer._get_platform_lookup(DatasetInfo('')))

    def test_get_instrument_lookup(self):
        """Test getting a lookup for the instrument"""
        self.assertEqual(
            self.normalizer._get_instrument_lookup(DatasetInfo('', {'instrument': 'foo'})),
            {'kind': 'gcmd_instrument', 'data__icontains': 'foo'})
        self.assertEqual(
            self.normalizer._get_instrument_lookup(
                DatasetInfo('', {'instrument': 'SAR', 'platform': 'S1B'})),
            {'kind': 'gcmd_instrument', 'data__icontains': 'SENTINEL-1 C-SAR'})
        self.assertIsNone(self.normalizer._get_instrument_lookup(DatasetInfo('')))

    def test_get_keywords(self):
        """Test getting the keywords"""
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords:
            self.assertEqual(
                self.normalizer.get_keywords(DatasetInfo(url='https://foo')),
                mock_find_keywords.return_value)

    def test_location_geometry(self):
        """location_geometry from RestoAPIMetadataNormalizer"""

        dataset_info = DatasetInfo('', {
            'geometry': '''{"type": "Polygon","coordinates": [[[-141.363,-70.8481],
                        [-142.187,-71.401],[-143.052,-71.9568],[-141.363,-70.8481]]}'''
        })

        self.assertEqual(self.normalizer.get_location_geometry(dataset_info),
                         dataset_info.metadata['geometry'])

    def test_location_geometry_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_location_geometry(DatasetInfo(''))
