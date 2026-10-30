"""Tests for the NOAA RTOFS normalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime
from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class NOAARTOFSMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the NOAA RTOFS ftp normalizer"""
    def setUp(self):
        self.normalizer = normalizers.noaa_rtofs.NOAARTOFSMetadataNormalizer()

    def test_entry_title(self):
        """entry_title from NOAARTOFSMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_entry_title(DatasetInfo('')),
            'Global operational Real-Time Ocean Forecast System')

    def test_entry_id(self):
        """entry_id from NOAARTOFSMetadataNormalizer """
        dataset_info = DatasetInfo(
            'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            'rtofs.20210518/rtofs_glo_3dz_f024_daily_3zsio.nc')
        self.assertEqual(
            self.normalizer.get_entry_id(dataset_info),
            '20210518/rtofs_glo_3dz_f024_daily_3zsio')

    def test_entry_id_error(self):
        """a MetadataNormalizationError must be raised when an entry_id cannot be found"""
        # wrong file format
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo('ftp://foo/bar.txt'))
        # no url attribute
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_summary(self):
        """summary from NOAARTOFSMetadataNormalizer """
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo('')),
            "Description: Real Time Ocean Forecast System (RTOFS) Global is a data-assimilating "
            "nowcast-forecast system operated by the National Weather Service's National "
            "Centers for Environmental Prediction (NCEP).;"
            "Processing level: 4;"
            "Product: RTOFS")

    def test_time_coverage_start_3dz_daily(self):
        """Should return the proper starting time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/rtofs.20210519/'
                'rtofs_glo_3dz_n024_daily_3zsio.nc')),
            datetime(year=2021, month=5, day=20, tzinfo=tzutc()))

    def test_time_coverage_start_3dz_6hourly(self):
        """Should return the proper starting time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/rtofs.20210518/'
                'rtofs_glo_3dz_f042_6hrly_hvr_US_east.nc')),
            datetime(year=2021, month=5, day=19, hour=18, tzinfo=tzutc()))

    def test_time_coverage_start_2ds(self):
        """Should return the proper starting time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/rtofs.20210518/'
                'rtofs_glo_2ds_f062_prog.nc')),
            datetime(year=2021, month=5, day=20, hour=14, tzinfo=tzutc()))

    def test_time_coverage_start_missing_attribute(self):
        """An exception must be raised if the attribute is missing"""
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_time_coverage_end_3dz_daily(self):
        """Should return the proper ending time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/rtofs.20210519/'
                'rtofs_glo_3dz_n024_daily_3zsio.nc')),
            datetime(year=2021, month=5, day=20, tzinfo=tzutc()))

    def test_time_coverage_end_3dz_6hourly(self):
        """Should return the proper ending time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/rtofs.20210518/'
                'rtofs_glo_3dz_f042_6hrly_hvr_US_east.nc')),
            datetime(year=2021, month=5, day=19, hour=18, tzinfo=tzutc()))

    def test_time_coverage_end_2ds(self):
        """Should return the proper ending time"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/rtofs.20210518/'
                'rtofs_glo_2ds_f062_prog.nc')),
            datetime(year=2021, month=5, day=20, hour=14, tzinfo=tzutc()))

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

    def test_location_geometry_global(self):
        """Should return the proper geometry"""
        dataset_info = DatasetInfo(
            'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            'rtofs.20210518/rtofs_glo_3dz_f024_daily_3zsio.nc')
        self.assertEqual(
            self.normalizer.get_location_geometry(dataset_info),
            'POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))'
        )

    def test_location_geometry_us_east(self):
        """Should return the proper geometry"""
        dataset_info = DatasetInfo(
            'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            'rtofs.20210518/rtofs_glo_3dz_f042_6hrly_hvr_US_east.nc')
        self.assertEqual(
            self.normalizer.get_location_geometry(dataset_info),
            ('POLYGON (('
                '-105.193603515625 0, -40.719970703125 0,'
                '-40.719970703125 79.74808502197266,'
                '-105.193603515625 79.74808502197266,'
                '-105.193603515625 0))'))

    def test_location_geometry_us_west(self):
        """Should return the proper geometry"""
        dataset_info = DatasetInfo(
            'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            'rtofs.20210518/rtofs_glo_3dz_f042_6hrly_hvr_US_west.nc')
        self.assertEqual(
            self.normalizer.get_location_geometry(dataset_info),
            ('POLYGON (('
                '-157.9200439453125 10.02840137481689,'
                '-74.239990234375 10.02840137481689,'
                '-74.239990234375 74.57466888427734,'
                '-157.9200439453125 74.57466888427734,'
                '-157.9200439453125 10.02840137481689))'))

    def test_location_geometry_alaska(self):
        """Should return the proper geometry"""
        dataset_info = DatasetInfo(
            'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            'rtofs.20210518/rtofs_glo_3dz_f042_6hrly_hvr_alaska.nc')
        self.assertEqual(
            self.normalizer.get_location_geometry(dataset_info),
            ('POLYGON (('
                '-179.1199951171875 45.77324676513672,'
                '-112.6572265625 45.77324676513672,'
                '-112.6572265625 78.41667938232422,'
                '-179.1199951171875 78.41667938232422,'
                '-179.1199951171875 45.77324676513672))'))

    def test_dataset_parameters_rtofs_2ds_diag(self):
        """Should return the proper dataset parameters"""
        dataset_info = DatasetInfo(
            'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            'rtofs.20210518/rtofs_glo_2ds_f063_diag.nc')
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list') as mock_utils_method:
            self.assertEqual(
                self.normalizer.get_dataset_parameters(dataset_info),
                mock_utils_method.return_value)
            mock_utils_method.assert_called_with([
                'sea_surface_height_above_geoid',
                'barotropic_eastward_sea_water_velocity',
                'barotropic_northward_sea_water_velocity',
                'surface_boundary_layer_thickness',
                'ocean_mixed_layer_thickness',
            ])

    def test_dataset_parameters_rtofs_2ds_prog(self):
        """Should return the proper dataset parameters"""
        dataset_info = DatasetInfo(
            'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            'rtofs.20210518/rtofs_glo_2ds_f062_prog.nc')
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list') as mock_utils_method:
            self.assertEqual(
                self.normalizer.get_dataset_parameters(dataset_info),
                mock_utils_method.return_value)
            mock_utils_method.assert_called_with([
                'eastward_sea_water_velocity',
                'northward_sea_water_velocity',
                'sea_surface_temperature',
                'sea_surface_salinity',
                'sea_water_potential_density',
            ])

    def test_dataset_parameters_rtofs_2ds_ice(self):
        """Should return the proper dataset parameters"""
        dataset_info = DatasetInfo(
            'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            'rtofs.20210518/rtofs_glo_2ds_f062_ice.nc')
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list') as mock_utils_method:
            self.assertEqual(
                self.normalizer.get_dataset_parameters(dataset_info),
                mock_utils_method.return_value)
            mock_utils_method.assert_called_with([
                'ice_coverage',
                'ice_temperature',
                'ice_thickness',
                'ice_uvelocity',
                'icd_vvelocity',
            ])

    def test_dataset_parameters_rtofs_3dz(self):
        """Should return the proper dataset parameters"""
        dataset_info = DatasetInfo(
            'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            'rtofs.20210518/rtofs_glo_3dz_f024_daily_3zsio.nc')
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list') as mock_utils_method:
            self.assertEqual(
                self.normalizer.get_dataset_parameters(dataset_info),
                mock_utils_method.return_value)
            mock_utils_method.assert_called_with([
                'eastward_sea_water_velocity',
                'northward_sea_water_velocity',
                'sea_surface_temperature',
                'sea_surface_salinity',
            ])
