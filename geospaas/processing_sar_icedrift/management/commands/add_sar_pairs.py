import os

import datetime as dt

from dateutil.parser import parse

from django.conf import settings
from django.core.management.base import BaseCommand
from geospaas.catalog.models import Dataset

from geospaas.processing_sar_icedrift.models import SARPair

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Add file to catalog archive'

    product_path = os.path.join(settings.PRODUCTS_ROOT,
                                'geospaas_processing_sar_icedrift',
                                'pairs')

    def add_arguments(self, parser):
        parser.add_argument('--start',
                            action='store',
                            default='2017-01-01',
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

        if not os.path.exists(self.product_path):
            os.makedirs(self.product_path)

        # find all matching datasets in UINT8 format
        datasets = (Dataset.objects
            .filter(entry_title='SAR_UINT8',
                    time_coverage_start__gte=start_date)
            .order_by('time_coverage_start'))

        # for each dataset, find pairs
        for ds in datasets:
            print 'Search for pairs for ', ds.time_coverage_start
            ds_geom = ds.geographic_location.geometry
            ds_geom_area = ds_geom.area
            ds_pairs = datasets.filter(
                time_coverage_start__gt=ds.time_coverage_start,
                time_coverage_end__lte=ds.time_coverage_start+dt.timedelta(seconds=max_timedelta),
                geographic_location__geometry__intersects=ds_geom)
            
            # find pair where intersection above threshold
            ds_pairs_data = ds_pairs.values_list('geographic_location__geometry', 'dataseturi__uri')
            for ds_pg, ds_pu in ds_pairs_data:
                intersecttion = ds_pg.intersection(ds_geom)
                if intersecttion.area / ds_geom_area > min_overlap:
                    SARPair.objects.get_or_create(ds.dataseturi_set.first().uri,
                                                  ds_pu,
                                                  self.product_path)
