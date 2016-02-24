from django.utils import timezone

from django.test import TestCase

from django.contrib.gis.geos import Polygon

from nansencloud.gcmd_keywords.models import Platform, Instrument
from nansencloud.gcmd_keywords.models import ISOTopicCategory, DataCenter
from nansencloud.catalog.models import *

class DatasetTests(TestCase):
    def test_dataset(self):
        ''' Shall create Dataset instance '''
        geolocation = GeographicLocation(
                geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()
        iso_category = ISOTopicCategory.objects.get(name='Oceans')
        dc = DataCenter.objects.get(short_name='NERSC')
        p = Platform.objects.get(short_name='AQUA')
        i = Instrument.objects.get(short_name='MODIS')
        source = Source(platform=p, instrument=i)
        source.save()
        ds = Dataset(
                entry_title='Test dataset', 
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
        # Add parameter

class DatasetURITests(TestCase):

    def test_DatasetURI(self):
        uri = 'file://this/is/some/file'
        mock_dataset = mock.create_autospec(Dataset)
        dsuri = DatasetURI(uri=uri, dataset=mock_dataset)
        dsuri.save()
        etitle = dsuri.dataset.entry_title 
        # Check that the entry_title attribute was accessed


        ''' Shall create DataLocation instance '''
        geolocation = GeographicLocation(
                geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()
        p = Platform.objects.get(short_name='AQUA')
        i = Instrument.objects.get(short_name='MODIS')
        source = Source(platform=p, instrument=i)
        source.save()
        dataset = Dataset(
                    entry_title = 'Test dataset',
                    ISO_topic_category = iso_category,
                    data_center = dc,
                    summary = 'This is a quite short summary about the test' \
                                ' dataset.',
                    time_coverage_start=timezone.datetime(2010,1,1,tzinfo=timezone.utc),
                    time_coverage_end=timezone.datetime(2010,1,2,
                        tzinfo=timezone.utc),
                    source=source,
                    geolocation=geolocation)
        dataset.save()
        dl = DataLocation(protocol=DataLocation.LOCALFILE,
                          uri='URL',
                          dataset=dataset)
        dl.save()

class DatasetParameterTests(TestCase):

    pass

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


