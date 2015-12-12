import os, glob, warnings
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
            wind_product_path = os.path.join(settings.PRODUCT_ROOT, 'sar_wind')
            wind_product_basename = os.path.basename(non_ingested_uri
                        ).split('.')[0] + '_windfield.nc'
            qp = QuadPol(non_ingested_uri, wind_direction='ncep_wind_online',
                    wind_product_path = wind_product_path,
                    wind_product_basename = wind_product_basename)

            ncFile = os.path.join(settings.PRODUCT_ROOT, 'sar_quad_pol',
                os.path.basename(uri).split('.')[0] + '.nc')
            qp.export(ncFile)
            self.stdout.write('Ingesting %s ...\n' % ncFile)
            ds, cr = Dataset.objects.get_or_create(ncFile)
            self.stdout.write('Successfully added: %s\n' % ncFile)

            ds, cr = Dataset.objects.get_or_create(os.path.join(
                wind_product_path, wind_product_basename))
            self.stdout.write('Successfully added: %s\n' %os.path.join(
                wind_product_path, wind_product_basename) )
