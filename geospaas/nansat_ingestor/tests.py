"""Tests for nansat_ingestor app"""
import sys
from contextlib import contextmanager
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from mock import PropertyMock, patch

from geospaas.catalog.models import DatasetURI
from geospaas.nansat_ingestor.models import Dataset
from geospaas.nansat_ingestor.management.commands.ingest_thredds_crawl import crawl_and_ingest


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

# See also:
# https://docs.python.org/3.5/library/unittest.mock-examples.html#applying-the-same-patch-to-every-test-method


class BasetForTests(TestCase):
    """Base class for creating the testing environment"""
    fixtures = ['vocabularies', 'catalog']
    predefined_metadata_dict = {
        'platform': '{"Category": "Earth Observation Satellites", "Series_Entity": "", "Short_Name": "ENVISAT", "Long_Name": "Environmental Satellite"}',
        'instrument': '{"Category": "Earth Remote Sensing Instruments", "Class": "Passive Remote Sensing", "Type": "Spectrometers/Radiometers", "Subtype": "Imaging Spectrometers/Radiometers", "Short_Name": "MERIS", "Long_Name": "Medium Resolution Imaging Spectrometer"}',
        'time_coverage_start': '2011-05-03T10:56:38.995099',
        'time_coverage_end': '2011-05-03T10:56:38.995099',
        'data_center': '{"Bucket_Level0": "MULTINATIONAL ORGANIZATIONS", "Bucket_Level1": "", "Bucket_Level2": "", "Bucket_Level3": "", "Short_Name": "ESA/EO", "Long_Name": "Observing the Earth, European Space Agency", "Data_Center_URL": "http://www.esa.int/esaEO/"}',
        'gcmd_location': '{"Location_Category": "VERTICAL LOCATION", "Location_Type": "SEA SURFACE", "Location_Subregion1": "", "Location_Subregion2": "", "Location_Subregion3": ""}',
        'ISO_topic_category': '{"iso_topic_category": "Oceans_XXXXX"}',
    }
    predefined_band_metadata_dict = {
        1: {'dataType': '2',
            'name': 'DN_HH',
            'SourceBand': '1',
            'SourceFilename': '/some/folder/filename.ext'},
        2: {'colormap': 'gray',
            'dataType': '6',
            'long_name': 'Normalized Radar Cross Section',
            'minmax': '0 0.1',
            'name': 'sigma0_HH',
            'PixelFunctionType': 'Sentinel1Calibration',
            'polarization': 'HH',
            'short_name': 'sigma0',
            'SourceBand': '1',
            'SourceFilename': '/vsimem/0BSD1QSPFL.vrt',
            'standard_name': 'surface_backwards_scattering_coefficient_of_radar_wave',
            'suffix': 'HH',
            'units': 'm/m',
            'wkv': 'surface_backwards_scattering_coefficient_of_radar_wave'},
        3: {'colormap': 'testing',
            'dataType': '6',
            'long_name': 'testing',
            'minmax': '0 0.1',
            'name': 'testing',
            'PixelFunctionType': 'testing',
            'polarization': 'testing',
            'short_name': 'testing',
            'SourceBand': '1',
            'SourceFilename': 'testing',
            'standard_name': 'longitude',  # <=== notice the difference between testing records
            'suffix': 'testing',
            'units': 'testing',
            'wkv': 'testing'},
        4: {'colormap': 'testing',
            'dataType': '10',
            'long_name': 'testing',
            'minmax': '0 0.1',
            'name': 'testing',
            'PixelFunctionType': 'testing',
            'polarization': 'testing',
            'short_name': 'testing',
            'SourceBand': '1',
            'SourceFilename': 'testing',
            'standard_name': 'latitude',  # <=== notice the difference between testing records
            'suffix': 'testing',
            'units': 'testing',
            'wkv': 'testing'},
        5: {'colormap': 'gray',
            'dataType': '6',
            'long_name': 'Normalized Radar Cross Section',
            'minmax': '0 0.1',
            'name': 'gamma0_HH',
            'PixelFunctionType': 'Sentinel1Calibration',
            'polarization': 'HH',
            'short_name': 'gamma0',
            'SourceBand': '1',
            'SourceFilename': '/vsimem/0BSD1QSPFL.vrt',
            'standard_name': 'surface_backwards_scattering_coefficient_of_radar_wave',
            'suffix': 'HH',
            'units': 'm/m',
            'wkv': 'surface_backwards_scattering_coefficient_of_radar_wave'},
    }

    def setUp(self):
        self.patcher = patch('geospaas.nansat_ingestor.managers.Nansat')
        self.mock_Nansat = self.patcher.start()
        self.mock_Nansat.return_value.get_metadata.side_effect = self.mock_get_metadata
        self.mock_Nansat.return_value.get_border_wkt.return_value = 'POLYGON((24.88 68.08,22.46 68.71,19.96 69.31,17.39 69.87,24.88 68.08))'
        self.mock_Nansat.return_value.bands.side_effect = self.mock_bands


        self.patcher2 = patch('geospaas.nansat_ingestor.managers.validate_uri')
        self.mock_validate_uri = self.patcher2.start()
        self.mock_validate_uri.return_value = None
        # in order to prevent "mock leak" in the tests
        self.addCleanup(patch.stopall)

    def mock_get_metadata(self, *args):
        """ Mock behaviour of Nansat.get_metadata method """
        if len(args) == 0:
            return self.predefined_metadata_dict
        if args[0] not in self.predefined_metadata_dict:
            raise
        return self.predefined_metadata_dict[args[0]]

    def mock_bands(self):
        return self.predefined_band_metadata_dict


