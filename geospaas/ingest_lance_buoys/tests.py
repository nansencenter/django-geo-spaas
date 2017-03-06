import os

from django.test import TestCase
from django.utils.six import StringIO
from django.core.management import call_command

from geospaas.ingest_lance_buoys.models import LanceBuoy

class TestLanceBuoy(TestCase):
    fixtures = ['vocabularies', 'catalog']

    def test_add_test_file(self):
        ''' Shall open file, read data and save'''
        uri = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'test_lance_buoy.csv')
        cnt1 = LanceBuoy.objects.add_buoy_data_from_file(uri)

        cnt2 = (LanceBuoy.objects
                .filter(source__platform__short_name='BUOYS')
                .filter(data_center__short_name='NO/NPI')
                .count())
        print '\nAdded test buoys: ', cnt1, cnt2
        self.assertTrue(cnt1 > 0)
        self.assertTrue(cnt2 > 0)
        self.assertEqual(cnt1, cnt2)

class TestIngestLanceBuoyCommand(TestCase):
    fixtures = ["vocabularies", "catalog"]

    def test_ingest_lane_buoys(self):
        out = StringIO()
        uri = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'test_lance_buoy.csv')
        call_command('ingest_lance_buoys', uri, stdout=out)
