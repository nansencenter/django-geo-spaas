import os
import numpy as np
import matplotlib.pyplot as plt

from django.db import models
from django.core.exceptions import ValidationError

from django.contrib.gis.geos import WKTReader

from nansat import Nansat

from nansencloud.catalog.models import DataLocation
from nansencloud.catalog.models import Product as CatalogProduct

class Product(CatalogProduct):
    class Meta:
        proxy = True

    @classmethod
    def process(cls, dataset):
        ''' Run HAB processing '''
        # TODO: read outdir from settings.hab_config
        outdir = '/vagrant/shared/develop_vm'
        outhttp = 'http://maires.nerc.no'
        dsUri = dataset.datalocation_set.filter(protocol='LOCALFILE')[0].uri
        dsBasename = os.path.split(dsUri)[1]
        prodBasename = dsBasename + 'chlor_a.png'
        prodFileName = os.path.join(outdir, prodBasename)
        prodUrl = os.path.join(outhttp, prodBasename)

        # actual 'processing'
        print 'PROCESSSS:', dsUri
        n = Nansat(dsUri)
        l = n['L_413']
        plt.imsave(prodFileName, l[::10, ::10])

        location = DataLocation.objects.get_or_create(protocol='LOCALFILE',
                           uri=prodUrl,
                           dataset=dataset)[0]

        return CatalogProduct(
            short_name='chlor_a',
            standard_name='chlorophyll_surface',
            long_name='CHLOROPHYLL',
            units='mg -1',
            dataset=dataset,
            location=location)
