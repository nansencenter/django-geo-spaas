from django.utils.six import StringIO
from django.test import TestCase
from django.core.management import call_command

from geospaas.noaa_ndbc.models import StandardMeteorologicalBuoy
from geospaas.noaa_ndbc.utils import crawl

class TestDataset(TestCase):

    fixtures = ['vocabularies', 'catalog']

    def test_getorcreate_opendap_uri(self):
        uri = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/0y2w3/0y2w3h2012.nc'
        ''' Shall open file, read metadata and save'''
        ds0, cr0 = StandardMeteorologicalBuoy.objects.get_or_create(uri)
        ds1, cr1 = StandardMeteorologicalBuoy.objects.get_or_create(uri)

        self.assertTrue(cr0)
        self.assertFalse(cr1)

    ## The below tests are time consuming and therefore commented out
    #def test_crawl(self):
    #    url = 'http://dods.ndbc.noaa.gov/thredds/catalog/data/stdmet/catalog.xml'
    #    select = '18ci3h2014.nc' # thredds ID
    #    added = crawl(url, select)
    #    self.assertEqual(added, 1)


    #def test_command_crawl(self):
    #    out = StringIO()
    #    url = 'http://dods.ndbc.noaa.gov/thredds/catalog/data/stdmet/catalog.xml'
    #    select = '18ci3h2014.nc' # thredds ID
    #    call_command('crawl_ndbc_stdmet', url, select, stdout=out)
    #    self.assertIn('Successfully added:', out.getvalue())

