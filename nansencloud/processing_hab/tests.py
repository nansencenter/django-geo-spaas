import datetime

from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase

from nansencloud.nansat_ingestor.models import Source, DataLocation, Dataset, GeographicLocation


class TestProcessHabCommand(TestCase):
    def test_process_hab(self):
        out = StringIO()
        f = '/vagrant/shared/test_data/meris_l1/MER_FRS_1PNPDK20120303_093810_000000333112_00180_52349_3561.N1'
        call_command('process_hab', f, stdout=out)
        self.assertIn('Successfully processed:', out.getvalue())