class TestDatasetManager(BasetForTests):
    """Class for containing all the tests of creating the datasets and related situations"""

    def test__get_or_create__with__entry_id__in__metadata(self):
        self.predefined_metadata_dict['entry_id'] = 'UNIQUE_ID_1000'
        uri = 'file://localhost/some/folder/filename.ext'
        _, cr0 = Dataset.objects.get_or_create(uri)
        self.assertTrue(cr0)

    def test_getorcreate_localfile_only_created_for_the_very_first_time(self):
        '''shall return the creation flag (the second returned value)
        equals to True for the first time and
        equals to False for the second time'''
        uri = 'file://localhost/some/folder/filename.ext'
        _, cr0 = Dataset.objects.get_or_create(uri)
        _, cr1 = Dataset.objects.get_or_create(uri)
        self.assertTrue(cr0)
        self.assertFalse(cr1)

    def test_getorcreate_localfile_is_matched_in_metadata(self):
        '''shall return the correct specification of dataset created based on
        predefined metadata declared in the test'''
        uri = 'file://localhost/some/folder/filename.ext'
        ds0, _ = Dataset.objects.get_or_create(uri)
        self.assertEqual(
            ds0.entry_id, self.predefined_metadata_dict['entry_id'])
        self.assertEqual(ds0.entry_title, 'NONE')
        self.assertEqual(ds0.summary, 'NONE')

    def test_getorcreate_localfile_matched_parameter(self):
        uri = 'file://localhost/some/folder/filename.ext'
        ds0, _ = Dataset.objects.get_or_create(uri)
        self.assertEqual(ds0.parameters.values()[0]['short_name'],
                         self.predefined_band_metadata_dict[2]['short_name'])

    def test_getorcreate_localfile_filtering_base_on_parameter(self):
        '''shall return standard name of
        an specified parameter of the correct filtered dataset
        based on parameter filtering'''
        uri = 'file://localhost/some/folder/filename.ext'
        Dataset.objects.get_or_create(uri)
        testingDataset = Dataset.objects.filter(
            parameters__standard_name='surface_backwards_scattering_coefficient_of_radar_wave')
        self.assertEqual(str(testingDataset.first().parameters.first()),
                         self.predefined_band_metadata_dict[2]['standard_name'])

    def test_dont_add_longitude_latitude(self):
        """ shall not add latitude and longitude into Parameters of Dataset table """
        uri = 'file://localhost/some/folder/filename.ext'
        ds0, _ = Dataset.objects.get_or_create(uri)
        ds_params_standard_names = ds0.parameters.values_list('standard_name', flat=True)
        # longitude should not be one of the parameters
        self.assertNotIn('longitude', ds_params_standard_names)
        # latitude should not be one of the parameters
        self.assertNotIn('latidtude', ds_params_standard_names)

    def test_add_sigma0_gamma0(self):
        """ shall add both sigma0 and gamma0 with same standard name into Parameters of Dataset table """
        uri = 'file://localhost/some/folder/filename.ext'
        ds0, _ = Dataset.objects.get_or_create(uri)
        ds_params_standard_names = ds0.parameters.values_list('standard_name', flat=True)
        ds_params_short_names = ds0.parameters.values_list('short_name', flat=True)
        self.assertEqual(len(ds_params_standard_names), 2)
        self.assertEqual(len(ds_params_short_names), 2)
        self.assertIn('surface_backwards_scattering_coefficient_of_radar_wave',
                      ds_params_standard_names)
        self.assertIn('sigma0', ds_params_short_names)
        self.assertIn('gamma0', ds_params_short_names)


