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

import numpy as np
import matplotlib.pyplot as plt

from nansat import Nansat

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from django.conf import settings

from nansencloud.catalog.models import Dataset, DataLocation, Product


class Command(BaseCommand):
    args = '<file_or_folder file_or_folder ...>'
    help = 'Add file to catalog archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')

        # first add new images
        call_command('ingest', *args)

        # find datasets that don't have chlorophyll
        rawDatasets = Dataset.objects.filter(source__instrument='MODIS').exclude(product__short_name='chlor_a')
        for rawDataset in rawDatasets:
            product = self.process(rawDataset)
            self.stdout.write('Successfully processed: %s\n' % product.location.uri)

    def process(self, dataset):
        dsUri = dataset.datalocation_set.filter(protocol='LOCALFILE')[0].uri
        dsBasename = os.path.split(dsUri)[1]
        prodBasename = dsBasename + 'chlor_a.png'
        prodFileName = os.path.join(settings.PROCESSING_HAB['outdir'], prodBasename)
        prodUrl = os.path.join(settings.PROCESSING_HAB['outhttp'], prodBasename)

        # actual 'processing'
        print 'PROCESSSS:', dsUri
        n = Nansat(dsUri)
        l = n[3]
        plt.imsave(prodFileName, l[::10, ::10])

        location = DataLocation.objects.get_or_create(protocol='HTTP',
                           uri=prodUrl,
                           dataset=dataset)[0]

        product = Product(
            short_name='chlor_a',
            standard_name='chlorophyll_surface',
            long_name='CHLOROPHYLL',
            units='mg -1',
            dataset=dataset,
            location=location)

        product.save()

        return product
