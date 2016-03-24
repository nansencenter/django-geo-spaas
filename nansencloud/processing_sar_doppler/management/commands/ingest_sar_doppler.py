''' Processing of SAR Doppler from Norut's GSAR '''
from django.core.management.base import BaseCommand

from nansencloud.utils import uris_from_args
from nansencloud.catalog.models import DatasetURI
from nansencloud.processing_sar_doppler.models import Dataset

class Command(BaseCommand):
    args = '<filename>'
    help = 'Add WS file to catalog archive and make png images for ' \
            'display in Leaflet'

    def handle(self, *args, **kwargs):
        #if not len(args)==1:
        #    raise IOError('Please provide one filename only')

        for non_ingested_uri in uris_from_args(*args):
            self.stdout.write('Ingesting %s ...\n' % non_ingested_uri)
            ds, cr = Dataset.objects.get_or_create(non_ingested_uri, **kwargs)
            self.stdout.write('Successfully added: %s\n' % non_ingested_uri)



