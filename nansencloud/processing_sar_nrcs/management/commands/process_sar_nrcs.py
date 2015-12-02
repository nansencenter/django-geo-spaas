import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from nansencloud.catalog.models import Dataset, Product
from nansencloud.catalog.models import DataLocation

from nansat.nansat import Domain, Nansat, Figure, NSR

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
                ).exclude( datalocation__product__short_name = 'nrcs' )
        for rawDataset in rawDatasets:
            num = self.process(rawDataset)
            if num>0:
                self.stdout.write('Successfully generated %d products from %s'
                        %(num,rawDataset))

    def process(self, ds):
        ''' Create quicklooks of all NRCS bands.

        TODO: move code out of nansencloud into a general SAR processing
        package
        '''
        dsURI = ds.datalocation_set.filter(
                protocol=DataLocation.LOCALFILE)[0].uri

        n = Nansat(dsURI)
        lon, lat = n.get_corners()
        d = Domain(NSR(3857),
                   '-lle %f %f %f %f -tr 500 500' % (
                        lon.min(), lat.min(), lon.max(), lat.max()))
        n.reproject(d)

        # Get all NRCS bands
        standard_name = 'surface_backwards_scattering_coefficient_of_radar_wave'
        s0bands = []
        for key, value in n.bands().iteritems():
            try:
                if value['standard_name']==standard_name:
                    s0bands.append(key)
            except KeyError:
                continue

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

        # Create png's for each band
        num_products = 0
        for band in s0bands:
            meta = n.bands()[band]
            product_filename = '%s_%s.png'%(meta['short_name'],
                    meta['polarization'])

            prodFileURI = os.path.join(products_media_path, product_filename)
            prodHttpURI = os.path.join(settings.MEDIA_URL,
                    self.__module__.split('.')[0],
                    self.__module__.split('.')[1],
                    prodBaseName, product_filename)

            # Set logscale=True and make sure units become correct...
            logscale = True
            if logscale:
                units = 'dB'
            else:
                units = meta['units']
            n.write_figure(fileName=prodFileURI, bands=band, clim=[-20,0],
                    logscale=logscale, cmapName='gray')

            location = DataLocation.objects.get_or_create(protocol='HTTP',
                           uri=prodHttpURI,
                           dataset=ds)[0]
            product = Product(
                short_name=meta['short_name'],
                standard_name=meta['standard_name'],
                long_name=meta['long_name'],
                units=units,
                location=location,
                time=ds.time_coverage_start)

            product.save()
            num_products += 1

        return num_products
