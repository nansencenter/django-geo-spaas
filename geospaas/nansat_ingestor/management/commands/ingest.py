from django.core.management.base import BaseCommand, CommandError

from geospaas.utils.utils import uris_from_args
from geospaas.catalog.models import DatasetURI
from geospaas.nansat_ingestor.models import Dataset

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Add file to catalog archive'
    n_points = 10

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='*', type=str)
        parser.add_argument('--nansat-option',
                            action='append',
                            help='''Option for Nansat() e.g.
                                    mapperName="sentinel1a_l1"
                                    (can be repated)''')

        parser.add_argument('--n_points',
                            action='store',
                            default=self.n_points,
                            help='''Number of points in the border''')

    def _get_args(self, *args, **options):
        """ Get arguments needed to create the Dataset
        """
        if len(options['files'])==0:
            raise IOError('Please provide at least one filename')
        n_points = int(options.get('n_points', self.n_points))

        non_ingested_uris = DatasetURI.objects.all().get_non_ingested_uris(
                uris_from_args(options['files'])
            )

        nansat_options = {}
        if options['nansat_option']:
            for opt in options['nansat_option']:
                var, val = opt.split('=')
                nansat_options[var] = val

        return non_ingested_uris, n_points, nansat_options

    def handle(self, *args, **options):
        """ Ingest one Dataset per file that has not previously been ingested
        """
        non_ingested_uris, n_points, nansat_options = self._get_args(*args, **options)

        for non_ingested_uri in non_ingested_uris:
            self.stdout.write('Ingesting %s ...\n' % non_ingested_uri)
            ds, cr = Dataset.objects.get_or_create(non_ingested_uri, n_points=n_points, **nansat_options)
            if cr:
                self.stdout.write('Successfully added: %s\n' % non_ingested_uri)
            elif type(ds) == Dataset:
                self.stdout.write('%s has been added before.\n' % non_ingested_uri)
            else:
                self.stdout.write('Could not add %s.\n' % non_ingested_uri)
