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

from nansencloud.utils import uris_from_args
from nansencloud.catalog.models import DatasetURI
from nansencloud.nansat_ingestor.models import Dataset

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Add file to catalog archive'

    def handle(self, *args, **kwargs):
        if len(args)==0:
            raise IOError('Please provide at least one filename')

        non_ingested_uris = DatasetURI.objects.all().get_non_ingested_uris(
                uris_from_args(*args)
            )
        for non_ingested_uri in non_ingested_uris:
            self.stdout.write('Ingesting %s ...\n' % non_ingested_uri)
            ds, cr = Dataset.objects.get_or_create(non_ingested_uri, **kwargs)
            self.stdout.write('Successfully added: %s\n' % non_ingested_uri)

