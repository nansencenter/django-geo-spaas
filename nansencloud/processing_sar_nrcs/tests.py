import datetime

from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase

class TestProcessSarNrcsCommand(TestCase):
    def test_process_hab(self):
        out = StringIO()
        f = '/vagrant/shared/test_data/asar/ASA_WSM_1PNPDK20081110_205618_000000922073_00401_35024_0844.N1'
        call_command('process_sar_nrcs', f, stdout=out)
        self.assertIn('Successfully processed:', out.getvalue())
        f = '/vagrant/shared/test_data/sentinel1a_l1/S1A_EW_GRDM_1SDH_20150702T172954_20150702T173054_006635_008DA5_55D1.zip'
        call_command('process_sar_nrcs', f, stdout=out)
        self.assertIn('Successfully processed:', out.getvalue())
