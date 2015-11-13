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
from nansencloud.processing_hab.tools.modis_l2_image import ModisL2Image

class Command(BaseCommand):
    args = '<file_or_folder file_or_folder ...>'
    help = 'Add file to catalog archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')

        # first add new images
        call_command('ingest', *args)

        # find datasets that don't have chlorophyll
        rawDatasets = Dataset.objects.filter( source__instrument = 'MODIS'
                ).exclude( datalocation__product__short_name = 'chlor_a' )
        for rawDataset in rawDatasets:
            product = self.process(rawDataset)
            if product is not None:
                self.stdout.write('Successfully processed: %s\n' % product.location.uri)

    def process(self, dataset):
        ''' L2 processing for HAB '''
        product = None
        dsUri = dataset.datalocation_set.filter(protocol='LOCALFILE')[0].uri

        # run processing
        mi = ModisL2Image(dsUri)
        productMetadata = mi.process_std(settings.PROCESSING_HAB)

        # add generated products
        for productMetadatum in productMetadata:
            prodBaseName = os.path.split(productMetadatum['uri'])[1]
            prodHttpUri = os.path.join(settings.PROCESSING_HAB['http_address'],
                                        prodBaseName)
            location = DataLocation.objects.get_or_create(protocol='HTTP',
                           uri=prodHttpUri,
                           dataset=dataset)[0]

            product = Product(
                short_name=productMetadatum['short_name'],
                standard_name=productMetadatum['standard_name'],
                long_name=productMetadatum['long_name'],
                units=productMetadatum['units'],
                location=location,
                time=dataset.time_coverage_start)

            product.save()

        return product
