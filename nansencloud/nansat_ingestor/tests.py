from django.test import TestCase
from django.core.management import call_command

class TestNansatIngestor(TestCase):

    def add_asar(self):
        f = '/vagrant/shared/test_data/asar/ASA_WSM_1PNPDK20081110_205618_000000922073_00401_35024_0844.N1'
        call_command('ingest_nansat', file=f)
