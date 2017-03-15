#-------------------------------------------------------------------------------
# Name:
# Purpose:
#
# Author:       Morten Wergeland Hansen
# Modified:
#
# Created:
# Last modified:
# Copyright:    (c) NERSC
# License:
#-------------------------------------------------------------------------------
import os, glob, warnings
from django.core.management.base import BaseCommand, CommandError

from geospaas.utils import uris_from_args
from geospaas.catalog.models import DatasetURI
from geospaas.nansat_ingestor.models import Dataset

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Add file to catalog archive'

    def add_arguments(self, parser):
        parser.add_argument('--nansat-option',
                            action='append',
                            help='''Option for Nansat() e.g.
                                    mapperName="sentinel1a_l1"
                                    (can be repated)''')

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')

        non_ingested_uris = DatasetURI.objects.all().get_non_ingested_uris(
                uris_from_args(*args)
            )

        nansat_options = {}
        if options['nansat_option']:
            for opt in options['nansat_option']:
                var, val = opt.split('=')
                nansat_options[var] = eval(val)
        for non_ingested_uri in non_ingested_uris:
            self.stdout.write('Ingesting %s ...\n' % non_ingested_uri)
            ds, cr = Dataset.objects.get_or_create(non_ingested_uri, **nansat_options)
            self.stdout.write('Successfully added: %s\n' % non_ingested_uri)

