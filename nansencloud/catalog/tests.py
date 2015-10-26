import datetime

from django.test import TestCase

from django.contrib.gis.geos import Polygon

from nansencloud.catalog.models import *

class GeographicLocationTests(TestCase):
    def test_geographiclocation(self):
        ''' Shall create GeographicLocation instance '''
        geolocation = GeographicLocation(geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))),
                                type='Polygon')

class SourceTests(TestCase):
    def test_source(self):
        ''' Shall create Source instance '''
        source = Source(type='Satellite',
                        platform='AQUA',
                        instrument='MODIS')

class DatasetTests(TestCase):
    def test_dataset(self):
        ''' Shall create Dataset instance '''
        geolocation = GeographicLocation(geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))),
                                type='Polygon')
        source = Source(type='Satellite',
                        platform='AQUA',
                        instrument='MODIS')
        ds = Dataset(geolocation=geolocation, source=source,
                     time_coverage_start=datetime.datetime(2010,1,1),
                     time_coverage_end=datetime.datetime(2010,1,2))

"""
class ProtocolTests(TestCase):
    def test_protocol(self):
        ''' Shall create Protocol instance '''
        p = Protocol(protocol='FS')

class DataLocationTests(TestCase):
    def test_DataLocation(self):
        ds =
        ''' Shall create DataLocation instance '''
        dl = DataLocation(protocol=Protocol(protocol='FS'),
                          uri = URL('URL'),
                          dataset=Dataset())
"""
