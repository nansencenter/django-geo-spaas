import glob
from django.core.management import call_command

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    args = '<pattern>'
    help = 'Add files matching given pattern to the catalog archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide a pattern')

        fn = glob.glob(args[0])
        for f in fn:
            call_command('ingest', f)
