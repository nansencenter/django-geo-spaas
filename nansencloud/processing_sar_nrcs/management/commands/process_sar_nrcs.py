from django.core.management.base import BaseCommand

class Command(BaseCommand):
    args = '<file_or_folder file_or_folder ...>'
    help = 'Add file to catalog archive'

    def handle(self, *args, **options):
        if len(args)>0:
            # first add new images
            call_command('ingest', *args)

        # find datasets that don't have NRCS
        rawDatasets = Dataset.objects.filter( source__instrument = 'MODIS'
                ).exclude( datalocation__product__short_name = 'nrcs' )
        for rawDataset in rawDatasets:
            product = self.process(rawDataset)
            if product is not None:
                self.stdout.write('Successfully processed: %s\n' % product.location.uri)


