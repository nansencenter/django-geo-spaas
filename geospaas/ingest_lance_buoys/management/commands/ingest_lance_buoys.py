from django.core.management.base import BaseCommand

from geospaas.utils import uris_from_args
from geospaas.ingest_lance_buoys.models import LanceBuoy

class Command(BaseCommand):
    args = '<filename> <filename> ...'
    help = 'Add buoy metadata to archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')

        uris = uris_from_args(*args)
        for uri in uris:
            LanceBuoy.objects.add_buoy_data_from_file(uri)
