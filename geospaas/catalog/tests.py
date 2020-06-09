import os
import json
from mock import patch, PropertyMock, Mock, MagicMock, DEFAULT

import django.db.utils
from django.test import TestCase
from django.utils import timezone
from django.contrib.gis.geos import Polygon
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

    def test_search_datasets(self):
        ''' Shall add one parameter to the first dataset
            shall find one Dataset without sst '''
        dataset1 = Dataset.objects.get(pk=1)
        p = Parameter.objects.get(
                standard_name='sea_surface_temperature')
        dp = DatasetParameter(dataset=dataset1, parameter=p)
        dp.save()
        dsearch = Dataset.objects.filter( source__instrument__short_name =
                'MODIS')
        dsearch = dsearch.exclude(datasetparameter__parameter__short_name =
                'SST' )
        self.assertEqual(dsearch.count(), 1)

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



class DatasetParameterTests(TestCase):

    fixtures = ["vocabularies", "catalog"]

    def test_add_sar_sigma0(self):
        ds = Dataset.objects.get(pk=1)
        p = Parameter.objects.get(
                standard_name='surface_backwards_scattering_coefficient_of_radar_wave',
                short_name='sigma0')
        dp = DatasetParameter(dataset=ds, parameter=p)
        dp.save()
        self.assertEqual(dp.parameter.short_name, 'sigma0')

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
