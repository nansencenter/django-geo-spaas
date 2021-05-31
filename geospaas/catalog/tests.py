import os
import json
from mock import patch, PropertyMock, Mock, MagicMock, DEFAULT

import django.db.utils
from django.test import TestCase
from django.utils import timezone
from django.contrib.gis.geos import Polygon
from django.contrib.gis.geos import WKTReader
from django.core.management import call_command
from django.core.exceptions import ValidationError
from io import StringIO
from django.conf import settings
from django.core.management.base import CommandError

from geospaas.vocabularies.models import Platform, Instrument, Parameter
from geospaas.vocabularies.models import ISOTopicCategory, DataCenter
from geospaas.catalog.models import *


class DatasetTests(TestCase):

    fixtures = ["vocabularies", "catalog"]

    @patch('os.path.isfile')
    def test_dataset(self, mock_isfile):
        mock_isfile.return_value = True
        ''' Shall create Dataset instance '''
        iso_category = ISOTopicCategory.objects.get(name='Oceans')
        dc = DataCenter.objects.get(short_name='NERSC')
        source = Source.objects.get(pk=1)
        geolocation = GeographicLocation.objects.get(pk=1)
        et = 'Test dataset'
        id = 'NERSC_test_dataset_1'
        ds = Dataset(
                entry_id = id,
                entry_title=et,
                ISO_topic_category = iso_category,
                data_center = dc,
                summary = 'This is a quite short summary about the test' \
                            ' dataset.',
                time_coverage_start=timezone.datetime(2010,1,1,
                    tzinfo=timezone.utc),
                time_coverage_end=timezone.datetime(2010,1,2,
                    tzinfo=timezone.utc),
                source=source,
                geographic_location=geolocation)
        ds.save()
        self.assertEqual(ds.entry_id, id)
        self.assertEqual(ds.entry_title, et)

        # Shall create new DatasetURI
        ds_uri1, cr1 = DatasetURI.objects.get_or_create(uri='file://localhost/test_name1.nc',
                                                      dataset=ds)
        self.assertIsInstance(ds_uri1, DatasetURI)
        self.assertEqual(cr1, True)

        # Shall NOT create new DatasetURI
        ds_uri2, cr2 = DatasetURI.objects.get_or_create(uri='file://localhost/test_name1.nc',
                                                      dataset=ds)
        self.assertEqual(ds_uri1, ds_uri2)
        self.assertEqual(cr2, False)

        # Shall create new DatasetURI
        ds_uri3, cr3 = DatasetURI.objects.get_or_create(uri='file://localhost/test_name2.nc',
                                                      dataset=ds)
        self.assertIsInstance(ds_uri3, DatasetURI)
        self.assertEqual(cr3, True)

        # Add parameter
        ## Dump data for use in fixture
        #with open('dataset.json', 'w') as out:
        #    call_command('dumpdata', '--natural-foreign', '--traceback',
        #            '--indent=4',
        #            'catalog.Dataset',
        #            'catalog.GeographicLocation',
        #            stdout=out)

    def test_entry_id_is_wrong(self):
        iso_category = ISOTopicCategory.objects.get(name='Oceans')
        dc = DataCenter.objects.get(short_name='NERSC')
        source = Source.objects.get(pk=1)
        geolocation = GeographicLocation.objects.get(pk=1)
        et = 'Test dataset'
        id = 'NERSC/test/dataset/1'
        ds = Dataset(
                entry_id = id,
                entry_title=et,
                ISO_topic_category = iso_category,
                data_center = dc,
                summary = 'This is a quite short summary about the test' \
                            ' dataset.',
                time_coverage_start=timezone.datetime(2010,1,1,
                    tzinfo=timezone.utc),
                time_coverage_end=timezone.datetime(2010,1,2,
                    tzinfo=timezone.utc),
                source=source,
                geographic_location=geolocation)
        with self.assertRaises(ValidationError):
            ds.full_clean()

    def test_entry_id_is_correct(self):
        iso_category = ISOTopicCategory.objects.get(name='Oceans')
        dc = DataCenter.objects.get(short_name='NERSC')
        source = Source.objects.get(pk=1)
        geolocation = GeographicLocation.objects.get(pk=1)
        et = 'Test dataset'
        id = 'NERSC_test_dataset_1.2'
        ds = Dataset(
                entry_id = id,
                entry_title=et,
                ISO_topic_category = iso_category,
                data_center = dc,
                summary = 'This is a quite short summary about the test' \
                            ' dataset.',
                time_coverage_start=timezone.datetime(2010,1,1,
                    tzinfo=timezone.utc),
                time_coverage_end=timezone.datetime(2010,1,2,
                    tzinfo=timezone.utc),
                source=source,
                geographic_location=geolocation)
        ds.full_clean()
        self.assertEqual(ds.entry_id, id)