class TestDatasetURI(BasetForTests):
    """Class for containing the tests of creation of dataseturi after creation of dataset"""
    def test_get_non_ingested_uris(self):
        ''' Shall return list with only  non existing files '''
        testfile = 'file://localhost/vagrant/shared/test_data/meris_l1/MER_FRS_1PNPDK20120303_093810_000000333112_00180_52349_3561.N1'
        Dataset.objects.get_or_create(testfile)
        new_uris = ['file://fake/path/file1.ext', 'file://fake/path/file2.ext']
        all_uris = new_uris + [testfile]
        uris = DatasetURI.objects.all().get_non_ingested_uris(all_uris)
        self.assertEqual(uris, new_uris)


class TestIngestNansatCommand(BasetForTests):
    def test_add_asar(self):
        out = StringIO()
        f = 'file://localhost/vagrant/shared/test_data/asar/ASA_WSM_1PNPDK20081110_205618_000000922073_00401_35024_0844.N1'
        call_command('ingest', f, stdout=out)
        self.assertIn('Successfully added:', out.getvalue())

    def test_add_asar_with_nansat_options(self):
        out = StringIO()
        f = 'file://localhost/vagrant/shared/test_data/asar/ASA_WSM_1PNPDK20081110_205618_000000922073_00401_35024_0844.N1'
        call_command('ingest', f, nansat_option=['mapperName=asar'], stdout=out)
        self.assertIn('Successfully added:', out.getvalue())


class TestIngestThreddsCrawl(TestCase):
    def setUp(self):
        self.uri = 'http://nbstds.met.no/TEST/thredds/dodsC/NBS/S2A/2019/01/24/'
        self.patch_crawl = patch(
            'geospaas.nansat_ingestor.management.commands.ingest_thredds_crawl.crawl_and_ingest')
        self.mock_crawl = self.patch_crawl.start()
        self.mock_crawl.return_value = 10

    def tearDown(self):
        self.patch_crawl.stop()

    def test_ingest_no_args(self):
        with captured_output() as (out, err):
            call_command('ingest_thredds_crawl', self.uri)
        output = out.getvalue().strip()
        self.assertEqual(output, 'Successfully added metadata of 10 datasets')

    def test_ingest_with_year_arg(self):
        with captured_output() as (out, err):
            call_command('ingest_thredds_crawl', self.uri, date=['2019/01/24'])
        output = out.getvalue().strip()
        self.assertEqual(output, 'Successfully added metadata of 10 datasets')

    def test_ingest_with_filename_arg(self):
        with captured_output() as (out, err):
            call_command('ingest_thredds_crawl', self.uri,
                         filename='S2A_MSIL1C_20190124T115401_N0207_R023_T30VWP_20190124T120414.nc')
        output = out.getvalue().strip()
        self.assertEqual(output, 'Successfully added metadata of 10 datasets')


