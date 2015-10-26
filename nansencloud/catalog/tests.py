from django.test import TestCase

from django.contrib.gis.geos import Polygon

from nansencloud.catalog.models import *

class FeatureTypeTests(TestCase):
    def test_featuretype(self):
        ft = FeatureType(wkt='Polygon')

class GeographicLocationTests(TestCase):
    def test_geographiclocation(self):
        gl = GeographicLocation(geometry=Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))),
                                feature_type=FeatureType(wkt='Polygon'))
