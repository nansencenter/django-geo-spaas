
"""Tests for the CMEMS normalizers"""

import logging
import unittest.mock as mock
from datetime import datetime, timezone

import django.test
from copernicusmarine.catalogue_parser.models import CopernicusMarineProduct

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class CMEMSMetadataNormalizerTestCase(django.test.TestCase):
    """Tests for the CMEMSMetadataNormalizer base class"""

    def setUp(self):
        self.normalizer = normalizers.cmems.CMEMSMetadataNormalizer()
        self.product_info = CopernicusMarineProduct(
            title='GLOBAL OCEAN ALONG-TRACK L3 SEA SURFACE HEIGHTS NRT',
            product_id='SEALEVEL_GLO_PHY_L3_NRT_008_044',
            thumbnail_url='https://foo/SEALEVEL_GLO_PHY_L3_NRT_008_044.jpg',
            description='SEALEVEL_GLO_PHY_L3_NRT_008_044 description',
            digital_object_identifier='id123',
            sources=['Satellite observations'],
            processing_level='Level 3',
            production_center='some production center',
            keywords=["global-ocean", "arctic-ocean", "level-3"],
            datasets=[],
        )

    def test_entry_id(self):
        """Test extracting the entry_id from a URL"""
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(url='https://foo/bar/baz123.nc')), 'baz123')
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(url='https://foo/bar/baz123.h5')), 'baz123')
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(url='https://foo/bar/baz123.nc.gz')), 'baz123')
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo(url='https://foo/bar/baz123.h5.gz')), 'baz123')

    def test_entry_id_error(self):
        """a MetadataNormalizationError must be raised when an entry_id cannot be found"""
        # wrong file format
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(url='ftp://foo/bar.txt'))
        # no url attribute
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(url=None))

    def test_summary(self):
        """Test getting the summary"""
        self.assertEqual(
            self.normalizer.get_summary(DatasetInfo(
                'foo', {'cmems_dataset_name': 'dataset_1', 'product_info': self.product_info})),
            'Description: SEALEVEL_GLO_PHY_L3_NRT_008_044 description;Processing level: Level 3;'
            'Product: SEALEVEL_GLO_PHY_L3_NRT_008_044;Dataset ID: dataset_1')

    def test_time_coverage(self):
        """Test the time coverage retrieval"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/nrt_global_allsat_phy_l4_20240603_20240609.nc')),
            datetime(2024, 6, 2, 12, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/nrt_global_allsat_phy_l4_20240603_20240609.nc')),
            datetime(2024, 6, 3, 12, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/dataset-uv-nrt-daily_20200301T0000Z_P20200307T0000.nc')),
            datetime(2020, 3, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'dataset-uv-nrt-daily_20200301T0000Z_P20200307T0000.nc')),
            datetime(2020, 3, 2, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/dataset-uv-nrt-monthly_202004T0000Z_P20200506T0000.nc')),
            datetime(2020, 4, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/dataset-uv-nrt-monthly_202004T0000Z_P20200506T0000.nc')),
            datetime(2020, 5, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/dataset-uv-nrt-hourly_20200906T0000Z_P20200912T0000.nc')),
            datetime(2020, 9, 6, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/dataset-uv-nrt-hourly_20200906T0000Z_P20200912T0000.nc')),
            datetime(2020, 9, 7, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/mercatorpsy4v3r1_gl12_mean_20160303_R20160316.nc')),
            datetime(2016, 3, 3, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/mercatorpsy4v3r1_gl12_mean_20160303_R20160316.nc')),
            datetime(2016, 3, 4, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/mercatorpsy4v3r1_gl12_thetao_20200404_18h_R20200405.nc')),
            datetime(2020, 4, 4, 18, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/mercatorpsy4v3r1_gl12_thetao_20200404_18h_R20200405.nc')),
            datetime(2020, 4, 4, 18, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/mercatorpsy4v3r1_gl12_uovo_20200403_06h_R20200404.nc')),
            datetime(2020, 4, 3, 6, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/mercatorpsy4v3r1_gl12_uovo_20200403_06h_R20200404.nc')),
            datetime(2020, 4, 3, 6, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/SMOC_20190515_R20190516.nc')),
            datetime(2019, 5, 15, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/SMOC_20190515_R20190516.nc')),
            datetime(2019, 5, 16, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/mercatorpsy4v3r1_gl12_hrly_20200511_R20200520.nc')),
            datetime(2020, 5, 11, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/mercatorpsy4v3r1_gl12_hrly_20200511_R20200520.nc')),
            datetime(2020, 5, 12, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/mercatorpsy4v3r1_gl12_mean_201807.nc')),
            datetime(2018, 7, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/mercatorpsy4v3r1_gl12_mean_201807.nc')),
            datetime(2018, 8, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20200601_d-CMCC--RFVL-MFSeas6-MEDATL-b20210101_an-sv07.00.nc')),
            datetime(2020, 6, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20200601_d-CMCC--RFVL-MFSeas6-MEDATL-b20210101_an-sv07.00.nc')),
            datetime(2020, 6, 2, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20210601_h-CMCC--RFVL-MFSeas6-MEDATL-b20210615_an-sv07.00.nc')),
            datetime(2021, 6, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20210601_h-CMCC--RFVL-MFSeas6-MEDATL-b20210615_an-sv07.00.nc')),
            datetime(2021, 6, 2, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20200502_qm-CMCC--RFVL-MFSeas6-MEDATL-b20210101_an-sv07.00.nc')),
            datetime(2020, 5, 2, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20200502_qm-CMCC--RFVL-MFSeas6-MEDATL-b20210101_an-sv07.00.nc')),
            datetime(2020, 5, 3, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20210601_hts-CMCC--RFVL-MFSeas6-MEDATL-b20210615_an-sv07.00.nc')),
            datetime(2021, 6, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20210601_hts-CMCC--RFVL-MFSeas6-MEDATL-b20210615_an-sv07.00.nc')),
            datetime(2021, 6, 2, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20210601_m-CMCC--RFVL-MFSeas6-MEDATL-b20210713_an-sv07.00.nc')),
            datetime(2021, 6, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20210601_m-CMCC--RFVL-MFSeas6-MEDATL-b20210713_an-sv07.00.nc')),
            datetime(2021, 7, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/CMEMS_v5r1_IBI_PHY_NRT_PdE_15minav_20201212_20201212_R20201221_AN04.nc'
            )),
            datetime(2020, 12, 12, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/CMEMS_v5r1_IBI_PHY_NRT_PdE_15minav_20201212_20201212_R20201221_AN04.nc'
            )),
            datetime(2020, 12, 13, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/CMEMS_v5r1_IBI_PHY_NRT_PdE_01dav_20210503_20210503_R20210510_AN06.nc'
            )),
            datetime(2021, 5, 3, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/CMEMS_v5r1_IBI_PHY_NRT_PdE_01dav_20210503_20210503_R20210510_AN06.nc'
            )),
            datetime(2021, 5, 4, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/CMEMS_v5r1_IBI_PHY_NRT_PdE_01hav_20191112_20191112_R20191113_AN07.nc'
            )),
            datetime(2019, 11, 12, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/CMEMS_v5r1_IBI_PHY_NRT_PdE_01hav_20191112_20191112_R20191113_AN07.nc'
            )),
            datetime(2019, 11, 13, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/CMEMS_v5r1_IBI_PHY_NRT_PdE_01hav3D_20210815_20210815_R20210816_HC01.nc'
            )),
            datetime(2021, 8, 15, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/CMEMS_v5r1_IBI_PHY_NRT_PdE_01hav3D_20210815_20210815_R20210816_HC01.nc'
            )),
            datetime(2021, 8, 16, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/CMEMS_v5r1_IBI_PHY_NRT_PdE_01mav_20191001_20191031_R20191031_AN01.nc'
            )),
            datetime(2019, 10, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/CMEMS_v5r1_IBI_PHY_NRT_PdE_01mav_20191001_20191031_R20191031_AN01.nc'
            )),
            datetime(2019, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20210204_dm-12km-NERSC-MODEL-TOPAZ4B-ARC-RAN.fv2.0.nc')),
            datetime(2021, 2, 4, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20210204_dm-12km-NERSC-MODEL-TOPAZ4B-ARC-RAN.fv2.0.nc')),
            datetime(2021, 2, 5, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/19910115_mm-12km-NERSC-MODEL-TOPAZ4B-ARC-RAN.fv2.0.nc')),
            datetime(1991, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/19910115_mm-12km-NERSC-MODEL-TOPAZ4B-ARC-RAN.fv2.0.nc')),
            datetime(1991, 2, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/19910101_ym-12km-NERSC-MODEL-TOPAZ4B-ARC-RAN.fv2.0.nc')),
            datetime(1991, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/19910101_ym-12km-NERSC-MODEL-TOPAZ4B-ARC-RAN.fv2.0.nc')),
            datetime(1992, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20180104_dm-metno-MODEL-topaz4-ARC-b20180108-fv02.0.nc')),
            datetime(2018, 1, 4, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20180104_dm-metno-MODEL-topaz4-ARC-b20180108-fv02.0.nc')),
            datetime(2018, 1, 5, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20180102_hr-metno-MODEL-topaz4-ARC-b20180102-fv02.0.nc')),
            datetime(2018, 1, 2, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20180102_hr-metno-MODEL-topaz4-ARC-b20180102-fv02.0.nc')),
            datetime(2018, 1, 3, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20220929_dm-metno-MODEL-topaz5-ARC-b20220922-fv02.0.nc')),
            datetime(2022, 9, 29, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20220929_dm-metno-MODEL-topaz5-ARC-b20220922-fv02.0.nc')),
            datetime(2022, 9, 30, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20211130_hr-metno-MODEL-topaz5-ARC-b20211130-fv02.0.nc')),
            datetime(2021, 11, 30, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20211130_hr-metno-MODEL-topaz5-ARC-b20211130-fv02.0.nc')),
            datetime(2021, 12, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/20211031_dm-metno-MODEL-topaz5_ecosmo-ARC-b20211028-fv02.0.nc')),
            datetime(2021, 10, 31, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/20211031_dm-metno-MODEL-topaz5_ecosmo-ARC-b20211028-fv02.0.nc')),
            datetime(2021, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/202011_mm-metno-MODEL-topaz5_ecosmo-ARC-fv02.0.nc')),
            datetime(2020, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/202011_mm-metno-MODEL-topaz5_ecosmo-ARC-fv02.0.nc')),
            datetime(2020, 12, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/mfwamglocep_2025040100_R20250402_00H.nc')),
            datetime(2025, 4, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/mfwamglocep_2025040100_R20250402_00H.nc')),
            datetime(2025, 4, 1, 12, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/mercatorbiomer4v2r1_global_mean_20230103.nc')),
            datetime(2023, 1, 3, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/mercatorbiomer4v2r1_global_mean_20230103.nc')),
            datetime(2023, 1, 4, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo(
                'https://foo/mercatorbiomer4v2r1_global_mean_202104.nc')),
            datetime(2021, 4, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo(
                'https://foo/mercatorbiomer4v2r1_global_mean_202104.nc')),
            datetime(2021, 5, 1, tzinfo=timezone.utc))

    def test_time_coverage_error(self):
        """An exception should be raised when time coverage retrieval
        fails
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo('foo'))

    def test_get_location_geometry(self):
        """Test getting the location"""
        self.assertEqual(
            self.normalizer.get_location_geometry(DatasetInfo('foo', {
                'variables': [mock.MagicMock(bbox=[-180, -78, 180, 81])]
            })),
            'POLYGON((-180 -78,180 -78,180 81,-180 81,-180 -78))')

    def test_get_keywords(self):
        """Test getting the keywords"""
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords:
            self.normalizer.get_keywords(DatasetInfo(
                'https://foo',
                {'cmems_dataset_name': 'dataset_1', 'product_info': self.product_info}))
            self.assertListEqual(
                mock_find_keywords.call_args_list,
                [
                    mock.call([{'kind': 'gcmd_provider', 'data__Short_Name': 'CMEMS'}]),
                    mock.call([
                        {'kind': 'gcmd_platform', 'data__icontains': 'dataset_1'},
                        {'kind': 'gcmd_platform', 'data__icontains': 'Satellite observations'},]),
                    mock.call([
                        {'kind': 'gcmd_instrument', 'data__icontains': 'dataset_1'},
                        {'kind': 'gcmd_instrument', 'data__icontains': 'Satellite observations'},]),
                ])

    def test_get_keywords_with_model_platform(self):
        """Test getting the keywords when the platform is a model"""
        mock_provider = mock.Mock(data={'Short_Name': 'cmems'})
        mock_platform = mock.Mock(data={'Category': 'Models'})
        mock_instrument = mock.Mock(data={'Short_Name': 'Computer'})
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords, \
             mock.patch('geospaas.vocabularies.models.Keyword.objects.filter') as mock_filter:
            mock_find_keywords.side_effect = ([mock_provider], [mock_platform])
            mock_filter.return_value.first.return_value = mock_instrument
            self.assertListEqual(
                self.normalizer.get_keywords(DatasetInfo(
                    'https://foo',
                    {'cmems_dataset_name': 'dataset_1', 'product_info': self.product_info})),
                [mock_provider, mock_platform, mock_instrument])

    def test_get_keywords_with_legacy_platform(self):
        """Test getting the keywords when the platform is a legacy keyword"""
        mock_provider = mock.Mock(data={'Short_Name': 'cmems'})
        mock_platform = mock.Mock(data={'category': 'foo'})
        mock_instrument = mock.Mock(data={'Short_Name': 'bar'})
        with mock.patch(
                'geospaas.harvesting.normalizers.utils.find_keywords') as mock_find_keywords:
            mock_find_keywords.side_effect = ([mock_provider], [mock_platform], [mock_instrument])
            self.assertListEqual(
                self.normalizer.get_keywords(DatasetInfo(
                    'https://foo',
                    {'cmems_dataset_name': 'dataset_1', 'product_info': self.product_info})),
                [mock_provider, mock_platform, mock_instrument])

    def test_get_dataset_parameters(self):
        """Test retrieval of variable names"""
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list'
                        ) as mock_create_parameter_list:
            with self.assertLogs(logger=self.normalizer.logger, level=logging.WARNING):
                self.normalizer.get_dataset_parameters(DatasetInfo('foo', {
                    'variables': (mock.MagicMock(standard_name='var1'),
                                    mock.MagicMock(standard_name='var2'),
                                    mock.MagicMock(standard_name='var3'),
                                    mock.MagicMock(short_name='v4', standard_name=None),
                                    mock.MagicMock(foo='bar', standard_name=None, short_name=None))
                })),
                mock_create_parameter_list.assert_called_once_with([
                    'var1', 'var2', 'var3', 'v4'
                ])
