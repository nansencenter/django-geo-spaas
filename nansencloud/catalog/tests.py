import datetime

from django.test import TestCase

from django.contrib.gis.geos import Polygon

from nansencloud.gcmd_keywords.models import Platform, Instrument
from nansencloud.catalog.models import *

class GeographicLocationTests(TestCase):
    def test_geographiclocation(self):
        ''' Shall create GeographicLocation instance '''
        geolocation = GeographicLocation(
            geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()


class SourceTests(TestCase):
    def test_source(self):
        ''' Shall create Source instance '''
        p = Platform.objects.get(short_name='AQUA')
        i = Instrument.objects.get(short_name='MODIS')
        source = Source(platform=p, instrument=i)
        source.save()


class DatasetTests(TestCase):
    def test_dataset(self):
        ''' Shall create Dataset instance '''
        geolocation = GeographicLocation(
                geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()
        p = Platform.objects.get(short_name='AQUA')
        i = Instrument.objects.get(short_name='MODIS')
        source = Source(platform=p, instrument=i)
        source.save()
        ds = Dataset(geolocation=geolocation, source=source,
                     time_coverage_start=datetime.datetime(2010,1,1),
                     time_coverage_end=datetime.datetime(2010,1,2))
        ds.save()


class DataLocationTests(TestCase):
    def test_DataLocation(self):
        ''' Shall create DataLocation instance '''
        geolocation = GeographicLocation(
                geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()
        p = Platform.objects.get(short_name='AQUA')
        i = Instrument.objects.get(short_name='MODIS')
        source = Source(platform=p, instrument=i)
        source.save()
        dataset = Dataset(geolocation=geolocation,
                            source=source,
                            time_coverage_start=datetime.datetime(2010,1,1),
                            time_coverage_end=datetime.datetime(2010,1,2))
        dataset.save()
        dl = DataLocation(protocol=DataLocation.LOCALFILE,
                          uri='URL',
                          dataset=dataset)
        dl.save()


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
                            time_coverage_start=datetime.datetime(2010,1,1),
                            time_coverage_end=datetime.datetime(2010,1,2))
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
                        time=datetime.datetime(2010,1,2))
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
                            time_coverage_start=datetime.datetime(2010,1,1),
                            time_coverage_end=datetime.datetime(2010,1,2))
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
                        time=datetime.datetime(2010,1,2))
        prod.save()

        geolocation2 = GeographicLocation(
                geometry=Polygon(((0, 1), (0, 10), (10, 10), (0, 10), (0, 1))))
        geolocation2.save()
        dataset2 = Dataset(geolocation=geolocation1,
                            source=source,
                            time_coverage_start=datetime.datetime(2015,1,1),
                            time_coverage_end=datetime.datetime(2015,1,2))
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
                            time_coverage_start=datetime.datetime(2010,1,1),
                            time_coverage_end=datetime.datetime(2010,1,2))
        child.save()
        parent = Dataset(geolocation=geolocation,
                            source=source,
                            time_coverage_start=datetime.datetime(2010,1,2),
                            time_coverage_end=datetime.datetime(2010,1,3))
        parent.save()
        dr = DatasetRelationship(child=child, parent=parent)
        dr.save()
