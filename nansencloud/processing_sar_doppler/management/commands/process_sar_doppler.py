''' Processing of SAR Doppler from Norut's GSAR '''
from django.core.management.base import BaseCommand

from nansencloud.catalog.models import DatasetURI
from nansencloud.processing_sar_doppler.models import Dataset

class Command(BaseCommand):
    args = '<filename>'
    help = 'Add WS file to catalog archive and make png images for ' \
            'display in Leaflet'

    def handle(self, *args, **kwargs):
        if not len(args)==1:
            raise IOError('Please provide one filename only')

        non_ingested_uris = DatasetURI.objects.all().get_non_ingested_uris(args)
        for non_ingested_uri in non_ingested_uris:
            self.stdout.write('Ingesting %s ...\n' % non_ingested_uri)
            ds, cr = Dataset.objects.get_or_create(non_ingested_uri, **kwargs)
            self.stdout.write('Successfully added: %s\n' % non_ingested_uri)



