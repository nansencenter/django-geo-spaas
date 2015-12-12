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
            qp = QuadPol(non_ingested_uri, wind_direction='ncep_wind_online')

            ## TODO: ingest model wind field as well
            #qp = QuadPol(non_ingested_uri)
            #auxwind = 'ncep_wind_online' + \
            #        datetime.strftime(self.start_time, ':%Y%m%d%H%M')
            #mw = Nansat(auxwind)
            #ds, cr = Dataset.objects.get_or_create(mw.fileName)
            #qp.set_wind(auxwind)
            #qp.set_non_polarized()

            ncFile = os.path.join(os.path.dirname(uri),
                os.path.basename(uri).split('.')[0] + '.nc')
            qp.export(ncFile)
            self.stdout.write('Ingesting %s ...\n' % ncFile)
            ds, cr = Dataset.objects.get_or_create(ncFile)
            self.stdout.write('Successfully added: %s\n' % ncFile)
