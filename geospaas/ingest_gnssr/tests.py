import os

from django.test import TestCase
from django.utils.six import StringIO
from django.core.management import call_command

from geospaas.ingest_gnssr.models import GNSSR

class TestGNSSR(TestCase):
    fixtures = ['vocabularies', 'catalog']

    def test_add_test_file(self):
        ''' Shall open file, read data and save'''
        uri = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'test_gnssr.xml')
        cnt1 = GNSSR.objects.add_gnssr_data_from_file(uri)

        cnt2 = (GNSSR.objects
                .filter(source__platform__short_name='GPS')
                .filter(data_center__short_name='U-SOTON/NOC')
                .count())
        print '\nAdded test gnssr: ', cnt1, cnt2
        self.assertTrue(cnt1 > 0)
        self.assertTrue(cnt2 > 0)
        self.assertEqual(cnt1, cnt2)

class TestIngestGNSSRCommand(TestCase):
    fixtures = ["vocabularies", "catalog"]

    def test_ingest_gnssr(self):
        out = StringIO()
        uri = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'test_gnssr.xml')
#       print '\n\n', uri, '\n\n'
        call_command('ingest_gnssr', uri, stdout=out)
