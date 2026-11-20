"""Tests for the tabledap normalizer"""

import unittest
import unittest.mock as mock
from datetime import datetime, timezone

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class TableDAPMetadataNormalizerTests(unittest.TestCase):
    """Tests for TableDAPMetadataNormalizer"""

    def setUp(self):
        self.normalizer = normalizers.tabledap.TableDAPMetadataNormalizer()
        self.empty_dataset_info = DatasetInfo('', {'product_metadata': {'table': {'rows': []}}})
        self.dataset_info = DatasetInfo('', {
            'entry_id': '123456',
            'url': 'http://foo/tabledap/bar.json',
            'temporal_coverage': ('2023-01-01T00:00:00Z', '2023-01-01T12:47:13Z'),
            'trajectory': 'LINESTRING (1 2, 3 4)',
            'product_metadata': {
                'table': {
                    'columnNames': [
                        "Row Type", "Variable Name", "Attribute Name", "Data Type", "Value"],
                    'rows': [
                        ["attribute", "NC_GLOBAL", "cdm_altitude_proxy", "String", "pres"],
                        ["attribute", "NC_GLOBAL", "cdm_data_type", "String", "TrajectoryProfile"],
                        ["attribute", "NC_GLOBAL", "time_coverage_end", "String",
                         "2026-12-27T14:48:20Z"],
                        ["attribute", "NC_GLOBAL", "time_coverage_start", "String",
                         "1997-07-28T20:26:20Z"],
                        ["attribute", "NC_GLOBAL", "title", "String", "Argo Float Measurements"],
                        ["attribute", "NC_GLOBAL", "summary", "String",
                         "Argo float vertical profiles from Coriolis Global Data Assembly Centres"],
                        ["attribute", "NC_GLOBAL", "source", "String", "Argo float"],
                        ["attribute", "NC_GLOBAL", "institution", "String", "Argo"],
                    ]
                }
            }
        })

    def test_get_product_attribute(self):
        """Test getting the value of an attribute from a tabledap
        product's metadata
        """
        self.assertEqual(
            normalizers.tabledap.TableDAPMetadataNormalizer.get_product_attribute(
                self.dataset_info.metadata['product_metadata'], 'cdm_data_type'),
            'TrajectoryProfile')
        with self.assertRaises(MetadataNormalizationError):
            normalizers.tabledap.TableDAPMetadataNormalizer.get_product_attribute(
                self.dataset_info.metadata['product_metadata'], 'foo')

    def test_get_entry_title(self):
        """Test getting the title"""
        self.assertEqual(self.normalizer.get_entry_title(self.dataset_info),
                         'Argo Float Measurements')

    def test_missing_title(self):
        """A MetadataNormalizationError should be raised if the raw title
        is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_title(self.empty_dataset_info)

    def test_get_entry_id(self):
        """Test getting the ID"""
        self.assertEqual(self.normalizer.get_entry_id(self.dataset_info), '123456')

    def test_entry_id_error(self):
        """A MetadataNormalizationError should be raised if ID is not found
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(self.empty_dataset_info)

    def test_summary(self):
        """Test getting the summary"""
        self.assertEqual(
            self.normalizer.get_summary(self.dataset_info),
            'Argo float vertical profiles from Coriolis Global Data Assembly Centres')

    def test_get_time_coverage_start(self):
        """Test getting the start of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(self.dataset_info),
            datetime(year=2023, month=1, day=1, tzinfo=timezone.utc))

    def test_missing_time_coverage_start(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_start raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(self.empty_dataset_info)

    def test_get_time_coverage_end(self):
        """Test getting the end of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(self.dataset_info),
            datetime(year=2023, month=1, day=1, hour=12, minute=47, second=13, tzinfo=timezone.utc))

    def test_missing_time_coverage_end(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_end raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_end(self.empty_dataset_info)

    def test_get_keywords(self):
        """Test getting the keywords"""
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords:
            self.assertEqual(
                self.normalizer.get_keywords(self.dataset_info),
                mock_find_keywords.return_value)
            mock_find_keywords.assert_called_with([
                {'kind': 'gcmd_platform', 'data__icontains': 'Argo-float'},
                {'kind': 'gcmd_project', 'data__Short_Name': 'ARGO'}])

    def test_get_keywords_non_argo(self):
        """Test getting the keywords for data which does not come from
        Argo floats
        """
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords:
            self.assertEqual(
                self.normalizer.get_keywords(DatasetInfo('', {
                    'product_metadata': {
                        'table': {
                            'columnNames': [
                                "Row Type", "Variable Name", "Attribute Name", "Data Type", "Value"
                            ],
                            'rows': [
                                ["attribute", "NC_GLOBAL", "source", "String", "S1A"],
                                ["attribute", "NC_GLOBAL", "institution", "String", "NERSC"],
                            ]
                        }
                    }
                })),
                mock_find_keywords.return_value)
            mock_find_keywords.assert_called_with([
                {'kind': 'gcmd_platform', 'data__icontains': 'S1A'},
                {'kind': 'gcmd_provider', 'data__icontains': 'NERSC'}])

    def test_get_location_geometry(self):
        """get_location_geometry() should return the location
        of the dataset
        """
        self.assertEqual(
            self.normalizer.get_location_geometry(self.dataset_info),
            'LINESTRING (1 2, 3 4)')
