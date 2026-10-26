"""Tests for the CPOM altimetry normalizer"""

import unittest
import unittest.mock as mock
from datetime import datetime, timezone

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo


class CPOMAltimetryMetadataNormalizerTests(unittest.TestCase):
    """Tests for CPOMAltimetryMetadataNormalizer"""

    def setUp(self):
        self.normalizer = normalizers.cpom.CPOMAltimetryMetadataNormalizer()


    def test_get_entry_title(self):
        """Test getting the title"""
        self.assertEqual(self.normalizer.get_entry_title(DatasetInfo('')), 'CPOM SLA')

    def test_get_entry_id(self):
        """Test getting the ID"""
        self.assertEqual(self.normalizer.get_entry_id(DatasetInfo('')), 'CPOM_DOT')

    def test_get_time_coverage_start(self):
        """Test getting the start of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo('')),
            datetime(year=2003, month=1, day=1, tzinfo=timezone.utc))

    def test_get_time_coverage_end(self):
        """Test getting the end of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo('')),
            datetime(year=2015, month=1, day=1, tzinfo=timezone.utc))

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
            self.normalizer.get_location_geometry(DatasetInfo('', {'geometry': 'POINT(10 10)'})),
            'POINT(10 10)')

    def test_missing_geometry(self):
        """An empty string must be returned when the geometry raw
        attribute is missing
        """
        self.assertEqual(self.normalizer.get_location_geometry(DatasetInfo('')), '')

    def test_dataset_parameters(self):
        """dataset_parameters from CEDAESACCIMetadataNormalizer """
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list'
                        ) as mock_get_gcmd_method:
            self.assertEqual(
                self.normalizer.get_dataset_parameters(DatasetInfo('')),
                mock_get_gcmd_method.return_value)
