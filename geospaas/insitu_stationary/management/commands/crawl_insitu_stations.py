import pythesint as pti

from thredds_crawler.crawl import Crawl

from django.core.management.base import BaseCommand, CommandError

from geospaas.utils.utils import validate_uri
from geospaas.insitu_stationary.models import InsituStationary

def crawl(url, **options):
    validate_uri(url)

    skips = Crawl.SKIPS + ['.*ncml']
    c = Crawl(url, skip=skips, debug=True)
    added = 0
    for ds in c.datasets:
        url = [s.get('url') for s in ds.services if
                s.get('service').lower()=='opendap'][0]

        # Get platform and instrument
        pp = pti.get_gcmd_platform('meteorological stations')
        ii = pti.get_gcmd_instrument('in situ/laboratory instruments')
        if options['platform']:
            pp = pti.get_gcmd_platform(options['platform'])
        if options['instrument']:
            ii = pti.get_gcmd_instrument(options['instrument'])

        if pp and ii:
            metno_obs_stat, cr = InsituStationary.objects.get_or_create(url, platform=pp, instrument=ii)
        else:
            metno_obs_stat, cr = InsituStationary.objects.get_or_create(url)
        if cr:
            added += 1
            print('Added %s, no. %d/%d'%(url, added, len(c.datasets)))
    return added

class Command(BaseCommand):
    args = '<url> <select>'
    help = """
        Add observation station metadata to the archive. Note that the default GCMD platform is
        'meteorological station', and the default GCMD instrument is 'in situ/laboratory
        instruments'. These can be changed by specifying the --platform and --instrument optional
        arguments.
        
        Args:
            <url>: the url to the thredds server
            --platform <platform>: GCMD platform
            --instrument <instrument>: GCMD instrument

        """
    def add_arguments(self, parser):
        parser.add_argument('url', nargs='*', type=str)
        parser.add_argument('--platform',
                            action='store',
                            default='',
                            help='''GCMD platform''')
        parser.add_argument('--instrument',
                            action='store',
                            default='',
                            help='''GCMD instrument''')

    def handle(self, *args, **options):
        if not len(options['url'])==1:
            raise IOError('Please provide a url to the data')
        url = options.pop('url')[0]
        added = crawl(url, **options)
        self.stdout.write(
            'Successfully added metadata of %s observation station datasets' %added)

