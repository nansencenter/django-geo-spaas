import os, glob, warnings
from django.core.management.base import BaseCommand, CommandError

from geospaas.utils import uris_from_args
from geospaas.catalog.models import DatasetURI
from geospaas.nansat_ingestor.models import Dataset

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Add file to catalog archive'
    nPoints = 10

    def add_arguments(self, parser):
        parser.add_argument('--nansat-option',
                            action='append',
                            help='''Option for Nansat() e.g.
                                    mapperName="sentinel1a_l1"
                                    (can be repated)''')

        parser.add_argument('--nPoints',
                            action='store',
                            default=self.nPoints,
                            help='''Number of points in the border''')

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')
        nPoints = int(options.get('nPoints', self.nPoints))

        non_ingested_uris = DatasetURI.objects.all().get_non_ingested_uris(
                uris_from_args(*args)
            )

        nansat_options = {}
        count = 0
        if options['nansat_option']:
            for opt in options['nansat_option']:
                var, val = opt.split('=')
                nansat_options[var] = val
        for non_ingested_uri in non_ingested_uris:
            self.stdout.write('Ingesting %s ...\n' % non_ingested_uri)
            ds, cr = Dataset.objects.get_or_create(non_ingested_uri, nPoints=nPoints, **nansat_options)
            if cr:
                self.stdout.write('Successfully added: %s\n' % non_ingested_uri)
                count += 1
            elif type(ds)==Dataset:
                self.stdout.write('%s has been added before.\n' % non_ingested_uri)
            else:
                self.stdout.write('Could not add %s.\n' % non_ingested_uri)
