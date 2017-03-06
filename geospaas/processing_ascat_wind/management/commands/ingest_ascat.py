''' Processing of Metop ASCAT wind data '''
from django.core.management.base import BaseCommand

from geospaas.utils import uris_from_args
from geospaas.processing_ascat_wind.models import Dataset

class Command(BaseCommand):
    args = '<filename>'
    help = 'Add file to catalog archive and make png images for ' \
            'display in Leaflet'

    def handle(self, *args, **options):

        for non_ingested_uri in uris_from_args(*args):
            self.stdout.write('Ingesting %s ...\n' % non_ingested_uri)
            ds, cr = Dataset.objects.get_or_create(non_ingested_uri, **options)
            if cr:
                self.stdout.write('Successfully added: %s\n' % non_ingested_uri)
            else:
                self.stdout.write('Was already added: %s\n' % non_ingested_uri)



