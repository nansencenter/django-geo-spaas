import datetime as dt

from dateutil.parser import parse

from django.core.management.base import BaseCommand
from geospaas.catalog.models import Dataset

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Add file to catalog archive'

    def add_arguments(self, parser):
        parser.add_argument('--start',
                            action='store',
                            default='2014-01-01',
                            help='''Start date''')

        parser.add_argument('--days',
                            action='store', 
                            default='3',
                            help='''Maximum difference between images in days''')

        parser.add_argument('--overlap',
                            action='store', 
                            default='0.2',
                            help='''Minimum overlap between images''')

    def handle(self, *args, **options):
        start_date = parse(options['start'])
        max_timedelta = float(options['days']) * 60 * 60 * 24
        min_overlap = float(options['overlap'])
                
        # find all matching datasets
        s1datasets = Dataset.objects.filter(
            source__platform__short_name__startswith='SENTINEL-1',
            time_coverage_start__gte=start_date)

        # for each dataset, find pairs
        pairs = []
        for s1d in s1datasets:
            print 'Search for pairs for ', s1d.time_coverage_start
            s1dgeom = s1d.geographic_location.geometry
            s1dgeom_area = s1dgeom.area
            s1pairs = s1datasets.filter(
                time_coverage_start__gt=s1d.time_coverage_start,
                time_coverage_end__lte=s1d.time_coverage_start+dt.timedelta(seconds=max_timedelta),
                geographic_location__geometry__intersects=s1dgeom)
            
            s1pairs_data = s1pairs.values_list('geographic_location__geometry', 'dataseturi__uri')
            for s1pg, s1pu in s1pairs_data:
                if s1pg.intersection(s1dgeom).area / s1dgeom_area > min_overlap:
                    pairs += [(s1d.dataseturi_set.first().uri, s1pu)]
                    print '-> ', s1pg.intersection(s1dgeom).area / s1dgeom_area, s1pu
        
        
        #for s1pair in s1pairs:
        #    pairs += [(s1d, s1pair)]

        #for p in pairs:
        #    print p, p[0].geographic_location.geometry.intersection(p[1].geographic_location.geometry).area / p[0].geographic_location.geometry.area
        
        
