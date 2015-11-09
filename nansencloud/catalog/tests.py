import datetime

from django.test import TestCase

from django.contrib.gis.geos import Polygon

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
        source = Source(type='Satellite',
                        platform='AQUA',
                        instrument='MODIS')
        source.save()


class DatasetTests(TestCase):
    def test_dataset(self):
        ''' Shall create Dataset instance '''
        geolocation = GeographicLocation(
                geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()
        source = Source(type=Source.SATELLITE,
                        platform='AQUA',
                        instrument='MODIS')
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
        source = Source(type=Source.SATELLITE,
                        platform='AQUA',
                        instrument='MODIS')
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
        source = Source(type=Source.SATELLITE,
                        platform='AQUA',
                        instrument='MODIS')
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
                        dataset=dataset,
                        location=location)
        var.save()

class DatasetRelationshipTests(TestCase):
    def test_variable(self):
        ''' Shall create DatasetRelationship instance '''
        geolocation = GeographicLocation(
                geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))))
        geolocation.save()
        source = Source(type=Source.SATELLITE,
                        platform='AQUA',
                        instrument='MODIS')
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
