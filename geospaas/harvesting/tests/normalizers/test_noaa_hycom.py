"""Tests for the NOAA HYCOM normalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime
from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class NOAAHYCOMMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the REMSS GMI ftp normalizer"""
    def setUp(self):
        self.normalizer = normalizers.noaa_hycom.NOAAHYCOMMetadataNormalizer()

    def test_entry_title(self):
        """entry_title from NOAAHYCOMMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_entry_title(DatasetInfo('')),
            'Global Hybrid Coordinate Ocean Model (HYCOM)')

    def test_entry_id(self):
        """entry_id from NOAAHYCOMMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(
                'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
                'hycom_glb_regp17_2020122000_t168.nc.gz')),
            'hycom_glb_regp17_2020122000_t168')
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(
                'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
                'hycom_glb_sfc_u_2020121900_t000.nc.gz')),
            'hycom_glb_sfc_u_2020121900_t000')

    def test_entry_id_error(self):
        """a MetadataNormalizationError must be raised when an entry_id cannot be found"""
        # wrong file format
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo('ftp://foo/bar.txt'))
        # no url attribute
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_summary(self):
        """summary from NOAAHYCOMMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo('')),
            'Description: This system provides 4-day forecasts at 3-hour time steps, updated at '
            '00Z daily. Navy Global HYCOM has a resolution of 1/12 degree in the horizontal and '
            'uses hybrid (isopycnal/sigma/z-level) coordinates in the vertical. The output is '
            'interpolated onto a regular 1/12-degree grid horizontally and 40 standard depth '
            'levels.;'
            'Processing level: 4;'
            'Product: HYCOM')

    def test_time_coverage_start_region_000(self):
        """Should return the proper starting time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
                'hycom_glb_regp01_2020121900_t000.nc.gz')),
            datetime(year=2020, month=12, day=19, hour=0, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_region_009(self):
        """Should return the proper starting time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
                'hycom_glb_regp01_2020121900_t009.nc.gz')),
            datetime(year=2020, month=12, day=19, hour=9, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_region_027(self):
        """Should return the proper starting time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
                'hycom_glb_regp01_2020121900_t027.nc.gz')),
            datetime(year=2020, month=12, day=20, hour=3, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_sfc(self):
        """Should return the proper starting time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
                'hycom_glb_sfc_u_2020121900_t003.nc.gz')),
            datetime(year=2020, month=12, day=19, hour=3, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_time_coverage_end_region_000(self):
        """Should return the proper ending time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
                'hycom_glb_regp01_2020121900_t000.nc.gz')),
            datetime(year=2020, month=12, day=19, hour=3, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_end_region_009(self):
        """Should return the proper ending time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
                'hycom_glb_regp01_2020121900_t009.nc.gz')),
            datetime(year=2020, month=12, day=19, hour=12, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_end_region_027(self):
        """Should return the proper ending time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
                'hycom_glb_regp01_2020121900_t027.nc.gz')),
            datetime(year=2020, month=12, day=20, hour=6, minute=0, second=0, tzinfo=tzutc()))

    def test_time_coverage_end_sfc(self):
        """Should return the proper ending time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
                'hycom_glb_sfc_u_2020121900_t003.nc.gz')),
            datetime(year=2020, month=12, day=19, hour=6, minute=0, second=0, tzinfo=tzutc()))

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

    def test_geometry_hycom_region1(self):
        """Should return the proper geometry"""
        dataset_info = DatasetInfo(
            'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
            'hycom_glb_regp01_2020121900_t030.nc.gz')
        self.assertEqual(
            self.normalizer.get_location_geometry(dataset_info),
            'POLYGON((-100.04 70.04, -100.04 -0.04, -49.96 -0.04, -49.96 70.04, -100.04 70.04))')

    def test_geometry_hycom_region6(self):
        """Should return the proper geometry"""
        dataset_info = DatasetInfo(
            'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
            'hycom_glb_regp06_2020121900_t030.nc.gz')
        self.assertEqual(
            self.normalizer.get_location_geometry(dataset_info),
            'POLYGON((149.96 70.04, 149.96 9.96, 210.04 9.96, 210.04 70.04, 149.96 70.04))')

    def test_geometry_hycom_region7(self):
        """Should return the proper geometry"""
        dataset_info = DatasetInfo(
            'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
            'hycom_glb_regp07_2020121900_t030.nc.gz')
        self.assertEqual(
            self.normalizer.get_location_geometry(dataset_info),
            'POLYGON((-150.04 60.04, -150.04 9.96, -99.96 9.96, -99.96 60.04, -150.04 60.04))')

    def test_geometry_hycom_region17(self):
        """Should return the proper geometry"""
        dataset_info = DatasetInfo(
            'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
            'hycom_glb_regp17_2020121900_t030.nc.gz')
        self.assertEqual(
            self.normalizer.get_location_geometry(dataset_info),
            'POLYGON((-180.04 80.02,-180.04 59.98,-119.96 59.98,-119.96 80.02,-180.04 80.02))')

    def test_geometry_hycom_sfc(self):
        """Should return the proper geometry"""
        dataset_info = DatasetInfo(
            'ftp://ftp.opc.ncep.noaa.gov/grids/operational/GLOBALHYCOM/Navy/'
            'hycom_glb_sfc_u_2020121900_t030.nc.gz')
        self.assertEqual(
            self.normalizer.get_location_geometry(dataset_info),
            'POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))')

    def test_unknown_geometry(self):
        """An exception should be raised if no geometry can be found"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_location_geometry(DatasetInfo('http://foo'))


    def test_dataset_parameters(self):
        """dataset_parameters from NOAAHYCOMMetadataNormalizer """
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list'
                        ) as mock_get_gcmd_method:
            self.assertEqual(
                self.normalizer.get_dataset_parameters(DatasetInfo('')),
                mock_get_gcmd_method.return_value)
