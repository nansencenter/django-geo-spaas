import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.gis.geos import Polygon
from django.core.management import call_command
from django.core.exceptions import ValidationError

from nansencloud.vocabularies.models import Platform, Instrument, Parameter
from nansencloud.vocabularies.models import ISOTopicCategory, DataCenter
from nansencloud.catalog.models import *

class DatasetTests(TestCase):

    fixtures = ["vocabularies", "catalog"]

    def test_dataset(self):
        ''' Shall create Dataset instance '''
        iso_category = ISOTopicCategory.objects.get(name='Oceans')
        dc = DataCenter.objects.get(short_name='NERSC')
        source = Source.objects.get(pk=1)
        geolocation = GeographicLocation.objects.get(pk=1)
        et = 'Test dataset'
        ds = Dataset(
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
        self.assertEqual(ds.entry_title, et)
        # Add parameter
        ## Dump data for use in fixture
        #with open('dataset.json', 'w') as out:
        #    call_command('dumpdata', '--natural-foreign', '--traceback',
        #            '--indent=4',
        #            'catalog.Dataset', 
        #            'catalog.GeographicLocation',
        #            stdout=out)

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

    def test_DatasetURI_created(self):
        uri = 'file://localhost/this/is/some/file'
        dsuri = DatasetURI(uri=uri, dataset=self.dataset)
        dsuri.save()
        self.assertEqual(dsuri.uri, uri)



class DatasetParameterTests(TestCase):

    fixtures = ["vocabularies", "catalog"]

    def test_add_sar_sigma0(self):
        ds = Dataset.objects.get(pk=1)
        p = Parameter.objects.get(
                standard_name='surface_backwards_scattering_coefficient_of_radar_wave')
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
