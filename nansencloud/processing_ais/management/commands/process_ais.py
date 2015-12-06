from django.core.management.base import BaseCommand, CommandError

from nansencloud.ingestor.models import DataLocation
from nansencloud.processing_ais.models import Dataset

class Command(BaseCommand):
    args = '<ais file>'
    help = 'Add ships in daily AIS file to the database - one dataset per ship'

    def handle(self, *args, **options):
        if not len(args)==1:
            raise IOError('Please provide a filename')

        non_ingested_uris = DataLocation.objects.all().get_non_ingested_uris(args)
        for non_ingested_uri in non_ingested_uris:
            self.stdout.write('Ingesting AIS data %s...\n' % non_ingested_uri)
            ds, cr = Dataset.objects.create_from_file(non_ingested_uri)
            self.stdout.write('Successfully added: %s\n' % non_ingested_uri)

