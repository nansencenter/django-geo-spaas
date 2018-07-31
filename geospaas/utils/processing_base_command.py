import os
import glob

from dateutil.parser import parse
from django.core.management.base import BaseCommand

from geospaas.catalog.models import Dataset, DatasetRelationship

def valid_date(s):
    ''' Test input datestring '''
    try:
        return dt.strptime(s, "%Y%m%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


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
                            default='POLYGON((-360 -90, 360 -90, 360 90, -360 90, -360 -90))',
                            help='Overlaping polygon',
                            type=str)

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
        start_date = parse(options['start'])
        stop_date = parse(options['stop'])
        polygon = options['polygon']
        mask = str(options['mask'])
        #self.limit = {0: None}.get(options['limit'], options['limit'])

        # find all input datasets
        return Dataset.objects.filter(
                time_coverage_start__gte=start_date,
                time_coverage_start__lte=stop_date,
                geographic_location__geometry__intersects=polygon,
                dataseturi__uri__contains=mask).order_by('time_coverage_start')

