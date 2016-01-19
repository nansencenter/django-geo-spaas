import os, glob, warnings
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sarqp.sarqp import QuadPol
from nansencloud.ingestor.models import DataLocation, Dataset

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Add file to catalog archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')

        non_ingested_uris = DataLocation.objects.all().get_non_ingested_uris(args)
        for non_ingested_uri in non_ingested_uris:
            model_wind_path = os.path.join(settings.DOWNLOAD_ROOT, 'ncep')
            wind_product_path = os.path.join(settings.PRODUCT_ROOT, 'sar_wind')
            wind_product_basename = os.path.basename(non_ingested_uri
                        ).split('.')[0] + '_windfield.nc'

            # Process SAR data
            qp = QuadPol(non_ingested_uri, wind_direction='ncep_wind_online',
                    wind_product_path = wind_product_path,
                    wind_product_basename = wind_product_basename,
                    model_wind_path=model_wind_path)

            # Store processed SAR netCDF
            product_dir_name = 'sar_quad_pol'
            if not os.path.exists(os.path.join(settings.PRODUCT_ROOT,
                    product_dir_name)):
                os.mkdir(os.path.join(settings.PRODUCT_ROOT, product_dir_name))
            ncFile = os.path.join(settings.PRODUCT_ROOT, product_dir_name,
                os.path.basename(non_ingested_uri).split('.')[0] + '.nc')
            qp.export(ncFile)

            # Ingest model wind field
            model_wind_file = qp.get_metadata(
                    bandID='windspeed')['model_wind_file']
            self.stdout.write('Ingesting %s ...\n' % model_wind_file)
            ds, cr = Dataset.objects.get_or_create(model_wind_file)
            self.stdout.write('Successfully added: %s\n' % model_wind_file)

            # Ingest processed SAR wind netCDF
            wind_nc_file = os.path.join(wind_product_path, wind_product_basename)
            self.stdout.write('Ingesting %s ...\n' % wind_nc_file)
            ds, cr = Dataset.objects.get_or_create(wind_nc_file)
            self.stdout.write('Successfully added: %s\n' %wind_nc_file )

            # Ingest processed SAR netCDF
            self.stdout.write('Ingesting %s ...\n' % ncFile)
            ds, cr = Dataset.objects.get_or_create(ncFile)
            self.stdout.write('Successfully added: %s\n' % ncFile)


