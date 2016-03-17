from django.test import TestCase
from django.core.management import call_command
from django.utils.six import StringIO

class TestProcessingSARDoppler(TestCase):

    fixtures = ["vocabularies"]

    def test_process_sar_doppler(self):
        out = StringIO()
        f = 'file://localhost/mnt/10.11.12.232/sat_downloads_asar/level-0/' \
                'gsar_rvl/RVL_ASA_WS_20091116195940116.gsar'
        wf = 'file://localhost/mnt/10.11.12.232/sat_auxdata/model/ncep/gfs/' \
                'gfs20091116/gfs.t18z.master.grbf03'
        call_command('ingest', wf, stdout=out)
        call_command('process_sar_doppler', f, stdout=out)
        self.assertIn('Successfully added:', out.getvalue())


