import datetime

from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase

from nansencloud.vocabularies.models import Instrument, Platform
from nansencloud.catalog.models import DatasetURI, GeographicLocation
from nansencloud.nansat_ingestor.models import Dataset


#Move to catalog.tests or delete
#class TestSource(TestCase):
#    def test_create_valid(self):
#        ''' shall create and save valid source '''
#        pp = Platform.objects.get(short_name='ENVISAT')
#        ii = Instrument.objects.get(short_name='MERIS')
#        s = Source.objects.create(platform=pp, instrument=ii)
#
#    def test_create_invalid(self):
#        ''' shall not create and save invalid source '''
#        with self.assertRaises(Exception):
#            Source.objects.create(platform='crap', instrument='crap')
#
#    def test_getorcreate_valid(self):
#        ''' create and save valid source '''
#        pp = Platform.objects.get(short_name='ENVISAT')
#        ii = Instrument.objects.get(short_name='ASAR')
#        src, cr = Source.objects.get_or_create(platform=pp, instrument=ii)
#        self.assertTrue(cr)


class TestDataset(TestCase):

    fixtures = ['vocabularies', 'catalog']

    def test_getorcreate_localfile(self):
        uri = 'file://localhost/vagrant/shared/test_data/meris_l1/MER_FRS_1PNPDK20120303_093810_000000333112_00180_52349_3561.N1'
        ''' Shall open file, read metadata and save'''
        ds0, cr0 = Dataset.objects.get_or_create(uri)
        ds1, cr1 = Dataset.objects.get_or_create(uri)

        self.assertTrue(cr0)
        self.assertFalse(cr1)

    def test_getorcreate_from_opendap(self):
        uri = 'http://www.ifremer.fr/opendap/cerdap1/globcurrent/v2.0/global_025_deg/geostrophic/2014/001/20140101000000-GLOBCURRENT-L4-CURgeo_0m-ALT_OI-v02.0-fv01.0.nc'
        ds0, cr0 = Dataset.objects.get_or_create(uri)
        self.assertTrue(cr0)

    def test_fail_invalid_uri(self):
        uri = '/this/is/some/file/but/not/an/uri'
        with self.assertRaises(ValueError):
            ds, created = Dataset.objects.get_or_create(uri)

class TestDatasetURI(TestCase):

    fixtures = ["vocabularies", "catalog"]

    def test_get_non_ingested_uris(self):
        ''' Shall return list with only  non existing files '''
        testfile = 'file://localhost/vagrant/shared/test_data/meris_l1/MER_FRS_1PNPDK20120303_093810_000000333112_00180_52349_3561.N1'
        ds = Dataset.objects.get_or_create(testfile)[0]
        new_uris = ['file://fake/path/file1.ext', 'file://fake/path/file2.ext']
        all_uris = new_uris + [testfile]

        uris = DatasetURI.objects.all().get_non_ingested_uris(all_uris)
        self.assertEqual(uris, new_uris)

class TestIngestNansatCommand(TestCase):

    fixtures = ["vocabularies", "catalog"]

    def test_add_asar(self):
        out = StringIO()
        f = 'file://localhost/vagrant/shared/test_data/asar/ASA_WSM_1PNPDK20081110_205618_000000922073_00401_35024_0844.N1'
        call_command('ingest', f, stdout=out)
        self.assertIn('Successfully added:', out.getvalue())
