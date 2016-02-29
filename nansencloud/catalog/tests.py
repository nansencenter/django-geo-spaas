import mock
import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.gis.geos import Polygon
from django.core.management import call_command
from django.core.exceptions import ValidationError

from nansencloud.gcmd_keywords.models import Platform, Instrument
from nansencloud.gcmd_keywords.models import ISOTopicCategory, DataCenter
from nansencloud.catalog.models import *

class DatasetTests(TestCase):

    fixtures = ["gcmd", "catalog"]

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

class DatasetURITests(TestCase):

    fixtures = ["gcmd", "catalog"]

    def setUp(self):
        self.dataset = Dataset.objects.get(pk=1)

    def test_DatasetURI_created(self):
        uri = 'file://this/is/some/file'
        dsuri = DatasetURI(uri=uri, dataset=self.dataset)
        try:
            dsuri.save()
        except ValidationError as e:
            print(e.message)
        self.assertEqual(dsuri.uri, uri)

    def test_fail_invalid_uri(self):
        uri = '/this/is/some/file/but/not/an/uri'
        with self.assertRaises(ValidationError):
            dsuri = DatasetURI(uri=uri, dataset=self.dataset)
            dsuri.save()

class DatasetParameterTests(TestCase):

    fixtures = ["gcmd", "catalog"]

    def test_add_well_known_variables(self):
        Parameter.objects.create_from_standards()
        ## Dump data for use in fixture
        #with open('parameters.json', 'w') as out:
        #    call_command('dumpdata', '--natural-foreign', '--traceback',
        #            '--indent=4',
        #            'catalog.Parameter', 
        #            stdout=out)

    def test_add_sar_sigma0(self):
        ds = Dataset.objects.get(pk=1)
        p = Parameter.objects.get(
                standard_name='surface_backwards_scattering_coefficient_of_radar_wave')
        dp = DatasetParameter(dataset=ds, parameter=p)
        dp.save()
        self.assertEqual(dp.parameter.short_name, 'sigma0')

class DatasetRelationshipTests(TestCase):
    def test_variable(self):
        ''' Shall create DatasetRelationship instance '''
        geolocation = GeographicLocation(
                geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()
        p = Platform.objects.get(short_name='AQUA')
        i = Instrument.objects.get(short_name='MODIS')
        source = Source(platform=p, instrument=i)
        source.save()
        child = Dataset(geolocation=geolocation,
                            source=source,
                            time_coverage_start=timezone.datetime(2010,1,1,
                                tzinfo=timezone.utc),
                            time_coverage_end=timezone.datetime(2010,1,2,
                                tzinfo=timezone.utc))
        child.save()
        parent = Dataset(geolocation=geolocation,
                            source=source,
                            time_coverage_start=timezone.datetime(2010,1,2,
                                tzinfo=timezone.utc),
                            time_coverage_end=timezone.datetime(2010,1,3,
                                tzinfo=timezone.utc))
        parent.save()
        dr = DatasetRelationship(child=child, parent=parent)
        dr.save()

class GeographicLocationTests(TestCase):
    def test_geographiclocation(self):
        ''' Shall create GeographicLocation instance '''
        geolocation = GeographicLocation(
            geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()

class PersonnelTests(TestCase):

    pass

class ParameterTests(TestCase):

    pass

class RoleTests(TestCase):

    pass

class SourceTests(TestCase):
    def test_source(self):
        ''' Shall create Source instance '''
        p = Platform.objects.get(short_name='AQUA')
        i = Instrument.objects.get(short_name='MODIS')
        source = Source(platform=p, instrument=i)
        source.save()




# Populate Parameter table with CF-variables and change this class to
class ProductTests(TestCase):
    def test_variable(self):
        ''' Shall create Product instance '''
        geolocation = GeographicLocation(
                geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()
        p = Platform.objects.get(short_name='AQUA')
        i = Instrument.objects.get(short_name='MODIS')
        source = Source(platform=p, instrument=i)
        source.save()
        dataset = Dataset(geolocation=geolocation,
                            source=source,
                            time_coverage_start=timezone.datetime(2010,1,1,
                                tzinfo=timezone.utc),
                            time_coverage_end=timezone.datetime(2010,1,2,
                                tzinfo=timezone.utc))
        dataset.save()
        location = DataLocation(protocol=DataLocation.LOCALFILE,
                                dataset=dataset,
                                uri='somefile.txt')
        location.save()
        var = Product(short_name='sst',
                        standard_name='sea_surface_temparture',
                        long_name='Temperature of Sea Surface',
                        units='K',
                        location=location,
                        time=timezone.datetime(2010,1,2, tzinfo=timezone.utc))
        var.save()

    def test_search_datasets(self):
        ''' Shall create two datasets and only one product
            shall find one Dataset without products '''
        p = Platform.objects.get(short_name='AQUA')
        i = Instrument.objects.get(short_name='MODIS')
        source = Source(platform=p, instrument=i)
        source.save()

        geolocation1 = GeographicLocation(
                geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation1.save()
        dataset1 = Dataset(geolocation=geolocation1,
                            source=source,
                            time_coverage_start=timezone.datetime(2010,1,1,
                                tzinfo=timezone.utc),
                            time_coverage_end=timezone.datetime(2010,1,2,
                                tzinfo=timezone.utc))
        dataset1.save()
        location1 = DataLocation(protocol=DataLocation.LOCALFILE,
                                dataset=dataset1,
                                uri='somefile.txt')
        location1.save()
        prod = Product(short_name='sst',
                        standard_name='sea_surface_temparture',
                        long_name='Temperature of Sea Surface',
                        units='K',
                        location=location1,
                        time=timezone.datetime(2010,1,2, tzinfo=timezone.utc))
        prod.save()

        geolocation2 = GeographicLocation(
                geometry=Polygon(((0, 1), (0, 10), (10, 10), (0, 10), (0, 1))))
        geolocation2.save()
        dataset2 = Dataset(geolocation=geolocation1,
                            source=source,
                            time_coverage_start=timezone.datetime(2015,1,1,
                                tzinfo=timezone.utc),
                            time_coverage_end=timezone.datetime(2015,1,2,
                                tzinfo=timezone.utc))
        dataset2.save()
        location2 = DataLocation(protocol=DataLocation.LOCALFILE,
                                dataset=dataset2,
                                uri='somefile2.txt')
        location2.save()

        newds = Dataset.objects.filter(
                source__instrument__short_name = 'MODIS'
            ).exclude(datalocation__product__short_name = 'sst' )
        print newds[0]

        self.assertEqual(newds.count(), 1)


