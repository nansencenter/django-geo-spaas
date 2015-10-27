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
from django.core.management import call_command

from nansencloud.catalog.models import Dataset
from nansencloud.hab_processing.models import Product

class Command(BaseCommand):
    args = '<file_or_folder file_or_folder ...>'
    help = 'Add file to catalog archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')

        # first add new images
        call_command('ingest_nansat', *args)

        # find datasets that don't have chlorophyll
        rawDatasets = Dataset.objects.exclude(product__short_name='chlor_a')
        for rawDataset in rawDatasets:
            p = Product.process(rawDataset)
            p.save()
            self.stdout.write('Successfully processed: %s\n' % p.location.uri)

