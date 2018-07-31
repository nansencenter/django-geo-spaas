from geospaas.catalog.utils import ProcessingBaseCommand

class Command(ProcessingBaseCommand):
    help = 'Dataset statistics'

    def handle(self, *args, **options):
        # find input datasets
        inp_datasets = self.find_datasets(**options)
        print('%d datasets' % inp_datasets.count())
