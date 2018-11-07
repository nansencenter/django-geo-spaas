import warnings
from thredds_crawler.crawl import Crawl

from django.core.management.base import BaseCommand, CommandError

from geospaas.utils.utils import validate_uri
from geospaas.nansat_ingestor.models import Dataset as NansatDataset

def crawl(url, **options):
    if not validate_uri(url):
        raise ValueError('Invalid url: %s'%url)

    if options['date']:
        select = ['(.*%s.*\.nc)' %options['date']]
        import ipdb
        ipdb.set_trace()
    elif options['filename']:
        select = ['(.*%s)' %options['filename']]
    else:
        select = None

    c = Crawl(url, select=select, skip=['.*ncml'], debug=True)
    added = 0
    for ds in c.datasets:
        url = [s.get('url') for s in ds.services if
                s.get('service').lower()=='opendap'][0]
        try:
            ds, cr = NansatDataset.objects.get_or_create(url)
        except IOError as e:
            warnings.warn(e.message)
            continue
        else:
            if cr:
                print 'Added %s, no. %d/%d'%(url, added, len(c.datasets))
                added += 1
    return added

class Command(BaseCommand):
    args = '<url> <select>'
    help = '''
        Add metadata of datasets available on thredds/opendap to archive. 
        
        Args:
            <url>: the url to the thredds server
            <select>: You can select datasets based on their THREDDS ID using
            the 'select' parameter.
            
        Example: 
            (1) Find all Sentinel-2A datasets in 2017

            url = http://nbstds.met.no/thredds/catalog/NBS/S2A/catalog.html
            select = 2017

            (2) Find a specific file

            url = http://nbstds.met.no/thredds/catalog/NBS/S2A/catalog.html
            select = S2A_MSIL1C_20170201T111301_N0204_R137_T32WNS_20170201T111255.nc
        '''
    def add_arguments(self, parser):
        parser.add_argument('url', nargs='*', type=str)
        parser.add_argument('--date',
                            action='store',
                            default='',
                            help='''Date of coverage (yyyy/mm/dd)''')
        parser.add_argument('--filename',
                            action='store',
                            default='',
                            help='''Filename of a specific dataset''')

    def handle(self, *args, **options):
        if not len(options['url'])==1:
            raise IOError('Please provide a url to the data')
        url = options.pop('url')[0]
        added = crawl(url, **options)
        self.stdout.write(
            'Successfully added metadata of %s datasets' %added)
