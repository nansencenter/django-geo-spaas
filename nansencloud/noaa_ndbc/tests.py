from django.test import TestCase
from nansencloud.noaa_ndbc.models import StandardMeteorologicalBuoy

class TestDataset(TestCase):

    fixtures = ['vocabularies', 'catalog']

    def test_getorcreate_opendap_uri(self):
        uri = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/0y2w3/0y2w3h2012.nc'
        ''' Shall open file, read metadata and save'''
        ds0, cr0 = StandardMeteorologicalBuoy.objects.get_or_create(uri)
        ds1, cr1 = StandardMeteorologicalBuoy.objects.get_or_create(uri)

        self.assertTrue(cr0)
        self.assertFalse(cr1)

# Create your tests here.
