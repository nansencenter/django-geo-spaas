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

from nansencloud.nansat_ingestor.models import DataLocation, Dataset

class Command(BaseCommand):
    args = '<file_or_folder file_or_folder ...>'
    help = 'Add file to catalog archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')

        new_uris = DataLocation.objects.all().new_uris(args)
        for new_uri in new_uris:
            ds, cr = Dataset.objects.get_or_create(new_uri)
            self.stdout.write('Successfully added: %s\n' % new_uri)

