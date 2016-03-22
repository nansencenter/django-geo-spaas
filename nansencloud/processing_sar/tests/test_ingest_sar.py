from django.test import TestCase
from django.core.management import call_command
from django.utils.six import StringIO

class TestIngestQuadPolCommand(TestCase):
    def test_add_sarqp(self):
        out = StringIO()
        f = '/mnt/10.11.12.232/sat_downloads_radarsat2/fine_quad_pol/RS2_20150518_055659_0004_FQ9_HHVVHVVH_SLC_397457_3572_11374712.zip'
        call_command('ingest_sar_quad_pol', f, stdout=out)
        self.assertIn('Successfully added:', out.getvalue())

