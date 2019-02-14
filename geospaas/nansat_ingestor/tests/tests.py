import datetime

from mock import patch, PropertyMock, Mock, MagicMock, DEFAULT

from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase

from geospaas.utils.utils import validate_uri
from geospaas.vocabularies.models import Instrument, Platform
from geospaas.catalog.models import DatasetURI, GeographicLocation
from geospaas.nansat_ingestor.models import Dataset

from geospaas.nansat_ingestor.management.commands.ingest_thredds_crawl import crawl

# See also:
# https://docs.python.org/3.5/library/unittest.mock-examples.html#applying-the-same-patch-to-every-test-method

class BasetForTests(TestCase):
    fixtures = ['vocabularies', 'catalog']
    predefined_metadata_dict = {
        'entry_id': 'UNIQUE_ID_1000',
        'platform': '{"Category": "Earth Observation Satellites", "Series_Entity": "", "Short_Name": "ENVISAT", "Long_Name": "Environmental Satellite"}',
        'instrument': '{"Category": "Earth Remote Sensing Instruments", "Class": "Passive Remote Sensing", "Type": "Spectrometers/Radiometers", "Subtype": "Imaging Spectrometers/Radiometers", "Short_Name": "MERIS", "Long_Name": "Medium Resolution Imaging Spectrometer"}',
        'time_coverage_start': '2011-05-03T10:56:38.995099',
        'time_coverage_end': '2011-05-03T10:56:38.995099',
        'data_center' : '{"Bucket_Level0": "MULTINATIONAL ORGANIZATIONS", "Bucket_Level1": "", "Bucket_Level2": "", "Bucket_Level3": "", "Short_Name": "ESA/EO", "Long_Name": "Observing the Earth, European Space Agency", "Data_Center_URL": "http://www.esa.int/esaEO/"}',
        'gcmd_location': '{"Location_Category": "VERTICAL LOCATION", "Location_Type": "SEA SURFACE", "Location_Subregion1": "", "Location_Subregion2": "", "Location_Subregion3": ""}',
        'ISO_topic_category' : '{"iso_topic_category": "Oceans"}',
        }

    def setUp(self):
        self.patcher = patch('geospaas.nansat_ingestor.managers.Nansat')
        self.mock_Nansat = self.patcher.start()
        self.mock_Nansat.return_value.get_metadata.side_effect = self.mock_get_metadata
        self.mock_Nansat.return_value.get_border_wkt.return_value = 'POLYGON((24.88 68.08,22.46 68.71,19.96 69.31,17.39 69.87,24.88 68.08))'

    def tearDown(self):
        self.patcher.stop()

    def mock_get_metadata(self, *args, **kwargs):
        """ Mock behaviour of Nansat.get_metadata method """
        if len(args) == 0:
            return self.predefined_metadata_dict
        if args[0] not in self.predefined_metadata_dict:
            raise
        return self.predefined_metadata_dict[args[0]]

class TestDatasetManager(BasetForTests):
    def test_getorcreate_localfile(self):
        uri = 'file://localhost/some/folder/filename.ext'
        ds0, cr0 = Dataset.objects.get_or_create(uri)
        ds1, cr1 = Dataset.objects.get_or_create(uri)

        self.assertTrue(cr0)
        self.assertFalse(cr1)
        self.assertEqual(ds0.entry_id, self.predefined_metadata_dict['entry_id'])
        self.assertEqual(ds0.entry_title, 'NONE')
        self.assertEqual(ds0.summary, 'NONE')

    def test_fail_invalid_uri(self):
        uri = '/this/is/some/file/but/not/an/uri'
        with self.assertRaises(ValueError):
            ds, created = Dataset.objects.get_or_create(uri)


class TestDatasetURI(BasetForTests):
    def test_get_non_ingested_uris(self):
        ''' Shall return list with only  non existing files '''
        testfile = 'file://localhost/vagrant/shared/test_data/meris_l1/MER_FRS_1PNPDK20120303_093810_000000333112_00180_52349_3561.N1'
        ds = Dataset.objects.get_or_create(testfile)[0]
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

    #def setUp(self):
    #    self.uri = 'http://nbstds.met.no/TEST/thredds/dodsC/NBS/S2A/2019/01/24/'
    #    with patch('urllib3.PoolManager') as self.mock_PoolManager:
    #        self.mock_PoolManager.return_value.request.return_value = PropertyMock(status=200)
    #    with patch('thredds_crawler.crawl.Crawl') as self.mock_Crawl:
    #        self.mock_Crawl.return_value.c.return_value.datasets.services.return_value = [{
    #            'name': 'odap', 
    #            'service': 'OPENDAP', 
    #            'url': 'http://nbstds.met.no/TEST/thredds/dodsC/NBS/S2A/2019/01/24/' \
    #                    'S2A_MSIL1C_20190124T115401_N0207_R023_T30VWP_20190124T120414.nc'
    #        }]

    def test__crawl__function(self):
        pass
        #uri = 'http://nbstds.met.no/TEST/thredds/dodsC/NBS/S2A/2019/01/24/'
        #with patch('geospaas.utils.utils.validate_uri') as mock_validate_uri:
        #    mock_validate_uri.return_value = True
        #    with patch('thredds_crawler.crawl.Crawl') as mock_Crawl:
        #        mock_Crawl.return_value.c.return_value.datasets.services.return_value = [{
        #            'name': 'odap', 
        #            'service': 'OPENDAP', 
        #            'url': 'http://nbstds.met.no/TEST/thredds/dodsC/NBS/S2A/2019/01/24/' \
        #                'S2A_MSIL1C_20190124T115401_N0207_R023_T30VWP_20190124T120414.nc'
        #        }]
        #        crawl(uri)
        #mock_validate_uri.assert_called_once_with(uri)
        #mock_Crawl.assert_called_once_with(uri)


    #@patch('urllib3.PoolManager')
    #def test_ingest_without_args(self, mock_PoolManager):
    #    mock_PoolManager.return_value.request.return_value = PropertyMock(status=200)
    #    uri = 'http://nbstds.met.no/thredds/catalog/NBS/S2A/test_catalog.html'
    #    call_command('ingest_thredds_crawl', uri)

    #def test_ingest_with_year_arg(self):
    #    uri = 'http://nbstds.met.no/thredds/catalog/NBS/S2A/2019/01/24/catalog.html'
    #    call_command('ingest_thredds_crawl', uri, date=['2019/01/31'])

    def test_ingest_with_filename_arg(self):
        pass

