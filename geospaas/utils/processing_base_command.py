import os
import glob

from datetime import datetime as dt
from django.core.management.base import BaseCommand

from geospaas.catalog.models import Dataset

def valid_date(s):
    ''' Test input datestring '''
    try:
        return dt.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise TypeError(msg)


class ProcessingBaseCommand(BaseCommand):
    """ Base class for geospaas-based processing commands for initial filtering on space and time.

    Usage
    -----
    from geospaas.utils import ProcessingBaseCommand
    class SomeProcessingCommand(ProcessingBaseCommand):
        args = '<filename filename ...>'
        help = 'Run classification of texture features'

        def handle(self, *args, **options):
            # find input datasets
            inp_datasets = self.find_datasets(**options)

            # continue to filter inp_datasets
            # continue to process inp_datasets
    """
    POLYGON_STR = 'POLYGON((%f %f, %f %f, %f %f, %f %f, %f %f))'
    def add_arguments(self, parser):
        parser.add_argument('--start',
                            action='store',
                            default='1900-01-01',
                            help='Start date',
                            type=valid_date)

        parser.add_argument('--stop',
                            action='store',
                            default='2100-12-31',
                            help='Stop date',
                            type=valid_date)

        parser.add_argument('--polygon',
                            action='store',
                            default='',
                            help='Overlaping polygon',
                            type=str)

        parser.add_argument('--lonlim',
                            action='store',
                            default=[-180, 180],
                            help='Longitude limits',
                            type=float,
                            nargs=2)

        parser.add_argument('--latlim',
                            action='store',
                            default=[-90, 90],
                            help='Latitude limits',
                            type=float,
                            nargs=2)

        parser.add_argument('--mask',
                            action='store',
                            default='',
                            help='Wildcard for filtering on filenames',
                            type=str)

        parser.add_argument('--force', action='store_true',
                            help='Force processing')

        parser.add_argument('--limit',
                            action='store',
                            default=None,
                            type=int,
                            help='Number of entries to process')

    def find_datasets(self, **options):
        # get polygon from input or generate from input lonlim, latlim params
        if options['polygon'] != '':
            polygon = options['polygon']
        else:
            polygon = self.POLYGON_STR % (
                        options['lonlim'][0], options['latlim'][0],
                        options['lonlim'][1], options['latlim'][0],
                        options['lonlim'][1], options['latlim'][1],
                        options['lonlim'][0], options['latlim'][1],
                        options['lonlim'][0], options['latlim'][0])

        print(polygon)
        # find all input datasets
        return Dataset.objects.filter(
                time_coverage_start__gte=options['start'],
                time_coverage_start__lte=options['stop'],
                geographic_location__geometry__intersects=polygon,
                dataseturi__uri__contains=options['mask']).order_by('time_coverage_start')

