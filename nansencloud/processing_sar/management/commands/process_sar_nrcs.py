import os
import numpy as np

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from nansencloud.catalog.models import Dataset, Product
from nansencloud.catalog.models import DataLocation

from nansencloud.processing_sar_nrcs.tools import *

from nansat.nansat import Domain, Nansat, Figure, NSR
from sarqp.sarqp import QuadPol

standard_name = 'surface_backwards_scattering_coefficient_of_radar_wave'

def create_product(prodHttpURI, ds, meta, units):
    location = DataLocation.objects.get_or_create(protocol='HTTP',
                    uri=prodHttpURI,
                    dataset=ds)[0]
    product = Product(
        short_name='%s_%s'%(meta['short_name'], meta['polarization']),
        standard_name=meta['standard_name'],
        long_name=meta['long_name'],
        units=units,
        location=location,
        time=ds.time_coverage_start)

    product.save()

class Command(BaseCommand):
    args = '<file_or_folder file_or_folder ...>'
    help = 'Add file to catalog archive'

    def handle(self, *args, **options):
        if len(args)>0:
            # first add new images
            call_command('ingest', *args)

        # find datasets that don't have NRCS
        rawDatasets = Dataset.objects.filter( source__instrument__type =
                'Imaging Radars'
                ).exclude( datalocation__product__standard_name = standard_name )
        for rawDataset in rawDatasets:
            num = self.process(rawDataset)
            if num>0:
                self.stdout.write('Successfully generated %d products from %s'
                        %(num,rawDataset))

        

    def process(self, ds):
        ''' Create quicklooks of all NRCS bands.

        TODO: major cleanup + move code out of nansencloud into a general SAR
        processing package
        '''
        clims = {
            'HH': [-20, 0],
            'HV': [-30, -10],
            'VV': [-20, 0],
            'VH': [-20, 0],
        }
        dsURI = ds.datalocation_set.filter(
                protocol=DataLocation.LOCALFILE)[0].uri

        qp = False
        try:
            n = QuadPol(dsURI, wind_direction='ncep_wind_online')
            qp = True
        except:
            n = Nansat(dsURI)

        # Get all NRCS bands
        s0bands = []
        pp = []
        for key, value in n.bands().iteritems():
            try:
                if value['standard_name']==standard_name:
                    s0bands.append(key)
                    pp.append(value['polarization'])
            except KeyError:
                continue

        if qp:
            for i, band in enumerate(s0bands):
                s0bands[i] = band+'_reduced'

        # Get the path of nansencloud media files
        ncloud_media_path = os.path.join(settings.MEDIA_ROOT,
                self.__module__.split('.')[0])
        if not os.path.exists(ncloud_media_path):
            os.mkdir(ncloud_media_path)

        # Get the path of nansencloud.processing_sar_nrcs media files
        proc_nrcs_media_path = os.path.join(ncloud_media_path,
                self.__module__.split('.')[1])
        if not os.path.exists(proc_nrcs_media_path):
            os.mkdir(proc_nrcs_media_path)

        # Get the path of products of the provided dataset
        prodBaseName = os.path.split(n.fileName)[-1].split('.')[0]
        products_media_path = os.path.join(proc_nrcs_media_path,
                prodBaseName)
        if not os.path.exists(products_media_path):
            os.mkdir(products_media_path)

        if qp:
            n.export(os.path.join(products_media_path, prodBaseName+'.nc'))

        lon, lat = n.get_corners()
        d = Domain(NSR(3857),
                   '-lle %f %f %f %f -tr 1000 1000' % (
                        lon.min(), lat.min(), lon.max(), lat.max()))
        n.reproject(d, eResampleAlg=1, tps=True)

        # Create png's for each band
        num_products = 0
        swathmask = n['swathmask']
        httpURIbase = os.path.join(settings.MEDIA_URL,
                    self.__module__.split('.')[0],
                    self.__module__.split('.')[1], prodBaseName)
        for band in s0bands:
            meta = n.bands()[band]
            product_filename = '%s_%s.png'%(meta['short_name'],
                    meta['polarization'])

            s0 = n[band]
            mask = np.copy(swathmask)
            mask[s0 == np.nan] = 0
            mask[s0 <= 0] = 0
            s0 = np.log10(s0)*10.

            nansatFigure(s0, mask, min, max, products_media_path,
                    product_filename)

            prodFileURI = os.path.join(products_media_path, product_filename)
            prodHttpURI = os.path.join(httpURIbase, product_filename)
            create_product(prodHttpURI, ds, meta, 'dB')
            num_products += 1

        if qp:
            print('Make PR image...')
            pname = make_PR_image(n, dir=products_media_path)
            prodFileURI = os.path.join(products_media_path, pname)
            prodHttpURI = os.path.join(httpURIbase, pname)
            create_product(prodHttpURI, ds, n.bands()['PR'], 'm/m')
            num_products += 1

            print('Make PD image...')
            pname = make_PD_image(n, dir=products_media_path)
            prodFileURI = os.path.join(products_media_path, pname)
            prodHttpURI = os.path.join(httpURIbase, pname)
            create_product(prodHttpURI, ds, n.bands()['PD'], 'm/m')
            num_products += 1

            try:
                print('Make NP image...')
                pname = make_NP_image(n, dir=products_media_path)
                prodFileURI = os.path.join(products_media_path, pname)
                prodHttpURI = os.path.join(httpURIbase, pname)
                create_product(prodHttpURI, ds, n.bands()['PD'], 'm/m')
                num_products += 1
            except Exception as e:
                print e
            print('Make CP image...')
            pname = make_NRCS_image(n, 'CP', dir=products_media_path)
            prodFileURI = os.path.join(products_media_path, pname)
            prodHttpURI = os.path.join(httpURIbase, pname)
            create_product(prodHttpURI, ds, n.bands()['PD'], 'm/m')
            num_products += 1


        return num_products
