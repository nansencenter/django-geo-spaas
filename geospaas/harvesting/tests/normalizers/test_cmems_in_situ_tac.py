"""Tests for the CMEMS in situ TAC metadata normalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime

from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class CMEMSInSituTACMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the CMEMS in situ TAC attributes normalizer"""

    def setUp(self):
        self.normalizer = normalizers.cmems_in_situ_tac.CMEMSInSituTACMetadataNormalizer()

    def test_get_entry_title(self):
        """Test getting the title"""
        self.assertEqual(
            self.normalizer.get_entry_title(DatasetInfo('', {'title': 'foo'})),
            'foo')

    def test_missing_title(self):
        """A MetadataNormalizationError should be raised if the raw title
        is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_title(DatasetInfo(''))

    def test_get_entry_id(self):
        """Test getting the ID"""
        self.assertEqual(self.normalizer.get_entry_id(DatasetInfo('', {'id': 'foo'})), 'foo')

    def test_missing_id(self):
        """A MetadataNormalizationError should be raised if the raw id
        is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_get_summary_013_030_from_raw_attributes(self):
        """Get the summary from the raw attributes for the 013_030
        product
        """
        url = '/foo/INSITU_GLO_NRT_OBSERVATIONS_013_030/dataset.nc'
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(url, {'summary': 'foo' })),
            'Description: foo;Processing level: 2;'
            'Product: INSITU_GLO_NRT_OBSERVATIONS_013_030'
        )

    def test_get_summary_013_048_from_raw_attributes(self):
        """Get the summary from the raw attributes for the 013_048
        product
        """
        url = '/foo/INSITU_GLO_UV_NRT_OBSERVATIONS_013_048/dataset.nc'
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(url, {'summary': 'foo'})),
            'Description: foo;Processing level: 2;'
            'Product: INSITU_GLO_UV_NRT_OBSERVATIONS_013_048'
        )

    def test_get_summary_unknown_from_raw_attributes(self):
        """Get the summary from the raw attributes for an unknown
        product
        """
        url = '/foo/bar/dataset.nc'
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(url, {'summary': 'foo'})),
            'Description: foo;Processing level: 2;'
            'Product: Unknown'
        )

    def test_get_summary_013_030_default(self):
        """If there is no summary in the attributes (or if it is
        empty), return the default summary for the 013_030 product
        """
        url = '/foo/INSITU_GLO_NRT_OBSERVATIONS_013_030/dataset.nc'
        default_summary = (
            'Description: '
                'Global Ocean - near real-time (NRT) in situ quality controlled observations, '
                'hourly updated and distributed by INSTAC within 24-48 hours from acquisition '
                'in average. Data are collected mainly through global networks '
                '(Argo, OceanSites, GOSUD, EGO) and through the GTS;'
            'Processing level: 2;'
            'Product: INSITU_GLO_NRT_OBSERVATIONS_013_030'
        )
        self.assertEqual(self.normalizer.get_summary(DatasetInfo(url)), default_summary)
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(url, {'summary': ''})),
            default_summary)
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(url, {'summary': '  '})),
            default_summary)

    def test_get_summary_013_048_default(self):
        """If there is no summary in the attributes (or if it is
        empty), return the default summary for the 013_048 product
        """
        url = '/foo/INSITU_GLO_UV_NRT_OBSERVATIONS_013_048/dataset.nc'
        default_summary = (
            'Description: '
                'This product is entirely dedicated to ocean current data observed in '
                'near-real time. Surface current data from 2 different types of instruments'
                ' are distributed: velocities calculated along the trajectories of drifting'
                ' buoys from the DBCP’s Global Drifter Program, and velocities measured by '
                'High Frequency radars from the European High Frequency radar Network;'
            'Processing level: 2;'
            'Product: INSITU_GLO_UV_NRT_OBSERVATIONS_013_048'
        )
        self.assertEqual(self.normalizer.get_summary(DatasetInfo(url)), default_summary)
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(url, {'summary': ''})),
            default_summary)
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(url, {'summary': '  '})),
            default_summary)

    def test_get_summary_unknown_default(self):
        """If there is no summary in the attributes (or if it is
        empty), return the default summary for an unknown product
        """
        url = '/foo/bar/dataset.nc'
        default_summary = (
            'Description: CMEMS in situ TAC data;'
            'Processing level: 2;'
            'Product: Unknown'
        )
        self.assertEqual(self.normalizer.get_summary(DatasetInfo(url)), default_summary)
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(url, {'summary': ''})),
            default_summary)
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(url, {'summary': '  '})),
            default_summary)

    def test_get_time_coverage_start(self):
        """get_time_coverage_start() should return the start time of
        the dataset
        """
        self.assertEqual(
            self.normalizer.get_time_coverage_start(
                DatasetInfo('', {'time_coverage_start': '2020-10-21T01:02:03Z'})),
            datetime(year=2020, month=10, day=21, hour=1, minute=2, second=3, tzinfo=tzutc())
        )

    def test_missing_time_coverage_start(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_start raw attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_get_time_coverage_end(self):
        """get_time_coverage_end() should return the start time
        of the dataset
        """
        self.assertEqual(
            self.normalizer.get_time_coverage_end(
                DatasetInfo('', {'time_coverage_end': '2020-10-21T01:02:03Z'})),
            datetime(year=2020, month=10, day=21, hour=1, minute=2, second=3, tzinfo=tzutc())
        )

    def test_missing_time_coverage_end(self):
        """A MetadataNormalizationError must be raised when the
        time_coverage_end raw attribute is missing
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
        self.assertIsNone(self.normalizer.get_location_geometry(DatasetInfo('')))