class TestIngestThreddsCrawl__crawl__function(TestCase):
    def setUp(self):
        self.uri = 'http://nbstds.met.no/TEST/thredds/dodsC/NBS/S2A/2019/01/24/'
        self.patch_LeafDataset = patch('thredds_crawler.crawl.LeafDataset')
        self.mock_LeafDataset = self.patch_LeafDataset.start()
        self.patch_validate_uri = patch(
            'geospaas.nansat_ingestor.management.commands.ingest_thredds_crawl.validate_uri')
        self.mock_validate_uri = self.patch_validate_uri.start()
        self.mock_validate_uri.return_value = True
        self.patch_Crawl = patch(
            'geospaas.nansat_ingestor.management.commands.ingest_thredds_crawl.Crawl')
        self.mock_Crawl = self.patch_Crawl.start()
        self.mock_Crawl.SKIPS = []
        self.patch_Dataset = patch(
            'geospaas.nansat_ingestor.management.commands.ingest_thredds_crawl.NansatDataset')
        self.mock_ds = self.patch_Dataset.start()
        pmod = 'geospaas.nansat_ingestor.management.commands.ingest_thredds_crawl.DatasetURI'
        self.patch_DatasetURI = patch(pmod)
        self.mock_dsuri = self.patch_DatasetURI.start()
        from thredds_crawler.crawl import LeafDataset
        test_LeafDataset = LeafDataset()
        test_LeafDataset.services = [
            {
                'name': 'odap',
                'service': 'OPENDAP',
                'url': 'http://nbstds.met.no/TEST/thredds/dodsC/NBS/S2A/2019/01/24/'
                'S2A_MSIL1C_20190124T115401_N0207_R023_T30VWP_20190124T120414.nc'
            }, {
                'name': 'httpService',
                'service': 'HTTPServer',
                'url': 'http://nbstds.met.no/TEST/fileServer/dodsC/NBS/S2A/2019/01/24/'
                'S2A_MSIL1C_20190124T115401_N0207_R023_T30VWP_20190124T120414.nc'
            }, {
                'name': 'wms',
                'service': 'WMS',
                'url': 'http://nbstds.met.no/TEST/wms/dodsC/NBS/S2A/2019/01/24/'
                'S2A_MSIL1C_20190124T115401_N0207_R023_T30VWP_20190124T120414.nc'
            }, {
                'name': 'wcs',
                'service': 'WCS',
                'url': 'http://nbstds.met.no/TEST/wcs/dodsC/NBS/S2A/2019/01/24/'
                'S2A_MSIL1C_20190124T115401_N0207_R023_T30VWP_20190124T120414.nc'
            }
        ]
        self.mock_Crawl.return_value = PropertyMock(
            datasets=[test_LeafDataset])
        self.addCleanup(patch.stopall)

    def test_ds_created(self):
        '''shall assert that NansatDataset.objects.get_or_create
        is called for only once with correct input calls (called with opendap)'''
        self.mock_ds.objects.get_or_create.return_value = (Dataset(), True)
        self.mock_dsuri.objects.get_or_create.return_value = (
            DatasetURI(), True)
        added = crawl_and_ingest(self.uri)
        self.mock_validate_uri.assert_called_once_with(self.uri)
        self.mock_Crawl.assert_called_once_with(
            self.uri, debug=True, select=None, skip=['.*ncml'])
        self.mock_ds.objects.get_or_create.assert_called_once_with(
            'http://nbstds.met.no/TEST/thredds/dodsC/NBS/S2A/2019/01/24/'
            'S2A_MSIL1C_20190124T115401_N0207_R023_T30VWP_20190124T120414.nc',
            uri_service_name='odap',
            uri_service_type='OPENDAP')
        self.assertEqual(added, 1)

    def test_dsuri_ds_created(self):
        '''shall assert that DatasetURI.objects.get_or_create
        is called several times with correct input calls'''
        self.mock_ds.objects.get_or_create.return_value = (Dataset(), True)
        self.mock_dsuri.objects.get_or_create.return_value = (
            DatasetURI(), True)
        crawl_and_ingest(self.uri)
        self.mock_validate_uri.assert_called_once_with(self.uri)
        self.mock_Crawl.assert_called_once_with(
            self.uri, debug=True, select=None, skip=['.*ncml'])
        self.assertEqual(
            self.mock_dsuri.objects.get_or_create.call_args_list[0].kwargs['name'], 'odap')
        self.assertEqual(
            self.mock_dsuri.objects.get_or_create.call_args_list[1].kwargs['service'], 'HTTPServer')
        self.assertEqual(
            self.mock_dsuri.objects.get_or_create.call_args_list[2].kwargs['name'], 'wms')
        self.assertEqual(
            self.mock_dsuri.objects.get_or_create.call_args_list[3].kwargs['service'], 'WCS')

    def test_ds_created_with_date_arg(self):
        self.mock_ds.objects.get_or_create.return_value = (Dataset(), True)
        self.mock_dsuri.objects.get_or_create.return_value = (
            DatasetURI(), True)

        added = crawl_and_ingest(self.uri, date='2019/01/01')
        self.mock_validate_uri.assert_called_once_with(self.uri)
        self.mock_Crawl.assert_called_once_with(self.uri, debug=True,
                                                select=['(.*2019/01/01.*\\.nc)'], skip=['.*ncml'])
        self.assertEqual(added, 1)

    def test_ds_created_with_filename_arg(self):
        self.mock_ds.objects.get_or_create.return_value = (Dataset(), True)
        self.mock_dsuri.objects.get_or_create.return_value = (
            DatasetURI(), True)
        fn = 'S2A_MSIL1C_20190124T115401_N0207_R023_T30VWP_20190124T120414.nc'
        added = crawl_and_ingest(self.uri, filename=fn)
        self.mock_validate_uri.assert_called_once_with(self.uri)
        self.mock_Crawl.assert_called_once_with(self.uri, debug=True,
                                                select=[
                                                    '(.*S2A_MSIL1C_20190124T115401_N0207_R023_T30VWP_20190124T120414.nc)'],
                                                skip=['.*ncml'])
        self.assertEqual(added, 1)

    def test_get_or_create_raises_IOError(self):
        # I am not sure which situations caused IOError, so this is not tested now (on 2019-02-15,
        # the S2 data access from the Norwegian ground segment was failing)
        pass

    def test_get_or_create_raises_AttributeError(self):
        # I am not sure which situations caused AttributeError, so this is not tested now (on 2019-02-15,
        # the S2 data access from the Norwegian ground segment was failing)
        pass