class DatasetURITests(TestCase):

    fixtures = ["vocabularies", "catalog"]

    def setUp(self):
        self.dataset = Dataset.objects.get(pk=1)

    @patch('os.path.isfile')
    def test_DatasetURI_created(self, mock_isfile):
        mock_isfile.return_value = True
        uri = 'file://localhost/this/is/some/file'
        dsuri = DatasetURI(uri=uri, dataset=self.dataset)
        dsuri.save()
        self.assertEqual(dsuri.uri, uri)


class DatasetRelationshipTests(TestCase):

    fixtures = ["vocabularies", "catalog"]

    def test_variable(self):
        ''' Shall create DatasetRelationship instance
        NOTE: this example dataset relationship doesn't seem very realistic. We
        should create a proper test that repeats the way we plan to use this...
        '''
        child = Dataset.objects.get(pk=1)
        parent = Dataset.objects.get(pk=2)
        dr = DatasetRelationship(child=child, parent=parent)
        dr.save()
        self.assertEqual(dr.child.source, dr.parent.source)


class GeographicLocationTests(TestCase):
    def test_geographiclocation(self):
        ''' Shall create GeographicLocation instance '''
        geolocation = GeographicLocation(
            geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()

    def test_unique_constraint_geographic_location(self):
        """Test that the same GeographicLocation can't be inserted twice"""
        attributes = {'geometry': Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0)))}
        geolocation1 = GeographicLocation(**attributes)
        geolocation2 = GeographicLocation(**attributes)

        geolocation1.save()

        with self.assertRaises(django.db.utils.IntegrityError):
            geolocation2.save()

    def test__reproduce__not_null_constraint_failed(self):
        geom_wkt = 'POLYGON((1.9952502916543926 43.079137301616434,1.8083614437225106 43.110281163194,1.6280391132319614 43.13999933989308,1.4543047771860391 43.168322409488,1.287178802518546 43.19527992537942,1.126680477150093 43.22090040126175,0.9728280404789855 43.24521129666272,0.8256387132257121 43.26823900332679,0.6851287265540695 43.2900088324148,0.5513133503959514 43.31054500249216,0.4177032107533156 43.3308546554019,0.4177032107533156 43.3308546554019,0.31209072545607186 42.966172534807384,0.2072770834059167 42.60138984322352,0.10324224766647609 42.23651548835664,-3.327518831779395e-05 41.87155835974214,-0.10256845388361147 41.50652732885059,-0.20438175048840848 41.14143124914533,-0.305491137731497 40.776278956093606,-0.4059141156224018 40.4110792671334,-0.5056677274094622 40.045840981598744,-0.6188735003262834 39.62838980058282,-0.6188735003262834 39.62838980058282,-0.4938090620192412 39.60834071737128,-0.36846516623385345 39.58812662484392,-0.2367679070115216 39.566753658618175,-0.09872965092928164 39.54419980869909,0.045636463325510676 39.520442055142105,0.19631650129236156 39.49545637806485,0.35329570832956364 39.469217768317954,0.516558484513175 39.441700238839005,0.686088358898322 39.412876836714965,0.8618679632011015 39.382719655976956,0.8618679632011015 39.382719655976956,0.985334472893415 39.799577386800905,1.0941941665822539 40.164279112775866,1.2038450353475123 40.52892574316672,1.3143064728956748 40.89350812553239,1.425598388091744 41.25801708090206,1.5377412226553768 41.622443403572326,1.6507559695776892 41.98677786085107,1.764664192292795 42.351011192745254,1.8794880446399878 42.71513411159017,1.9952502916543926 43.079137301616434))'
        try:
            with self.assertRaises(django.db.utils.IntegrityError):
                gg, created = GeographicLocation.objects.get_or_create(geometry=WKTReader().read(geom_wkt))
        except AssertionError:
            print('In catalog.tests.GeographicLocationTests.'
                  'test__reproduce__not_null_constraint_failed, the expected error did not happen.')
        geom_wkt = 'POLYGON((1.995 43.079,1.808 43.1102,1.628 43.139,1.454 43.168,1.287 43.195,1.126 43.220,0.972 43.245,0.825 43.268,0.685 43.290,0.551 43.310,0.417 43.330,0.417 43.330,0.312 42.966,0.207 42.601,0.103 42.236,0.0 41.871,-0.102 41.506,-0.204 41.141,-0.305 40.776,-0.405 40.411,-0.505 40.045,-0.618 39.628,-0.618 39.628,-0.493 39.608,-0.368 39.588,-0.236 39.566,-0.098 39.544,0.0456 39.520,0.196 39.495,0.353 39.469,0.516 39.441,0.686 39.412,0.861 39.382,0.861 39.382,0.985 39.799,1.094 40.164,1.203 40.528,1.314 40.893,1.425 41.258,1.537 41.622,1.650 41.986,1.764 42.351,1.879 42.715,1.995 43.079))'
        gg, created = GeographicLocation.objects.get_or_create(geometry=WKTReader().read(geom_wkt))
        self.assertTrue(created)
        gg, created = GeographicLocation.objects.get_or_create(geometry=WKTReader().read(geom_wkt))
        self.assertFalse(created)
        # Conclusion: db can't handle numbers with too many decimals (NOT NULL constraint failed)


