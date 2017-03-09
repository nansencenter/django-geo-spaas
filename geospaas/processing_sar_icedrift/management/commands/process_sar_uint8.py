import os

import datetime as dt

from dateutil.parser import parse

import numpy as np

from django.conf import settings
from django.core.management.base import BaseCommand
from geospaas.catalog.models import Dataset

from geospaas.nansat_ingestor.management.commands.ingest import Command as NansatIngestCommand

from nansat import Nansat

from sea_ice_drift.lib import get_uint8_image

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Add file to catalog archive'

    band_name = 'sigma0_HV'
    vmin = -28
    vmax = -14
    factor = 0.5
    product_path = os.path.join(settings.PRODUCTS_ROOT,
                                'geospaas_processing_sar_icedrift')

    def add_arguments(self, parser):
        parser.add_argument('--start',
                            action='store',
                            default='2017-01-01',
                            help='''Start date''')

        parser.add_argument('--mask',
                            action='store',
                            default='EW_GRDM_1SDH_',
                            help='''Start date''')


    def handle(self, *args, **options):
        start_date = parse(options['start'])
        mask = str(options['mask'])

        if not os.path.exists(self.product_path):
            os.makedirs(self.product_path)

        # find all input datasets
        datasets = (Dataset.objects
            .filter(
                source__instrument__short_name__contains='SAR',
                time_coverage_start__gte=start_date,
                dataseturi__uri__contains=mask)
            .exclude(entry_title='SAR_UINT8'))

        # find uint8 datasets
        uint8datasets = Dataset.objects.filter(
            source__instrument__short_name__contains='SAR',
            time_coverage_start__gte=start_date,
            entry_title='SAR_UINT8')
        uint8filenames = [os.path.basename(uri[0]) for uri in uint8datasets.values_list('dataseturi__uri')]

        # for each input dataset, process if not yet
        for ds in datasets:
            ds_uri = ds.dataseturi_set.first().uri
            if os.path.basename(ds_uri)+'.tif' not in uint8filenames:
                print 'Generate SAR_UINT8', ds.time_coverage_start
                uint8filename = self.create_uint8_file(ds_uri)
                NansatIngestCommand().handle(uint8filename, nansat_option=None)

    def create_uint8_file(self, uri):
        ''' Create a GeoTiff with one uint8 band (sigma0_HV), 80 m resolution'''
        filename = uri.replace('file://localhost', '')
        n = Nansat(filename)
        n.resize(self.factor)
        array = get_uint8_image(10*np.log10(n[self.band_name]), self.vmin, self.vmax)
        n1 = Nansat(domain=n,
                    array=array,
                    parameters={'name': 'sigma0_HV',
                                'standard_name': 'surface_backwards_scattering_coefficient_of_radar_wave'})
        ofilename = os.path.join(self.product_path,
                                 os.path.basename(filename)+'.tif')
        n1.set_metadata({'Data Center': 'NERSC',
                         'Entry Title': 'SAR_UINT8'})
        n1.export(ofilename, driver='GTiff')
        return ofilename
        
