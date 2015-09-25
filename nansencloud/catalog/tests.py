from django.test import TestCase

from nansencloud.catalog.models import *

class CatalogTests(TestCase):

    def test_create_data_location(self):
        asarfile = '/vagrant/shared/test_data/asar/' \
            'ASA_WSM_1PNPDK20081110_205618_000000922073_00401_35024_0844.N1'
        dl = DataLocation(file = asarfile)
        dl.save()
        self.assertEqual(dl.file.file.readline(),
            'PRODUCT="ASA_WSM_1PNPDK20081110_205618_000000922073_00401_35024_0844.N1"\n')
        # Test other functions and attributes