class PersonnelTests(TestCase):
    ''' We should add user admin with, e.g., with the Personnel model. Skip
    testing before that is in place
    '''
    pass


class RoleTests(TestCase):
    pass


class SourceTests(TestCase):

    fixtures = ["vocabularies"]

    def test_source(self):
        ''' Shall create Source instance '''
        p = Platform.objects.get(short_name='AQUA')
        i = Instrument.objects.get(short_name='MODIS')
        source = Source(platform=p, instrument=i)
        source.save()

    def test_without_short_names(self):
        ''' retrieving objects without short_name from the database and creating source
        based on them'''
        p = Platform.objects.get(pk=168)
        i = Instrument.objects.get(pk=140)
        source = Source(platform=p, instrument=i)
        source.save()
        self.assertEqual(source.platform.short_name, "")
        self.assertEqual(source.platform.series_entity, "Earth Explorers")
        self.assertEqual(source.instrument.short_name, "")
        self.assertEqual(source.instrument.subtype, "Lidar/Laser Spectrometers")

    def test_empty_short_names(self):
        ''' creating objects without short_name and creating source
        based on them'''
        platform2=Platform(category = '',
        series_entity = '',
        short_name = '',
        long_name = '')
        instrument2=Instrument(
                category ='',
        instrument_class = '',
        type = '',
        subtype = '',
        short_name = '',
        long_name = '')
        platform2.save()
        instrument2.save()
        source2 = Source(platform=platform2, instrument=instrument2)
        source2.save()
        self.assertEqual(source2.platform.long_name, "")
        self.assertEqual(source2.platform.series_entity, "")
        self.assertEqual(source2.instrument.long_name, "")
        self.assertEqual(source2.instrument.category, "")

    def test_source_uniqueness(self):

        plat1 = Platform.objects.get(pk=661) # "short_name": ""
        inst1 = Instrument.objects.get(pk=139)# "short_name": ""
        source, created1 = Source.objects.get_or_create(platform=plat1, instrument=inst1)
        source2, created2 = Source.objects.get_or_create(platform=plat1, instrument=inst1)
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(source2, source)
        inst2 = Instrument.objects.get(pk=160)# "short_name": ""
        source3,_ = Source.objects.get_or_create(platform=plat1, instrument=inst2)
        self.assertNotEqual(source3, source2)



class TestCountCommand(TestCase):
    fixtures = ['vocabularies', 'catalog']
    def test_count_command(self):
        out = StringIO()
        call_command('count', stdout=out)
        self.assertEqual('Found 2 matching datasets\n', out.getvalue())

        out = StringIO()
        call_command('count', start='2010-01-02', stdout=out)
        self.assertEqual('Found 1 matching datasets\n', out.getvalue())

        out = StringIO()
        call_command('count', extent=[0, 10, 0, 10], stdout=out)
        self.assertEqual('Found 1 matching datasets\n', out.getvalue())

        out = StringIO()
        with self.assertRaises(CommandError) as ce:
            call_command('count', geojson='fake_filename', stdout=out)
        self.assertIn('GeoJSON file', ce.exception.args[0])

    def test_count_command_bad_start(self):
        out = StringIO()
        with self.assertRaises(CommandError) as ce:
            call_command('count', start='abrakadabra', stdout=out)
        self.assertIn('Not a valid date', ce.exception.args[0])

    @patch('geospaas.utils.processing_base_command.open')
    def test_count_command_good_geojson_polygon(self, mock_open):
        mock_open.return_value.__enter__.return_value.read.return_value = '{ "type": "Polygon", "coordinates": [ [ [ -1, -1 ], [ -1, 11 ], [ 11, 11 ], [ 11, -1 ], [ -1, -1 ] ] ] }'
        out = StringIO()
        call_command('count', geojson=os.path.realpath(__file__), stdout=out)
        self.assertEqual('Found 1 matching datasets\n', out.getvalue())

    @patch('geospaas.utils.processing_base_command.open')
    def test_count_command_good_geojson_point(self, mock_open):
        mock_open.return_value.__enter__.return_value.read.return_value = '{ "type": "Point", "coordinates": [ 1, 1 ] }'
        out = StringIO()
        call_command('count', geojson=os.path.realpath(__file__), stdout=out)
        self.assertEqual('Found 1 matching datasets\n', out.getvalue())

    @patch('geospaas.utils.processing_base_command.open')
    def test_count_command_wrong_geojson_content(self, mock_open):
        mock_open.return_value.__enter__.return_value.read.return_value = 'wrong json'
        out = StringIO()
        with self.assertRaises(CommandError) as ce:
            call_command('count', geojson=os.path.realpath(__file__), stdout=out)
        self.assertIn('Failed to read valid GeoJSON from', ce.exception.args[0])
