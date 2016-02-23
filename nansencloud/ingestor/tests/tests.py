import datetime

from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase

from nansencloud.gcmd_keywords.models import Instrument, Platform
from nansencloud.catalog.models import GeographicLocation
from nansencloud.ingestor.models import Source, DatasetURI, Dataset


class TestSource(TestCase):
    def test_create_valid(self):
        ''' shall create and save valid source '''
        pp = Platform.objects.get(short_name='ENVISAT')
        ii = Instrument.objects.get(short_name='MERIS')
        s = Source.objects.create(platform=pp, instrument=ii)

    def test_create_invalid(self):
        ''' shall not create and save invalid source '''
        with self.assertRaises(Exception):
            Source.objects.create(platform='crap', instrument='crap')

    def test_getorcreate_valid(self):
        ''' create and save valid source '''
        pp = Platform.objects.get(short_name='ENVISAT')
        ii = Instrument.objects.get(short_name='ASAR')
        src, cr = Source.objects.get_or_create(platform=pp, instrument=ii)
        self.assertTrue(cr)


class TestDataset(TestCase):
    def setUp(self):
        self.testfile = '/vagrant/shared/test_data/meris_l1/MER_FRS_1PNPDK20120303_093810_000000333112_00180_52349_3561.N1'

    def test_getorcreate(self):
        ''' Shall open file, read metadata and save'''
        ds0, cr0 = Dataset.objects.get_or_create(self.testfile)
        ds1, cr1 = Dataset.objects.get_or_create(self.testfile)

        self.assertTrue(cr0)
        self.assertFalse(cr1)


class TestDatasetURI(TestCase):
    def setUp(self):
        self.testfile = '/vagrant/shared/test_data/meris_l1/MER_FRS_1PNPDK20120303_093810_000000333112_00180_52349_3561.N1'
        self.ds = Dataset.objects.get_or_create(self.testfile)[0]

    def test_create_valid(self):
        ''' Shall create valid DatasetURI '''
        dl = DatasetURI.objects.create(protocol=DatasetURI.LOCALFILE,
                                        uri=self.testfile,
                                        dataset=self.ds)

    def test_create_invalid(self):
        ''' Shall not create invalid DatasetURI '''
        with self.assertRaises(Exception):
            dl = DatasetURI.objects.create(protocol='crap',
                                        uri=self.testfile,
                                        dataset=self.ds)

    def test_get_non_ingested_uris(self):
        ''' Shall return list with only  non existing files '''
        new_uris = ['/fake/path/file1.ext', '/fake/path/file2.ext']
        all_uris = new_uris + [self.testfile]

        uris = DatasetURI.objects.all().get_non_ingested_uris(all_uris)
        self.assertEqual(uris, new_uris)


class TestIngestNansatCommand(TestCase):
    def test_add_asar(self):
        out = StringIO()
        f = '/vagrant/shared/test_data/asar/ASA_WSM_1PNPDK20081110_205618_000000922073_00401_35024_0844.N1'
        call_command('ingest', f, stdout=out)
        self.assertIn('Successfully added:', out.getvalue())
