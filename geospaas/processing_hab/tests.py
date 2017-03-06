import datetime

from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase

class TestProcessHabCommand(TestCase):
    def test_process_hab(self):
        out = StringIO()
        f = '/vagrant/shared/test_data/obpg_l2/A2015121113500.L2_LAC.NorthNorwegianSeas.hdf'
        call_command('process_hab', f, stdout=out)
        self.assertIn('Successfully processed:', out.getvalue())