class TestsForUpdateAbility(BasetForTests):
    predefined_metadata_dict = {
        'entry_id': 'NERSC_test_dataset_titusen',
        'entry_title': 'new title from nansat mapper',
        'platform': '{"Category": "Earth Observation Satellites", "Series_Entity": "", "Short_Name": "ENVISAT", "Long_Name": "Environmental Satellite"}',
        'instrument': '{"Category": "Earth Remote Sensing Instruments", "Class": "Passive Remote Sensing", "Type": "Spectrometers/Radiometers", "Subtype": "Imaging Spectrometers/Radiometers", "Short_Name": "MERIS", "Long_Name": "Medium Resolution Imaging Spectrometer"}',
        'time_coverage_start': '2011-05-03T10:56:38.995099',
        'time_coverage_end': '2012-05-03T10:56:38.995099'
    }

    def test_for_examining_the_updating_purpose_of_ingestor_code(self):
        '''shall update the previous record (existing dataset) in the database without creating a new one'''
        uri = 'file://localhost/some/folder/filename.ext'
        d0, _ = Dataset.objects.get_or_create(uri)
        # assertion of updating ability
        self.assertEqual(d0.entry_title, 'new title from nansat mapper')
        # assertion of presence of both online link and offline link are present in the set of uri
        self.assertEqual(2, d0.dataseturi_set.all().count())
        self.assertIn('file://localhost/some/test/file1.ext', [d0.dataseturi_set.first(
        ).uri, d0.dataseturi_set.last().uri])  # assertion of online link
        self.assertIn('file://localhost/some/folder/filename.ext', [d0.dataseturi_set.first(
        ).uri, d0.dataseturi_set.last().uri])  # assertion of offline link
