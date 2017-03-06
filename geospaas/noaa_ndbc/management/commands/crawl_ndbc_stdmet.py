from django.core.management.base import BaseCommand, CommandError

from geospaas.noaa_ndbc.utils import crawl

class Command(BaseCommand):
    args = '<url> <select>'
    help = '''
        Add buoy metadata to archive. 
        
        Args:
            <url>: the url to the thredds server
            <select>: You can select datasets based on their THREDDS ID using
            the 'select' parameter.
            
        Example: 
            (1) Find all NOAA NDBC standard meteorological buoys in 2009

            url = http://dods.ndbc.noaa.gov/thredds/catalog/data/stdmet/catalog.xml
            select = 2009

            (2) Find a specific file

            url = http://dods.ndbc.noaa.gov/thredds/catalog/data/stdmet/catalog.xml
            select = 0y2w3h2012.nc
        '''

    def handle(self, *args, **options):
        added = crawl(*args, **options)
        self.stdout.write(
            'Successfully added metadata of %s stdmet buouy datasets' %added)
